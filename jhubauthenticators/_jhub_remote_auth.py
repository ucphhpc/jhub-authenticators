import re
from base64 import b32encode, b32decode
from jupyterhub.handlers import BaseHandler
from jupyterhub.auth import Authenticator
from jupyterhub.auth import LocalAuthenticator
from jupyterhub.utils import url_path_join
from tornado import gen, web
from traitlets import Unicode, List
from ast import literal_eval


def safeinput_encode(input_str):
    """
    :param input_str: string
    :return: b32encoded utf-8 string with stripped padding equals
    """
    encoded_str = str(b32encode(bytes(input_str, 'utf-8')), 'utf-8')
    return encoded_str.replace('=', '')


def safeinput_decode(input_str):
    """
    :param input_str: expects a b32encoded utf-8 string
    :return: a decoded utf-8 string
    """
    # Encoder removed "=" padding to satisfy validate_input
    # Pad with "="" according to:
    # https://tools.ietf.org/html/rfc3548 :
    # (1) the final quantum of encoding input is an integral multiple of 40
    # bits; here, the final unit of encoded output will be an integral
    # multiple of 8 characters with no "=" padding.
    if len(input_str) % 8 != 0:
        padlen = 8 - (len(input_str) % 8)
        padding = "".join('=' for i in range(padlen))
        decode_str = "{}{}".format(input_str, padding)
    else:
        decode_str = input_str

    return str(b32decode(bytes(decode_str, 'utf-8')), 'utf-8')


def extract_headers(request, headers):
    user_data = {}
    for i, header in enumerate(headers):
        value = request.headers.get(header, "")
        if value:
            try:
                user_data[header] = value
            except KeyError:
                pass
    return user_data


class PartialBaseURLHandler(BaseHandler):
    """
    Fix against /base_url requests are not redirected to /base_url/home
    """
    @web.authenticated
    @gen.coroutine
    def get(self):
        self.redirect(url_path_join(self.hub.server.base_url, 'home'))


class RemoteUserLogoutHandler(BaseHandler):

    @gen.coroutine
    def get(self):
        user = self.get_current_user()
        if user:
            self.clear_login_cookie()
        self.redirect(self.hub.server.base_url)


class RemoteUserLoginHandler(BaseHandler):

    @gen.coroutine
    def prepare(self):
        """ login user """
        if self.get_current_user() is not None:
            self.log.info("User: {} is already authenticated"
                          .format(self.get_current_user(), self.get_current_user().name))
            self.redirect(url_path_join(self.hub.server.base_url, 'home'))
        else:
            user_data = extract_headers(self.request, self.authenticator.auth_headers)
            if 'Remote-User' not in user_data:
                raise web.HTTPError(401, "You are not Authenticated to do this")
            yield self.login_user(user_data)

            argument = self.get_argument("next", None, True)
            if argument is not None:
                self.redirect(argument)
            else:
                self.redirect(url_path_join(self.hub.server.base_url, 'home'))


class DataHandler(BaseHandler):
    """
    If the request is properly authenticated, check for a valid HTTP header,
    Excepts a string structure that can be interpreted by the ast module.
    If valid the passed information is appended to the authenticated user's state data
    dictionary where the header name is used as the key value.
    """

    @web.authenticated
    @gen.coroutine
    def post(self):
        user_data = extract_headers(self.request,
                                    self.authenticator.data_headers)
        if not user_data:
            raise web.HTTPError(403, "No valid data header was received")

        user = self.get_current_user()
        for k, d in user_data.items():
            # Try to parse the passed information into a valid dtype
            try:
                evaled_data = literal_eval(d)
            except ValueError as err:
                msg = "Failed to interpret the data header"
                self.log.error("User: {} - {}-{}-{}".format(
                    user, d, msg, err))
                raise web.HTTPError(403, msg)

            self.log.info("User: {}-{} Accepted data header: {}".format(
                user, user.name, evaled_data
            ))

            if not hasattr(user, 'data'):
                user.data = {}
            user.data[k] = evaled_data
        self.redirect(url_path_join(self.hub.server.base_url, 'home'))


class RemoteUserAuthenticator(Authenticator):
    """
    Accept the authenticated user name from the Remote-User HTTP header.
    """
    header_name = Unicode(
        default_value='Remote-User',
        config=True,
        help="""HTTP header to inspect for the authenticated username.""")

    def get_handlers(self, app):
        return [
            (r'/login', RemoteUserLoginHandler),
            (r'/logout', RemoteUserLogoutHandler)
        ]

    @gen.coroutine
    def authenticate(self, *args):
        raise NotImplementedError()


class RemoteUserLocalAuthenticator(LocalAuthenticator):
    """
    Accept the authenticated user name from the Remote-User HTTP header.
    Derived from LocalAuthenticator for use of features such as adding
    local accounts through the admin interface.
    """
    header_name = Unicode(
        default_value='Remote-User',
        config=True,
        help="""HTTP header to inspect for the authenticated username.""")

    def get_handlers(self, app):
        return [
            (r'/login', RemoteUserLoginHandler),
            (r'/logout', RemoteUserLogoutHandler)
        ]

    @gen.coroutine
    def authenticate(self, *args):
        raise NotImplementedError()


class DataRemoteUserAuthenticator(RemoteUserAuthenticator):
    """
    An Authenticator that supports dynamic header information
    """

    auth_headers = List(
        default_value=['Remote-User'],
        config=True,
        help="""List of allowed HTTP headers to get from user data"""
    )

    data_headers = List(
        default_value=[],
        config=True,
        help="""List of allowed data headers"""
    )

    # These paths are an extension of the prefix base url e.g. /dag/hub
    def get_handlers(self, app):
        return [
            (r'/login', RemoteUserLoginHandler),
            (r'/logout', RemoteUserLogoutHandler),
            (r'/data', DataHandler),
        ]

    @gen.coroutine
    def authenticate(self, hander, data):
        if 'Remote-User' not in data:
            self.log.info("A Remote-User header is required")
            return None

        # Login
        real_name = data['Remote-User'].lower()
        encoded_name = safeinput_encode(data['Remote-User']).lower()
        user = {
            'name': encoded_name,
            'auth_state': {
                'real_name': real_name
            }
        }
        self.log.info("Authenticated: {} - Login".format(user))
        return user

    @gen.coroutine
    def pre_spawn_start(self, user, spawner):
        """Pass upstream_token to spawner via environment variable"""
        auth_state = yield user.get_auth_state()
        if not auth_state:
            # auth_state not enabled
            return

        if isinstance(auth_state, dict) and 'real_name' in auth_state:
            # Make it alphanumeric
            pattern = re.compile('[\W_]+', re.UNICODE)
            user.real_name = pattern.sub('', auth_state['real_name'])
            self.log.debug("Pre-Spawn: {} set user real_name {}".format(
                user, user.real_name))
