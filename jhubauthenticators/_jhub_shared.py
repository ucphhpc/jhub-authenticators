import json
from re import search
from tornado import gen, web
from jupyterhub.handlers import BaseHandler
from jupyterhub.utils import url_path_join
from traitlets import CRegExp
from traitlets.config import LoggingConfigurable


class HeaderLoginHandler(BaseHandler):
    """
    Class that is used to handle whether the user is authenticated or not
    """

    @gen.coroutine
    def prepare(self):
        """ Checks whether the user is authenticated, if so
         the user is redirected to / hub.server.base_url / home """
        if self.get_current_user() is not None:
            self.log.info("User: {} is already authenticated"
                          .format(self.get_current_user(), self.get_current_user().name))
            self.redirect(url_path_join(self.hub.server.base_url, 'home'))
        else:
            headers = self.request.headers
            # Authenticate user
            user = yield self.login_user(headers)
            if not user:
                raise web.HTTPError(401, "The specified authentication method failed "
                                    "to authenticate you. Please contact the system "
                                    "adminsitrator for more information")

            argument = self.get_argument("next", None, True)
            if argument:
                self.redirect(argument)
            else:
                self.redirect(url_path_join(self.hub.server.base_url, 'home'))


class LogoutHandler(BaseHandler):

    @gen.coroutine
    def get(self):
        user = self.get_current_user()
        if user:
            self.clear_login_cookie()
        self.redirect(self.hub.server.base_url)


class Parser(LoggingConfigurable):

    def parse(self, data):
        return data


class RegexUsernameParser(Parser):

    username_extract_regex = CRegExp(
        default_value=None,
        allow_none=False,
        help="""Regex used to extract the jupyterhub username
    from the Remote - User header"""
    ).tag(config=True)

    def parse(self, data):
        if not data:
            self.log.error("RegexUsernameParser - Didn't "
                           "receive any input missing data: {}".format(data))
            return None

        if not isinstance(data, str):
            self.log.error("RegexUsernameParser - Incorrect type was attempted to "
                           "be parsed, requires str but "
                           "data is of type: {}".format(type(data)))
            return None

        username = data
        match = search(self.username_extract_regex,
                       username)
        if not match:
            self.log.error("RegexUsernameParser - Failed to find a valid "
                           "regex match with pattern: {} in {}".format(
                               self.username_extract_regex, username))
            return None
        groups = match.groups()
        if not groups:
            self.log.error("RegexUsernameParser - No username_extract_regex "
                           "matches found in: {}".format(username))
            return None
        if len(groups) > 1:
            self.log.error("RegexUsernameParser - username_extract_regex "
                           "More than 1 match was found in: {}".format(username))
            return None
        username = groups[0]
        self.log.debug("RegexUsernameParser - Found username_extract_regex "
                       "matched: {}".format(username))
        return username


class JSONParser(Parser):

    json_types = (str, bytes, bytearray)

    def parse(self, data):
        if not data:
            self.log.error("JSONParser - Didn't "
                           "receive any input missing data: {}".format(data))
            return None
        self.log.debug("JSONParser - Data: {}, type: {}".format(data, type(data)))
        if not isinstance(data, JSONParser.json_types):
            self.log.error("JSONParser - data: {} is of an incorrect type: {} "
                           "must be one of type: {}".format(
                               data, type(data), JSONParser.json_types
                           ))
            return None

        json_obj = json.loads(data)
        return json_obj
