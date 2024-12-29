from gdo.base.GDT import GDT
from gdo.irc.IRCCommand import IRCCommand


class CMD_433(IRCCommand):

    def gdo_execute(self) -> GDT:
        self._env_server.get_connector().send_nick_cmd()
        return self.empty()
