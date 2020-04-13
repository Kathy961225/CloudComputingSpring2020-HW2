import json
import boto3
import time
import logging
from boto3.dynamodb.conditions import Key, Attr
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


dynamodb = boto3.resource('dynamodb')
table_p = dynamodb.Table('passcodes')
table_v = dynamodb.Table('visitors')


def lambda_handler(event, context):
    logger.debug("lambda0 for visitor start")
    passcode = get_passcode_from_request(event)
    logger.debug("get opt passcode from visitor: {}".format(passcode))
    if passcode is None:
        return give_failure_response_body("sorry,we don't get your OPT, please input again")
    faceId = find_visitor(passcode)
    if faceId is None:
        return give_failure_response_body("sorry,this is a wrong OPT, please input again")
    visitor = get_visitor_info(faceId)
    if visitor is None:
        return give_failure_response_body("sorry,you are not allowed to get in by owner, permission dennied")
    else:
        return give_success_response_body(visitor)
    




def get_passcode_from_request(event):
    
    body = event
    if "messages" not in body:
        logger.error("body type error")
        return None
    messages = event["messages"]
    if not isinstance(messages,list) or len(messages) < 1:
        logger.error("messages type error or no message")
        return None
    message = messages[0]
    if "unconstructed" not in message:
        logger.error("message missing unconstructed")
        return None
    if "passcode" not in message["unconstructed"]: 
        logger.error("message missing passcode")
        return None
    passcode = message["unconstructed"]["passcode"]
    return passcode

def find_visitor(passcode):
    responce = table_p.get_item(Key={"passcode": passcode})
    if "Item" not in responce:
        return None
    faceId = responce['Item']['faceId']
    # print("hahahahahha:",faceId)
    return faceId
    
def get_visitor_info(visitor):
    responce = table_v.get_item(Key={"faceId": visitor})
    if "Item" not in responce:
        return None
    visitor = responce["Item"]
    return visitor
    
def give_success_response_body(visitor):
    text = ""
    body = {
        "messages":[
            {
                "type":"success response",
                "unconstructed":{
                    "valid": True,
                    "visitor_info":visitor,
                    "text": text,
                    "time":time.time()
                }
            }]
    }
    
    return {
        'statusCode': 200,
        'headers': {
            "Access-Control-Allow-Origin" : "*"
        },
        'body': body
    }

def give_failure_response_body(text):
    
    body = {
        "messages":[
            {
                "type":"failure response",
                "unconstructed":{
                    "valid": False,
                    "vaistor_info": None,
                    "text": text,
                    "time":time.time()
                }
            }]
    }
    
    return {
        'statusCode': 200,
        'headers': {
            "Access-Control-Allow-Origin" : "*"
        },
        'body': body
    }