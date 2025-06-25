#!/usr/bin/env python3
"""
Deploy Glue Jobs Script

This script uploads Glue job scripts to S3 and updates job definitions.
Designed to be run from CI/CD pipeline.
"""

import argparse
import boto3
import os
import sys
import json
from pathlib import Path
from typing import Dict, List
import yaml


class GlueJobDeployer:
    def __init__(self, environment: str, aws_region: str = "us-east-1"):
        self.environment = environment
        self.aws_region = aws_region
        self.s3_client = boto3.client('s3', region_name=aws_region)
        self.glue_client = boto3.client('glue', region_name=aws_region)
        
        # Load configuration
        self.config = self._load_config()
        
    def _load_config(self) -> Dict:
        """Load configuration from YAML files"""
        config_file = f"config/{self.environment}.yml"
        
        if not os.path.exists(config_file):
            # Fallback to tfvars for basic config
            tfvars_file = f"config/{self.environment}.tfvars"
            if os.path.exists(tfvars_file):
                return self._parse_tfvars(tfvars_file)
            else:
                raise FileNotFoundError(f"Configuration file not found: {config_file}")
        
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)
    
    def _parse_tfvars(self, tfvars_file: str) -> Dict:
        """Parse basic configuration from tfvars file"""
        config = {
            'project_name': 'etl-pipeline',
            'script_bucket': f'etl-pipeline-{self.environment}-scripts',
            'glue_jobs': {}
        }
        
        # This is a simplified parser - in production you might want to use HCL parser
        with open(tfvars_file, 'r') as f:
            for line in f:
                if 'bucket_prefix' in line and '=' in line:
                    value = line.split('=')[1].strip().strip('"')
                    config['script_bucket'] = f"{value}-scripts"
                elif 'project_name' in line and '=' in line:
                    value = line.split('=')[1].strip().strip('"')
                    config['project_name'] = value
        
        return config
    
    def upload_script_to_s3(self, local_path: str, s3_key: str) -> str:
        """Upload a script file to S3"""
        bucket_name = self.config.get('script_bucket', f'etl-pipeline-{self.environment}-scripts')
        
        try:
            print(f"Uploading {local_path} to s3://{bucket_name}/{s3_key}")
            
            with open(local_path, 'rb') as f:
                self.s3_client.put_object(
                    Bucket=bucket_name,
                    Key=s3_key,
                    Body=f,
                    ServerSideEncryption='AES256'
                )
            
            s3_url = f"s3://{bucket_name}/{s3_key}"
            print(f"Successfully uploaded to {s3_url}")
            return s3_url
            
        except Exception as e:
            print(f"Error uploading {local_path}: {str(e)}")
            raise
    
    def update_glue_job(self, job_name: str, script_location: str, job_config: Dict):
        """Update or create a Glue job"""
        full_job_name = f"{self.config.get('project_name', 'etl-pipeline')}-{self.environment}-{job_name}"
        
        job_definition = {
            'Name': full_job_name,
            'Role': job_config.get('role_arn', f"arn:aws:iam::123456789012:role/{self.config.get('project_name')}-{self.environment}-glue-role"),
            'Command': {
                'Name': 'glueetl',
                'ScriptLocation': script_location,
                'PythonVersion': '3'
            },
            'DefaultArguments': {
                '--job-language': job_config.get('job_language', 'python'),
                '--job-bookmark-option': 'job-bookmark-enable',
                '--enable-metrics': 'true',
                '--enable-continuous-cloudwatch-log': 'true',
                '--enable-spark-ui': 'true',
                '--spark-event-logs-path': f"s3://{self.config.get('script_bucket')}/spark-logs/",
                '--TempDir': f"s3://{self.config.get('script_bucket')}/temp/",
                '--DATABASE_NAME': f"{self.config.get('project_name')}_{self.environment}_database",
                '--DATA_BUCKET': f"{self.config.get('project_name')}-{self.environment}-data",
                '--PROCESSED_BUCKET': f"{self.config.get('project_name')}-{self.environment}-processed",
                '--ENVIRONMENT': self.environment
            },
            'MaxCapacity': job_config.get('max_capacity', 2),
            'Timeout': job_config.get('timeout', 60),
            'MaxRetries': job_config.get('max_retries', 1),
            'GlueVersion': '4.0'
        }
        
        # Add worker configuration if specified
        if 'worker_type' in job_config:
            job_definition['WorkerType'] = job_config['worker_type']
            job_definition['NumberOfWorkers'] = job_config.get('number_of_workers', 2)
            # Remove MaxCapacity when using WorkerType
            job_definition.pop('MaxCapacity', None)
        
        try:
            # Check if job exists
            try:
                self.glue_client.get_job(JobName=full_job_name)
                job_exists = True
            except self.glue_client.exceptions.EntityNotFoundException:
                job_exists = False
            
            if job_exists:
                print(f"Updating existing Glue job: {full_job_name}")
                response = self.glue_client.update_job(
                    JobName=full_job_name,
                    JobUpdate=job_definition
                )
            else:
                print(f"Creating new Glue job: {full_job_name}")
                response = self.glue_client.create_job(**job_definition)
            
            print(f"Successfully {'updated' if job_exists else 'created'} job: {full_job_name}")
            return response
            
        except Exception as e:
            print(f"Error updating/creating Glue job {full_job_name}: {str(e)}")
            raise
    
    def deploy_all_jobs(self):
        """Deploy all Glue jobs"""
        glue_jobs_dir = Path("glue_jobs")
        
        if not glue_jobs_dir.exists():
            print("Error: glue_jobs directory not found")
            return False
        
        jobs_deployed = 0
        
        # Define job configurations
        job_configs = {
            'extract-sales-data': {
                'script_path': 'glue_jobs/extract/extract_sales_data.py',
                'job_language': 'python',
                'max_capacity': 2 if self.environment == 'dev' else 4,
                'timeout': 60 if self.environment == 'dev' else 120,
                'max_retries': 1 if self.environment == 'dev' else 2,
                'worker_type': 'Standard',
                'number_of_workers': 2 if self.environment == 'dev' else 4
            },
            'transform-sales-data': {
                'script_path': 'glue_jobs/transform/transform_sales_data.py',
                'job_language': 'python',
                'max_capacity': 4 if self.environment == 'dev' else 8,
                'timeout': 120 if self.environment == 'dev' else 180,
                'max_retries': 2,
                'worker_type': 'Standard',
                'number_of_workers': 4 if self.environment == 'dev' else 8
            },
            'load-sales-data': {
                'script_path': 'glue_jobs/load/load_sales_data.py',
                'job_language': 'python',
                'max_capacity': 2 if self.environment == 'dev' else 4,
                'timeout': 60 if self.environment == 'dev' else 120,
                'max_retries': 1 if self.environment == 'dev' else 2,
                'worker_type': 'Standard',
                'number_of_workers': 2 if self.environment == 'dev' else 4
            }
        }
        
        for job_name, job_config in job_configs.items():
            try:
                script_path = job_config['script_path']
                
                if not os.path.exists(script_path):
                    print(f"Warning: Script file not found: {script_path}")
                    continue
                
                # Upload script to S3
                s3_key = f"{job_name.split('-')[0]}/{os.path.basename(script_path)}"
                script_location = self.upload_script_to_s3(script_path, s3_key)
                
                # Update Glue job
                self.update_glue_job(job_name, script_location, job_config)
                
                jobs_deployed += 1
                
            except Exception as e:
                print(f"Failed to deploy job {job_name}: {str(e)}")
                return False
        
        print(f"Successfully deployed {jobs_deployed} Glue jobs to {self.environment} environment")
        return True
    
    def deploy_single_job(self, job_name: str):
        """Deploy a single Glue job"""
        # Implementation for deploying single job
        pass


def main():
    parser = argparse.ArgumentParser(description='Deploy Glue jobs to AWS')
    parser.add_argument('--environment', '-e', required=True,
                       choices=['dev', 'staging', 'prod'],
                       help='Target environment')
    parser.add_argument('--region', '-r', default='us-east-1',
                       help='AWS region (default: us-east-1)')
    parser.add_argument('--job-name', '-j',
                       help='Deploy specific job only')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be deployed without making changes')
    
    args = parser.parse_args()
    
    try:
        deployer = GlueJobDeployer(args.environment, args.region)
        
        if args.dry_run:
            print(f"DRY RUN: Would deploy Glue jobs to {args.environment} environment")
            return
        
        if args.job_name:
            success = deployer.deploy_single_job(args.job_name)
        else:
            success = deployer.deploy_all_jobs()
        
        if success:
            print("\n✅ Deployment completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Deployment failed!")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Deployment failed with error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()