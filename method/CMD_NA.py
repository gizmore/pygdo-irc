from gdo.base.GDT import GDT
from gdo.irc.IRCCommand import IRCCommand


class CMD_NA(IRCCommand):

    def gdo_execute(self) -> GDT:
        return self.reply('err_stub')
