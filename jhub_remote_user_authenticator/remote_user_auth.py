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


class RemoteUserLoginHandler(BaseHandler):
    def get(self):
        header_name = self.authenticator.header_name
        remote_user = self.request.headers.get(header_name, "")
        if remote_user == "":
            raise web.HTTPError(401, "You are not authenticated to do this")
        else:
            safe_user = safeinput_encode(remote_user)
            user = self.user_from_username(safe_user)
            self.set_login_cookie(user)
            self.redirect(url_path_join(self.hub.server.base_url, 'home'))


class MIGMountHandler(BaseHandler):
    """
    If the request is properly authenticated, check for Mig-Mount HTTP header,
    Excepts a string structure that can be interpreted by python
    The data is set to the user's mig_mount attribute
    """

    def get(self):
        user = self.get_current_user()
        if user is None:
            raise web.HTTPError(401)
        else:
            header_name = self.authenticator.mount_header
            mount_header = self.request.headers.get(header_name, "")
            if mount_header == "":
                raise web.HTTPError(404,
                                    "A valid mount header was not present")
            else:
                user.mig_mount = literal_eval(mount_header)


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


class MIGMountRemoteUserAuthenticator(RemoteUserAuthenticator):
    """
    Accept the authenticated user name from the Remote-User HTTP header.
    In addition to this it also allows MIG to pass user mount data that allows
    the jhub to mount the MIG home drive for that particular user
    """
    header_name = Unicode(
        default_value='Remote-User',
        config=True,
        help="""HTTP header to inspect for the authenticated username.""")

    mount_header = Unicode(
        default_value='Mig-Mount',
        config=True,
        help="""HTTP header to inspect for the users mount information"""
    )

    def get_handlers(self, app):
        return [
            (r'/login', RemoteUserLoginHandler),
            (r'/mount', MIGMountHandler)
        ]

    @gen.coroutine
    def authenticate(self, *args):
        raise NotImplemented()
