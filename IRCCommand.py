from gdo.base.Method import Method
from gdo.base.Util import Strings
from gdo.core.GDO_User import GDO_User
from gdo.irc.connector.IRC import IRC


class IRCCommand(Method):
    _irc_prefix: str
    _irc_params: list[str]

    def gdo_trigger(self) -> str:
        return ''

    def get_server_id(self) -> str:
        return self._env_server.get_id()

    def irc_connector(self) -> IRC:
        return self._env_server.get_connector()

    def irc_user(self, prefix: str) -> GDO_User:
        username = Strings.substr_to(prefix, '!', prefix)
        return self._env_server.get_or_create_user(username)

    def irc_channel(self, name: str):
        return self._env_server.get_or_create_channel(name)

    def is_own_user(self):
        return self._env_user.get_name() == self.irc_connector()._own_nick

