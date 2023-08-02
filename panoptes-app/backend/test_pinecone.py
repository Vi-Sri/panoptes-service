import pinecone
import boto3
from PIL import Image
import clip
import torch
import uuid
import os
import joblib

pinecone.init(api_key="4ccf9bfd-91b0-4ed7-8b3c-6f11c9b2fcf0", environment="us-east-1-aws")
s3 = boto3.client('s3', 
                  region_name='us-east-1', 
                  aws_access_key_id='###########', 
                  aws_secret_access_key='##########')
index = pinecone.Index("panoptes-frame-vectors-shadow")
model, preprocess = clip.load("ViT-B/32", device="cpu")
model_obj = {"model": model, "preprocess_fn": preprocess}
preprocess = model_obj['preprocess_fn']
model = model_obj['model']
response = s3.list_objects(Bucket="user-5ce111fe-7ac9-4bdc-8f47-93fe84d5ac0a")
objects = response['Contents']
print(objects)
prediction_output = {}
prediction_output["vectors"] = []
prediction_output["user_id"] = "user-5ce111fe-7ac9-4bdc-8f47-93fe84d5ac0a"
for obj in objects:
    s3.download_file("user-5ce111fe-7ac9-4bdc-8f47-93fe84d5ac0a", obj['Key'], 'temp_image.jpg')
    image = Image.open('temp_image.jpg')
    image_input = preprocess(image).unsqueeze(0).to("cpu")
    with torch.no_grad():
        image_features = model.encode_image(image_input)
    frame_id = str(uuid.uuid4())
    vector_dict = {
        'id' : frame_id,
        'values' : image_features.cpu().numpy().tolist()[0],
        'metadata': {
            'video' : 'images_10secsimple_cup_beach.mp4',
            'image_name' : obj['Key']
        }
    }
    # print(vector_dict)
    prediction_output["vectors"].append(vector_dict)

joblib.dump(prediction_output, "vector_dump.z")
index.upsert(prediction_output["vectors"], namespace=prediction_output["user_id"], show_progress=True)

query_tokens = clip.tokenize(["Cup on a table"]).to("cpu")
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