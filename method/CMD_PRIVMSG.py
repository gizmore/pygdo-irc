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

    def gdo_execute(self):
        Application.mode(Mode.IRC)
        line = self._irc_params[1]
        self._env_user = self.irc_user(self._irc_prefix)

        self._env_session = GDO_Session.for_user(self._env_user)
        rec_name = self._irc_params[0]
        if rec_name.startswith('#'):
            self._env_channel = self.irc_channel(rec_name)

        message = Message(line, Mode.IRC).env_copy(self).env_mode(Mode.IRC)

        event_loop = self._env_server.get_connector()._event_loop
        asyncio.ensure_future(message.execute(), loop=event_loop)

        return self.empty()
