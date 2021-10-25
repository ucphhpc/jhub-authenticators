OWNER=ucphhpc
IMAGE=jhub-authenticators
TAG=edge

.PHONY: build

all: clean build

build:
	python3 setup.py sdist bdist_wheel
	docker build -t ${OWNER}/${IMAGE}:${TAG} .

clean:
	rm -fr dist build jhub_authenticators.egg-info
	docker rmi -f ${OWNER}/${IMAGE}:${TAG}

push:
	docker push ${OWNER}/${IMAGE}:${TAG}

test:
	$(MAKE) build
	pip3 install -r tests/requirements.txt
	pytest -s -v tests/