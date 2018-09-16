.. image:: https://travis-ci.org/rasmunk/jhub-authenticators.svg?branch=devel
    :target: https://travis-ci.org/rasmunk/jhub-authenticators

====================================
Jupyterhub Remote-User Authenticator
====================================

Authenticate to Jupyterhub using an authenticating proxy that can set
the Remote-User header.
Also supports for passing additional information to the jupyter user. This includes a
Mount header.

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

-------------------------------------------------------------
Remote User Authentication extended with Mount capability
-------------------------------------------------------------

Provides the capability to supply the jupyterhub user with additional state information
via the /mount path, it accepts a stringified dictionary with a mount key that can
later be used to mount that particular user's homedrive, the extended authenticator
can be activated by setting the following option in the jupyterhub config file::

    c.JupyterHub.authenticator_class = 'jhubauthenticators.MountRemoteUserAuthenticator'

Beyond providing the Mount header possibility, the authenticator also by default
encodes the Remote-User header with 'b32encode'. The authenticator therefore also provides
the possibility of storing the actual value for debugging purposes in the user.real_name
variable via the jupyterhub auth_state mechanism of passing information to
the spawner as noted on `Authenticators <https://jupyterhub.readthedocs
.io/en/stable/reference/authenticators.html>`_.

This adds two base request paths to the jupyterhub web application::

'/login' -> requires a non empty Remote-User header
'/mount' -> requires both a non empty Remote-User and Mount header

The expected format of the Mount header is that the passed string can be evaluated to a python dictionary via::

            try:
                mount_header_dict = literal_eval(mount_header)

The internal format of the Mount header is not evaluated, this is dependent on the underlying mount implementation and should be verified there.

Note:
=====
Upon successful parsing of the header, the active jupyterhub user instance is appended with a 'mount' property that contains the accepted dictionary header.
