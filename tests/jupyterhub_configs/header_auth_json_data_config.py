"""A simple jupyter config file for testing the authenticator."""
c = get_config()

c.JupyterHub.hub_ip = '0.0.0.0'

c.JupyterHub.spawner_class = 'dockerspawner.DockerSpawner'
c.DockerSpawner.image = 'jupyter/base-notebook:latest'
c.DockerSpawner.network_name = 'jhub_auth_json_network'

c.JupyterHub.authenticator_class = 'jhubauthenticators.HeaderAuthenticator'
c.HeaderAuthenticator.user_external_allow_attributes = ['data']
