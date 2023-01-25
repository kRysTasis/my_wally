# FROM python:3.9-buster
FROM nvidia/cuda:11.0.3-cudnn8-devel-ubuntu20.04

ENV PYTHONUNBUFFERED 1

RUN ln -sf /usr/share/zoneinfo/Asia/Tokyo /etc/localtime

RUN apt-get update && apt-get install -y tzdata
# ENV TZ=Asia/Tokyo

RUN apt-get update
RUN apt-get install -y --no-install-recommends \
	python3.9 \
	net-tools \
	sudo \
	bzip2 \
	curl \
	gcc \
	git \
	python3-dev \
	vim \
	libgl1-mesa-dev
RUN apt-get clean

RUN python3 -m pip install --upgrade pip \
&&  pip install --no-cache-dir \
	# black \
    # jupyterlab \
    # jupyterlab_code_formatter \
    # jupyterlab-git \
    # lckr-jupyterlab-variableinspector \
    # jupyterlab_widgets \
    # ipywidgets \
    # import-ipynb \
    flask \
	line-bot-sdk \
	requests \
	Flask-SQLAlchemy \
	psycopg2-binary \
	Flask-Migrate \
	numpy \
	Pillow \
	opencv-python \	
	cloudinary \
	torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cpu \
	onnxruntime==1.13.1 \
	insightface

COPY . .

# flask db init & flask db migrate & flask db upgrade &

CMD flask run -h 0.0.0.0 -p 10000