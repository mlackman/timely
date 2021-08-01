"""An AWS Python Pulumi program"""
from typing import Union
from pathlib import Path
from contextlib import contextmanager
import os
import zipfile
import json

import pulumi
from pulumi_aws import iam, lambda_, s3

lambda_execution_policy = iam.Policy(
    'lambdaexecution',
    path='/',
    policy=json.dumps(
    {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:*"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "lambda:InvokeFunction"
            ],
            "Resource": [
                "*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:*"
            ],
            "Resource": "arn:aws:s3:::*"
        },
    ]
    })
)
lambda_execution_role = iam.Role(
    'lambda-execution-role',
    assume_role_policy=json.dumps({
		"Version": "2012-10-17",
		"Statement": [
		{
		  "Sid": "",
		  "Effect": "Allow",
		  "Principal": {
			"Service": [
			  "lambda.amazonaws.com",
			]
		  },
		  "Action": "sts:AssumeRole"
		}
	  ]
    }),
    managed_policy_arns=[lambda_execution_policy.arn]
)

code_bucket = s3.Bucket('webhook.club')

@contextmanager
def cwd(new_cwd: Union[str, Path]):
    original_cwd = os.getcwd()
    os.chdir(new_cwd)
    try:
        yield Path(new_cwd)
    finally:
        os.chdir(original_cwd)

with cwd('..') as root:
    deployment_path = Path('.deploy')
    deployment_path.mkdir(exist_ok=True);
    zip_filename = deployment_path / 'code.zip'
    with zipfile.ZipFile(zip_filename, 'w') as deployment_zip:
        with cwd('./timely/schedule'):
            deployment_zip.write(Path('./handler.py'))

    code_object = s3.BucketObject(
        'code.zip',
        bucket=code_bucket,
        source=pulumi.FileArchive(str(zip_filename.absolute()))
    )

lambdafunc = lambda_.Function(
    'test-lambda',
    role=lambda_execution_role.arn,
    runtime='python3.8',
    handler='handler.lambda_handler',
    s3_bucket=code_bucket.bucket,
    s3_key='code.zip',
)


"""
queue = sqs.Queue(
    'schedule-queue',
);
queue.arn.apply(lambda arn: print(f'queue  arn {arn}'));
"""
