from gdo.irc.IRCCommand import IRCCommand


class CMD_ERROR(IRCCommand):

    def gdo_execute(self):
        self.irc_connector().disconnected()