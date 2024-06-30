from aws_cdk import (Stack)
from constructs import Construct
from lambdas import Lambdas
from databases import Tables

class ConnectLlmStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        Tb = Tables(self, 'Tb')
        Fn  = Lambdas(self,'Fn')

        
        Fn.get_response_delta.add_environment("PARTIAL_MESSAGES_TABLE", Tb.partialMessages.table_name)

        Fn.async_llm_call.add_environment("TABLE_NAME", Tb.conversationHistory.table_name)
        Fn.async_llm_call.add_environment("CHECKIN_TABLE_NAME", Tb.checkIns.table_name)
        Fn.async_llm_call.add_environment("PARTIAL_MESSAGES_TABLE", Tb.partialMessages.table_name)


        Fn.fulfillment.add_environment("FULFILLMENT_ASYNC_LAMBDA", Fn.async_llm_call.function_arn)
        Fn.async_llm_call.grant_invoke(Fn.fulfillment)

        Tb.conversationHistory.grant_read_write_data(Fn.async_llm_call)
        Tb.checkIns.grant_read_write_data(Fn.async_llm_call)
        
        Tb.partialMessages.grant_read_write_data(Fn.async_llm_call)
        Tb.partialMessages.grant_read_write_data(Fn.get_response_delta)

        
