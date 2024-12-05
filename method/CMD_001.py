from gdo.base.Application import Application
from gdo.irc.IRCCommand import IRCCommand


class CMD_001(IRCCommand):

    def gdo_execute(self):
        Application.EVENTS.publish(f'irc_connected', self._env_server, self)
        self._env_server.get_connector().setup_dog_user(self._irc_params[0])
        return self.empty()
