.. image:: https://travis-ci.org/rasmunk/jhub-authenticators.svg?branch=master
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

    c.JupyterHub.authenticator_class = 'jhub-authenticators.RemoteUserAuthenticator'

You should be able to start jupyterhub.  The "/login" resource
will look for the authenticated user name in the HTTP header "Remote-User".
If found, and not blank, you will be logged in as that user.

Alternatively, you can use `RemoteUserLocalAuthenticator`::

    c.JupyterHub.authenticator_class = 'jhub-authenticators.RemoteUserLocalAuthenticator'

This provides the same authentication functionality but is derived from
`LocalAuthenticator` and therefore provides features such as the ability
to add local accounts through the admin interface if configured to do so.

-------------------------------------------------------------
Remote User Authentication extended with Mount capability
-------------------------------------------------------------

Provides the capability to supply the jupyterhub user with a set of ssh keys that can later be used to mount that particular user's homedrive, the extended authenticator can be activated by setting the following option in the jupyterhub config file::

    c.JupyterHub.authenticator_class = 'jhub-authenticators.MountRemoteUserAuthenticator'
    
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
