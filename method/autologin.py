from gdo.base.Application import Application
from gdo.base.Message import Message
from gdo.base.Method import Method
from gdo.core.GDO_User import GDO_User
import re


class VerifiedIRCReplay(Message):
    """Do not replay an authenticated command after quit or reconnect."""

    def guard(self, server, user, connector):
        self._auth_server = server
        self._auth_user = user
        self._auth_connector = connector
        self._auth_reader = connector._recv_thread
        return self

    async def execute(self):
        if (not self._auth_user._authenticated or
                self._auth_server.get_connector() is not self._auth_connector or
                self._auth_connector._recv_thread is not self._auth_reader or
                self._auth_server._users.get(self._auth_user.get_name()) is not self._auth_user):
            return None
        return await super().execute()


class autologin(Method):

    PROBES: dict[str, tuple[float, Message]] = {}
    EUIRC_STATUS: dict[str, tuple[float, object]] = {}

    @classmethod
    def invalidate(cls, user):
        key = user.get_name_sid()
        cls.PROBES.pop(key, None)
        cls.EUIRC_STATUS.pop(key, None)

    @classmethod
    def invalidate_server(cls, server):
        suffix = '{' + server.get_name().lower() + '}'
        for collection in (cls.PROBES, cls.EUIRC_STATUS):
            for key in list(collection):
                if key.lower().endswith(suffix):
                    collection.pop(key, None)

    @classmethod
    def gdo_trigger(cls) -> str:
        return ''

    async def maybe_probe(self, user: GDO_User, original_message: Message):
        username = user.get_name_sid()
        if username in self.__class__.PROBES:
            probe = self.__class__.PROBES[username]
            if probe[0] < Application.TIME:
                pass
            else:
                return False
        self.__class__.PROBES[username] = (Application.TIME + 300, original_message.message_copy())
        await self._env_server.get_connector().send_raw(f"WHOIS {user.get_name()}")
        return True

    async def confirm_probe(self, user):
        """Authenticate and replay only the still-pending original command."""
        key = user.get_name_sid()
        probe = self.PROBES.get(key)
        if (user._authenticated or not probe or probe[0] < Application.TIME or
                probe[1]._env_user is not user or probe[1]._env_server is not self._env_server):
            return False
        connector = self._env_server.get_connector()
        await user.authenticate(None)
        self.PROBES.pop(key, None)
        self.EUIRC_STATUS.pop(key, None)
        original = probe[1]
        replay = VerifiedIRCReplay(original._message, original._env_mode).env_copy(original).guard(self._env_server, user, connector)
        replay._platform_authenticated = True
        Application.MESSAGES.put(replay)
        return True

    async def euirc_registered_nick(self, nickname):
        """A 307 indicates registration, not authentication; ask services."""
        if self._env_server.get_name().casefold() != 'euirc':
            return False
        if not re.fullmatch(r'[A-Za-z0-9_\-\[\]\\`^{}|]+', nickname):
            return False
        user = await self._env_server.get_or_create_user(nickname)
        key = user.get_name_sid()
        probe = self.PROBES.get(key)
        if not probe or probe[0] < Application.TIME or user._authenticated or probe[1]._env_user is not user:
            return False
        connector = self._env_server.get_connector()
        self.EUIRC_STATUS[key] = (min(probe[0], Application.TIME + 30), connector)
        await connector.send_raw(f'PRIVMSG NickServ :STATUS {nickname}')
        return True

    async def identified_nick(self, nickname):
        if not re.fullmatch(r'[A-Za-z0-9_\-\[\]\\`^{}|]+', nickname):
            return False
        user = await self._env_server.get_or_create_user(nickname)
        return await self.confirm_probe(user)

    async def euirc_status_notice(self, prefix, target, text):
        if self._env_server.get_name().casefold() != 'euirc':
            return False
        connector = self._env_server.get_connector()
        if prefix.casefold() != 'nickserv!services@euirc.net' or target.casefold() != connector._own_nick.casefold():
            return False
        match = re.fullmatch(r'STATUS ([A-Za-z0-9_\-\[\]\\`^{}|]+) ([0-3])', text.strip(), re.IGNORECASE)
        if not match:
            return False
        nickname, status = match.groups()
        user = await self._env_server.get_or_create_user(nickname)
        key = user.get_name_sid()
        pending = self.EUIRC_STATUS.pop(key, None)
        probe = self.PROBES.get(key)
        if not pending or pending[0] < Application.TIME or pending[1] is not connector or not probe or probe[0] < Application.TIME or probe[1]._env_user is not user:
            return False
        if status != '3':
            return False
        return await self.confirm_probe(user)
