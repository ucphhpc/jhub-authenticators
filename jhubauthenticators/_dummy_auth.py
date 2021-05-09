from jupyterhub.auth import Authenticator
from traitlets import Unicode


class DummyAuthenticator(Authenticator):
    """
    Accepts any user as long as the password matches with the global password
    """

    password = Unicode(None, allow_none=True, config=True, help="""global password""")

    async def authenticate(self, handler, data):
        if data["password"] != self.password:
            return None
        else:
            return {"name": data["username"]}
