import json
import boto3
import time
import logging
import random
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)


dynamodb = boto3.resource('dynamodb')
table_p = dynamodb.Table('passcodes')
table_v = dynamodb.Table('visitors')

s3 = boto3.resource('s3')
s3_client = boto3.client('s3')
bucket1='gate-known-faces-bucket'
bucket2 = '2020-cc-smart-door'
sns = boto3.client("sns", region_name="us-west-2")

rekognition=boto3.client('rekognition')
collection_id='gateCollection'



def lambda_handler(event, context):
    name, phone, img = get_info_from_owner_request(event)
    if None in [name,phone,img]:
        return give_failure_response_body("can not match new visitor")
    if phoneCheck(phone) is False:
        return give_failure_response_body("wrong phone number")

    img_name = save_known_img(img,name)
    faceId = add_faces_to_collection(img_name)
    if faceId is None:
        return give_failure_response_body("can not match new visitor")
    
    store_visitor_record(faceId,name,phone,img_name)
    
    passcode = generate_passcode()
  
    store_passcode_record(passcode,faceId)
  
    send_message(phone,passcode)
    
    delete_unknown_img(img)
    
    return give_success_response_body("new visitor updated, we have sent the passcode to the phone:{}".format(phone))



def phoneCheck(phone):
    phone = phone.replace('-', '')
    if len(phone) != 10:
        return False
    for i in phone:
        if not i.isalnum():
            return False
    return 


def get_info_from_owner_request(event):
    body = event
    if "messages" not in body:
        return None,None,None
    messages = event["messages"]
    if not isinstance(messages,list) or len(messages) < 1:
        logger.error("no message")
        return None,None,None
    message = messages[0]
    if "unconstructed" not in message:
        logger.error("message missing unconstructed")
        return None,None,None
    if "name" not in message["unconstructed"]: 
        logger.error("message missing name")
        return None,None,None
    if "phone" not in message["unconstructed"]: 
        logger.error("message missing phone")
        return None,None,None
    if "img" not in message["unconstructed"]: 
        logger.error("message missing img")
        return None,None,None
    name = message["unconstructed"]["name"]
    phone = message["unconstructed"]["phone"]
    img = message["unconstructed"]["img"]
    
    img = img.split('/')[-1]
    return name, phone, img


def save_known_img(img,name):
    img_str = name + ".jpg"
    
    s3_client.download_file(bucket2, img, '/tmp/visitor.jpg')
    try:
        response = s3_client.upload_file('/tmp/visitor.jpg', bucket1, img_str, ExtraArgs={'ACL':'public-read'})
    except ClientError as e:
        logging.error(e)
  
    return img_str

def delete_unknown_img(img):
    s3.Object(bucket2, img).delete()
    

def add_faces_to_collection(photo):
    
    response=rekognition.index_faces(CollectionId=collection_id,
                                Image={'S3Object':{'Bucket':bucket1,'Name':photo}},
                                ExternalImageId=photo,
                                MaxFaces=1,
                                QualityFilter="AUTO",
                                DetectionAttributes=['ALL'])

                            
    for faceRecord in response['FaceRecords']:
         logger.info('  Face ID: ' + faceRecord['Face']['FaceId'] + '  Location: {}'.format(faceRecord['Face']['BoundingBox']))
    
    faceId = response['FaceRecords'][0]['Face']['FaceId']
    return faceId
    
def store_visitor_record(faceId,name,phone,img_str):
    named_tuple = time.localtime() 
    time_string = time.strftime("%m-%d-%YT%H:%M:%S", named_tuple)
    table_v.put_item(
        Item={
            "faceId": faceId,
            "name": name,
            "phoneNumber": phone,
            "photos": [
                {
                 "bucket": bucket1,
                 "createdTimeStamp": time_string,
                 "objectKey": img_str
                }
            ]
        }
    )

def generate_passcode():
    PIN = ""
    for i in range(6):
        PIN = PIN + str(random.randint(0,9))
    passcode = PIN
    return passcode


def store_passcode_record(passcode,faceId):
    expiration_time = int(time.time() + 300)
    # print(type(expiration_time))
    table_p.put_item(
        Item={
            "passcode":passcode,
            "faceId": faceId,
            "expirationTime": expiration_time
        }
    )


def send_message(phone,passcode):
    txt = "hi, your passcode is:" + str(passcode) + "\nPlease use this url to get into the door\n"+"http://gate-door-visitors.s3-website-us-east-1.amazonaws.com"
    sns.publish(
        PhoneNumber= "1" + str(phone),
        Message=txt
    )


def give_success_response_body(visitor):
    text = ""
    body = {
        "messages":[
            {
                "type":"successresponce",
                "unconstructed":{
                    "valid": True,
                    "text": text,
                    "time":time.time()
                }
            }]
    }
    
    return {
        'statusCode': 200,
        'headers' : {
            "Access-Control-Allow-Origin" : "*"
        },
        'body': body
    }

def give_failure_response_body(text):
    
    body = {
        "messages":[
            {
                "type":"failure responce",
                "unconstructed":{
                    "valid": False,
                    "text": text,
                    "time":time.time()
                }
            }]
    }
    
    return {
        'statusCode': 200,
        'headers' : {
            "Access-Control-Allow-Origin" : "*"
        },
        'body': body
    }