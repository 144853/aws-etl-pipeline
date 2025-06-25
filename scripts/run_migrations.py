#!/usr/bin/env python3
"""
Database Migration Script

This script runs database migrations against the target database.
Designed to be run from CI/CD pipeline.
"""

import argparse
import psycopg2
import boto3
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import re


class DatabaseMigrator:
    def __init__(self, environment: str, aws_region: str = "us-east-1"):
        self.environment = environment
        self.aws_region = aws_region
        self.secrets_client = boto3.client('secretsmanager', region_name=aws_region)
        self.connection = None
        
    def get_database_credentials(self) -> Dict:
        """Get database credentials from AWS Secrets Manager"""
        secret_name = f"etl-pipeline-{self.environment}-db-password"
        
        try:
            response = self.secrets_client.get_secret_value(SecretId=secret_name)
            secret_data = json.loads(response['SecretString'])
            
            return {
                'host': self._get_rds_endpoint(),
                'port': 5432,
                'database': f'etl_db_{self.environment}',
                'username': secret_data['username'],
                'password': secret_data['password']
            }
            
        except Exception as e:
            print(f"Error retrieving database credentials: {str(e)}")
            raise
    
    def _get_rds_endpoint(self) -> str:
        """Get RDS endpoint from environment or AWS"""
        # Try environment variable first
        endpoint = os.environ.get(f'RDS_ENDPOINT_{self.environment.upper()}')
        if endpoint:
            return endpoint
        
        # Fallback to standard naming convention
        return f"etl-pipeline-{self.environment}-db.cluster-xyz.{self.aws_region}.rds.amazonaws.com"
    
    def connect_to_database(self):
        """Establish database connection"""
        creds = self.get_database_credentials()
        
        try:
            self.connection = psycopg2.connect(
                host=creds['host'],
                port=creds['port'],
                database=creds['database'],
                user=creds['username'],
                password=creds['password']
            )
            self.connection.autocommit = True
            print(f"Connected to database: {creds['host']}/{creds['database']}")
            
        except Exception as e:
            print(f"Error connecting to database: {str(e)}")
            raise
    
    def get_applied_migrations(self) -> List[int]:
        """Get list of already applied migrations"""
        try:
            cursor = self.connection.cursor()
            
            # Check if migrations table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'schema_migrations'
                )
            """)
            
            table_exists = cursor.fetchone()[0]
            
            if not table_exists:
                print("Migrations table doesn't exist, will be created")
                return []
            
            # Get applied migrations
            cursor.execute("SELECT version FROM schema_migrations ORDER BY version")
            applied_migrations = [row[0] for row in cursor.fetchall()]
            
            print(f"Found {len(applied_migrations)} applied migrations: {applied_migrations}")
            return applied_migrations
            
        except Exception as e:
            print(f"Error checking applied migrations: {str(e)}")
            raise
        finally:
            if cursor:
                cursor.close()
    
    def get_pending_migrations(self) -> List[Tuple[int, str]]:
        """Get list of pending migrations"""
        migrations_dir = Path("database/migrations")
        
        if not migrations_dir.exists():
            print("No migrations directory found")
            return []
        
        # Get all migration files
        migration_files = []
        for file_path in migrations_dir.glob("*.sql"):
            # Extract version number from filename (e.g., 001_initial_schema.sql -> 1)
            match = re.match(r'(\d+)_.*\.sql', file_path.name)
            if match:
                version = int(match.group(1))
                migration_files.append((version, str(file_path)))
        
        # Sort by version
        migration_files.sort(key=lambda x: x[0])
        
        # Filter out already applied migrations
        applied_migrations = self.get_applied_migrations()
        pending_migrations = [
            (version, file_path) for version, file_path in migration_files 
            if version not in applied_migrations
        ]
        
        print(f"Found {len(pending_migrations)} pending migrations")
        return pending_migrations
    
    def run_migration(self, version: int, file_path: str) -> bool:
        """Run a single migration"""
        print(f"Running migration {version}: {os.path.basename(file_path)}")
        
        try:
            # Read migration file
            with open(file_path, 'r') as f:
                migration_sql = f.read()
            
            cursor = self.connection.cursor()
            
            # Execute migration
            cursor.execute(migration_sql)
            
            print(f"Successfully applied migration {version}")
            return True
            
        except Exception as e:
            print(f"Error running migration {version}: {str(e)}")
            # Rollback transaction
            self.connection.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
    
    def run_all_pending_migrations(self) -> bool:
        """Run all pending migrations"""
        pending_migrations = self.get_pending_migrations()
        
        if not pending_migrations:
            print("No pending migrations to run")
            return True
        
        success_count = 0
        
        for version, file_path in pending_migrations:
            if self.run_migration(version, file_path):
                success_count += 1
            else:
                print(f"Migration {version} failed, stopping")
                break
        
        if success_count == len(pending_migrations):
            print(f"\n✅ Successfully applied {success_count} migrations")
            return True
        else:
            print(f"\n❌ Applied {success_count} of {len(pending_migrations)} migrations")
            return False
    
    def validate_database_schema(self) -> bool:
        """Validate that required tables exist"""
        print("Validating database schema...")
        
        required_tables = [
            'sales_fact',
            'product_dim',
            'date_dim',
            'daily_sales_summary',
            'product_sales_summary',
            'etl_job_log',
            'schema_migrations'
        ]
        
        try:
            cursor = self.connection.cursor()
            
            for table_name in required_tables:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'sales_dw' OR table_schema = 'public'
                        AND table_name = %s
                    )
                """, (table_name,))
                
                table_exists = cursor.fetchone()[0]
                
                if table_exists:
                    print(f"✅ Table {table_name} exists")
                else:
                    print(f"❌ Table {table_name} missing")
                    return False
            
            print("✅ Database schema validation passed")
            return True
            
        except Exception as e:
            print(f"Error validating schema: {str(e)}")
            return False
        finally:
            if cursor:
                cursor.close()
    
    def create_initial_data(self):
        """Create initial reference data"""
        print("Creating initial reference data...")
        
        try:
            cursor = self.connection.cursor()
            
            # Insert sample products if none exist
            cursor.execute("SELECT COUNT(*) FROM sales_dw.product_dim")
            product_count = cursor.fetchone()[0]
            
            if product_count == 0:
                print("Inserting sample products...")
                sample_products = [
                    (1, 'Laptop Pro', 'Electronics', 'TechCorp', 'High'),
                    (2, 'Wireless Mouse', 'Electronics', 'TechCorp', 'Low'),
                    (3, 'Office Chair', 'Furniture', 'OfficeMax', 'Medium'),
                    (4, 'Standing Desk', 'Furniture', 'OfficeMax', 'High'),
                    (5, 'Coffee Mug', 'Kitchen', 'HomeGoods', 'Low')
                ]
                
                for product in sample_products:
                    cursor.execute("""
                        INSERT INTO sales_dw.product_dim 
                        (product_id, product_name, category, supplier, price_category)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (product_id) DO NOTHING
                    """, product)
                
                print(f"Inserted {len(sample_products)} sample products")
            
            print("✅ Initial data creation completed")
            
        except Exception as e:
            print(f"Error creating initial data: {str(e)}")
            raise
        finally:
            if cursor:
                cursor.close()
    
    def close_connection(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            print("Database connection closed")


def main():
    parser = argparse.ArgumentParser(description='Run database migrations')
    parser.add_argument('--environment', '-e', required=True,
                       choices=['dev', 'staging', 'prod'],
                       help='Target environment')
    parser.add_argument('--region', '-r', default='us-east-1',
                       help='AWS region (default: us-east-1)')
    parser.add_argument('--validate-only', action='store_true',
                       help='Only validate schema without running migrations')
    parser.add_argument('--create-sample-data', action='store_true',
                       help='Create initial sample data')
    
    args = parser.parse_args()
    
    migrator = None
    
    try:
        migrator = DatabaseMigrator(args.environment, args.region)
        migrator.connect_to_database()
        
        if args.validate_only:
            success = migrator.validate_database_schema()
        else:
            success = migrator.run_all_pending_migrations()
            
            if success and args.create_sample_data:
                migrator.create_initial_data()
            
            # Always validate after migrations
            if success:
                success = migrator.validate_database_schema()
        
        if success:
            print("\n✅ Database operations completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Database operations failed!")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Database operations failed with error: {str(e)}")
        sys.exit(1)
    
    finally:
        if migrator:
            migrator.close_connection()


if __name__ == "__main__":
    main()