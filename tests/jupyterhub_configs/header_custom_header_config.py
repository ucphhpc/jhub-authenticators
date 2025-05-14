"""A simple jupyter config file for testing the authenticator."""

from jhubauthenticators import Parser, JSONParser

c = get_config()

c.JupyterHub.authenticator_class = "jhubauthenticators.HeaderAuthenticator"
c.HeaderAuthenticator.allowed_headers = {"auth": "Remote-User", "mount": "Mount"}
c.HeaderAuthenticator.header_parser_classes = {"auth": Parser, "mount": JSONParser}
