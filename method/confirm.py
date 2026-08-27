from gdo.base.GDT import GDT
from gdo.base.Method import Method
from gdo.core.GDO_Permission import GDO_Permission
from gdo.core.GDT_Server import GDT_Server
from gdo.core.GDT_String import GDT_String


class confirm(Method):
    """Send a NickServ registration confirmation on a selected IRC server."""

    @classmethod
    def gdo_trigger(cls) -> str:
        return 'irc.confirm'

    def gdo_user_permission(self) -> str | None:
        return GDO_Permission.STAFF

    def gdo_parameters(self) -> list[GDT]:
        return [
            GDT_Server('server').not_null().positional(),
            GDT_String('token').ascii().minlen(1).maxlen(128).not_null().positional(),
        ]

    async def gdo_execute(self) -> GDT:
        server = self.param_value('server')
        if server.get_connector_name() != 'irc':
            return self.err('err_irc_confirm_not_irc', (server.get_name(),))
        await server.get_connector().send_raw(
            f'PRIVMSG NickServ :CONFIRM {self.param_val("token")}'
        )
        return self.reply('msg_irc_confirm_sent', (server.get_name(),))
