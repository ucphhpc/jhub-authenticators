ARG BASE_IMAGE=debian:bookworm-slim
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

RUN npm install -g configurable-http-proxy@4.6.3

ADD jhubauthenticators /app/jhubauthenticators
ADD setup.py /app/setup.py
ADD requirements.txt /app/requirements.txt
ADD requirements-dev.txt /app/requirements-dev.txt
ADD tests/requirements.txt /app/tests/requirements.txt

WORKDIR /app

RUN pip3 install dockerspawner --break-system-packages \
    && touch README.rst \
    && pip3 install . --break-system-packages

WORKDIR /etc/jupyterhub

# Make sure the jupyter_config is mounted upon run
CMD ["jupyterhub"]
