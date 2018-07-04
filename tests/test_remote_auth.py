import requests
import docker
import pytest
import time
from os.path import join, dirname, realpath
from docker.types import Mount

IMAGE_NAME = "jupyterhub"
IMAGE_TAG = "test"
IMAGE = "".join([IMAGE_NAME, ":", IMAGE_TAG])

# root dir
docker_path = dirname(dirname(realpath(__file__)))

# mount paths
config_path = join(dirname(realpath(__file__)), 'jupyterhub_config.py')

# image build
jhub_image = {'path': docker_path, 'tag': IMAGE,
              'rm': 'True', 'pull': 'True'}

# container cmd
jhub_cont = {'image': IMAGE, 'name': IMAGE_NAME,
             'mounts': [Mount(source=config_path,
                              target='/etc/jupyterhub/jupyterhub_config.py',
                              read_only=True,
                              type='bind')],
             'ports': {8000: 8000},
             'detach': 'True'}


@pytest.mark.parametrize('image', [jhub_image], indirect=['image'])
@pytest.mark.parametrize('container', [jhub_cont], indirect=['container'])
def tests_auth_hub(image, container):
    """
    Test that the client is able to,
    - Not access the home path without being authed
    - Authenticate with the Remote-User header
    """
    # not ideal, wait for the jhub container to start, update with proper check
    time.sleep(5)
    client = docker.from_env()
    containers = client.containers.list()
    assert len(containers) > 0
    session = requests.session()

    # wait for jhub to be ready
    jhub_ready = False
    while not jhub_ready:
        resp = session.get("http://127.0.0.1:8000/hub/home")
        if resp.status_code != 404:
            jhub_ready = True

    # Not allowed, -> not authed
    no_auth_response = session.get("http://127.0.0.1:8000/hub/home")
    assert no_auth_response.status_code == 401

    # Auth requests
    user_cert = '/C=DK/ST=NA/L=NA/O=NBI/OU=NA/CN=Name' \
                '/emailAddress=mail@sdfsf.com'
    cert_auth_header = {
        'Remote-User': user_cert
    }

    auth_response = session.post("http://127.0.0.1:8000/hub/login",
                                 headers=cert_auth_header)
    assert auth_response.status_code == 200


