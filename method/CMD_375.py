from gdo.base.GDT import GDT
from gdo.irc.IRCCommand import IRCCommand
from gdo.irc.method.motd import motd


class CMD_375(IRCCommand):

    def gdo_execute(self) -> GDT:
        motd.MOTDS[self._env_server.get_id()] = ''
        return self.empty()
