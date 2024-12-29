from gdo.base.GDT import GDT
from gdo.irc.IRCCommand import IRCCommand


class CMD_366(IRCCommand):
    def gdo_execute(self) -> GDT:
        return self.empty()
