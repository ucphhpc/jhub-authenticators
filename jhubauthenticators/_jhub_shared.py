import json
from json import JSONDecodeError
from re import search
from tornado import gen, web
from tornado.escape import json_decode
from jupyterhub.handlers import BaseHandler
from jupyterhub.utils import url_path_join
from traitlets import CRegExp, Dict
from traitlets.config import LoggingConfigurable


class HeaderLoginHandler(BaseHandler):
    """
    Class that is used to handle whether the user is authenticated or not
    """

    @gen.coroutine
    def prepare(self):
        """ Checks whether the user is authenticated, if so
         the user is redirected to / hub.server.base_url / home """
        user = yield self.get_current_user()
        if user:
            if hasattr(user, "name"):
                self.log.info("User: {} is already authenticated".format(user.name))

            argument = self.get_argument("next", None, True)
            if argument:
                self.redirect(argument)
            else:
                self.redirect(url_path_join(self.hub.server.base_url, "home"))
        else:
            # You need to authenticate first
            headers = self.request.headers
            # Authenticate user
            user = yield self.login_user(headers)
            if not user:
                raise web.HTTPError(
                    401,
                    "The specified authentication method failed "
                    "to authenticate you. Please contact the system "
                    "adminsitrator for more information",
                )

            argument = self.get_argument("next", None, True)
            if argument:
                self.redirect(argument)
            else:
                self.redirect(url_path_join(self.hub.server.base_url, "home"))


class UserDataHandler(BaseHandler):
    """
    Handles the post requests where an authenticated user want's to set an
    internal user attribute with a JSON body.
    """

    @web.authenticated
    @gen.coroutine
    def post(self):
        user = yield self.get_current_user()
        self.log.debug(
            "UserDataHandler - Request: {}, "
            "Body: {}".format(self.request, self.request.body)
        )
        data = None
        try:
            data = json_decode(self.request.body)
        except JSONDecodeError as err:
            self.log.error(
                "UserDataHandler - Failed to json decode: {}, err: {}".format(data, err)
            )
            raise web.HTTPError(500, "Failed to parse user data input")

        if not data:
            self.log.debug(
                "UserDataHandler - no json data was received: {}".format(
                    self.request.json
                )
            )
            raise web.HTTPError(
                403, "No data was recieved that can be used" " to set an attribute"
            )
        self.log.debug(
            "UserDataHandler - Received: {} as a user json data post".format(data)
        )

        if not isinstance(data, dict):
            self.log.error(
                "UserDataHandler - invalid internal json post structure, "
                "expects: {}, recieved: {}".format(dict, type(data))
            )
            raise web.HTTPError(403, "An invalid data type was recieved")

        valid_attributes = self.authenticator.user_external_allow_attributes
        if not valid_attributes:
            raise web.HTTPError(
                500,
                "No attributes were enabled to be defined via "
                "user data, Please contact an administrator "
                "to resolve this",
            )

        for valid_attr in valid_attributes:
            data_val = data.get(valid_attr, "")
            if data_val:
                try:
                    setattr(user, valid_attr, data_val)
                except AttributeError as err:
                    self.log.error(
                        "UserDataHandler - Failed to set attribute: {} "
                        "to value: {}, err: {}".format(
                            "self.spawner.user." + valid_attr, data_val, err
                        )
                    )
            else:
                self.log.debug(
                    "UserDataHandler - {} was not found "
                    "recieved data: {}".format(valid_attr, data)
                )


class Parser(LoggingConfigurable):
    def parse(self, data):
        return data


class RegexUsernameParser(Parser):

    username_extract_regex = CRegExp(
        default_value=None,
        allow_none=False,
        help="""Regex used to extract the jupyterhub username
    from the Remote - User header""",
    ).tag(config=True)

    replace_extract_chars = Dict(
        default_value=None,
        allow_none=True,
        help="""Dict of 'key' identified character(s) in the regex extract result that
        should be replaced with 'value' character(s).

        E.g: replace every '@' with a '.'
        replace_extract_chars = {'@': '.'}
        """,
    ).tag(config=True)

    def parse(self, data):
        if not data:
            self.log.error(
                "RegexUsernameParser - Didn't "
                "receive any input missing data: {}".format(data)
            )
            return None

        if not isinstance(data, str):
            self.log.error(
                "RegexUsernameParser - Incorrect type was attempted to "
                "be parsed, requires str but "
                "data is of type: {}".format(type(data))
            )
            return None

        username = data
        match = search(self.username_extract_regex, username)
        if not match:
            self.log.error(
                "RegexUsernameParser - Failed to find a valid "
                "regex match with pattern: {} in {}".format(
                    self.username_extract_regex, username
                )
            )
            return None
        groups = match.groups()
        if not groups:
            self.log.error(
                "RegexUsernameParser - No username_extract_regex "
                "matches found in: {}".format(username)
            )
            return None
        if len(groups) > 1:
            self.log.error(
                "RegexUsernameParser - username_extract_regex "
                "More than 1 match was found in: {}".format(username)
            )
            return None
        username = groups[0]
        self.log.debug(
            "RegexUsernameParser - Found username_extract_regex "
            "matched: {}".format(username)
        )

        if self.replace_extract_chars:
            self.log.debug(
                "RegexUsernameParser - replace_extract_chars "
                "{}".format(self.replace_extract_chars)
            )
            for replace_key, replace_val in self.replace_extract_chars.items():
                username = username.replace(replace_key, replace_val)
            self.log.info(
                "RegexUsernameParser - username post replace_extract_chars: "
                " {}".format(username)
            )
        return username


class JSONParser(Parser):

    json_types = (str, bytes, bytearray)

    def parse(self, data):
        if not data:
            self.log.error(
                "JSONParser - Didn't " "receive any input missing data: {}".format(data)
            )
            return None
        self.log.debug("JSONParser - Data: {}, type: {}".format(data, type(data)))
        if not isinstance(data, JSONParser.json_types):
            self.log.error(
                "JSONParser - data: {} is of an incorrect type: {} "
                "must be one of type: {}".format(
                    data, type(data), JSONParser.json_types
                )
            )
            return None

        json_obj = json.loads(data)
        return json_obj
