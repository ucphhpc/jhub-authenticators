import os
import requests
import logging
import docker
import pytest
from random import SystemRandom
from os.path import join, dirname, realpath
from docker.types import Mount
from util import (
    wait_for_site,
    wait_for_container,
)

IMAGE_NAME = "jupyterhub"
IMAGE_TAG = "test"
IMAGE = "".join([IMAGE_NAME, ":", IMAGE_TAG])
PORT = 8000
JHUB_URL = "http://127.0.0.1:{}".format(PORT)
JHUB_HUB_URL = "{}/hub".format(JHUB_URL)

JUPYTERHUB_START_ERROR = "The JupyterHub service never emerged"

# Logger
logging.basicConfig(level=logging.INFO)
test_logger = logging.getLogger()

# root dir
docker_path = dirname(dirname(realpath(__file__)))

# mount paths
remote_config_path = join(
    dirname(realpath(__file__)), "jupyterhub_configs", "remote_auth_config.py"
)

# image build
jhub_image = {"path": docker_path, "tag": IMAGE, "rm": "True", "pull": "True"}

rand_key = "".join(SystemRandom().choice("0123456789abcdef") for _ in range(32))

target_config = os.path.join(os.sep, "etc", "jupyterhub", "jupyterhub_config.py")
# container cmd
jhub_cont = {
    "image": IMAGE,
    "name": IMAGE_NAME,
    "mounts": [
        Mount(
            source=remote_config_path, target=target_config, read_only=True, type="bind"
        )
    ],
    "ports": {PORT: PORT},
    "detach": "True",
    "command": ["jupyterhub", "-f", target_config],
}


@pytest.mark.parametrize("build_image", [jhub_image], indirect=["build_image"])
@pytest.mark.parametrize("container", [jhub_cont], indirect=["container"])
def test_auth_hub(build_image, container):
    """
    Test that the client is able to,
    Not access the home path without being authed
    Authenticate with the Remote-User header
    """
    test_logger.info("Start of test_auth_hub")
    client = docker.from_env()
    service_name = "jupyterhub"
    if not wait_for_container(client, service_name, minutes=5):
        raise RuntimeError(JUPYTERHUB_START_ERROR)
    assert wait_for_site(JHUB_URL, valid_status_code=401) is True

    with requests.Session() as session:
        # Auth requests
        user_cert = (
            "/C=DK/ST=NA/L=NA/O=NBI/OU=NA/CN=Name" "/emailAddress=mail@sdfsf.com"
        )
        other_user = "idfsf"

        cert_auth_header = {"Remote-User": user_cert}

        other_auth_header = {"Remote-User": other_user}

        auth_response = session.post(
            "".join([JHUB_HUB_URL, "/login"]), headers=cert_auth_header
        )
        assert auth_response.status_code == 200

        auth_response = session.get(
            "".join([JHUB_HUB_URL, "/home"]), headers=other_auth_header
        )
        assert auth_response.status_code == 200
    test_logger.info("End of test_auth_hub")


@pytest.mark.parametrize("build_image", [jhub_image], indirect=["build_image"])
@pytest.mark.parametrize("container", [jhub_cont], indirect=["container"])
def test_auth_data_header(build_image, container):
    """
    Test that the client is able to.
    Once authenticated, pass a correctly formatted custom Data header
    """
    # not ideal, wait for the jhub container to start, update with proper check
    test_logger.info("Start of test_auth_data_header")
    client = docker.from_env()
    service_name = "jupyterhub"
    if not wait_for_container(client, service_name, minutes=5):
        raise RuntimeError(JUPYTERHUB_START_ERROR)
    assert wait_for_site(JHUB_URL, valid_status_code=401) is True
    with requests.Session() as session:
        no_auth_mount = session.post("".join([JHUB_HUB_URL, "/data"]))
        assert no_auth_mount.status_code == 403

        # Auth requests
        user_cert = (
            "/C=DK/ST=NA/L=NA/O=NBI/OU=NA/CN=Name" "/emailAddress=mail@sdfsf.com"
        )

        cert_auth_header = {"Remote-User": user_cert}

        auth_response = session.get(
            "".join([JHUB_HUB_URL, "/home"]), headers=cert_auth_header
        )
        assert auth_response.status_code == 200

        auth_response = session.post(
            "".join([JHUB_HUB_URL, "/login"]), headers=cert_auth_header
        )
        assert auth_response.status_code == 200

        wrong_header = {"Mount": "SDfssdfsesdfsfdsdfsxv"}

        # Random key set
        correct_dict = {
            "HOST": "hostaddr",
            "USERNAME": "randomstring_unique_string",
            "PATH": "@host.localhost:",
        }

        correct_header = {"Mount": str(correct_dict)}

        # Invalid mount header
        auth_mount_response = session.post(
            "".join([JHUB_HUB_URL, "/data"]), headers=wrong_header
        )
        assert auth_mount_response.status_code == 403

        # Valid mount header
        auth_mount_response = session.post(
            "".join([JHUB_HUB_URL, "/data"]), headers=correct_header
        )
        assert auth_mount_response.status_code == 200
    test_logger.info("End of test_auth_data_header")
