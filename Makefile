OWNER=rasmunk
IMAGE=jhub-authenticators
TAG=edge

.PHONY: build

all: clean build

build:
	docker build -t ${OWNER}/${IMAGE}:${TAG} .

clean:
	docker rmi -f ${OWNER}/${IMAGE}:${TAG}

push:
	docker push ${OWNER}/${IMAGE}:${TAG}

test:
	$(MAKE) build
	pip3 install -r tests/requirements.txt
	pytest -s -v tests/