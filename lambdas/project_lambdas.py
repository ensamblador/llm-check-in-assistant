import sys

from aws_cdk import (aws_lambda, Duration, aws_iam as iam)

from constructs import Construct


LAMBDA_TIMEOUT= 30

BASE_LAMBDA_CONFIG = dict (
    timeout=Duration.seconds(LAMBDA_TIMEOUT),       
    memory_size=256,
    tracing= aws_lambda.Tracing.ACTIVE)

PYTHON_LAMBDA_CONFIG = dict (runtime=aws_lambda.Runtime.PYTHON_3_8, **BASE_LAMBDA_CONFIG)



class Lambdas(Construct):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        COMMON_LAMBDA_CONF = dict(environment= {},**PYTHON_LAMBDA_CONFIG)

        self.fulfillment = aws_lambda.Function(
            self, "LexFullfillment", handler="lambda_function.lambda_handler",
            code = aws_lambda.Code.from_asset("./lambdas/code/fulfillment"), **COMMON_LAMBDA_CONF)
        
        self.fulfillment.add_to_role_policy(iam.PolicyStatement(actions=['dynamodb:*'],resources=["*"]))
        self.fulfillment.add_to_role_policy(iam.PolicyStatement(actions=['bedrock:*'],resources=["*"]))