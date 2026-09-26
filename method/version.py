from gdo.base.GDT import GDT
from gdo.core.GDT_Server import GDT_Server
from gdo.core.GDO_Permission import GDO_Permission
from gdo.core.GDT_String import GDT_String
from gdo.irc.IRCCommand import IRCCommand


class version(IRCCommand):
    """Request the current IRC daemon version (RPL_VERSION / 351)."""

    @classmethod
    def gdo_trigger(cls) -> str:
        return 'irc.version'

    def gdo_user_permission(self) -> str | None:
        return GDO_Permission.STAFF

    def gdo_parameters(self) -> list[GDT]:
        return [GDT_Server('server').default_current().positional(False)]

    @classmethod
    def gdo_method_config_server(cls) -> list[GDT]:
        # Server-scoped method settings avoid a core-table migration and keep
        # non-IRC connectors free of IRC daemon metadata.
        return [
            GDT_String('irc_version').ascii().maxlen(128).initial(''),
            GDT_String('irc_revision').ascii().maxlen(128).initial(''),
        ]

    def save_server_version(self, token: str):
        """Persist a daemon name plus its complete startup revision token."""
        token = token.strip()
        # IRCd startup tokens conventionally begin ``DaemonName-<number>``.
        # Keep a nonconforming token intact as the name rather than inventing
        # a split; the complete token remains available as the revision.
        software, separator, suffix = token.rpartition('-')
        name = software if separator and suffix[:1].isdigit() else token
        self.save_config_server('irc_version', name.casefold())
        self.save_config_server('irc_revision', token.casefold())

    async def gdo_execute(self) -> GDT:
        server = self.param_value('server') or self._env_server
        if not server or server.get_connector_name() != 'irc':
            return self.err('err_irc_confirm_not_irc', (server.get_name() if server else '-',))
        if not server.get_connector().is_connected():
            return self.err('err_irc_raw_disconnected')
        await server.get_connector().send_raw('VERSION')
        return self.reply('msg_irc_version_requested', (server.get_name(),))
