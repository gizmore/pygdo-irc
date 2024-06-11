from gdo.base.Application import Application
from gdo.irc.IRCCommand import IRCCommand


class CMD_001(IRCCommand):

    def gdo_execute(self):
        Application.EVENTS.publish(f'irc{self.get_server_id()}_connected', self)
        # self.irc_connector().send_user_cmd()
        return self.empty()
