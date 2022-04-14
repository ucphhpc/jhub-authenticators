"""A simple jupyter config file for testing the authenticator."""
from jhubauthenticators import Parser, JSONParser

c = get_config()

c.JupyterHub.hub_ip = "0.0.0.0"

c.JupyterHub.spawner_class = "dockerspawner.DockerSpawner"
c.DockerSpawner.image = "jupyter/base-notebook:latest"
c.DockerSpawner.network_name = "jhub_auth_state_network"
# Due a change in how the DockerSpawner escapes usernames in >=12.0.0
# https://jupyterhub-dockerspawner.readthedocs.io/en/latest/changelog.html#id1
# The - character is the new escape character, meaning that the 
# usage of the - character will be automatically escaped by the escape string '-d2'
c.DockerSpawner.escape = "legacy"

c.JupyterHub.authenticator_class = "jhubauthenticators.HeaderAuthenticator"
c.HeaderAuthenticator.allowed_headers = {
    "auth": "Remote-User",
    "strdata": "StringData",
    "jsondata": "JsonData",
}

c.HeaderAuthenticator.header_parser_classes = {
    "auth": Parser,
    "strdata": JSONParser,
    "jsondata": JSONParser,
}
c.HeaderAuthenticator.spawner_shared_headers = ["StringData", "JsonData"]
c.HeaderAuthenticator.enable_auth_state = True
