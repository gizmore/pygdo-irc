from gdo.irc.IRCCommand import IRCCommand


class CMD_NA(IRCCommand):

    def gdo_execute(self):
        return self.reply('err_stub')
