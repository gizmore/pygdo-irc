from gdo.base.GDT import GDT
from gdo.irc.IRCCommand import IRCCommand


class CMD_ERROR(IRCCommand):

    def gdo_execute(self) -> GDT:
        self.irc_connector().disconnect(f"ERROR: {self._irc_params[0]}")
        return self.empty()
