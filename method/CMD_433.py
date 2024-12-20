from gdo.base.GDT import GDT
from gdo.irc.IRCCommand import IRCCommand


class CMD_433(IRCCommand):

    async def gdo_execute(self) -> GDT:
        self.irc_connector().send_nick_cmd()
        return self.empty()
