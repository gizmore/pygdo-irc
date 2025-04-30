from gdo.base.GDT import GDT
from gdo.core.GDT_RestOfText import GDT_RestOfText
from gdo.irc.IRCCommand import IRCCommand


class irc_raw(IRCCommand):

    @classmethod
    def gdo_trigger(cls) -> str:
        return 'irc.raw'

    def gdo_user_permission(self) -> str | None:
        return 'admin'

    def gdo_parameters(self) -> list[GDT]:
        return [
            GDT_RestOfText('cmd'),
        ]

    def gdo_execute(self) -> GDT:
        cmd = self.param_value('cmd')
        self.irc_connector().send_raw(cmd)
        return self.empty()
