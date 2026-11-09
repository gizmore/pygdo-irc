import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from gdo.base.Application import Application
from gdo.base.Render import Mode
from gdo.irc.method.autologin import autologin


class EuIRCAutologinTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        Application.mode(Mode.render_irc)
        self.user = MagicMock()
        self.user.get_name_sid.return_value = 'gizmore{euirc}'
        self.user.get_name.return_value = 'gizmore'
        self.user._authenticated = False
        self.user.authenticate = AsyncMock()
        self.connector = MagicMock()
        self.connector._own_nick = 'Mira'
        self.connector._recv_thread = object()
        self.connector.send_raw = AsyncMock()
        self.server = MagicMock()
        self.server.get_name.return_value = 'euirc'
        self.server.get_connector.return_value = self.connector
        self.server.get_or_create_user = AsyncMock(return_value=self.user)
        self.server._users = {'gizmore': self.user}
        self.method = autologin()
        self.method._env_server = self.server
        self.original = MagicMock()
        self.original._env_user = self.user
        self.original._env_server = self.server
        self.original._env_mode = Mode.render_irc
        self.original._message = '$btx Hello'
        autologin.PROBES.clear()
        autologin.EUIRC_STATUS.clear()
        autologin.PROBES['gizmore{euirc}'] = (1030, self.original)

    def tearDown(self):
        autologin.PROBES.clear()
        autologin.EUIRC_STATUS.clear()

    async def test_307_only_requests_status_not_authentication(self):
        with patch.object(Application, 'TIME', 1000):
            self.assertTrue(await self.method.euirc_registered_nick('gizmore'))
        self.connector.send_raw.assert_awaited_once_with('PRIVMSG NickServ :STATUS gizmore')
        self.user.authenticate.assert_not_awaited()

    async def test_307_handler_rejects_user_prefix_and_malformed_numeric(self):
        from gdo.irc.method.CMD_307 import CMD_307
        method = CMD_307()
        method._env_server = self.server
        method.empty = MagicMock()
        with patch('gdo.irc.method.CMD_307.autologin') as factory:
            method._irc_prefix = 'someone!ident@host'
            method._irc_params = ['Mira', 'gizmore']
            await method.gdo_execute()
            method._irc_prefix = 'irc.euirc.net'
            method._irc_params = ['Mira']
            await method.gdo_execute()
        factory.assert_not_called()

    async def test_password_identified_status_authenticates_and_replays(self):
        queue = MagicMock()
        with patch.object(Application, 'TIME', 1000), patch.object(Application, 'MESSAGES', queue):
            await self.method.euirc_registered_nick('gizmore')
            self.assertTrue(await self.method.euirc_status_notice('NickServ!services@euirc.net', 'Mira', 'STATUS gizmore 3'))
        self.user.authenticate.assert_awaited_once_with(None)
        replay = queue.put.call_args.args[0]
        self.assertTrue(replay._platform_authenticated)
        self.assertEqual('$btx Hello', replay._message)

    async def test_330_reuses_confirmed_probe_and_guards_replay(self):
        from gdo.irc.method.CMD_330 import CMD_330
        method = CMD_330()
        method._env_server = self.server
        method._env_user = method._env_channel = method._env_session = method._env_reply_to = None
        method._env_http = False
        method._env_mode = Mode.render_irc
        method._irc_prefix = 'irc.example.net'
        method._irc_params = ['Mira', 'gizmore', 'account']
        method.empty = MagicMock()
        queue = MagicMock()
        with patch.object(Application, 'TIME', 1000), patch.object(Application, 'MESSAGES', queue):
            await method.gdo_execute()
        self.user.authenticate.assert_awaited_once_with(None)
        self.assertTrue(queue.put.call_args.args[0]._platform_authenticated)
        self.assertNotIn('gizmore{euirc}', autologin.PROBES)

    async def test_confirmation_rejects_missing_expired_or_foreign_probe(self):
        with patch.object(Application, 'TIME', 1000):
            self.original._env_server = MagicMock()
            self.assertFalse(await self.method.confirm_probe(self.user))
            self.original._env_server = self.server
            autologin.PROBES['gizmore{euirc}'] = (999, self.original)
            self.assertFalse(await self.method.confirm_probe(self.user))
            autologin.PROBES.clear()
            self.assertFalse(await self.method.confirm_probe(self.user))
        self.user.authenticate.assert_not_awaited()

    async def test_unidentified_or_access_list_status_never_authenticates(self):
        for status in ('0', '1', '2'):
            with self.subTest(status=status), patch.object(Application, 'TIME', 1000):
                await self.method.euirc_registered_nick('gizmore')
                self.assertFalse(await self.method.euirc_status_notice('NickServ!services@euirc.net', 'Mira', f'STATUS gizmore {status}'))
        self.user.authenticate.assert_not_awaited()

    async def test_wrong_sender_target_server_expired_or_connection_are_rejected(self):
        with patch.object(Application, 'TIME', 1000):
            await self.method.euirc_registered_nick('gizmore')
            self.assertFalse(await self.method.euirc_status_notice('NickServ!evil@elsewhere', 'Mira', 'STATUS gizmore 3'))
            self.assertFalse(await self.method.euirc_status_notice('NickServ!services@euirc.net', '#channel', 'STATUS gizmore 3'))
            self.server.get_name.return_value = 'other'
            self.assertFalse(await self.method.euirc_status_notice('NickServ!services@euirc.net', 'Mira', 'STATUS gizmore 3'))
            self.server.get_name.return_value = 'euirc'
            self.server.get_connector.return_value = MagicMock(_own_nick='Mira')
            self.assertFalse(await self.method.euirc_status_notice('NickServ!services@euirc.net', 'Mira', 'STATUS gizmore 3'))
            self.server.get_connector.return_value = self.connector
            await self.method.euirc_registered_nick('gizmore')
        with patch.object(Application, 'TIME', 1031):
            self.assertFalse(await self.method.euirc_status_notice('NickServ!services@euirc.net', 'Mira', 'STATUS gizmore 3'))
        self.user.authenticate.assert_not_awaited()

    async def test_changed_user_and_no_probe_are_rejected(self):
        with patch.object(Application, 'TIME', 1000):
            self.original._env_user = MagicMock()
            self.assertFalse(await self.method.euirc_registered_nick('gizmore'))
            autologin.PROBES.clear()
            self.assertFalse(await self.method.euirc_registered_nick('gizmore'))
        self.connector.send_raw.assert_not_awaited()

    async def test_replay_is_discarded_after_logout_or_reconnect(self):
        from gdo.irc.method.autologin import VerifiedIRCReplay
        replay = VerifiedIRCReplay('$btx Hello', Mode.render_irc).guard(self.server, self.user, self.connector)
        self.user._authenticated = False
        self.assertIsNone(await replay.execute())
        self.user._authenticated = True
        self.connector._recv_thread = object()
        self.assertIsNone(await replay.execute())

    async def test_quit_invalidates_pending_authentication(self):
        from gdo.irc.method.CMD_QUIT import CMD_QUIT
        method = CMD_QUIT()
        method._irc_prefix = 'gizmore!ident@host'
        method.irc_user = AsyncMock(return_value=self.user)
        method.is_own_user = MagicMock(return_value=False)
        method.empty = MagicMock()
        self.user.get_server.return_value = self.server
        self.user._authenticated = True
        self.server.on_user_disconnected = AsyncMock()
        self.server.on_user_quit = AsyncMock()
        autologin.EUIRC_STATUS['gizmore{euirc}'] = (1030, self.connector)
        await method.gdo_execute()
        self.assertFalse(self.user._authenticated)
        self.assertNotIn('gizmore{euirc}', autologin.PROBES)
        self.assertNotIn('gizmore{euirc}', autologin.EUIRC_STATUS)

    async def test_nonnumeric_nickname_cannot_inject_commands(self):
        with patch.object(Application, 'TIME', 1000):
            self.assertFalse(await self.method.euirc_registered_nick('gizmore\r\nOPER admin'))
        self.connector.send_raw.assert_not_awaited()
