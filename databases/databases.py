from aws_cdk import (
    RemovalPolicy,
    aws_dynamodb as ddb
)
from constructs import Construct


REMOVAL_POLICY = RemovalPolicy.RETAIN

TABLE_CONFIG = dict (removal_policy=REMOVAL_POLICY, billing_mode= ddb.BillingMode.PAY_PER_REQUEST)

class Tables(Construct):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.conversationHistory = ddb.Table(
            self, "ConversationHistory", 
            partition_key=ddb.Attribute(name="sessionId", type=ddb.AttributeType.STRING),
            **TABLE_CONFIG)

        self.checkIns = ddb.Table(
            self, "CheckIn", 
            partition_key=ddb.Attribute(name="sessionId", type=ddb.AttributeType.STRING),
            **TABLE_CONFIG)
