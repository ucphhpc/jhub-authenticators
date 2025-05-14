import requests
import logging
import pytest
from os.path import join, dirname, realpath
from docker.types import Mount
from util import wait_for_site

IMAGE_NAME = "jupyterhub"
IMAGE_TAG = "test"
IMAGE = "".join([IMAGE_NAME, ":", IMAGE_TAG])
PORT = 8000
JHUB_URL = "http://127.0.0.1:{}".format(PORT)

# root dir
docker_path = dirname(dirname(realpath(__file__)))

# Logger
logging.basicConfig(level=logging.INFO)
test_logger = logging.getLogger()

# mount paths
config_path = join(
    dirname(realpath(__file__)), "jupyterhub_configs", "dummy_auth_config.py"
)

# image build
jhub_image = {"path": docker_path, "tag": IMAGE, "rm": "True", "pull": "True"}

target_config = "/etc/jupyterhub/jupyterhub_config.py"
# container cmd
jhub_cont = {
    "image": IMAGE,
    "name": IMAGE_NAME,
    "mounts": [
        Mount(source=config_path, target=target_config, read_only=True, type="bind")
    ],
    "ports": {PORT: PORT},
    "detach": "True",
}


@pytest.mark.parametrize("build_image", [jhub_image], indirect=["build_image"])
@pytest.mark.parametrize("container", [jhub_cont], indirect=["container"])
def test_dummy_auth(build_image, container):
    """
    Test that the client is able to.
    - Once authenticated, pass a correctly formatted Mount Header
    """
    test_logger.info("Start of test_dummy_auth")
    assert wait_for_site(JHUB_URL) is True
    with requests.Session() as session:
        # login
        user = "a-new-user"
        # Refresh cookies
        session.get(JHUB_URL)

        # next to hub/home, else the login by
        #  default will return 500 because it will
        #  try and start a server right away with the new user
        # Which fails because the default
        #  spawner requires a matching local username
        login_response = session.post(
            JHUB_URL + "/hub/login?next=/hub/home",
            data={"username": user, "password": "password"},
            params={"_xsrf": session.cookies["_xsrf"]},
        )
        assert login_response.status_code == 200
        resp = session.get(JHUB_URL + "/hub/home")
        assert resp.status_code == 200
    test_logger.info("End of test_dummy_auth")
