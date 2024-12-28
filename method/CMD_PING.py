from gdo.base.GDT import GDT
from gdo.irc.IRCCommand import IRCCommand


class CMD_PING(IRCCommand):

    def gdo_execute(self) -> GDT:
        data = self._irc_params[0]
        self.irc_connector().send_raw(f"PONG {data}")
        return self.empty()
