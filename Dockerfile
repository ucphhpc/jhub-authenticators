# https://github.com/tianon/docker-brew-ubuntu-core/commit/d4313e13366d24a97bd178db4450f63e221803f1
ARG BASE_IMAGE=ubuntu:bionic-20191029@sha256:6e9f67fa63b0323e9a1e587fd71c561ba48a034504fb804fd26fd8800039835d
FROM $BASE_IMAGE AS builder

USER root

RUN apt-get update && apt-get install --no-install-recommends -yq \
    build-essential \
    ca-certificates \
    locales \
    python3-dev \
    python3-pip \
    python3-pycurl \
    nodejs \
    npm \
    quota \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --upgrade setuptools pip wheel

RUN pip3 install jupyterhub==1.1.0

RUN npm install -g configurable-http-proxy

ADD jhubauthenticators /app/jhubauthenticators
ADD setup.py /app/setup.py
ADD version.py /app/version.py
ADD requirements.txt /app/requirements.txt
ADD requirements-dev.txt /app/requirements-dev.txt
ADD tests/requirements.txt /app/tests/requirements.txt


WORKDIR /app

RUN touch README.rst \
    && pip3 install .

RUN pip3 install dockerspawner

# Make sure the jupyter_config is mounted upon run
CMD ["jupyterhub", "-f", "/etc/jupyterhub/jupyterhub_config.py"]
