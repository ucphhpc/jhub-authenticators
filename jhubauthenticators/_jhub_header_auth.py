from tornado import gen, web
from jupyterhub.auth import Authenticator
from traitlets import Dict, List, Type, Instance, Unicode, default
from ._jhub_shared import HeaderLoginHandler, LogoutHandler, Parser


class HeaderAuthenticator(Authenticator):
    """
    Accept the authenticated user name from the Remote-User HTTP header.
    """
    allowed_headers = Dict(
        default_value={'auth': 'Remote-User'},
        allow_none=False,
        help="""Dict of HTTP/HTTPS headers that the authenticator will process.
         The 'auth' key must be set to a header, default is Remote-User
        """
    ).tag(config=True)

    header_parser_classes = Dict(
        default_value={'auth': Parser},
        traits={Unicode(): Type(Parser, Parser)},
        allow_none=True,
        help="""Dict of classes that should be used to parse the allowed_headers dictionary
        """
    ).tag(config=True)

    header_parsers = Dict({'auth': Instance(Parser)})

    @default('header_parsers')
    def _header_parsers_default(self):
        return {parser_key: parser_val(parent=self)
                for parser_key, parser_val in self.header_parser_classes.items()}

    spawner_shared_headers = List(
        default_value=[],
        allow_none=False,
        config=True,
        help=""" List of headers that should be shared from the auth_state dict as environment
         variables to the spawner via the pre_spawn_start hook.
        """
    )

    def __init__(self, **kwargs):
        if 'auth' not in self.allowed_headers:
            self.log.error("HeaderAuthenticator - requires that the allowed_headers "
                           "has an 'auth' key")
            raise KeyError("Missing required 'auth' key in allowed_headers")
        super().__init__(**kwargs)

    def get_handlers(self, app):
        return [
            (r'/login', HeaderLoginHandler),
            (r'/logout', LogoutHandler)
        ]

    @gen.coroutine
    def authenticate(self, handler, data):
        self.log.debug("HeaderAuthenticator - Request authentication with "
                       "handler: {}, data: {} of type: {}".format(handler, data,
                                                                  type(data)))
        user_data = {}
        # Process remaining allowed_headers, save valid in user_data
        for auth_index, auth_value in self.allowed_headers.items():
            auth_data = data.get(auth_value, '')
            if auth_data:
                prepared_data = None
                if auth_index in self.header_parsers:
                    prepared_data = self.header_parsers[auth_index].parse(auth_data)
                else:
                    prepared_data = data
                if prepared_data:
                    user_data[auth_value] = prepared_data

        self.log.debug("HeaderAuthenticator - Prepared user_data: {} "
                       "for auth check".format(user_data))
        if self.allowed_headers['auth'] not in user_data:
            self.log.error("HeaderAuthenticator - Failed to find the 'auth' key "
                           "in the user_data dictionary, this is required "
                           "to set the authenticated user's username")
            raise web.HTTPError(401, "Authentication failed, "
                                "missing information to authenticate you with")

        user = {
            'name': user_data.pop(self.allowed_headers['auth'], None)
        }
        # Something left in user_data, put in auth_state
        if user_data:
            user.update({'auth_state': user_data})

        self.log.info("Authenticated: {} - Login".format(user))
        return user

    @gen.coroutine
    def pre_spawn_start(self, user, spawner):
        """Pass upstream_token to spawner via environment variable"""
        auth_state = yield user.get_auth_state()
        if not auth_state:
            self.log.debug("HeaderAuthenticator - pre_spawn_hook, "
                           "auth_state: {}".format(auth_state))
            # auth_state not enabled
            return None

        self.log.debug("HeaderAuthenticator - pre_spawn_hook, "
                       "loaded auth_state {}".format(auth_state))
        # Share permitted headers
        if not self.spawner_shared_headers:
            self.log.debug("HeaderAuthenticator - no headers were "
                           "shared with spawner environment: {}".format(
                               self.spawner_shared_headers))
            return None

        for auth_key, auth_val in auth_state.items():
            if auth_key in self.spawner_shared_headers:
                spawner.environment[auth_key.upper()] = auth_val
        self.log.debug("HeaderAuthenticator - shared auth_state headers: {} with "
                       "spawner environment: {}".format(self.spawner_shared_headers,
                                                        spawner.environment))
