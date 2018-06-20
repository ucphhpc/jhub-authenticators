from base64 import b32encode, b32decode
from jupyterhub.handlers import BaseHandler
from jupyterhub.auth import Authenticator
from jupyterhub.auth import LocalAuthenticator
from jupyterhub.utils import url_path_join
from tornado import gen, web
from traitlets import Unicode
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
    # multiple of 8 characters with no "=" padding,
    if len(input_str) % 8 != 0:
        padlen = 8 - (len(input_str) % 8)
        padding = "".join('=' for i in range(padlen))
        decode_str = "{}{}".format(input_str, padding)
    else:
        decode_str = input_str

    return str(b32decode(bytes(decode_str, 'utf-8')), 'utf-8')


class PartialBaseURLHandler(BaseHandler):
    """
    Fix against /base_url requests are not redirected to /base_url/home
    """

    def get(self):
        self.redirect(url_path_join(self.hub.server.base_url, 'home'))


class RemoteUserLoginHandler(BaseHandler):
    def get(self):
        header_name = self.authenticator.header_name
        remote_user = self.request.headers.get(header_name, "")
        if remote_user == "":
            raise web.HTTPError(401, "You are not authenticated to do this")
        else:
            safe_user = safeinput_encode(remote_user)
            user = self.user_from_username(safe_user)
            user.real_name = remote_user
            self.set_login_cookie(user)
            argument = self.get_argument("next", None, True)
            if argument is not None:
                self.redirect(argument)
            else:
                self.redirect(url_path_join(self.hub.server.base_url, 'home'))


class MountHandler(BaseHandler):
    """
    If the request is properly authenticated, check for Mount HTTP header,
    Excepts a string structure that can be interpreted by python
    The data is set to the user's mount attribute
    """

    @web.authenticated
    def post(self):
        header_name = self.authenticator.mount_header
        mount_header = self.request.headers.get(header_name, "")
        user = self.get_current_user().real_name
        if mount_header == "":
            raise web.HTTPError(403, "The request must contain a Mount "
                                     "header")
        else:
            try:
                mount_header_dict = literal_eval(mount_header)
            except ValueError as err:
                msg = "passed invalid Mount header format"
                self.log.error("User: {} - {} - {}".format(user, msg, err))
                raise web.HTTPError(403, "{}".format(msg))

            if type(mount_header_dict) is not dict:
                msg = "Mount header must be a dictionary"
                self.log.error("User: {} - {}".format(user, msg))
                raise web.HTTPError(403, "{}".format(msg))

            # Required keys
            required_keys = ['HOST', 'USERNAME',
                             'PATH', 'MOUNTSSHPRIVATEKEY']
            missing_keys = [key for key in required_keys if key
                            not in mount_header_dict]
            if len(missing_keys) > 0:
                msg = "Missing Mount header keys: {}" \
                    .format(",".join(missing_keys))
                self.log.error("User: {} - {}".format(user, msg))
                raise web.HTTPError(403, "{}".format(msg))

            self.log.debug("User: {} - Accepted mount header: {}"
                           .format(user, mount_header_dict))
            self.get_current_user().mount = mount_header_dict
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
        ]

    @gen.coroutine
    def authenticate(self, *args):
        raise NotImplementedError()


class MountRemoteUserAuthenticator(RemoteUserAuthenticator):
    """
    Accept the authenticated user name from the Remote-User HTTP header.
    In addition to this it also allows Mount to pass user mount data that allows
    the jhub to mount an external storage
    """
    header_name = Unicode(
        default_value='Remote-User',
        config=True,
        help="""HTTP header to inspect for the authenticated username.""")

    mount_header = Unicode(
        default_value='Mount',
        config=True,
        help="""HTTP header to inspect for the users mount information"""
    )

    # These paths are an extension of the prefix base url e.g. /dag/hub
    def get_handlers(self, app):
        # redirect baseurl e.g. /hub/ and /hub to /hub/home
        return [
            (app.base_url[:-1], PartialBaseURLHandler),
            (app.base_url, PartialBaseURLHandler),
            (r'/login', RemoteUserLoginHandler),
            (r'/mount', MountHandler),
        ]

    @gen.coroutine
    def authenticate(self, *args):
        raise NotImplemented()
