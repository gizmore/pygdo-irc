from gdo.base.GDT import GDT
from gdo.irc.IRCCommand import IRCCommand
from gdo.irc.method.motd import motd


class CMD_376(IRCCommand):

    def gdo_execute(self) -> GDT:
        motd().env_copy(self).save_motd()
        return self.empty()
