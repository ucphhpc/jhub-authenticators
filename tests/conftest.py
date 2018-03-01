import os
import docker
import pytest
import time

HUB_IMAGE_TAG = "hub:test"
HUB_CONTAINER_NAME = "jupyterhub"


@pytest.fixture(scope="session")
def hub_image():
    """Build the image for the jupyterhub. We'll run this as a service
    that's going to then spawn the notebook server services.
    """
    client = docker.from_env()

    # Build the image from the root of the package
    parent_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    image = client.images.build(path=parent_dir, tag=HUB_IMAGE_TAG, rm=True,
                                pull=True, forcerm=True)
    yield image
    if type(image) == tuple:
        client.images.remove(image[0].tags[0])
    else:
        client.images.remove(image.tags[0])


# Setup a container before handing over to the test that requires a
# hub_container
@pytest.fixture
def hub_container(hub_image):
    """Launch the hub service.
    Note that we don't directly use any of the arguments, but those fixtures need to be
    in place before we can launch the service.
    """

    client = docker.from_env()
    config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               "jupyter_config.py")
    container = client.containers.run(
        image=HUB_IMAGE_TAG,
        name=HUB_CONTAINER_NAME,
        mounts=[
            docker.types.Mount(source=config_path,
                               target='/srv/jupyterhub/jupyter_config.py',
                               read_only=True,
                               type='bind')
        ],
        ports={8000: 8000},
        detach=True)

    # Wait for container to be running
    while container.status != "running":
        time.sleep(1)
        container = client.containers.get(HUB_CONTAINER_NAME)

    # TODO -> investigate whether jhub has a check call for when it is ready
    # And wait some more. This is...not great, but there seems to be
    # a period after the task is running but before the hub will accept
    # connections.
    # If the test code attempts to connect to the hub during that time,
    # it fails.
    time.sleep(10)

    yield container
    # ensure that the container is gone before returning
    exist = True
    while exist:
        try:
            container.remove(v=True, force=True)
        except docker.errors.NotFound:
            exist = False
