from gdo.irc.IRCCommand import IRCCommand


class CMD_366(IRCCommand):
    """
    End of 353 user list.
    """

    def gdo_execute(self):
        return self.empty()
