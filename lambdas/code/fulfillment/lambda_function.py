import time
import json
import os
import boto3
import logging
import dialogstate_utils as dialog


logger = logging.getLogger()
lambda_client = boto3.client("lambda")
FULFILLMENT_ASYNC_LAMBDA = os.environ.get("FULFILLMENT_ASYNC_LAMBDA")



def lambda_handler(event, context):
    print("event: ", event)
    intent = dialog.get_intent(event)
    active_contexts = dialog.get_active_contexts(event)
    session_attributes = dialog.get_session_attributes(event)

    user_utterance = event['inputTranscript']

    if user_utterance == "" :
        return dialog.elicit_intent(
            active_contexts, session_attributes, intent, 
            [{'contentType': 'PlainText', 'content': "mmm... puedes repetir?"}])

    intent_name = intent['name']

    if intent_name in ['FallbackIntent', 'llmIntent']:
        print (f"Intent: {intent_name}")
        response = lambda_client.invoke(
            FunctionName=FULFILLMENT_ASYNC_LAMBDA, InvocationType="Event", Payload=json.dumps(event)
        )
        print(f"Invocation:{response}")
    
    return dialog.close(active_contexts, session_attributes, intent, [])
