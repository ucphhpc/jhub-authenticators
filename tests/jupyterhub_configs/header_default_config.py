"""A simple jupyter config file for testing the authenticator."""

c = get_config()

c.JupyterHub.authenticator_class = "jhubauthenticators.HeaderAuthenticator"
c.Authenticator.allowed_users = ("my-username-0",)
