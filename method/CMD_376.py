from gdo.irc.IRCCommand import IRCCommand
from gdo.irc.method.motd import motd


class CMD_376(IRCCommand):

    def gdo_execute(self):
        motd().env_copy(self).save_motd()
