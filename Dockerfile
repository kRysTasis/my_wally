FROM python:3.9-buster

ENV PYTHONUNBUFFERED 1

RUN apt-get update
RUN apt-get install -y --no-install-recommends \
	net-tools \
	sudo \
	bzip2 \
	curl \
	gcc \
	git \
	python3-dev \
	vim
RUN apt-get clean

RUN python3 -m pip install --upgrade pip \
&&  pip install --no-cache-dir \
    flask \
    requests

COPY . .

CMD flask run -h 0.0.0.0 -p 10000