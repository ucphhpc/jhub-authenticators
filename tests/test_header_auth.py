import os
import requests
import docker
import pytest
import time
import json
import base64
from os.path import join, dirname, realpath
from docker.types import Mount

IMAGE_NAME = "jupyterhub"
IMAGE_TAG = "test"
IMAGE = "".join([IMAGE_NAME, ":", IMAGE_TAG])

JHUB_URL = "http://127.0.0.1:8000"
# root dir
docker_path = dirname(dirname(realpath(__file__)))
configs_dir_path = join(dirname(realpath(__file__)),
                        'jupyterhub_configs')
# mount paths
default_config = join(configs_dir_path, 'header_default_config.py')
email_username_config = join(configs_dir_path,
                             'header_email_username_config.py')
custom_data_header_config = join(configs_dir_path,
                                 'header_custom_header_config.py')
auth_state_header_config = join(configs_dir_path,
                                'header_auth_state_header_config.py')
auth_json_data_config = join(configs_dir_path,
                             'header_auth_json_data_config.py')

# image build
jhub_image = {'path': docker_path, 'tag': IMAGE,
              'rm': 'True', 'pull': 'True'}

target_config = '/etc/jupyterhub/jupyterhub_config.py'
# container cmd
default_jhub_cont = {'image': IMAGE, 'name': IMAGE_NAME,
                     'mounts': [Mount(source=default_config,
                                      target=target_config,
                                      read_only=True,
                                      type='bind')],
                     'ports': {8000: 8000},
                     'detach': 'True'}
email_jhub_cont = {'image': IMAGE, 'name': IMAGE_NAME,
                   'mounts': [Mount(source=email_username_config,
                                    target=target_config,
                                    read_only=True,
                                    type='bind')],
                   'ports': {8000: 8000},
                   'detach': 'True'}
custom_data_header_jhub_cont = {'image': IMAGE, 'name': IMAGE_NAME,
                                'mounts': [
                                    Mount(source=custom_data_header_config,
                                          target=target_config,
                                          read_only=True,
                                          type='bind')],
                                'ports': {8000: 8000},
                                'detach': 'True'}
AUTH_STATE_NETWORK_NAME = 'jhub_auth_state_network'
auth_state_network_config = {'name': AUTH_STATE_NETWORK_NAME,
                             'driver': 'bridge',
                             'attachable': True}
auth_state_data_header_jhub_cont = {'image': IMAGE, 'name': IMAGE_NAME,
                                    'mounts': [
                                        Mount(source=auth_state_header_config,
                                              target=target_config,
                                              read_only=True,
                                              type='bind'),
                                        Mount(source='/var/run/docker.sock',
                                              target='/var/run/docker.sock',
                                              read_only=True,
                                              type='bind')],
                                    'ports': {8000: 8000},
                                    'detach': 'True',
                                    'environment': {
                                        'JUPYTERHUB_CRYPT_KEY':
                                            base64.b64encode(os.urandom(32))},
                                    'network': AUTH_STATE_NETWORK_NAME}
AUTH_JSON_DATA_NETWORK_NAME = 'jhub_auth_json_network'
auth_json_data_network_config = {'name': AUTH_JSON_DATA_NETWORK_NAME,
                                 'driver': 'bridge',
                                 'attachable': True}
auth_state_json_data_jhub_cont = {'image': IMAGE, 'name': IMAGE_NAME,
                                  'mounts': [
                                      Mount(source=auth_json_data_config,
                                            target=target_config,
                                            read_only=True,
                                            type='bind'),
                                      Mount(source='/var/run/docker.sock',
                                            target='/var/run/docker.sock',
                                            read_only=True,
                                            type='bind')],
                                  'ports': {8000: 8000},
                                  'detach': 'True',
                                  'environment': {
                                      'JUPYTERHUB_CRYPT_KEY':
                                          base64.b64encode(os.urandom(32))},
                                  'network': AUTH_JSON_DATA_NETWORK_NAME}


@pytest.mark.parametrize('build_image', [jhub_image], indirect=['build_image'])
@pytest.mark.parametrize('container', [default_jhub_cont],
                         indirect=['container'])
