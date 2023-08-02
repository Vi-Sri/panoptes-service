FROM python:3.8-slim-buster

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    wget \
    git

RUN pip3 install --no-cache-dir \
    torch==1.7.1 \
    torchvision==0.8.2 \
    torchtext==0.8.1 \
    numpy \
    opencv-python-headless \
    pillow \
    boto3 \
    sagemaker-inference \
    retrying \
    ftfy \
    regex \
    pinecone-client

RUN pip3 install git+https://github.com/openai/CLIP.git


ENV PYTHONUNBUFFERED=TRUE
ENV PYTHONDONTWRITEBYTECODE=TRUE
ENV CUDA_VISIBLE_DEVICES=""
ENV PATH="/opt/program:${PATH}"

COPY clip_inference.py /opt/program/clip_inference.py

WORKDIR /opt/program

ENTRYPOINT ["python3", "clip_inference.py"]