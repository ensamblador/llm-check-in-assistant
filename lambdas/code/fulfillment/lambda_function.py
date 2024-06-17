"""
 This code sample demonstrates an implementation of the Lex Code Hook Interface
 in order to serve a bot which manages Insurance account services. Bot, Intent,
 and Slot models which are compatible with this sample can be found in the 
 Lex Console as part of the 'TelecomMobileServices' template.
"""

import time
import os
import logging
import dialogstate_utils as dialog
import llm

from datetime import datetime


logger = logging.getLogger()
#logger.setLevel(logging.DEBUG)
    
# --- Main handler & Dispatch ---

def dispatch(intent_request):
    """
    Route to the respective intent module code
    """
    #print(intent_request)
    intent = dialog.get_intent(intent_request)
    intent_name = intent['name']
    active_contexts = dialog.get_active_contexts(intent_request)
    session_attributes = dialog.get_session_attributes(intent_request)
    number_of_attempts = dialog.get_session_attribute(intent_request, 'number_of_attempts') or '0'
    if number_of_attempts: number_of_attempts = int(number_of_attempts)
    
    
    # Default dialog state is set to delegate
    # next_state = dialog.delegate(active_contexts, session_attributes, intent)
    
    # Dispatch to in-built Lex intents
    if intent_name in ['FallbackIntent', 'llmIntent']:
        next_state = llm.handler(intent_request)
    return next_state




def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    # By default, treat the user request as coming from the America/New_York time zone.
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    print('event: ', event)

    return dispatch(event)
