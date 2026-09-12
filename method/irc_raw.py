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
        # Server IDs are numeric; an IRC verb starts the command when omitted.
        first = self._raw_args.pargs[0] if self._raw_args.pargs else None
        positional_server = isinstance(first, str) and first.isdecimal()
        return [
            GDT_Server('server').default_current().positional(positional_server),
            GDT_RestOfText('cmd').not_null(),
        ]

    async def gdo_execute(self) -> GDT:
        # Do not use Message.CURRENT: another async message may have replaced it.
        server = self.param_value('server') if self.parameter('server').get_val() else self._env_server
        if not server or server.get_connector_name() != 'irc':
            return self.err('err_irc_confirm_not_irc', (server.get_name() if server else '-',))
        cmd = self.param_value('cmd')
        if not cmd or not cmd.strip() or any(char in cmd for char in '\r\n\0'):
            return self.err('err_irc_raw_line')
        if not server.get_connector().is_connected():
            return self.err('err_irc_raw_disconnected')
        await server.get_connector().send_raw(cmd)
        return self.empty()
