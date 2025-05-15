"""A simple jupyter config file for testing the authenticator."""

c = get_config()

c.JupyterHub.authenticator_class = "jhubauthenticators.HeaderAuthenticator"
# Introduced in Jupyterhub 5.x https://jupyterhub.readthedocs.io/en/stable/reference/changelog.html#id25
# can be set to False if a user should be authorized after a succesfull authentication.
c.Authenticator.allow_all = True
