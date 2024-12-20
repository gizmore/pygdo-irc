from gdo.base.GDT import GDT
from gdo.irc.IRCCommand import IRCCommand


class CMD_366(IRCCommand):
    """
    End of 353 user list.
    """

    async def gdo_execute(self) -> GDT:
        return self.empty()
