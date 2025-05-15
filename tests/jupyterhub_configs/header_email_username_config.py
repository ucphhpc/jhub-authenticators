"""A simple jupyter config file for testing the authenticator."""

from jhubauthenticators import RegexUsernameParser

c = get_config()

c.JupyterHub.authenticator_class = "jhubauthenticators.HeaderAuthenticator"
# Introduced in Jupyterhub 5.x https://jupyterhub.readthedocs.io/en/stable/reference/changelog.html#id25
# can be set to False if a user should be authorized after a succesfull authentication.
c.Authenticator.allow_all = True
# RegexUsernameParser
c.HeaderAuthenticator.header_parser_classes = {"auth": RegexUsernameParser}
# Email regex
RegexUsernameParser.username_extract_regex = (
    "([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)"
)
RegexUsernameParser.replace_extract_chars = {"@": "_", ".": "_"}
