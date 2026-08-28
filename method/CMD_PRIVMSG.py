import asyncio

from gdo.base.Application import Application
from gdo.base.GDT import GDT
from gdo.base.Message import Message
from gdo.base.Render import Mode
from gdo.core.GDO_Session import GDO_Session
from gdo.core.GDT_UInt import GDT_UInt
from gdo.date.GDT_Duration import GDT_Duration
from gdo.irc.IRCCommand import IRCCommand
from gdo.irc.method.autologin import autologin


class CMD_PRIVMSG(IRCCommand):

    @classmethod
    def gdo_method_config_server(cls) -> list[GDT]:
        return [
            GDT_UInt('max_msg_len').initial('256'),
            # One reply per second is deliberately conservative for IRC.
            # Operators may adapt both values per server in the method config.
            GDT_Duration('flood_period').not_null().initial('1s').min(0),
            GDT_UInt('flood_burst').not_null().initial('1').min(1).max(20),
        ]

    def get_max_msg_len(self) -> int:
        return self.get_config_server_value('max_msg_len')

    async def gdo_execute(self) -> GDT:
        line = self._irc_params[1]
        self._env_user = await self.irc_user(self._irc_prefix)
        self._env_session = GDO_Session.for_user(self._env_user)
        rec_name = self._irc_params[0]
        if rec_name.startswith('#'):
            self._env_channel = self.irc_channel(rec_name)
        message = Message(line, Mode.render_irc).env_copy(self)
        if not self._env_user._authenticated:
            if not await autologin().env_copy(self).maybe_probe(self._env_user, message):
                pass
        return message.execute()
