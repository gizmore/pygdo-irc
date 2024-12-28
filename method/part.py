from gdo.irc.IRCCommand import IRCCommand


class part(IRCCommand):

    def gdo_trigger(self):
        return 'irc.part'
