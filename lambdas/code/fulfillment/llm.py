import dialogstate_utils as dialog
import boto3
import json
import os

bedrock_client      = boto3.client('bedrock-runtime')
dynamodb            = boto3.resource('dynamodb')

model_id            = "anthropic.claude-3-haiku-20240307-v1:0"
#model_id            = "anthropic.claude-3-sonnet-20240229-v1:0"

system_prompt       = """
Hola. Tu eres Kiut, un agente IA de ayuda a de check-in para vuelos.

Aquí están las reglas importantes para la interacción:
- Saludar al pasajero y solicitarle su número de reserva y apellido. con probabilidad el primer mensaje del usuario sea esta información.
- Tu objetivo principal es recopilar solo dos datos y nada más: el localizador o número de reserva (una secuencia de 6 caracteres que consta de 3
letras seguidas de 3 dígitos) y el apellido del pasajero.
- el numero de reserva puede ser dicho por el pasajero tal como se escucha, por ejemplo
si dice: a. b. c. uno dos cuatro. el numero de reserva es ABC124.

- Sea natural pero conciso en sus respuestas.
- Si la conversación comienza a desviarse del tema, cortésmente devuélvala al proceso de check-in.
- Al final de la conversación, confirma el numero de reserva y apellido que recopilaste con el
pasajero. El numero de reserva debe estar encerrado en la etiqueta <prosody rate="medium"><say-as interpret-as="spell-out">{codigo_reserva}</say-as></prosody> (usa rate="medium" normalmente, si el cliente pide más lento puedes usar rate="slow")."""

TABLE_NAME          = os.environ['TABLE_NAME']


def not_meaningful(user_utterance):
    if user_utterance == '' or len(user_utterance) < 3:
        return True
    return False



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

    messages = [
        {"role": "user", "content": [{"type":"text", "text": "Hola"}]},
        {"role": "assistant", "content": [{"type":"text", "text": "Hola. Soy Kiut, estoy aquí para ayudarte en tu proceso de check-in. Indícame el código de reserva y apellido para comenzar."}]}
    ]

    return dict(**key,  messages= messages)


def put_chat_history(item):
    print (f"Guardando en DynamoDB: {item}")
    table = dynamodb.Table(TABLE_NAME)
    response  = table.put_item(Item=item)
    return response


def handler(intent_request):
    intent = dialog.get_intent(intent_request)
    user_utterance = intent_request['inputTranscript']
    if user_utterance == "" :
        return dialog.elicit_intent(
            active_contexts, session_attributes, intent, 
            [{'contentType': 'PlainText', 'content': "Hola, no entendí lo que dijiste, puedes repetir?"}])

    session_id = intent_request.get('sessionId')

    chat_history = get_chat_history(session_id)

    assistant_reply = call_llm(user_utterance, messages=chat_history['messages'])
    chat_history['messages'].append({"role": "user", "content": [{"type":"text", "text": user_utterance}]})
    chat_history['messages'].append({"role": "assistant", "content": [{"type":"text", "text": assistant_reply}]})
    
    active_contexts = dialog.get_active_contexts(intent_request)
    session_attributes = dialog.get_session_attributes(intent_request)

    put_chat_history(chat_history)


    return dialog.elicit_intent(
        active_contexts, session_attributes, intent, 
        [{'contentType': 'SSML', 'content': f"<speak>{assistant_reply}</speak>" }])
