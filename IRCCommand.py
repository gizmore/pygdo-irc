from gdo.base.Method import Method
from gdo.base.Util import Strings
from gdo.core.GDO_Channel import GDO_Channel
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

    def irc_channel(self, name: str) -> GDO_Channel:
        return self._env_server.get_or_create_channel(name)

    def init_channel(self, param_num: int = 0) -> GDO_Channel:
        self._env_channel = self._env_server.get_or_create_channel(self._irc_params[param_num])
        return self._env_channel

    def is_own_user(self):
        return self._env_user.get_name() == self.irc_connector()._own_nick
