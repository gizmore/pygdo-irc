from gdo.base.Application import Application
from gdo.base.GDT import GDT
from gdo.base.Message import Message
from gdo.base.Render import Mode
from gdo.base.Trans import t
from gdo.irc.IRCCommand import IRCCommand
from gdo.irc.method.autologin import autologin


class CMD_330(IRCCommand):

    async def gdo_execute(self) -> GDT:
        user = self._env_server.get_or_create_user(self._irc_params[1])
        user._authenticated = True
        original_message = autologin.PROBES[user.get_name_sid()][1]
        await self._env_server.send_to_user(user, t('msg_autologin'))
        Application.MESSAGES.put(Message(original_message._message, Mode.IRC).env_copy(original_message))
        return self.empty()
