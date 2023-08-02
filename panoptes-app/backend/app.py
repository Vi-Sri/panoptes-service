from flask import Flask, request, send_from_directory, jsonify
from flask_cors import CORS
import os
import boto3
import uuid
import cv2
import tempfile
import shutil
import json
import torch
from PIL import Image
import clip
import pinecone

app = Flask(__name__, static_folder='../panoptes-ui/build')
index = pinecone.Index("panoptes-frame-vectors-shadow")
model, preprocess = clip.load("ViT-B/32", device="cpu")
model_obj = {"model": model, "preprocess_fn": preprocess}
CORS(app)

def invoke_sagemaker_endpoint(bucket_name, video_name, user_id):
    try:
        endpoint_name = "clip-inference-endpoint"
        payload = json.dumps({
            "bucket_name": 'user-1234',
            "user_id": user_id})

        sagemaker_runtime_client = boto3.client('sagemaker')
        response = sagemaker_runtime_client.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType='application/json',
            Body=payload
        )
        result = json.loads(response['Body'].read().decode())
    except:
        print("ZzzZ")
    return "Executed"

@app.route('/generate-userid', methods=['GET'])
def generate_user_id():
    user_id = str(uuid.uuid4())
    return {'success': True, 'userId': user_id}

@app.route('/create-bucket', methods=['POST'])
def create_bucket():
    user_id = request.json.get('userId')
    if not user_id:
        return {'success': False, 'message': 'User ID is required'}
    
    s3 = boto3.client('s3', 
                      region_name='us-east-1', 
                      aws_access_key_id='############', 
                      aws_secret_access_key='############')

    bucket_name = 'user-' + user_id
    s3.create_bucket(Bucket=bucket_name)
    return {'success': True, 'bucketName': bucket_name}

@app.route('/indexvideo', methods=['POST'])
def upload_file():
    s3 = boto3.client('s3', 
                      region_name='us-east-1', 
                      aws_access_key_id='###########', 
                      aws_secret_access_key='##########')
    
    file = request.files['file']
    bucket_name = request.form['bucketName']

    if file:
        try:
            temp_dir = tempfile.mkdtemp()
            file_path = os.path.join(temp_dir, file.filename)
            file.save(file_path)
            video = cv2.VideoCapture(file_path)
            frame_rate = video.get(cv2.CAP_PROP_FPS)
            frame_num = 0
            print("Frame Rate :", frame_rate)
            while True:
                ret, frame = video.read()
                if ret:
                    if frame_num % frame_rate == 0:
                        frame_file = os.path.join(temp_dir, f'frame_{frame_num:04d}.jpg')
                        cv2.imwrite(frame_file, frame)
                        with open(frame_file, 'rb') as data:
                            s3.upload_fileobj(data, bucket_name, f'images_{file.filename}/frame_{frame_num:04d}.jpg')
                    frame_num += 1
                else:
                    break
            video.release()
            shutil.rmtree(temp_dir)
            _ = invoke_sagemaker_endpoint(bucket_name, file.name, str(uuid.uuid4()))
            return {"success": True}
        except Exception as e:
            return {"success": False, "message": str(e)}

    return {"success": False, "message": "No file provided"}

@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    query = data.get('query')
    query_tokens = clip.tokenize([query]).to("cpu")

    with torch.no_grad():
        query_features = model.encode_text(query_tokens)
    query_features = query_features.cpu().numpy().tolist()[0]

    query_response = index.query(
        namespace='user-5ce111fe-7ac9-4bdc-8f47-93fe84d5ac0a',
        top_k=5,
        include_metadata=True,
        vector=query_features,
        filter={
            'video': {'$in': ['images_10secsimple_cup_beach.mp4']}
        }
    )

    print(query_response)

    timestamps = [int(id) for id in query_response.ids]
    return jsonify({"timestamps": timestamps, "status": 200})

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(port=3001)