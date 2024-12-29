from gdo.base.Application import Application
from gdo.base.GDT import GDT
from gdo.base.Message import Message
from gdo.base.Render import Mode
from gdo.base.Trans import t
from gdo.irc.IRCCommand import IRCCommand
from gdo.irc.method.autologin import autologin


class CMD_330(IRCCommand):

    def gdo_execute(self) -> GDT:
        username = self._irc_params[0]
        user = self._env_server.get_or_create_user(username)
        user._authenticated = True
        original_message = autologin.__class__.PROBES[username][1]
        self._env_server.send_to_user(user, t('msg_autologin'))
        Application.MESSAGES.put(Message(original_message._message, Mode.IRC).env_copy(original_message))
        return self.empty()
