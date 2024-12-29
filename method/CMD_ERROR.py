from gdo.base.GDT import GDT
from gdo.irc.IRCCommand import IRCCommand


class CMD_ERROR(IRCCommand):

    def gdo_execute(self) -> GDT:
        self.irc_connector().disconnected()
        return self.empty()
