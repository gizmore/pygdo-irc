from gdo.base.GDT import GDT
from gdo.core.GDT_RestOfText import GDT_RestOfText
from gdo.core.GDT_Server import GDT_Server
from gdo.core.GDO_Permission import GDO_Permission
from gdo.base.Method import Method


class irc_raw(Method):

    @classmethod
    def gdo_trigger(cls) -> str:
        return 'irc.raw'

    def gdo_user_permission(self) -> str | None:
        return GDO_Permission.ADMIN

    def gdo_parameters(self) -> list[GDT]:
        return [
            GDT_Server('server').not_null().positional(),
            GDT_RestOfText('cmd').not_null(),
        ]

    async def gdo_execute(self) -> GDT:
        server = self.param_value('server')
        if server.get_connector_name() != 'irc':
            return self.err('err_irc_confirm_not_irc', (server.get_name(),))
        cmd = self.param_value('cmd')
        await server.get_connector().send_raw(cmd)
        return self.empty()
