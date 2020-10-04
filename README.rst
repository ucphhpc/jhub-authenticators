=========================
Jupyterhub Authenticators
=========================
.. image:: https://travis-ci.com/rasmunk/jhub-authenticators.svg?branch=master
    :target: https://travis-ci.com/rasmunk/jhub-authenticators
.. image:: https://badge.fury.io/py/jhub-authenticators.svg
    :target: https://badge.fury.io/py/jhub-authenticators

An extended collection of HTTP(S) header JupyterHub Authenticators that relies on proxy authenticating.
Every mentioned authenticator should be used while following
the mentioned security recommendations at `cwaldbieser <https://github.com/cwaldbieser/jhub_remote_user_authenticator/blob/master/README.rst#architecture-and-security-recommendations>`_.

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

You should edit your ``jupyterhub_config.py`` config file to set the
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

-----------------------------------------------------------------------------------------------------
Remote User Authentication extended with user-defined headers (Deprecated, use Header Authentication)
-----------------------------------------------------------------------------------------------------

Provides the capability to supply the jupyterhub user with additional state information
via the /data path. This adds two base request paths to the jupyterhub web application::

'/login' -> requires a non empty Remote-User header
'/data' -> requires both an authenticated request and a valid configured header

Before information can be passed to the user via the ``/data`` path, a list of valid
headers is required. These preset valid headers are then upon a POST request to the
``/data`` URl appended to the current authenticated jupyterhub user data dictionary. I.e.
user.data[Header] = HeaderValue

The extended authenticator can be activated by setting the following option in the
jupyterhub config file::

    c.JupyterHub.authenticator_class = 'jhubauthenticators.DataRemoteUserAuthenticator'
    # Making 'State' a valid header to pass to /data
    c.DataRemoteUserAuthenticator.data_headers = ['State']

Beyond providing the custom header possibility, the authenticator also by default
encodes the Remote-User header with ``b32encode``. The authenticator therefore also provides
the possibility of storing the actual value for debugging purposes in the user.real_name
variable via the jupyterhub auth_state mechanism of passing information to
the spawner as noted at `Authenticators <https://jupyterhub.readthedocs
.io/en/stable/reference/authenticators.html>`_.

---------------------
Header Authentication
---------------------

This Header Authentication method provides multiple functionalities beyond mere authentication, and should in the future 
replace the RemoteUserAuthenticator and DataRemoteUserAuthenticator. It can activated by adding the following to the JupyterHub configuration::

    c.JupyterHub.authenticator_class = 'jhubauthenticators.HeaderAuthenticator'
    
By default, it exposes the following paths::

    '/login' -> is utilizied to authenticate the user, relies on the 'allowed_headers' parameter to accomplish this.
    '/logout' -> clears the users authenticated session.
    '/user-data' -> allows an authenticated user to provide data to be persisted during the authenticated session. Controlled via 'user_external_allow_attributes' parameter.

Specify Authentication Header
-----------------------------

First it provides the possibility to define a custom authentication header,
this is accomplished by overriding the default allowed_headers dict required ``auth`` key::

    c.HeaderAuthenticator.allowed_headers = {'auth': 'MyAuthHeader'}

This will overrive the default ``Remote-User`` header authentication to use the ``MyAuthHeader`` instead.

Additional User Data Headers
----------------------------
Beyond the ``auth`` key, the administrator is allowed to set additional headers that the authenticator will accept requests on.

For instance, if the ``MyCustomHeader`` should be accepted as well during authentication::

    c.HeaderAuthenticator.enable_auth_state = True
    c.HeaderAuthenticator.allowed_headers = {'auth': 'MyAuthHeader',
                                             'auth_data': 'MyCustomHeader'}

Any information provided via the ``MyCustomHeader`` during authentication will be added to the JupyterHub user's ``auth_state``,
dictionary as defined by `Authenticators auth_state <https://jupyterhub.readthedocs.io/en/stable/reference/authenticators.html#authentication-state>`_. The data will be added to the ``auth_state`` by utilizing the header value in the 
``allowed_headers`` dictionary as the key in the 'auth_state' dictionary. For instance the above configuration, will produce the following user profile::

    user = {
        name: 'stored MyAuthHeader value',
        'auth_state': {'MyCustomHeader': 'stored MyCustomHeader value'}
    }

It's important to note here, that this information is only persisted for the life-time of the authenticated session.

Sharing auth_state data with Spawner Environement
-------------------------------------------------
If any of the defined ``auth_state`` key-value pairs should be set as Spawner environement variables before a notebook is spawned, the ``spawner_shared_headers`` parameter is available to define this, E.g if the "MyCustomHeader' should do this, it can be accomplished with the following addition to the configuration::

    c.HeaderAuthenticator.spawner_shared_headers = ['MyCustomHeader']

Which during `pre_spawn_hook <https://jupyterhub.readthedocs
.io/en/stable/reference/authenticators.html>`_ will produce the following environment variable::

    ~>env | grep MyCustomHeader

    MyCustomHeader="stored MyCustomHeader value"


Special Parsers
---------------
If the administrator requires that the defined ``allowed_headers`` should be parsed in a special way.
The administrator can use the ``header_parser_classes`` parameter to define how a request with a particular header should be parsed, E.g::
    
    from jhubauthenticators import Parser, JSONParser

    c.HeaderAuthenticator.header_parser_classes = {'auth': Parser,
                                                   'auth_data': JSONParser}

The ``auth`` header is here set to be parsed by the default Parser, which just returns the provided value unchanged.
The JSONParser, however does what it indicated, attempts to parse the data as JSON.

In addition to these, the authenticator also provides the ``RegexUsernameParser`` which can be used as an ``auth`` parser, E.g::

    # RegexUsernameParser
    c.HeaderAuthenticator.header_parser_classes = {'auth': RegexUsernameParser}
    # Email regex
    RegexUsernameParser.username_extract_regex = '([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)'

Which will try to expand an email from the defined ``auth`` allowed_headers Header. If this can't be accomplished, the user will not be authenticated.

Related to the ``username_extract_regex``, the ``RegexUsernameParser.replace_extract_chars`` parameter exists to accomplish post filtering of illegal characters on the extracted username, E.g::

    # Replace every '@' and '.' char in the extracted username with '_'
    RegexUsernameParser.replace_extract_chars = {'@': '_', '.': '_'}

It is possible to define additional parsers by extending the Parser class and implementing the required parse method, E.g::

    class MyParser(Parser)

        # MyAdvancedParser
        def parse(self, data)
            return data

Which can subsequently be activate by adding it to the ``header_parser_classes`` parameter, E.g.::

    # MyAdvancedParser
    c.HeaderAuthenticator.header_parser_classes = {'auth': MyParser}

Set User state after Authentication
-----------------------------------

Finally, the HeaderAuthenticator also provides the administrator the possibility to define the ``user_external_allow_attributes`` parameter.
This allows defines which user attributes an authenticated user is allowed to set the ``user.data`` variable via the ``/user-data`` URL, E.g::

    c.HeaderAuthenticator.user_external_allow_attributes = ['data']

By default the ``user_external_allow_attributes`` allows no such attributes and has to be explicitly enabled/defined.
In addition, any posted value to the ``/user-data`` path
The provided data on this URL, has to be decodable as JSON or it will fail.

Additional configuration examples can be found in the ``tests/jupyterhub_configs`` directory.
