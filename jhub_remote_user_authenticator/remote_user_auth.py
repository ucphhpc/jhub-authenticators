import os
from jupyterhub.handlers import BaseHandler
from jupyterhub.auth import Authenticator
from jupyterhub.auth import LocalAuthenticator
from jupyterhub.utils import url_path_join
from tornado import gen, web
from traitlets import Unicode
from ast import literal_eval


class RemoteUserLoginHandler(BaseHandler):
    def get(self):
        header_name = self.authenticator.header_name
        remote_user = self.request.headers.get(header_name, "")
        if remote_user == "":
            raise web.HTTPError(401)
        else:
            user = self.user_from_username(remote_user)
            self.set_login_cookie(user)
            self.redirect(url_path_join(self.hub.server.base_url, 'home'))


class MIGMountHandler(BaseHandler):
    def get(self):
        user = self.get_current_user()
        if user is None:
            raise web.HTTPError(401)
        else:
            self.log.warning("Hello from mount handler")
            header_name = self.authenticator.mount_header
            mount_header = self.request.headers.get(header_name, "")
            if mount_header == "":
                raise web.HTTPError(404)
            else:
                user.mig_mount = literal_eval(mount_header)

class RemoteUserAuthenticator(Authenticator):
    """
    Accept the authenticated user name from the REMOTE_USER HTTP header.
    """
    header_name = Unicode(
        default_value='REMOTE_USER',
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
    Accept the authenticated user name from the REMOTE_USER HTTP header.
    Derived from LocalAuthenticator for use of features such as adding
    local accounts through the admin interface.
    """
    header_name = Unicode(
        default_value='REMOTE_USER',
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
    Accept the authenticated user name from the REMOTE_USER HTTP header.
    In addition to this it also allows MIG to pass user mount data that allows the jhub to mount the MIG home drive
    for that particular user
    """
    header_name = Unicode(
        default_value='REMOTE_USER',
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
