import json
import boto3

client = boto3.client('s3')
boto_session = boto3.Session()

def create_bucket():

    try:
        region = boto_session.region_name
        account = boto3.client('sts').get_caller_identity().get('Account')
        bucket='cloudformations-'+region+'-'+account

        response = client.create_bucket(
            ACL='private',
            Bucket=bucket,
            CreateBucketConfiguration={
                'LocationConstraint': region
            },
            ObjectLockEnabledForBucket=True,
            ObjectOwnership='BucketOwnerPreferred'
            )
        print(response)

        # This will set the public block settings
        client.put_public_access_block(
            Bucket=bucket,
            PublicAccessBlockConfiguration={
                'BlockPublicAcls': True,
                'IgnorePublicAcls': True,
                'BlockPublicPolicy': True,
                'RestrictPublicBuckets': False
            }
        )

        return {
            'statusCode': 200,
            'body': json.dumps('Bucket = '+bucket+' . Successfully Created')
        }

    except Exception as e:
        print(e)

create_bucket()
