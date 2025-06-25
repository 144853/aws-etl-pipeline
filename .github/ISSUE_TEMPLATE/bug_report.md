---
name: Bug Report
about: Create a report to help us improve the ETL pipeline
title: '[BUG] '
labels: bug
assignees: ''
---

## Bug Description

A clear and concise description of what the bug is.

## Environment

- Environment: [dev/staging/prod]
- AWS Region: [e.g., us-east-1]
- Date/Time: [when the issue occurred]
- Affected Components: [Glue jobs, RDS, S3, etc.]

## Steps to Reproduce

1. Go to '...'
2. Click on '...'
3. Scroll down to '...'
4. See error

## Expected Behavior

A clear and concise description of what you expected to happen.

## Actual Behavior

A clear and concise description of what actually happened.

## Error Messages

```
Paste any error messages, stack traces, or relevant log output here
```

## Screenshots

If applicable, add screenshots to help explain your problem:
- CloudWatch logs
- Glue job console
- Database query results
- Monitoring dashboards

## Impact Assessment

- [ ] Production data pipeline affected
- [ ] Data quality issues
- [ ] Performance degradation
- [ ] Staging environment only
- [ ] Development environment only
- [ ] Documentation issue

## Severity

- [ ] Critical (P0) - Production completely down
- [ ] High (P1) - Major functionality broken
- [ ] Medium (P2) - Minor functionality affected
- [ ] Low (P3) - Enhancement or documentation

## Additional Context

### Recent Changes
List any recent deployments, configuration changes, or code updates:

1. 
2. 
3. 

### Troubleshooting Attempted
Describe what you've already tried to fix the issue:

- [ ] Checked CloudWatch logs
- [ ] Ran health check script
- [ ] Verified AWS permissions
- [ ] Checked database connectivity
- [ ] Reviewed recent deployments
- [ ] Consulted troubleshooting guide

### Logs and Diagnostics

Please attach or paste relevant logs:

**Glue Job Logs:**
```
[Paste Glue job logs here]
```

**CloudWatch Logs:**
```
[Paste CloudWatch logs here]
```

**Database Logs:**
```
[Paste database error logs here]
```

**Health Check Output:**
```
[Paste health check script output here]
```

### System Information

- Terraform Version: [e.g., 1.5.0]
- AWS CLI Version: [e.g., 2.13.0]
- Python Version: [e.g., 3.9]
- Glue Version: [e.g., 4.0]

## Possible Solution

If you have any ideas about what might be causing the issue or how to fix it, please describe them here.

## Related Issues

Link any related issues or previous bug reports:

- #123
- #456

---

**For ETL Pipeline Team:**

### Investigation Checklist

- [ ] Reproduce the issue
- [ ] Check related AWS services status
- [ ] Review recent infrastructure changes
- [ ] Analyze error patterns in logs
- [ ] Assess data integrity impact
- [ ] Document root cause
- [ ] Implement fix
- [ ] Add monitoring/alerting if needed
- [ ] Update documentation