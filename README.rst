====================================
Jupyterhub REMOTE_USER Authenticator (Forked Extension)
====================================

Authenticate to Jupyterhub using an authenticating proxy that can set
the REMOTE_USER header.

------------
Installation
------------

Installation from local git repository::

    cd jhub_remote_user_authenticator
    pip install .

-------------
Configuration
-------------

You should edit your :file:`jupyterhub_config.py` to set the authenticator 
class::

    c.JupyterHub.authenticator_class = 'jhub_remote_user_authenticator.remote_user_auth.RemoteUserAuthenticator'

You should be able to start jupyterhub.  The "/remote_user_login" resource
will look for the authenticated user name in the HTTP header "REMOTE_USER".
If found, and not blank, you will be logged in as that user.

Alternatively, you can use `RemoteUserLocalAuthenticator`::

    c.JupyterHub.authenticator_class = 'jhub_remote_user_authenticator.remote_user_auth.RemoteUserLocalAuthenticator'

This provides the same authentication functionality but is derived from
`LocalAuthenticator` and therefore provides features such as the ability
to add local accounts through the admin interface if configured to do so.

# Extension

Provide the possibility to provide MIG mount information for the authenticated user.

i.e

    c.JupyterHub.authenticator_class = 'jhub_remote_user_authenticator.remote_user_auth.MIGMountRemoteUserAuthenticator'
