"""A simple jupyter config file for testing the authenticator."""
from jhubauthenticators import Parser, JSONParser

c = get_config()

c.JupyterHub.hub_ip = "0.0.0.0"

c.JupyterHub.spawner_class = "dockerspawner.DockerSpawner"
c.DockerSpawner.image = "jupyter/base-notebook:latest"
c.DockerSpawner.network_name = "jhub_auth_state_network"

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
