# Example config
c = get_config()

c.JupyterHub.ip = "0.0.0.0"
c.JupyterHub.hub_ip = "0.0.0.0"

c.JupyterHub.spawner_class = "dockerspawner.DockerSpawner"

c.DockerSpawner.container_image = "nielsbohr/base-notebook:latest"
c.DockerSpawner.remove_containers = True
c.DockerSpawner.network_name = "jupyterhub_default"
# Due a change in how the DockerSpawner escapes usernames in >=12.0.0
# https://jupyterhub-dockerspawner.readthedocs.io/en/latest/changelog.html#id1
# The - character is the new escape character, meaning that the 
# usage of the - character will be automatically escaped by the escape string '-d2'
c.DockerSpawner.escape = "legacy"


c.JupyterHub.authenticator_class = "jhubauthenticators.DummyAuthenticator"
c.DummyAuthenticator.password = "password"
