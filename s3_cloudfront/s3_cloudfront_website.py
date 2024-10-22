from constructs import Construct
from aws_cdk import ( 
    aws_s3_deployment as s3deploy,
    aws_s3 as s3, RemovalPolicy)


class S3Deploy(Construct):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        
        self.bucket = s3.Bucket(self, "Bucket",access_control=s3.BucketAccessControl.PRIVATE, removal_policy=RemovalPolicy.RETAIN)
    

    def deploy(self, id,  files_loc, prefix):
        deployment = s3deploy.BucketDeployment(self, id,
            sources=[s3deploy.Source.asset(files_loc)],
            destination_bucket = self.bucket,
            retain_on_delete=False,
            destination_key_prefix=prefix
        )
        return deployment






