import requests
import docker
import pytest
import time
import json
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
                                'mounts': [Mount(source=custom_data_header_config,
                                                 target=target_config,
                                                 read_only=True,
                                                 type='bind')],
                                'ports': {8000: 8000},
                                'detach': 'True'}


@pytest.mark.parametrize('build_image', [jhub_image], indirect=['build_image'])
@pytest.mark.parametrize('container', [default_jhub_cont], indirect=['container'])
def test_default_header_config(build_image, container):
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
@pytest.mark.parametrize('container', [email_jhub_cont], indirect=['container'])
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
@pytest.mark.parametrize('container', [email_jhub_cont], indirect=['container'])
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
        remote_user = '/C=DK/ST=NA/L=NA/O=NBI/OU=NA/CN=Name'\
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
