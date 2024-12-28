from gdo.base.Application import Application
from gdo.irc.IRCCommand import IRCCommand


class CMD_NOTICE(IRCCommand):

    def gdo_execute(self):
        # Application.EVENTS.publish(f'irc{self._env_server.get_id()}_notice', self)
        pass
