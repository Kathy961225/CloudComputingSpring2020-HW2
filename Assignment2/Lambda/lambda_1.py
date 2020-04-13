import time
import random
import logging
import base64
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
import sys
sys.path.insert(1, '/opt')
import cv2
import json
import boto3


#### Change later
dynamodb = boto3.resource('dynamodb')
table_passcodes = dynamodb.Table('passcodes')
table_visitors = dynamodb.Table('visitors')


#### Change later

s3 = boto3.resource('s3')
s3_client = boto3.client('s3')
bucket = "2020-cc-smart-door"


#### Basic Settings
owner_phone_number = "9176558190"
owner_email = "yw4002@nyu.edu"
web_url_for_visitor = "http://gate-door-visitors.s3-website-us-east-1.amazonaws.com"


def lambda_handler(event, context):
    data = decode_data(event)
    have_face, faceId = get_face(data)
    exist, name, phone = exist_visitor(have_face,faceId)
    
    if have_face:
        if exist:
            passcode = generate_passcode()
            store_passcode_record(passcode, faceId)
            txt = sns_for_visitor(passcode, name)
            send_message(phone, txt)
        else:
            phone = "9176558190"
            img_url = get_unknown_visitor_image()
            print (img_url)
            web_authorize_url = get_webpage_for_authorize(img_url)
            txt = sns_for_owner(web_authorize_url)
            send_email(owner_email, web_authorize_url)
       

def decode_data(event):
    code = event['Records'][0]['kinesis']['data']
    code_b = code.encode("UTF-8")
    data_b = base64.b64decode(code_b)
    data = data_b.decode("UTF-8")
    print (data)
    data = json.loads(data)
    return data

def get_face(data):
    face_data = data["FaceSearchResponse"]
    if len(face_data) ==0:
        return False, None
    match_faces = face_data[0]["MatchedFaces"]
    if len(match_faces) == 0:
        return True, None
    face = match_faces[0]
    faceId = face["Face"]["FaceId"]
    return True, faceId

def exist_visitor(valid, faceId):
    if not valid:
        return False, None, None
    if faceId is None:
        return False, None, None
    response = table_visitors.get_item(Key={"faceId": faceId})
    if "Item" not in response:
        return False, None, None
    visitor = response["Item"]
    return True, visitor["name"], visitor["phoneNumber"]

def generate_passcode():
    # 6 bit PIN only contains number
    PIN = ""
    for i in range(6):
        PIN = PIN + str(random.randint(0,9))
    passcode = PIN
    return passcode


def store_passcode_record(passcode, faceId):
    # expire after 5 minutes
    expire_time = int(time.time() + 300)
    print(type(expire_time))
    table_passcodes.put_item(
        Item={
            "passcode": passcode,
            "faceId": faceId,
            "expirationTime": expire_time
        }
    )


################## Send the sns to visitor or owner ##################
def sns_for_visitor(passcode, name):
    txt = "Hi " + name + ", your passcode is:" + str(passcode) + "\nPlease use the following url to get into the door!\n" + web_url_for_visitor
    return txt
def sns_for_owner(web_url):
    txt = "Hi, master. There is a visitor trying to visit you, please give the permission.\n" + web_url
    return txt

def send_message(phone, txt):
    sns = boto3.client("sns", region_name="us-west-2")
    sns.publish(
        PhoneNumber="+1" + phone,
        Message=txt
    )
    
def send_email(email, web_url):
    ses = boto3.client("ses")
    response = ses.send_email(
        Source="mw4259@nyu.edu",
        Destination={
            'ToAddresses': [
                email,
            ],
        },
        Message={
            'Subject': {
                'Data': 'SES',
                'Charset': 'UTF-8'
            },
            'Body': {
                'Text': {
                    'Data': web_url,
                    'Charset': 'UTF-8'
                },
            }
        },
    )

def get_unknown_visitor_image():
    ### Kinesisvideo
    stream_ARN = "arn:aws:kinesisvideo:us-east-1:102653291286:stream/KVS2/1586737676416"

    kvs = boto3.client("kinesisvideo")

    response = kvs.get_data_endpoint(
        StreamARN = stream_ARN,
        APIName = 'GET_MEDIA'
    )

    endpoint_url = response['DataEndpoint']

    stream_client = boto3.client(
        'kinesis-video-media', 
        endpoint_url = endpoint_url, 
    )

    kinesis_stream = stream_client.get_media(
        StreamARN=stream_ARN,
        # Identifies the fragment on the Kinesis video stream where you want to start getting the data from
        StartSelector={
            # Start with the latest chunk on the stream
            'StartSelectorType': 'NOW'
            }
    )

    with open('/tmp/stream.mkv', 'wb') as f:
        streamBody = kinesis_stream['Payload'].read(512*512)
        f.write(streamBody)
       
        cap = cv2.VideoCapture('/tmp/stream.mkv')
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('H','2','6','4'))
        ret, frame = cap.read() 
        cv2.imwrite('/tmp/frame.jpg', frame)
        img_name = "unknown.jpg" 
        s3_client.upload_file(
            '/tmp/frame.jpg',
            bucket, 
            img_name,
            ExtraArgs={'ACL':'public-read'}
        )
        cap.release()
        
    img_url = "https://" + bucket + ".s3.amazonaws.com/" + img_name
    return img_url

def get_webpage_for_authorize(img_url):
    ### Change 
    web_authorize_url = "http://gate-door-owners.s3-website-us-east-1.amazonaws.com"
    return web_authorize_url

