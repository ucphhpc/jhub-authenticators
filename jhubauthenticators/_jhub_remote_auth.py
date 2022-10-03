from jupyterhub.handlers import BaseHandler
from jupyterhub.utils import url_path_join
from tornado import gen, web
from ast import literal_eval


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
        self.redirect(url_path_join(self.hub.server.base_url, "home"))


class DataHandler(BaseHandler):
    """
    If the request is properly authenticated, check for a valid HTTP header,
    Excepts a string structure that can be interpreted by the ast module.
    If valid the passed information is appended to the authenticated user's state data
    dictionary where the header name is used as the key value.
    """

    @web.authenticated
    async def post(self):
        user_data = extract_headers(self.request, self.authenticator.data_headers)
        if not user_data:
            raise web.HTTPError(403, "No valid data header was received")

        self.log.debug("Prepared user_data dict: {}".format(user_data))
        user = await self.get_current_user()
        for k, d in user_data.items():
            # Try to parse the passed information into a valid dtype
            try:
                evaled_data = literal_eval(d)
            except ValueError as err:
                msg = "Failed to interpret the data header"
                self.log.error("User: {} - {}-{}-{}".format(user, d, msg, err))
                raise web.HTTPError(403, msg)

            self.log.debug(
                "User: {}-{} Accepted data header: {}".format(
                    user, user.name, evaled_data
                )
            )

            if not hasattr(user, "data"):
                user.data = {}
            user.data[k] = evaled_data
        self.redirect(url_path_join(self.hub.server.base_url, "home"))
