from gdo.base.Application import Application
from gdo.irc.IRCCommand import IRCCommand


class CMD_NOTICE(IRCCommand):

    def gdo_execute(self):
        Application.EVENTS.publish('irc_notice', self)
