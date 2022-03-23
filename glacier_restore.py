#!/usr/bin/env python3

import boto3
import os
import re
import argparse

from botocore.config import Config

__version__ = '1.0.0'
__author__ = "Dmytro Prokhorenkov <liet@liet.kiev.ua>"


def s3_list_to_csv(bucket, prefix, config, verbose):
    filename = "glacier_restore_{0}_{1}.csv".format(bucket, re.sub('\/', '_', prefix))
    glacier_csv = open(filename, 'w')

    s3 = boto3.client('s3', config=config)
    paginator = s3.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=bucket, Prefix=prefix+'/')

    for page in pages:
        for obj in page['Contents']:
            if obj['StorageClass'] in ['GLACIER', 'DEEP_ARCHIVE', 'GLACIER_IR']:
                glacier_csv.write(bucket+","+obj['Key']+"\n")
            if verbose:
                print("{0} {1}".format(obj['Key'], obj['StorageClass']))

    glacier_csv.close()
    return filename


def upload_output_to_s3(bucket, filename, config):
    s3 = boto3.client('s3', config=config)
    s3.upload_file(filename, bucket, "jobs/"+filename)

    filename_info = s3.head_object(
        Bucket=bucket,
        Key="jobs/"+filename
    )

    return filename_info['ETag']


def create_glacier_task(bucket,
                        filename,
                        etag,
                        role_arn,
                        expire,
                        report_scope,
                        config):
    s3 = boto3.client('s3control', config=config)
    s3.create_job(
        AccountId=boto3.client('sts').get_caller_identity().get('Account'),
        RoleArn=role_arn,
        Priority=100,
        ConfirmationRequired=False,
        Operation={
            'S3InitiateRestoreObject': {
                'ExpirationInDays': expire,
                'GlacierJobTier': 'STANDARD'
            },
        },
        Manifest={
            'Spec': {
                'Format': 'S3BatchOperations_CSV_20180820',
                'Fields': [
                    'Bucket', 'Key'
                ]
            },
            'Location': {
                'ObjectArn': 'arn:aws:s3:::'+bucket+'/jobs/'+filename,
                'ETag': etag
            }
        },
        Report={
            'Bucket': 'arn:aws:s3:::'+bucket,
            'Format': 'Report_CSV_20180820',
            'Enabled': True,
            'Prefix': 'jobs',
            'ReportScope': report_scope
        },
    )


def parse_args():
    argp = argparse.ArgumentParser(add_help=True,
                                   description='Restore objects from S3 Glacier',
                                   epilog='{0}: v{1} by {2}'.format(os.path.basename(__file__), __version__, __author__))
    argp.add_argument('-b', '--bucket', type=str, required=True,
                      help="S3 bucket name where objects are stored")
    argp.add_argument('-p', '--prefix', type=str, required=True,
                      help="Prefix from where we  need to restore files")
    argp.add_argument('-e', '--expire', dest='expire', type=int, default=14,
                      help="Defines after what time files won't be available from S3 standard tier")
    argp.add_argument('-r', '--role', type=str, required=True,
                      help="Role ARN which will be used to restore files")
    argp.add_argument('-R', '--region', type=str, default='us-east-1',
                      help="AWS region where S3 bucket is located")
    argp.add_argument('-s', '--scope', type=str, default='AllTasks',
                      choices=['AllTasks', 'FailedTasksOnly'],
                      help="Scope of report file. Default: AllTasks")
    argp.add_argument('-c', '--cleanup', action='store_true', dest='cleanup',
                      help="Cleanup report file after job creation. Default: False")
    argp.add_argument('-g', '--glacierJobTier', type=str, default='STANDARD',
                      choices=['STANDARD', 'BULK'],
                      help="Glacier job tier. Default: STANDARD")
    argp.add_argument('-v', '--verbose', action='store_true',
                      help="Enable verbose output inside some functions")
    argp.add_argument('-d', '--dry-run', action='store_true', dest='dryrun',
                      help="Perform dry run without creating a job")
    argp.set_defaults(cleanup=False)
    argp.set_defaults(verbose=False)
    argp.set_defaults(dryrun=False)
    args = argp.parse_args()
    return args


def run_cleanup(filename, verbose):
    if verbose:
        print("Removing local copy of '{0}'".format(filename))
    os.remove(filename)


def main():
    parsed_args = parse_args()

    config = Config(
        region_name=parsed_args.region
    )

    print(parsed_args)

    filename = s3_list_to_csv(parsed_args.bucket,
                              parsed_args.prefix,
                              config,
                              parsed_args.verbose)
    etag = upload_output_to_s3(parsed_args.bucket,
                               filename,
                               config)
    if parsed_args.dryrun:
        create_glacier_task(parsed_args.bucket,
                            filename,
                            etag,
                            parsed_args.role,
                            parsed_args.expire,
                            parsed_args.scope,
                            config)
    if parsed_args.cleanup:
        run_cleanup(filename, parsed_args.verbose)


if __name__ == '__main__':
    main()
