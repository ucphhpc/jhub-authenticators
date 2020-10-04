from tornado import gen, web
from jupyterhub.auth import Authenticator
from jupyterhub.handlers.login import LogoutHandler
from traitlets import Dict, List, Type, Instance, Unicode, default
from ._jhub_shared import HeaderLoginHandler, UserDataHandler, Parser


class HeaderAuthenticator(Authenticator):
    """
    Authenticates the user via the allowed_headers
    defined 'auth' HTTP/HTTPS header.
    """

    allowed_headers = Dict(
        default_value={"auth": "Remote-User"},
        allow_none=False,
        help="""Dict of HTTP/HTTPS headers that the authenticator will process during login.
         The 'auth' key must be set to a header, default is Remote-User.
         Additional headers will be stored in the user's 'auth_state' session store
        """,
    ).tag(config=True)

    header_parser_classes = Dict(
        default_value={"auth": Parser},
        traits={Unicode(): Type(Parser, Parser)},
        allow_none=True,
        help="""Dict of classes that should be used to parse the allowed_headers dictionary
        """,
    ).tag(config=True)

    header_parsers = Dict({"auth": Instance(Parser)})

    @default("header_parsers")
    def _header_parsers_default(self):
        return {
            parser_key: parser_val(parent=self)
            for parser_key, parser_val in self.header_parser_classes.items()
        }

    spawner_shared_headers = List(
        default_value=[],
        allow_none=False,
        help="""List of headers that should be shared from the auth_state dict as environment
         variables to the spawner via the pre_spawn_start hook.
        """,
    ).tag(config=True)

    user_external_allow_attributes = List(
        default_value=[],
        traits=[Unicode()],
        allow_none=True,
        help="""List of user attributes that are allowed to be defined externally
         via a JSON post request. Submit via /user-data
        """,
    ).tag(config=True)

    def __init__(self, **kwargs):
        if "auth" not in self.allowed_headers:
            self.log.error(
                "HeaderAuthenticator - requires that the allowed_headers "
                "has an 'auth' key"
            )
            raise KeyError("Missing required 'auth' key in allowed_headers")
        super().__init__(**kwargs)

    def get_handlers(self, app):
        return [
            (r"/login", HeaderLoginHandler),
            (r"/logout", LogoutHandler),
            (r"/user-data", UserDataHandler),
        ]

    @gen.coroutine
    def authenticate(self, handler, data):
        self.log.debug(
            "HeaderAuthenticator - Request authentication with "
            "handler: {}, data: {} of type: {}".format(handler, data, type(data))
        )
        user_data = {}
        # Process remaining allowed_headers, save valid in user_data
        for allowed_index, allowed_value in self.allowed_headers.items():
            auth_data = data.get(allowed_value, "")
            if auth_data:
                prepared_data = None
                if allowed_index in self.header_parsers:
                    prepared_data = self.header_parsers[allowed_index].parse(auth_data)
                else:
                    prepared_data = data
                if prepared_data:
                    user_data[allowed_value] = prepared_data

        self.log.debug(
            "HeaderAuthenticator - Prepared user_data: {} "
            "for auth check".format(user_data)
        )
        if self.allowed_headers["auth"] not in user_data:
            self.log.error(
                "HeaderAuthenticator - Failed to find the 'auth' key "
                "in the user_data dictionary, this is required "
                "to set the authenticated user's username"
            )
            raise web.HTTPError(
                401,
                "Authentication failed, "
                "missing information to authenticate you with",
            )

        user = {"name": user_data.pop(self.allowed_headers["auth"], None)}
        # Something left in user_data, put in auth_state
        if user_data:
            user.update({"auth_state": user_data})

        self.log.info("Authenticated: {} - Login".format(user))
        return user

    @gen.coroutine
    def pre_spawn_start(self, user, spawner):
        """Pass upstream_token to spawner via environment variable"""
        auth_state = yield user.get_auth_state()
        if not auth_state:
            self.log.debug(
                "HeaderAuthenticator - pre_spawn_hook, "
                "auth_state: {}".format(auth_state)
            )
            # auth_state not enabled
            return

        self.log.debug(
            "HeaderAuthenticator - pre_spawn_hook, "
            "loaded auth_state {}".format(auth_state)
        )
        # Share permitted headers
        if not self.spawner_shared_headers:
            self.log.debug(
                "HeaderAuthenticator - no headers were "
                "shared with spawner environment: {}".format(
                    self.spawner_shared_headers
                )
            )
            return

        for auth_key, auth_val in auth_state.items():
            if auth_key in self.spawner_shared_headers:
                spawner.environment[auth_key] = auth_val
        self.log.debug(
            "HeaderAuthenticator - shared auth_state headers: {} with "
            "spawner environment: {}".format(
                self.spawner_shared_headers, spawner.environment
            )
        )
