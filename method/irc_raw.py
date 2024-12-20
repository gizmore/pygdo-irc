from gdo.base.GDT import GDT
from gdo.core.GDT_RestOfText import GDT_RestOfText
from gdo.irc.IRCCommand import IRCCommand


class irc_raw(IRCCommand):

    def gdo_trigger(self) -> str:
        return 'irc.raw'

    def gdo_user_permission(self) -> str | None:
        return 'admin'

    def gdo_parameters(self) -> list[GDT]:
        return [
            GDT_RestOfText('cmd'),
        ]

    async def gdo_execute(self) -> GDT:
        cmd = self.param_val('cmd')
        self.irc_connector().send_raw(cmd)
        return self.empty()
