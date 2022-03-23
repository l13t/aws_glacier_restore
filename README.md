# AWS Glacier restore to S3 Standard Tier

## Introduction

This script allows to restore from Glacier and Deep Archive multiple files inside folder in S3 bucket.

The script generates CSV list of files located inside folder and stored in Glacier. After that it creates folder `jobs` in your S3 bucket and uploads CSV file into it. And as the last step script schedule job to perform restore of all objects listed file.

## Help output

```bash
usage: glacier_restore.py [-h] -b BUCKET -p PREFIX [-e EXPIRE] -r ROLE [-R REGION] [-s {AllTasks,FailedTasksOnly}] [-c]
                          [-g {STANDARD,BULK}] [-v] [-d]

Restore objects from S3 Glacier

optional arguments:
  -h, --help            show this help message and exit
  -b BUCKET, --bucket BUCKET
                        S3 bucket name where objects are stored
  -p PREFIX, --prefix PREFIX
                        Prefix from where we need to restore files
  -e EXPIRE, --expire EXPIRE
                        Defines after what time files won't be available from S3 standard tier
  -r ROLE, --role ROLE  Role ARN which will be used to restore files
  -R REGION, --region REGION
                        AWS region where S3 bucket is located
  -s {AllTasks,FailedTasksOnly}, --scope {AllTasks,FailedTasksOnly}
                        Scope of report file. Default: AllTasks
  -c, --cleanup         Cleanup report file after job creation. Default: False
  -g {STANDARD,BULK}, --glacierJobTier {STANDARD,BULK}
                        Glacier job tier. Default: STANDARD
  -v, --verbose         Enable verbose output inside some functions
  -d, --dry-run         Perform dry run without creating a job

glacier_restore.py: v1.0.0 by Dmytro Prokhorenkov <liet@liet.kiev.ua>
```
