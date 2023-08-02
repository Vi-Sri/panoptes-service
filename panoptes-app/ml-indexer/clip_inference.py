import json
import torch
import boto3
import os
import sys
import numpy as np
import clip
from PIL import Image
import pinecone
import uuid

s3 = boto3.client('s3', 
                  region_name='us-east-1', 
                  aws_access_key_id='###########', 
                  aws_secret_access_key='##########')
pinecone.init(api_key="##########", environment="us-east-1-aws")
index_name = "panoptes-frame-vectors"
index = pinecone.Index(index_name)
device = torch.device("cpu")

def model_fn(model_dir):
    model, preprocess = clip.load("ViT-B/32", device=device)
    print("Model Loaded", file=sys.stdout)
    return {"model": model, "preprocess_fn": preprocess}

def input_fn(request_body, request_content_type):
    if request_content_type == 'application/json':
        data = json.loads(request_body)
        print("Request : {data}", file=sys.stdout)
        bucket_name = data['bucket_name']
        inference_mode = data['inference_mode']
        user_id = data['user_id']
        video_name = data['video_name']
        return {'bucketName': bucket_name, 'inference_mode': inference_mode, 'user_id': user_id, 'video_name': video_name}
    else:
        raise ValueError(f"Unsupported content type: {request_content_type}")

def predict_fn(request_info, model_obj):
    bucket_name = request_info['bucket_name']
    inference_mode = request_info['inference_mode']
    user_id = request_info['user_id']
    video_name = request_info['video_name']
    preprocess = model_obj['preprocess_fn']
    model = model_obj['model']
    response = s3.list_objects(Bucket=bucket_name)
    objects = response['Contents']
    prediction_output = {}
    prediction_output["vectors"] = []
    prediction_output["user_id"] = user_id
    for obj in objects:
        s3.download_file(bucket_name, obj['Key'], 'temp_image.jpg')
        image = Image.open('temp_image.jpg')
        image_input = preprocess(image).unsqueeze(0).to(device)
        with torch.no_grad():
            image_features = model.encode_image(image_input)
        frame_id = str(uuid.uuid4())
        image_name = os.path.splitext(obj['Key'])[0]
        vector_dict = {
            'id' : frame_id,
            'values' : list(image_features.cpu().numpy()),
            'metadata': {
                'video' : video_name,
                'image_name' : image_name.split(".")[0]
            }
        }
        prediction_output["vectors"].append(vector_dict)
    return prediction_output

def output_fn(prediction_output, content_type):
    for image_name, image_vector in prediction_output.items():
        index.upsert(items={image_name: image_vector})
    return json.dumps({"statusCode" : 200, "status": "Completed", "mode" : "index", 'prediction_output' : prediction_output})