def test_default_header_config(build_image, container):
    """
    Test that an authenticated client is able to pass
     a correctly formatted Mount Header
    """
    # not ideal, wait for the jhub container to start, update with proper check
    time.sleep(5)
    client = docker.from_env()
    containers = client.containers.list()
    assert len(containers) > 0
    with requests.session() as session:
        jhub_base_url = 'http://127.0.0.1:8000/hub'
        # wait for jhub to be ready
        jhub_ready = False
        while not jhub_ready:
            resp = session.get(''.join([jhub_base_url, '/home']))
            if resp.status_code != 404:
                jhub_ready = True

        # Auth requests
        remote_user = 'myusername'
        auth_header = {
            'Remote-User': remote_user
        }

        auth_response = session.get(''.join([jhub_base_url, '/home']),
                                    headers=auth_header)
        assert auth_response.status_code == 200

        auth_response = session.post(''.join([jhub_base_url, '/login']),
                                     headers=auth_header)
        assert auth_response.status_code == 200


@pytest.mark.parametrize('build_image', [jhub_image], indirect=['build_image'])
@pytest.mark.parametrize('container', [custom_data_header_jhub_cont],
                         indirect=['container'])
def test_custom_data_header_auth(build_image, container):
    """
    Test that the client is able to.
    Once authenticated, pass a correctly formatted Mount Header
    """
    # not ideal, wait for the jhub container to start, update with proper check
    time.sleep(5)
    client = docker.from_env()
    containers = client.containers.list()
    assert len(containers) > 0
    with requests.session() as session:
        jhub_base_url = 'http://127.0.0.1:8000/hub'
        # wait for jhub to be ready
        jhub_ready = False
        while not jhub_ready:
            resp = session.get(''.join([jhub_base_url, '/home']))
            if resp.status_code != 404:
                jhub_ready = True

        # Auth requests
        remote_user = 'myusername'
        data_dict = {'HOST': 'hostaddr',
                     'USERNAME': 'randomstring_unique_string',
                     'PATH': '@host.localhost:'}
        auth_data_header = {
            'Remote-User': remote_user,
            'Mount': json.dumps(data_dict)
        }

        auth_response = session.post(''.join([jhub_base_url, '/login']),
                                     headers=auth_data_header)
        assert auth_response.status_code == 200


@pytest.mark.parametrize('build_image', [jhub_image], indirect=['build_image'])
@pytest.mark.parametrize('network', [auth_state_network_config],
                         indirect=['network'])
@pytest.mark.parametrize('container', [auth_state_data_header_jhub_cont],
                         indirect=['container'])
def test_auth_state_header_auth(build_image, network, container):
    """
    Test that the client is able to. Test that auth_state recieves
    the specified test data headers.
    """
    # not ideal, wait for the jhub container to start, update with proper check
    time.sleep(5)
    client = docker.from_env()
    containers = client.containers.list()
    assert len(containers) > 0
    with requests.session() as session:
        jhub_base_url = 'http://127.0.0.1:8000/hub'
        # wait for jhub to be ready
        jhub_ready = False
        while not jhub_ready:
            resp = session.get(''.join([jhub_base_url, '/home']))
            if resp.status_code != 404:
                jhub_ready = True

        # Auth requests
        remote_user = 'myusername'
        data_str = "blablabla"
        data_dict = {'HOST': 'hostaddr',
                     'USERNAME': 'randomstring_unique_string',
                     'PATH': '@host.localhost:'}
        env_data = {
            'StringData': data_str,
            'JsonData': data_dict
        }
        auth_data_header = {
            'Remote-User': remote_user,
        }

        # Cast to json data types before submission
        auth_data_header.update({env_key: json.dumps(env_val)
                                 for env_key, env_val in env_data.items()})
        auth_response = session.post(''.join([jhub_base_url, '/login']),
                                     headers=auth_data_header)
        assert auth_response.status_code == 200
        # Spawn with auth_state
        spawn_response = session.post(''.join([jhub_base_url, '/spawn']))
        assert spawn_response.status_code == 200
        time.sleep(15)
        post_spawn_containers = client.containers.list()

        jupyter_containers = [jup_container for jup_container in
                              post_spawn_containers
                              if "jupyter-" in jup_container.name]
        assert len(jupyter_containers) > 0
        # Check container for passed environments
        for container in jupyter_containers:
            envs = {env.split('=')[0]: env.split('=')[1]
                    for env in container.attrs['Config']['Env']}
            for data_key, data_value in env_data.items():
                assert data_key in envs
                assert envs[data_key] == str(data_value)


