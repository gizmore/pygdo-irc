from gdo.base.GDT import GDT
from gdo.base.Util import Random
from gdo.core.GDO_Permission import GDO_Permission
from gdo.core.GDT_Bool import GDT_Bool
from gdo.core.GDT_Secret import GDT_Secret
from gdo.core.GDT_Server import GDT_Server
from gdo.irc.IRCCommand import IRCCommand


class signup(IRCCommand):
    """Register the configured IRC nickname with NickServ once."""

    NICKSERV_EMAIL = 'mira@mira-gpt.org'
    PENDING_PASSWORD = 'pending_password'
    KNOWN_REGISTERED = 'known_registered'

    @classmethod
    def gdo_trigger(cls) -> str:
        return 'irc.signup'

    def gdo_user_permission(self) -> str | None:
        return GDO_Permission.STAFF

    @classmethod
    def gdo_method_config_server(cls) -> list[GDT]:
        return [
            GDT_Secret(cls.PENDING_PASSWORD),
            GDT_Bool(cls.KNOWN_REGISTERED).initial('0'),
        ]

    def gdo_parameters(self) -> list[GDT]:
        """An explicit IRC server also makes signup usable from TCP/WebSocket."""
        return [
            GDT_Server('server').positional(),
            GDT_Bool('force').not_null().initial('0'),
        ]

    async def gdo_execute(self) -> GDT:
        selected_server = self.param_value('server', False)
        server = selected_server or self._env_server
        if selected_server and server.get_connector_name() != 'irc':
            return self.err('err_irc_confirm_not_irc', (server.get_name(),))
        if selected_server:
            self.env_server(server)
        if server.gdo_val('serv_password'):
            return self.reply('msg_irc_signup_registered', (server.get_username(),))
        if self.get_config_server_value(self.KNOWN_REGISTERED):
            return self.err('err_irc_signup_password_unknown', (server.get_username(),))
        password = self.get_config_server_val(self.PENDING_PASSWORD)
        if password and not self.param_value('force'):
            return self.reply('msg_irc_signup_pending', (server.get_username(),))

        password = password or Random.token(16)
        await self.irc_connector().send_raw(
            f'PRIVMSG NickServ :REGISTER {password} {self.NICKSERV_EMAIL}'
        )
        self.save_config_server(self.PENDING_PASSWORD, password)
        return self.reply('msg_irc_signup_sent', (server.get_username(), self.NICKSERV_EMAIL))

    async def on_nickserv_notice(self, text: str) -> bool:
        """Promote the pending password only after NickServ confirms the nick."""
        password = self.get_config_server_val(self.PENDING_PASSWORD)
        nickname = self._env_server.get_username()
        if not password or not self.is_registration_confirmed(nickname, text):
            if password and self.is_already_registered(text):
                self.save_config_server(self.PENDING_PASSWORD, '')
                self.save_config_server(self.KNOWN_REGISTERED, '1')
            return False
        self._env_server.save_val('serv_password', password)
        self.save_config_server(self.PENDING_PASSWORD, '')
        self.save_config_server(self.KNOWN_REGISTERED, '1')
        return True

    @staticmethod
    def is_registration_confirmed(nickname: str, text: str) -> bool:
        message = text.casefold()
        nick = nickname.casefold()
        # Anope on GermanLeets confirms registration by echoing the generated
        # password, without repeating the nickname.
        if 'dein passwort ist' in message or 'your password is' in message:
            return True
        if nick not in message or 'not registered' in message or 'already registered' in message:
            return False
        return any(marker in message for marker in (
            'is now registered',
            'has been registered',
            'has been confirmed',
            'has been verified',
            f'nickname {nick} registered',
        ))

    @staticmethod
    def is_already_registered(text: str) -> bool:
        return 'already registered' in text.casefold()
