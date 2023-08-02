#!/bin/bash
docker login -u AWS -p $(aws ecr get-login-password --region us-east-1) 204206184567.dkr.ecr.us-east-1.amazonaws.com
docker tag clip_inference:latest 204206184567.dkr.ecr.us-east-1.amazonaws.com/clip_inference:latest
docker push 204206184567.dkr.ecr.us-east-1.amazonaws.com/clip_inference:latest