import asyncio

from gdo.base.Application import Application
from gdo.base.GDT import GDT
from gdo.base.Message import Message
from gdo.base.Render import Mode
from gdo.core.GDO_Session import GDO_Session
from gdo.core.GDT_UInt import GDT_UInt
from gdo.irc.IRCCommand import IRCCommand


class CMD_PRIVMSG(IRCCommand):

    def gdo_method_config_server(self) -> [GDT]:
        return [
            GDT_UInt('max_msg_len').initial('256'),
        ]

    def get_max_msg_len(self) -> int:
        return self.get_config_server_value('max_msg_len')

    async def gdo_execute(self) -> GDT:
        Application.mode(Mode.IRC)
        line = self._irc_params[1]
        self._env_user = await self.irc_user(self._irc_prefix)
        self._env_session = GDO_Session.for_user(self._env_user)
        rec_name = self._irc_params[0]
        if rec_name.startswith('#'):
            self._env_channel = self.irc_channel(rec_name)
        message = Message(line, Mode.IRC).env_copy(self).env_mode(Mode.IRC)
        await message.execute()
        return self.empty()
