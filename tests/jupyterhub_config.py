"""A simple jupyter config file for testing the authenticator."""

c = get_config()

c.JupyterHub.hub_ip = '0.0.0.0'
c.JupyterHub.authenticator_class = 'jhub_remote_auth_mount.MountRemoteUserAuthenticator'