@pytest.mark.parametrize('image', [jhub_image], indirect=['image'])
@pytest.mark.parametrize('container', [jhub_cont], indirect=['container'])
def test_auth_mount(image, container):
    """
    Test that the client is able to.
    - Once authenticated, pass a correctly formatted Mount Header
    """
    # not ideal, wait for the jhub container to start, update with proper check
    time.sleep(5)
    client = docker.from_env()
    containers = client.containers.list()
    assert len(containers) > 0
    session = requests.session()

    # wait for jhub to be ready
    jhub_ready = False
    while not jhub_ready:
        resp = session.get("http://127.0.0.1:8000/hub/home")
        if resp.status_code != 404:
            jhub_ready = True

    no_auth_mount = session.post("http://127.0.0.1:8000/hub/mount")
    assert no_auth_mount.status_code == 403

    # Auth requests
    user_cert = '/C=DK/ST=NA/L=NA/O=NBI/OU=NA/CN=Name' \
                '/emailAddress=mail@sdfsf.com'

    cert_auth_header = {
        'Remote-User': user_cert
    }

    auth_response = session.post("http://127.0.0.1:8000/hub/login",
                                 headers=cert_auth_header)
    assert auth_response.status_code == 200

    wrong_header = {
        'Mount': "SDfssdfsesdfsfdsdfsxv"
    }

    # Random key set
    correct_dict = {'HOST': 'hostaddr',
                    'USERNAME': 'randomstring_unique_string',
                    'PATH': '@host.localhost:',
                    'PRIVATEKEY': '''-----BEGIN RSA PRIVATE KEY-----
    0d9c24374728ee0d8c7317d3f533ef127dc565a4
    MIIEpAIBAAKCAQEA00VP99Nbg6AFrfeByzHtC4G2eLZGDCXP0pBG5tNNmaXKq5sU
    IrDPA7fJczwIfMNlqWeoYjEYg46vbMRxwIDXDDA990JK49+CrpwppxWgSE01WPis
    gtqfmaV16z8CS4WmkjSZnUKQf+2Yk9zdBXOOjWLiXBog7dGpUZQUV/j3u262DIl5
    oLGtoy/mljPx3rwGTSqVoavUW2zh7k0tFIhGt/T14E3TuATdUIDAsPmfLVXFFx76
    W0JxYv3uoCGAUOd2pFhqUXDPLYsSG5reWoQ8iXHJS84E8wHAImcLhYccRLg2AT3b
    TXmC1/BX3lfrwXjaBLfMZiUk/cdSLUh6hxtSPQIDAQABAoIBAQDP4SKHYmNohzsv
    axs+OXjZ2p8V9ZvE9iugLzBkjUOMzHI4GlZcsAZxzRQeG9LqGEVew80OGOra/7mi
    10RqOxveNVWzhnoz78ghUS0253OX0MiOK9lqw/1IbGMzvwLeFrrIn5MLBuUxyzJX
    Q3oClCqO+d5q65a9CpCE4aSGz0XLGKGe9iD5Rd1UjVJn/KvZnjObd0WJBAQCoNVU
    VCULblmR/1c+2lL/0Snv3j7w7G6+2H6o1MI3dbBQ0/SCGjw5cJOXYuGZq9YRXfnj
    3WxQW04j39gOtvZqJfCXK8lh+GE2BqgVG/ei9VGV27FshTM/3AkPACvzFZXTnjoP
    2uc5k8fBAoGBAO59ZzJyRYN+qOIRmM4e3ApZCfpUCaxMsksSDvvIVcJHENu4WcA3
    vPBVsnyDmgn5ZpEwXuoYhnMoDIQobob81jiVARG9RRS+4Kd71E2jOr5UBXFDD05R
    yvxh2deZ9T3hNWIE31T/37d3xLGdnkxQ+nqAyNjYAG7IemqxR877kw7tAoGBAOLI
    Tj7Aaa9cBzjmWVfJOExMT8PpDrGg4MGYh7nQFJB37A6SMrC1jXe6ZqwQtouOC+pG
    Jk310lMjAeC3Gokr769CHE40BY347wcMIBQHnKUW3elZx2APswETMyKYsNllnJWe
    j1f7gc5ZMr8bjWMPjRgIbazdrLCM3lv3ITMDNZaRAoGAXi13SxyFBuBFoMCCLyNQ
    kWWH4yq8hyXiYnLHJ/Z8pzOZHKs4Bgf8vIua6ECv27B5KGyJjrgQn/j4uFefDf9a
    OQ3eVjr/xKl73aewttf2oqJbY9avfKYgGnoppFJP3hfJFOQHrXE9zx2ktt8fW9O+
    lhG1PqxNv3G7pdZMHRiLgiECgYEAgyCazYHoGfM2YdofMrkwij1dqcOqMV76VjZh
    1DjSiy4sGcjC8pYndGEdWMRZKJw7m3xwTYej01pcjZiSCVqUPlwVjcpao9qaKxMB
    wVMdaf+s1G6K76pkMGzvlkN/jlRIk+KYs6DDT5MX2pSNzgeB57GH6PpMDdGGCNr+
    IUbrx2ECgYAck/GKM9grs2QSDmiQr3JNz1aUS0koIrE/jz4rYk/hIG4x7YFoPG4L
    D8rT/LeoFbxDarVRGkgu1pz13IQN2ItBp1qQVr4FqbN4emgj73wOWiFgrlRvasYV
    ojR4eIsIc//+fVpkr56fg2OUGhmI+jw87k9hG5uxgBCqOAJuWjEo7A==
    -----END RSA PRIVATE KEY-----'''}

    correct_header = {
        'Mount': str(correct_dict)
    }

    # Invalid mount header
    auth_mount_response = session.post("http://127.0.0.1:8000/hub/mount",
                                       headers=wrong_header)
    assert auth_mount_response.status_code == 403

    # Valid mount header
    auth_mount_response = session.post("http://127.0.0.1:8000/hub/mount",
                                       headers=correct_header)
    assert auth_mount_response.status_code == 200
