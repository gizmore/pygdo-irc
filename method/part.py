from gdo.irc.IRCCommand import IRCCommand


class part(IRCCommand):

    @classmethod
    def gdo_trigger(cls) -> str:
        return 'irc.part'
