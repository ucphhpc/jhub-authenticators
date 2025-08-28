"""A simple jupyter config file for testing the authenticator."""

c = get_config()

c.JupyterHub.hub_ip = "0.0.0.0"

c.JupyterHub.spawner_class = "dockerspawner.DockerSpawner"
c.DockerSpawner.image = "quay.io/jupyter/base-notebook:latest"
c.DockerSpawner.network_name = "jhub_auth_json_network"
# Due a change in how the DockerSpawner escapes usernames in >=12.0.0
# https://jupyterhub-dockerspawner.readthedocs.io/en/latest/changelog.html#id1
# The - character is the new escape character, meaning that the
# usage of the - character will be automatically escaped by the escape string '-d2'
c.DockerSpawner.escape = "legacy"

c.JupyterHub.authenticator_class = "jhubauthenticators.HeaderAuthenticator"
c.Authenticator.allowed_users = ("new_user",)
c.HeaderAuthenticator.user_external_allow_attributes = ["data"]
