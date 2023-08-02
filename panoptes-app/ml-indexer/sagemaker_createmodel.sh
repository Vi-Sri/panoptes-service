#!/bin/bash

aws sagemaker create-model \
    --model-name clip-inference \
    --primary-container Image='204206184567.dkr.ecr.us-east-1.amazonaws.com/clip_inference:latest',Mode='SingleModel' \
    --execution-role-arn arn:aws:iam::204206184567:role/service-role/AmazonSageMaker-ExecutionRole-20230530T133535

aws sagemaker create-endpoint-config \
    --endpoint-config-name clip-inference-config \
    --production-variants VariantName='default',ModelName='clip-inference',InitialInstanceCount=1,InstanceType='ml.m5.large'

aws sagemaker create-endpoint \
    --endpoint-name clip-inference-endpoint \
    --endpoint-config-name clip-inference-config