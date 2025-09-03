PACKAGE_NAME=jhub-authenticators
PACKAGE_NAME_FORMATTED=$(subst -,_,${PACKAGE_NAME})
OWNER=ucphhpc
IMAGE=${PACKAGE_NAME}
# Enable that the builder should use buildkit
# https://docs.docker.com/develop/develop-images/build_enhancements/
DOCKER_BUILDKIT=1
# NOTE: dynamic lookup with docker as default and fallback to podman
DOCKER = $(shell which docker 2>/dev/null || which podman 2>/dev/null)
TAG=edge
ARGS=

.PHONY: all
all: venv install-dep init dockerbuild

.PHONY: init
init:
ifeq ($(shell test -e defaults.env && echo yes), yes)
ifneq ($(shell test -e .env && echo yes), yes)
		ln -s defaults.env .env
endif
endif

.PHONY: dockerbuild
dockerbuild:
	${DOCKER} build -t ${OWNER}/${IMAGE}:${TAG} .

.PHONY: dockerclean
dockerclean:
	${DOCKER} rmi -f ${OWNER}/${IMAGE}:${TAG}

.PHONY: dockerpush
dockerpush:
	${DOCKER} push ${OWNER}/${IMAGE}:${TAG}

.PHONY: clean
clean:
	$(MAKE) dockerclean
	$(MAKE) distclean
	$(MAKE) venv-clean
	rm -fr .env
	rm -fr .pytest_cache
	rm -fr tests/__pycache__

.PHONY: dist
dist: venv install-dist-dep
	$(VENV)/python -m build .

.PHONY: install-dist-dep
install-dist-dep: venv
	$(VENV)/pip install build

.PHONY: distclean
distclean:
	rm -fr dist build $(PACKAGE_NAME).egg-info $(PACKAGE_NAME_FORMATTED).egg-info

.PHONY: maintainer-clean
maintainer-clean:
	@echo 'This command is intended for maintainers to use; it'
	@echo 'deletes files that may need special tools to rebuild.'
	$(MAKE) distclean

.PHONY: install-dep
install-dep:
	$(VENV)/pip install -r requirements.txt

.PHONY: install
install: install-dep
	$(VENV)/pip install .

.PHONY: uninstall
uninstall:
	$(VENV)/pip uninstall -y -r requirements.txt
	$(VENV)/pip uninstall -y -r $(PACKAGE_NAME)

.PHONY: installtest
installtest:
	$(VENV)/pip install -r tests/requirements.txt

.PHONY: uninstalltest
uninstalltest:
	$(VENV)/pip uninstall -y -r requirements.txt

.PHONY: install-dev
install-dev: venv
	$(VENV)/pip install -r requirements-dev.txt

.PHONY: uninstall-dev
uninstall-dev: venv
	$(VENV)/pip uninstall -y -r requirements-dev.txt

# The tests requires access to the docker socket
.PHONY: test
test:
	. $(VENV)/activate; python3 setup.py check -rms
	. $(VENV)/activate; pytest -s -v tests/

include Makefile.venv