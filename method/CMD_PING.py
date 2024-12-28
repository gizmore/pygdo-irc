from gdo.irc.IRCCommand import IRCCommand
from gdo.ui.GDT_HTML import GDT_HTML


class CMD_PING(IRCCommand):

    def gdo_execute(self):
        pong = self._irc_params[0]
        self.irc_connector().send_raw(f"PONG {pong}")
        return GDT_HTML()
