from gdo.base.Application import Application
from gdo.base.Method import Method
from gdo.base.Util import Strings
from gdo.core.GDO_Channel import GDO_Channel
from gdo.core.GDO_User import GDO_User
from gdo.core.GDT_UserType import GDT_UserType
from gdo.irc.connector.IRC import IRC
import asyncio

class IRCCommand(Method):
    _irc_prefix: str
    _irc_params: list[str]
    SERVICE_BOTS = frozenset(('chanserv', 'nickserv'))

    @classmethod
    def gdo_trigger(cls) -> str:
        return ''

    def get_server_id(self) -> str:
        return self._env_server.get_id()

    def irc_connector(self) -> IRC:
        return self._env_server.get_connector()

    async def irc_user(self, prefix: str) -> GDO_User:
        username = Strings.substr_to(prefix, '!', prefix)
        user = self._env_user = await self._env_server.get_or_create_user(username)
        # IRC service accounts participate in NAMES/JOIN just like ordinary
        # nicks.  Keep their persistent type accurate so games and other
        # channel features can exclude them without special-casing names.
        if username.casefold() in self.SERVICE_BOTS and user.get_user_type() != GDT_UserType.BOT:
            user.save_val('user_type', GDT_UserType.BOT)
        Application.set_current_user(user)
        return user

    def irc_channel(self, name: str) -> GDO_Channel:
        return self._env_server.get_or_create_channel(name)

    def target_irc_channel(self, name: str) -> GDO_Channel:
        """Resolve an explicit IRC channel when invoked through another connector.

        Commands such as ``irc.join #channel`` are also useful from the TCP
        console.  Their connector must be the channel's IRC server, never the
        connector that delivered the command.
        """
        if isinstance(self._env_server.get_connector(), IRC):
            return self._env_server.get_or_create_channel(name)
        channel = GDO_Channel.table().get_by_name(name)
        if channel and isinstance(channel.get_server().get_connector(), IRC):
            self.env_server(channel.get_server()).env_channel(channel)
            return channel
        raise ValueError(f'Unknown IRC channel: {name}')

    def init_channel(self, param_num: int = 0) -> GDO_Channel:
        self._env_channel = self._env_server.get_or_create_channel(self._irc_params[param_num])
        return self._env_channel

    def is_own_user(self):
        return self._env_user.get_name().casefold() == self.irc_connector()._own_nick.casefold()