@pytest.mark.parametrize('build_image', [jhub_image], indirect=['build_image'])
@pytest.mark.parametrize('container', [email_jhub_cont],
                         indirect=['container'])
def test_remote_oid_user_header_auth(build_image, container):
    """
    Test that the client is able to.
    Once authenticated, pass a correctly formatted Mount Header
    """
    # not ideal, wait for the jhub container to start, update with proper check
    time.sleep(5)
    client = docker.from_env()
    containers = client.containers.list()
    assert len(containers) > 0
    with requests.session() as session:
        jhub_base_url = 'http://127.0.0.1:8000/hub'
        # wait for jhub to be ready
        jhub_ready = False
        while not jhub_ready:
            resp = session.get(''.join([jhub_base_url, '/home']))
            if resp.status_code != 404:
                jhub_ready = True

        # Auth requests
        remote_user = 'https://oid.migrid.test/openid/id/fballam0@auda.org.au'
        auth_header = {
            'Remote-User': remote_user
        }

        auth_response = session.get(''.join([jhub_base_url, '/home']),
                                    headers=auth_header)
        assert auth_response.status_code == 200

        auth_response = session.post(''.join([jhub_base_url, '/login']),
                                     headers=auth_header)
        assert auth_response.status_code == 200


@pytest.mark.parametrize('build_image', [jhub_image], indirect=['build_image'])
@pytest.mark.parametrize('container', [email_jhub_cont],
                         indirect=['container'])
def test_basic_cert_user_header_auth(build_image, container):
    """
    Test that the client is able to.
    Once authenticated, pass a correctly formatted Mount Header
    """
    # not ideal, wait for the jhub container to start, update with proper check
    time.sleep(5)
    client = docker.from_env()
    containers = client.containers.list()
    assert len(containers) > 0
    session = requests.session()
    with requests.session() as session:
        jhub_base_url = 'http://127.0.0.1:8000/hub'
        # wait for jhub to be ready
        jhub_ready = False
        while not jhub_ready:
            resp = session.get(''.join([jhub_base_url, '/home']))
            if resp.status_code != 404:
                jhub_ready = True

        # Auth requests
        remote_user = '/C=DK/ST=NA/L=NA/O=NBI/OU=NA/CN=Name' \
                      '/emailAddress=mail@sdfsf.com'
        auth_header = {
            'Remote-User': remote_user
        }

        auth_response = session.get(''.join([jhub_base_url, '/home']),
                                    headers=auth_header)
        assert auth_response.status_code == 200

        auth_response = session.post(''.join([jhub_base_url, '/login']),
                                     headers=auth_header)
        assert auth_response.status_code == 200
        # TODO, validate username is actual email regex


@pytest.mark.parametrize('build_image', [jhub_image], indirect=['build_image'])
@pytest.mark.parametrize('network', [auth_json_data_network_config],
                         indirect=['network'])
@pytest.mark.parametrize('container', [auth_state_json_data_jhub_cont],
                         indirect=['container'])
def test_json_data_post(build_image, network, container):
    """
    Test that the client is able to submit a json data to the authenticated user.
    """
    # not ideal, wait for the jhub container to start, update with proper check
    time.sleep(5)
    client = docker.from_env()
    containers = client.containers.list()
    assert len(containers) > 0
    session = requests.session()
    with requests.session() as session:
        jhub_base_url = 'http://127.0.0.1:8000/hub'
        # wait for jhub to be ready
        jhub_ready = False
        while not jhub_ready:
            resp = session.get(''.join([jhub_base_url, '/home']))
            if resp.status_code != 404:
                jhub_ready = True

        # Auth requests
        remote_user = 'new_user'
        auth_header = {
            'Remote-User': remote_user,
        }

        auth_response = session.post(''.join([jhub_base_url, '/login']),
                                     headers=auth_header)
        assert auth_response.status_code == 200
        # Post json
        data_str = "blablabla"
        data_dict = {'HOST': 'hostaddr',
                     'USERNAME': 'randomstring_unique_string',
                     'PATH': '@host.localhost:'}
        env_data = {
            'StringData': data_str,
            'JsonData': data_dict
        }

        json_data = {'data': env_data}
        post_response = session.post(''.join([jhub_base_url, '/user-data']),
                                     json=json_data)
        assert post_response.status_code == 200
