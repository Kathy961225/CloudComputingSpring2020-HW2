# CloudComputingSpring2020-HW2
CloudComputingSpring2020 Homework 2

## Create Rekognition Part
```python
aws rekognition create-collection --collection-id "gateCollection"

aws rekognition create-stream-processor --name gate-StreamProcessor \
   --input '{"KinesisVideoStream":{"Arn":"arn:aws:kinesisvideo:us-east-1:102653291286:stream/KVS2/1586737676416"}}' \
   --stream-processor-output '{"KinesisDataStream":{"Arn":"arn:aws:kinesis:us-east-1:102653291286:stream/KDS2"}}' \
   --role-arn arn:aws:iam::102653291286:role/gate-rekognition \
   --settings '{"FaceSearch":{"CollectionId":"gateCollection","FaceMatchThreshold":85.5}}'

aws rekognition stop-stream-processor --name gate-StreamProcessor --region us-east-1

gst-launch-1.0 -v avfvideosrc ! videoconvert ! vtenc_h264_hw allow-frame-reordering=FALSE 
   realtime=TRUE max-keyframe-interval=45 ! kvssink name=sink stream-name="KVS2" 
   storage-size=512 access-key="AKIARPZU45MLBE7NL7M5" secret-key="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" 
   aws-region="us-east-1" osxaudiosrc ! audioconvert ! avenc_aac ! queue ! sink.
```
