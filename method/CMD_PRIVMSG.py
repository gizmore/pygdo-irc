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
        line = self._irc_params[1]
        self._env_user = self.irc_user(self._irc_prefix)
        self._env_session = GDO_Session.for_user(self._env_user)
        rec_name = self._irc_params[0]
        trigger = self._env_server.get_trigger()
        if rec_name[0] == '#':
            self._env_channel = self.irc_channel(rec_name)
            trigger = self._env_channel.get_trigger()

        message = Message(line, Mode.IRC).env_copy(self)
        Application.EVENTS.publish('new_message', message)

        if line.startswith(trigger):
            line = line[1:]
            message._message = line
            try:
                asyncio.run(message.execute())
            except Exception as ex:
                message._result = Application.get_page()._top_bar.render_irc()
                message._result += str(ex)
                asyncio.run(message.deliver())

        return self.empty()
