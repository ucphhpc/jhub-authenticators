.. image:: https://travis-ci.org/rasmunk/jhub-authenticators.svg?branch=devel
    :target: https://travis-ci.org/rasmunk/jhub-authenticators

=========================
Jupyterhub Authenticators
=========================

Authenticate to Jupyterhub using an authenticating proxy that can set
the Remote-User header.
Also supports for passing additional information to the jupyter user. This includes a
list of user defined /data headers.

------------
Installation
------------

Installation from pypi::

    pip install jhub-authenticators

Installation from local git repository::

    cd jhub-authenticators
    pip install .

-------------
Configuration
-------------

You should edit your `jupyterhub_config.py` config file to set the
authenticator class::

    c.JupyterHub.authenticator_class = 'jhubauthenticators.RemoteUserAuthenticator'

You should be able to start jupyterhub.  The "/login" resource
will look for the authenticated user name in the HTTP header "Remote-User".
If found, and not blank, you will be logged in as that user.

Alternatively, you can use `RemoteUserLocalAuthenticator`::

    c.JupyterHub.authenticator_class = 'jhubauthenticators.RemoteUserLocalAuthenticator'

This provides the same authentication functionality but is derived from
`LocalAuthenticator` and therefore provides features such as the ability
to add local accounts through the admin interface if configured to do so.

--------------------
Dummy Authentication
--------------------

Provides an option for testing JupyterHub authentication with a dummy authenticator
that can have a global preset password for any account::

    c.JupyterHub.authenticator_class = 'jhubauthenticators.DummyAuthenticator'
    c.DummyAuthenticator.password = 'password'


Note! Don't use in production.

-------------------------------------------------------------
Remote User Authentication extended with user-defined headers
-------------------------------------------------------------

Provides the capability to supply the jupyterhub user with additional state information
via the /data path. This adds two base request paths to the jupyterhub web application::

'/login' -> requires a non empty Remote-User header
'/data' -> requires both an authenticated request and a valid configured header

Before information can be passed to the user via the '/data' path, a list of valid
headers is required. These preset valid headers are then upon a POST request to the
'/data' URl appended to the current authenticated jupyterhub user data dictionary. I.e.
user.data[Header] = HeaderValue

The extended authenticator can be activated by setting the following option in the
jupyterhub config file::

    c.JupyterHub.authenticator_class = 'jhubauthenticators.DataRemoteUserAuthenticator'
    # Making 'State' a valid header to pass to /data
    c.DataRemoteUserAuthenticator.data_headers = ['State']

Beyond providing the custom header possibility, the authenticator also by default
encodes the Remote-User header with 'b32encode'. The authenticator therefore also provides
the possibility of storing the actual value for debugging purposes in the user.real_name
variable via the jupyterhub auth_state mechanism of passing information to
the spawner as noted at `Authenticators <https://jupyterhub.readthedocs
.io/en/stable/reference/authenticators.html>`_.