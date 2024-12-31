from gdo.base.Application import Application
from gdo.base.GDT import GDT
from gdo.irc.IRCCommand import IRCCommand


class CMD_001(IRCCommand):

    def gdo_execute(self) -> GDT:
        Application.EVENTS.publish(f'irc_connected', self._env_server, self)
        self.irc_connector().setup_dog_user(self._irc_params[0])
        return self.empty()
