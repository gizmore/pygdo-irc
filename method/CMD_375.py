from gdo.irc.IRCCommand import IRCCommand
from gdo.irc.method.motd import motd


class CMD_375(IRCCommand):

    def gdo_execute(self):
        motd.MOTDS[self._env_server.get_id()] = ''


