from gdo.base.Application import Application
from gdo.irc.IRCCommand import IRCCommand


class CMD_001(IRCCommand):

    def gdo_execute(self):
        Application.EVENTS.publish('irc_connected', self)
        return self.empty()
