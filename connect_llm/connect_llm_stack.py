from aws_cdk import (Stack)
from constructs import Construct
from lambdas import Lambdas
from databases import Tables

class ConnectLlmStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)


        Tb = Tables(self, 'Tb')
        Fn  = Lambdas(self,'Fn')
        Fn.fulfillment.add_environment("TABLE_NAME", Tb.conversationHistory.table_name)
        Tb.conversationHistory.grant_read_write_data(Fn.fulfillment)
        
