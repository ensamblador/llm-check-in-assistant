import dialogstate_utils as dialog
import logging
import boto3
import json
import os

print (boto3.__version__)


bedrock_client      = boto3.client('bedrock-runtime')
dynamodb            = boto3.resource('dynamodb')

model_id            = "anthropic.claude-3-haiku-20240307-v1:0"
model_id            = "anthropic.claude-3-sonnet-20240229-v1:0"

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

system_prompt       = """
Hola. Tu eres Kiut, un agente IA de ayuda a de check-in para vuelos.

Aquí están las reglas importantes para la interacción:
- Inicia Saludando al pasajero y solicita su número de reserva y apellido. Es posible que el primer mensaje del usuario sea esta información.
- Tu objetivo principal es recopilar solo dos datos y nada más: el código o número de reserva (una secuencia de 6 caracteres que consta de 3
letras seguidas de 3 dígitos) y el apellido del pasajero.
- el numero de reserva puede ser dicho por el pasajero tal como se escucha, por ejemplo si dice: "a. b. c. uno dos cuatro." el numero de reserva es ABC124. También puede decir "a, v de vaca, c de casa, ciento veinti nueve" que es AVC129.
- Sea natural pero conciso en sus respuestas.
- Si la conversación comienza a desviarse del tema, cortésmente devuélvala al proceso de check-in.
- Al final de la conversación, confirma el numero de reserva y apellido del pasajero, cuando lo digas, el número de reserva debe estar encerrado en la etiqueta <prosody rate="medium"><say-as interpret-as="spell-out">{codigo_reserva}</say-as></prosody> (usa rate="medium" normalmente, si el cliente pide más lento puedes usar rate="slow")."""

tool_config = {
    "tools": [
        {
            "toolSpec": {
                "name": "confirm_check_in",
                "description": "Confirma el checkin del pasajero usando record locator y apellido",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "locator": {
                                "type": "string",
                                "description": "El record locator en formato ABC123 (tres letras y tres dígitos)",
                            },
                            "last_name": {
                                "type": "string",
                                "description": "El apellido del pasajero como Rodríguez, Vásquez o Garrido",
                            },
                        },
                        "required": ["locator", "last_name"],
                    }
                },
            }
        }
    ]
}


TABLE_NAME          = os.environ['TABLE_NAME']
CHECKIN_TABLE_NAME          = os.environ['CHECKIN_TABLE_NAME']


def not_meaningful(user_utterance):
    if user_utterance == '' or len(user_utterance) < 3:
        return True
    return False

def confirm_check_in(session_id,locator, last_name):
    print (f"Guardando en checkin table")
    table = dynamodb.Table(CHECKIN_TABLE_NAME)
    response  = table.put_item(Item={"sessionId": session_id, "last_name": last_name, "record_locator": locator})

    print (locator, last_name)
    print (response)
    return "check-in confirmado"



# Old version without tools
def call_llm ( user_input, messages =[]):

    # copy messages into new list
    new_messages = [m for m in messages]

    new_messages.append({"role": "user","content": [{"type":"text", "text": user_input}]})

    body=json.dumps(
        {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 100,
            "system": system_prompt,
            "messages": new_messages
        }  
    ) 
    response = bedrock_client.invoke_model( modelId=model_id,body=body)
    response_body = json.loads(response.get('body').read())
    assistant_reply = response_body.get('content')[0].get('text')
    print (f"user: {user_input}")
    print (f"assistant: {assistant_reply}")
    return assistant_reply

def call_llm_with_tools(session_id, user_input, messages =[]):
    new_messages = [m for m in messages]
    new_messages.append({"role": "user","content": [{"text": user_input}]})
    
    print (new_messages)
    
    response = bedrock_client.converse(
        modelId=model_id,
        system = [{"text": system_prompt}],
        messages=new_messages,
        toolConfig=tool_config
    )

    output_message = response['output']['message']
    new_messages.append(output_message)
    stop_reason = response['stopReason']


    if stop_reason == 'tool_use':
        # Tool use requested. Call the tool and send the result to the model.
        tool_requests = response['output']['message']['content']
        for tool_request in tool_requests:
            if 'toolUse' in tool_request:
                tool = tool_request['toolUse']
                logger.info("Requesting tool %s. Request: %s",
                            tool['name'], tool['toolUseId'])

                if tool['name'] == 'confirm_check_in':
                    tool_result = {}
                    print (tool['input'])
                    res = confirm_check_in(session_id, tool['input']['locator'], tool['input']['last_name'])
                    tool_result = {
                        "toolUseId": tool['toolUseId'],
                        "content": [{"json": {"result": res}}]
                    }
      

                    tool_result_message = {
                        "role": "user",
                        "content": [
                            {
                                "toolResult": tool_result

                            }
                        ]
                    }
                    new_messages.append(tool_result_message)

                    # Send the tool result to the model.
                    response = bedrock_client.converse(
                        modelId=model_id,
                        messages=new_messages,
                        toolConfig=tool_config
                    )
                    output_message = response['output']['message']
                    new_messages.append(output_message)

    return output_message['content'][0]['text'], new_messages


def get_item(table_name, key):
    table = dynamodb.Table(table_name)
    response  = table.get_item(Key=key)
    return response.get('Item')


def get_chat_history(sessionId):
    key = {"sessionId": sessionId}
    if sessionId:
        current_history = get_item(TABLE_NAME, key)
        if current_history:
            print("Hay Chat History")
            return current_history
    
    print ("No hay Chat History")

    messages = []

    return dict(**key,  messages= messages)


def put_chat_history(item):
    print (f"Guardando en DynamoDB: {item}")
    table = dynamodb.Table(TABLE_NAME)
    response  = table.put_item(Item=item)
    return response


def handler(intent_request):
    intent = dialog.get_intent(intent_request)
    active_contexts = dialog.get_active_contexts(intent_request)
    session_attributes = dialog.get_session_attributes(intent_request)

    user_utterance = intent_request['inputTranscript']
    if user_utterance == "" :
        return dialog.elicit_intent(
            active_contexts, session_attributes, intent, 
            [{'contentType': 'PlainText', 'content': "Hola, no entendí lo que dijiste, puedes repetir?"}])

    session_id = intent_request.get('sessionId')

    chat_history = get_chat_history(session_id)

    assistant_reply, new_messges = call_llm_with_tools(session_id, user_utterance, messages=chat_history['messages'])
    
    chat_history['messages'] = new_messges

    put_chat_history(chat_history)


    return dialog.elicit_intent(
        active_contexts, session_attributes, intent, 
        [{'contentType': 'SSML', 'content': f"<speak>{assistant_reply}</speak>" }])
