"""A simple jupyter config file for testing the authenticator."""

from jhubauthenticators import RegexUsernameParser

c = get_config()

c.JupyterHub.authenticator_class = "jhubauthenticators.HeaderAuthenticator"
c.Authenticator.allowed_users = ("mail_sdfsf_com", "fballam0_auda_org_au")
# RegexUsernameParser
c.HeaderAuthenticator.header_parser_classes = {"auth": RegexUsernameParser}
# Email regex
RegexUsernameParser.username_extract_regex = (
    "([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)"
)
RegexUsernameParser.replace_extract_chars = {"@": "_", ".": "_"}
