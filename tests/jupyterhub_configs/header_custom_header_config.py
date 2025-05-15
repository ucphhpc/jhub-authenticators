"""A simple jupyter config file for testing the authenticator."""

from jhubauthenticators import Parser, JSONParser

c = get_config()

c.JupyterHub.authenticator_class = "jhubauthenticators.HeaderAuthenticator"
# Introduced in Jupyterhub 5.x https://jupyterhub.readthedocs.io/en/stable/reference/changelog.html#id25
# can be set to False if a user should be authorized after a succesfull authentication.
c.Authenticator.allow_all = True
c.HeaderAuthenticator.allowed_headers = {"auth": "Remote-User", "mount": "Mount"}
c.HeaderAuthenticator.header_parser_classes = {"auth": Parser, "mount": JSONParser}
