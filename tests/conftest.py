import time
import pytest
import docker
from docker.errors import NotFound


@pytest.fixture(scope='function')
def image(request):
    client = docker.from_env()
    _image = client.images.build(**request.param)
    yield _image

    # Remove image after test usage
    image_obj = _image[0]
    image_id = image_obj.id
    client.images.remove(image_obj.tags[0], force=True)

    removed = False
    while not removed:
        try:
            client.images.get(image_id)
        except NotFound:
            removed = True


@pytest.fixture(scope='function')
def container(request):
    client = docker.from_env()
    _container = client.containers.run(**request.param)
    while _container.status != "running":
        time.sleep(1)
        _container = client.containers.get(_container.name)

    yield _container
    assert hasattr(_container, 'id')

    _container.stop()
    _container.wait()
    _container.remove()
    removed = False
    while not removed:
        try:
            client.containers.get(_container.id)
        except NotFound:
            removed = True
