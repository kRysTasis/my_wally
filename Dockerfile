# FROM python:3.9-buster
FROM nvidia/cuda:11.0.3-cudnn8-devel-ubuntu20.04

ENV PYTHONUNBUFFERED 1

RUN ln -sf /usr/share/zoneinfo/Asia/Tokyo /etc/localtime

RUN apt-get update
RUN apt-get install -y --no-install-recommends \
	net-tools \
	sudo \
	bzip2 \
	curl \
	gcc \
	git \
	vim \
	libgl1-mesa-dev \
	build-essential \
    ca-certificates \
    libopenblas-base \
    libopencv-dev \
    pandoc \
    python3-dev \
    python3-pip \
    python3-setuptools \
RUN apt-get clean

RUN python3 -m pip install --upgrade pip setuptools \
&&  pip install --no-cache-dir \
    flask \
	Cython \
	mxnet \
	# line-bot-sdk \
	requests \
	Flask-SQLAlchemy \
	psycopg2-binary \
	Flask-Migrate \
	numpy \
	onnxruntime-gpu==1.8.1 \
	Pillow \
	pypandoc==1.6.3 \
	insightface \
	opencv-python \	
	cloudinary
	# torch

COPY . .
CMD flask run -h 0.0.0.0 -p 10000