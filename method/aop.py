from gdo.base.GDT import GDT
from gdo.core.GDO_Permission import GDO_Permission
from gdo.core.GDT_Channel import GDT_Channel
from gdo.core.GDT_User import GDT_User
from gdo.irc.IRCCommand import IRCCommand
from gdo.irc.method.version import version


class aop(IRCCommand):
    """Add a known IRC account to a channel's ChanServ AOP list."""

    # IRCd and services are independent programs, so this is deliberately a
    # conservative compatibility map.  Solanum/ratbox-style networks commonly
    # expose Atheme's FLAGS interface; the established fallback is the Anope
    # XOP/AOP syntax.  New service combinations can extend this table.
    ATHEME_IRCDS = frozenset(('solanum', 'ircd-ratbox', 'plexus'))

    @classmethod
    def gdo_trigger(cls) -> str:
        return 'irc.aop'

    def gdo_user_permission(self) -> str | None:
        return GDO_Permission.ADMIN

    def gdo_parameters(self) -> list[GDT]:
        return [
            GDT_Channel('channel').connectors('irc').default_current().not_null().positional(False),
            GDT_User('user').not_null().positional(),
        ]

    @classmethod
    def aop_command(cls, ircd_version: str, channel: str, username: str) -> str:
        if ircd_version.casefold() in cls.ATHEME_IRCDS:
            return f'FLAGS {channel} {username} +O'
        return f'AOP {channel} ADD {username}'

    @staticmethod
    def get_ircd_version(server) -> str:
        metadata = version()
        metadata._env_server = server
        return metadata.get_config_server_val('irc_version')

    async def gdo_execute(self) -> GDT:
        channel = self.param_value('channel')
        user = self.param_value('user')
        server = channel.get_server()
        if server.get_connector_name() != 'irc':
            return self.err('err_irc_confirm_not_irc', (server.get_name(),))
        if user.get_server_id() != server.get_id():
            return self.err('err_irc_aop_other_server')

        channel_name = channel.get_name()
        username = user.get_name()
        # Both values originate in persisted IRC objects, but reject any old
        # malformed record rather than allowing it to create another IRC line.
        if any(char.isspace() or char in '\\r\\n\\0:' for char in channel_name + username):
            return self.err('err_irc_aop_target')
        if not server.get_connector().is_connected():
            return self.err('err_irc_raw_disconnected')

        command = self.aop_command(
            self.get_ircd_version(server), channel_name, username)
        await server.get_connector().send_raw(f'PRIVMSG ChanServ :{command}')
        return self.reply('msg_irc_aop_sent', (username, channel_name))
