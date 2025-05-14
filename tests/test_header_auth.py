import os
import requests
import logging
import docker
import pytest
import json
import base64
from urllib.parse import urljoin
from os.path import join, dirname, realpath
from docker.types import Mount
from util import (
    wait_for_site,
    delete,
    get_container_user,
    get_container,
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
configs_dir_path = join(dirname(realpath(__file__)), "jupyterhub_configs")

# mount paths
default_config = join(configs_dir_path, "header_default_config.py")
email_username_config = join(configs_dir_path, "header_email_username_config.py")
custom_data_header_config = join(configs_dir_path, "header_custom_header_config.py")
auth_state_header_config = join(configs_dir_path, "header_auth_state_header_config.py")
auth_json_data_config = join(configs_dir_path, "header_auth_json_data_config.py")

# image build
jhub_image = {"path": docker_path, "tag": IMAGE, "rm": "True", "pull": "True"}

target_config = os.path.join(os.sep, "etc", "jupyterhub", "jupyterhub_config.py")
docker_socket_path = os.path.join(os.sep, "var", "run", "docker.sock")


# container cmd
default_jhub_cont = {
    "image": IMAGE,
    "name": IMAGE_NAME,
    "mounts": [
        Mount(source=default_config, target=target_config, read_only=True, type="bind")
    ],
    "ports": {PORT: PORT},
    "detach": "True",
    "command": ["jupyterhub", "--debug", "-f", target_config],
}
email_jhub_cont = {
    "image": IMAGE,
    "name": IMAGE_NAME,
    "mounts": [
        Mount(
            source=email_username_config,
            target=target_config,
            read_only=True,
            type="bind",
        )
    ],
    "ports": {PORT: PORT},
    "detach": "True",
    "command": ["jupyterhub", "--debug", "-f", target_config],
}
custom_data_header_jhub_cont = {
    "image": IMAGE,
    "name": IMAGE_NAME,
    "mounts": [
        Mount(
            source=custom_data_header_config,
            target=target_config,
            read_only=True,
            type="bind",
        )
    ],
    "ports": {PORT: PORT},
    "detach": "True",
    "command": ["jupyterhub", "--debug", "-f", target_config],
}
AUTH_STATE_NETWORK_NAME = "jhub_auth_state_network"
auth_state_network_config = {
    "name": AUTH_STATE_NETWORK_NAME,
    "driver": "bridge",
    "attachable": True,
}
auth_state_data_header_jhub_cont = {
    "image": IMAGE,
    "name": IMAGE_NAME,
    "mounts": [
        Mount(
            source=auth_state_header_config,
            target=target_config,
            read_only=True,
            type="bind",
        ),
        Mount(
            source=docker_socket_path,
            target=docker_socket_path,
            read_only=True,
            type="bind",
        ),
    ],
    "ports": {PORT: PORT},
    "detach": "True",
    "environment": {"JUPYTERHUB_CRYPT_KEY": base64.b64encode(os.urandom(32))},
    "network": AUTH_STATE_NETWORK_NAME,
    "command": ["jupyterhub", "--debug", "-f", target_config],
}
AUTH_JSON_DATA_NETWORK_NAME = "jhub_auth_json_network"
auth_json_data_network_config = {
    "name": AUTH_JSON_DATA_NETWORK_NAME,
    "driver": "bridge",
    "attachable": True,
}
auth_state_json_data_jhub_cont = {
    "image": IMAGE,
    "name": IMAGE_NAME,
    "mounts": [
        Mount(
            source=auth_json_data_config,
            target=target_config,
            read_only=True,
            type="bind",
        ),
        Mount(
            source=docker_socket_path,
            target=docker_socket_path,
            read_only=True,
            type="bind",
        ),
    ],
    "ports": {PORT: PORT},
    "detach": "True",
    "environment": {"JUPYTERHUB_CRYPT_KEY": base64.b64encode(os.urandom(32))},
    "network": AUTH_JSON_DATA_NETWORK_NAME,
    "command": ["jupyterhub", "--debug", "-f", target_config],
}


@pytest.mark.parametrize("build_image", [jhub_image], indirect=["build_image"])
@pytest.mark.parametrize("container", [default_jhub_cont], indirect=["container"])
def test_default_header_config(build_image, container):
    """
    Test that an authenticated client is able to pass
     a correctly formatted Mount Header
    """
    test_logger.info("Start of test_default_header_config")
    client = docker.from_env()
    service_name = "jupyterhub"
    if not wait_for_container(client, service_name, minutes=5):
        raise RuntimeError(JUPYTERHUB_START_ERROR)
    assert wait_for_site(JHUB_URL, valid_status_code=401) is True
    with requests.session() as session:
        # Auth requests
        remote_user = "my-username-0"
        auth_header = {"Remote-User": remote_user}
        # Refresh cookies
        session.get(JHUB_HUB_URL)

        auth_response = session.get(
            "".join([JHUB_HUB_URL, "/home"]),
            headers=auth_header,
            params={"_xsrf": session.cookies["_xsrf"]},
        )
        assert auth_response.status_code == 200

        auth_response = session.post(
            "".join([JHUB_HUB_URL, "/login"]),
            headers=auth_header,
            params={"_xsrf": session.cookies["_xsrf"]},
        )
        assert auth_response.status_code == 200
    test_logger.info("End of test_default_header_config")


@pytest.mark.parametrize("build_image", [jhub_image], indirect=["build_image"])
@pytest.mark.parametrize(
    "container", [custom_data_header_jhub_cont], indirect=["container"]
)
def test_custom_data_header_auth(build_image, container):
    """
    Test that the client is able to.
    Once authenticated, pass a correctly formatted Mount Header
    """
    test_logger.info("Start of test_custom_data_header_auth")
    client = docker.from_env()
    service_name = "jupyterhub"
    if not wait_for_container(client, service_name, minutes=5):
        raise RuntimeError(JUPYTERHUB_START_ERROR)
    assert wait_for_site(JHUB_URL, valid_status_code=401) is True
    with requests.session() as session:
        # Refresh cookies
        session.get(JHUB_URL)

        # Auth requests
        remote_user = "my-username-2"
        data_dict = {
            "HOST": "hostaddr",
            "USERNAME": "randomstring_unique_string",
            "PATH": "@host.localhost:",
        }
        auth_data_header = {"Remote-User": remote_user, "Mount": json.dumps(data_dict)}

        auth_response = session.post(
            "".join([JHUB_HUB_URL, "/login"]),
            headers=auth_data_header,
            params={"_xsrf": session.cookies["_xsrf"]},
        )
        assert auth_response.status_code == 200
    test_logger.info("End of test_custom_data_header_auth")


@pytest.mark.parametrize("build_image", [jhub_image], indirect=["build_image"])
@pytest.mark.parametrize("network", [auth_state_network_config], indirect=["network"])
@pytest.mark.parametrize(
    "container", [auth_state_data_header_jhub_cont], indirect=["container"]
)
def test_auth_state_header_auth(build_image, network, container):
    """
    Test that the client is able to. Test that auth_state recieves
    the specified test data headers.
    """
    test_logger.info("Start of test_auth_state_header_auth")
    client = docker.from_env()
    service_name = "jupyterhub"
    if not wait_for_container(client, service_name, minutes=5):
        raise RuntimeError(JUPYTERHUB_START_ERROR)
    assert wait_for_site(JHUB_URL, valid_status_code=401) is True
    with requests.session() as session:
        # Refresh cookies
        session.get(JHUB_URL)

        # Auth requests
        remote_user = "my-username-3"
        data_str = "blablabla"
        data_dict = {
            "HOST": "hostaddr",
            "USERNAME": "randomstring_unique_string",
            "PATH": "@host.localhost:",
        }
        env_data = {"StringData": data_str, "JsonData": data_dict}
        auth_data_header = {
            "Remote-User": remote_user,
        }

        # Cast to json data types before submission
        auth_data_header.update(
            {env_key: json.dumps(env_val) for env_key, env_val in env_data.items()}
        )
        auth_response = session.post(
            "".join([JHUB_HUB_URL, "/login"]),
            headers=auth_data_header,
            params={"_xsrf": session.cookies["_xsrf"]},
        )
        assert auth_response.status_code == 200
        # Spawn with auth_state
        spawn_response = session.post(
            "".join([JHUB_HUB_URL, "/spawn"]),
            params={"_xsrf": session.cookies["_xsrf"]},
        )
        assert spawn_response.status_code == 200

        test_logger.info("Spawn POST response message: {}".format(spawn_response.text))
        assert spawn_response.status_code == 200

        target_container_name = "{}-{}".format("jupyter", remote_user)
        wait_min = 5
        if not wait_for_container(client, target_container_name, minutes=wait_min):
            raise RuntimeError(
                "No container with name: {} appeared within: {} minutes".format(
                    service_name, wait_min
                )
            )

        spawned_container = get_container(client, target_container_name)
        # Validate that the container has the passed environment values defined
        # in env_data
        envs = {
            env.split("=")[0]: env.split("=")[1]
            for env in spawned_container.attrs["Config"]["Env"]
        }
        for data_key, data_value in env_data.items():
            assert data_key in envs
            assert envs[data_key] == str(data_value)

        # Shutdown the container
        # Delete the spawned service
        jhub_user = get_container_user(spawned_container)
        assert jhub_user is not None
        delete_url = urljoin(JHUB_URL, "/hub/api/users/{}/server".format(jhub_user))

        deleted = delete(session, delete_url)
        assert deleted
        # Remove the stopped container
        spawned_container.stop()
        spawned_container.wait()
        spawned_container.remove()

        deleted_container = get_container(client, target_container_name)
        assert deleted_container is None
    test_logger.info("End of test_auth_state_header_auth")


@pytest.mark.parametrize("build_image", [jhub_image], indirect=["build_image"])
@pytest.mark.parametrize("container", [email_jhub_cont], indirect=["container"])
def test_remote_oid_user_header_auth(build_image, container):
    """
    Test that the client is able to.
    Once authenticated, pass a correctly formatted Mount Header
    """
    test_logger.info("Start of test_remote_oid_user_header_auth")
    client = docker.from_env()
    service_name = "jupyterhub"
    if not wait_for_container(client, service_name, minutes=5):
        raise RuntimeError(JUPYTERHUB_START_ERROR)
    assert wait_for_site(JHUB_URL, valid_status_code=401) is True
    with requests.session() as session:
        # Refresh cookies
        session.get(JHUB_URL)
        # Auth requests
        remote_user = "https://oid.migrid.test/openid/id/fballam0@auda.org.au"
        auth_header = {"Remote-User": remote_user}

        auth_response = session.get(
            "".join([JHUB_HUB_URL, "/home"]), headers=auth_header
        )
        assert auth_response.status_code == 200

        auth_response = session.post(
            "".join([JHUB_HUB_URL, "/login"]),
            headers=auth_header,
            params={"_xsrf": session.cookies["_xsrf"]},
        )
        assert auth_response.status_code == 200
    test_logger.info("End of test_remote_oid_user_header_auth")


@pytest.mark.parametrize("build_image", [jhub_image], indirect=["build_image"])
@pytest.mark.parametrize("container", [email_jhub_cont], indirect=["container"])
def test_basic_cert_user_header_auth(build_image, container):
    """
    Test that the client is able to.
    Once authenticated, pass a correctly formatted Mount Header
    """
    test_logger.info("Start of test_basic_cert_user_header_auth")
    client = docker.from_env()
    service_name = "jupyterhub"
    if not wait_for_container(client, service_name, minutes=5):
        raise RuntimeError(JUPYTERHUB_START_ERROR)
    assert wait_for_site(JHUB_URL, valid_status_code=401) is True
    with requests.session() as session:
        # Refresh cookies
        session.get(JHUB_URL)
        # Auth requests
        remote_user = (
            "/C=DK/ST=NA/L=NA/O=NBI/OU=NA/CN=Name" "/emailAddress=mail@sdfsf.com"
        )
        auth_header = {"Remote-User": remote_user}

        auth_response = session.get(
            "".join([JHUB_HUB_URL, "/home"]), headers=auth_header
        )
        assert auth_response.status_code == 200

        auth_response = session.post(
            "".join([JHUB_HUB_URL, "/login"]),
            headers=auth_header,
            params={"_xsrf": session.cookies["_xsrf"]},
        )
        assert auth_response.status_code == 200
        # TODO, validate username is actual email regex
    test_logger.info("End of test_basic_cert_user_header_auth")


@pytest.mark.parametrize("build_image", [jhub_image], indirect=["build_image"])
@pytest.mark.parametrize(
    "network", [auth_json_data_network_config], indirect=["network"]
)
@pytest.mark.parametrize(
    "container", [auth_state_json_data_jhub_cont], indirect=["container"]
)
def test_json_data_post(build_image, network, container):
    """
    Test that the client is able to submit a json data to the authenticated user.
    """
    test_logger.info("Start of test_json_data_post")
    client = docker.from_env()
    service_name = "jupyterhub"
    if not wait_for_container(client, service_name, minutes=5):
        raise RuntimeError(JUPYTERHUB_START_ERROR)
    assert wait_for_site(JHUB_URL, valid_status_code=401) is True
    with requests.session() as session:
        # Refresh cookies
        session.get(JHUB_URL)
        # Auth requests
        remote_user = "new_user"
        auth_header = {
            "Remote-User": remote_user,
        }

        auth_response = session.post(
            "".join([JHUB_HUB_URL, "/login"]),
            headers=auth_header,
            params={"_xsrf": session.cookies["_xsrf"]},
        )
        assert auth_response.status_code == 200
        # Post json
        data_str = "blablabla"
        data_dict = {
            "HOST": "hostaddr",
            "USERNAME": "randomstring_unique_string",
            "PATH": "@host.localhost:",
        }
        env_data = {"StringData": data_str, "JsonData": data_dict}

        json_data = {
            "data": env_data,
        }
        post_response = session.post(
            "".join([JHUB_HUB_URL, "/set-user-data"]),
            json=json_data,
            params={"_xsrf": session.cookies["_xsrf"]},
        )
        assert post_response.status_code == 200
    test_logger.info("End of test_json_data_post")
