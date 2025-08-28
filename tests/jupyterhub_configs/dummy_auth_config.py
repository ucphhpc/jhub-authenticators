"""A simple jupyter config file for testing the authenticator."""

c = get_config()

c.JupyterHub.authenticator_class = "jhubauthenticators.DummyAuthenticator"
c.Authenticator.allowed_users = ("a-new-user",)
c.DummyAuthenticator.password = "password"
