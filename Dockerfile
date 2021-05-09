ARG BASE_IMAGE=ubuntu:focal-20210416
FROM $BASE_IMAGE AS builder

USER root

RUN apt-get update && apt-get install --no-install-recommends -yq \
    ca-certificates \
    locales \
    python3-dev \
    python3-pip \
    python3-pycurl \
    npm \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

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
CMD ["jupyterhub"]
