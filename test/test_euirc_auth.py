import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from gdo.base.Application import Application
from gdo.base.Render import Mode
from gdo.base.Message import Message
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
        autologin.PENDING.clear()
        autologin.FAILED_UNTIL.clear()
        self.events_patch = patch.object(Application, 'EVENTS', MagicMock(), create=True)
        self.events_patch.start()
        autologin.PROBES['gizmore{euirc}'] = (1030, self.original)

    def tearDown(self):
        autologin.PROBES.clear()
        autologin.EUIRC_STATUS.clear()
        autologin.PENDING.clear()
        autologin.FAILED_UNTIL.clear()
        self.events_patch.stop()

    def message(self, text):
        message = Message(text, Mode.render_irc)
        message._env_server = self.server
        message._env_user = self.user
        message._env_session = message._env_reply_to = None
        return message

    async def test_pending_commands_release_once_in_order_on_success(self):
        autologin.PROBES.clear()
        queue = MagicMock()
        with patch.object(Application, 'TIME', 1000), patch.object(Application, 'MESSAGES', queue):
            await self.method.maybe_probe(self.user, self.message('$ping'))
            await self.method.maybe_probe(self.user, self.message('$btx hello'))
            self.assertEqual(0, queue.put.call_count)
            self.assertTrue(await self.method.confirm_probe(self.user))
            timeout = Application.EVENTS.add_timer_async.call_args.args[1]
            await timeout()
        self.assertEqual(['$ping', '$btx hello'], [c.args[0]._message for c in queue.put.call_args_list])
        self.assertTrue(all(c.args[0]._platform_authenticated for c in queue.put.call_args_list))
        self.connector.send_raw.assert_awaited_once()

    async def test_timeout_releases_once_unauthenticated(self):
        autologin.PROBES.clear()
        queue = MagicMock()
        with patch.object(Application, 'TIME', 1000), patch.object(Application, 'MESSAGES', queue):
            await self.method.maybe_probe(self.user, self.message('$ping'))
            timeout = Application.EVENTS.add_timer_async.call_args.args[1]
            await timeout()
            await timeout()
            self.assertFalse(await self.method.confirm_probe(self.user))
        self.assertEqual(1, queue.put.call_count)
        self.assertFalse(queue.put.call_args.args[0]._platform_authenticated)
        self.user.authenticate.assert_not_awaited()
        self.assertEqual(1900, autologin.FAILED_UNTIL['gizmore{euirc}'])

    async def test_invalidation_clears_failed_probe_cooldown(self):
        key = 'gizmore{euirc}'
        autologin.FAILED_UNTIL[key] = 1900
        autologin.invalidate(self.user)
        self.assertNotIn(key, autologin.FAILED_UNTIL)
        autologin.FAILED_UNTIL[key] = 1900
        autologin.invalidate_server(self.server)
        self.assertNotIn(key, autologin.FAILED_UNTIL)

    async def test_end_of_whois_releases_pending_without_waiting_for_timeout(self):
        from gdo.irc.method.CMD_318 import CMD_318
        autologin.PROBES.clear()
        queue = MagicMock()
        with patch.object(Application, 'TIME', 1000), patch.object(Application, 'MESSAGES', queue):
            await self.method.maybe_probe(self.user, self.message('$ping'))
            command = CMD_318()
            command._env_server = self.server
            command._irc_prefix = 'irc.example'
            command._irc_params = ['Mira', 'gizmore', 'End of WHOIS']
            await command.gdo_execute()
            timeout = Application.EVENTS.add_timer_async.call_args.args[1]
            await timeout()
        self.assertEqual(1, queue.put.call_count)
        self.assertFalse(queue.put.call_args.args[0]._platform_authenticated)
        self.user.authenticate.assert_not_awaited()

    async def test_end_of_whois_waits_for_pending_nickserv_status(self):
        from gdo.irc.method.CMD_318 import CMD_318
        autologin.PROBES.clear()
        queue = MagicMock()
        with patch.object(Application, 'TIME', 1000), patch.object(Application, 'MESSAGES', queue):
            await self.method.maybe_probe(self.user, self.message('$ping'))
            await self.method.euirc_registered_nick('gizmore')
            command = CMD_318()
            command._env_server = self.server
            command._irc_prefix = 'irc.example'
            command._irc_params = ['Mira', 'gizmore', 'End of WHOIS']
            await command.gdo_execute()
            queue.put.assert_not_called()
            self.assertIn('gizmore{euirc}', autologin.PENDING)

    async def test_disconnect_discards_pending(self):
        autologin.PROBES.clear()
        queue = MagicMock()
        with patch.object(Application, 'TIME', 1000), patch.object(Application, 'MESSAGES', queue):
            await self.method.maybe_probe(self.user, self.message('$ping'))
            timeout = Application.EVENTS.add_timer_async.call_args.args[1]
            autologin.invalidate(self.user)
            await timeout()
        queue.put.assert_not_called()

    async def test_failed_status_releases_unauthenticated(self):
        autologin.PROBES.clear()
        queue = MagicMock()
        with patch.object(Application, 'TIME', 1000), patch.object(Application, 'MESSAGES', queue):
            await self.method.maybe_probe(self.user, self.message('$ping'))
            await self.method.euirc_registered_nick('gizmore')
            self.assertFalse(await self.method.euirc_status_notice('NickServ!services@euirc.net', 'Mira', 'STATUS gizmore 0'))
        self.assertFalse(queue.put.call_args.args[0]._platform_authenticated)

    async def test_whois_send_failure_releases_unauthenticated(self):
        autologin.PROBES.clear()
        self.connector.send_raw.side_effect = OSError('disconnected')
        queue = MagicMock()
        with patch.object(Application, 'TIME', 1000), patch.object(Application, 'MESSAGES', queue):
            await self.method.maybe_probe(self.user, self.message('$ping'))
        self.assertFalse(queue.put.call_args.args[0]._platform_authenticated)
        self.assertNotIn('gizmore{euirc}', autologin.PENDING)

    async def test_reconnect_before_timeout_discards_pending(self):
        autologin.PROBES.clear()
        queue = MagicMock()
        with patch.object(Application, 'TIME', 1000), patch.object(Application, 'MESSAGES', queue):
            await self.method.maybe_probe(self.user, self.message('$ping'))
            self.connector._recv_thread = object()
            await Application.EVENTS.add_timer_async.call_args.args[1]()
        queue.put.assert_not_called()

    async def test_pending_queue_is_bounded(self):
        autologin.PROBES.clear()
        with patch.object(Application, 'TIME', 1000), patch.object(autologin, 'MAX_PENDING', 1):
            await self.method.maybe_probe(self.user, self.message('$ping'))
            extra = self.message('$ping')
            extra.deliver = AsyncMock()
            self.assertFalse(await self.method.maybe_probe(self.user, extra))
            extra.deliver.assert_awaited_once()
            self.assertIn('too many commands', extra._result)

    async def test_privmsg_does_not_execute_before_probe_finishes(self):
        from gdo.irc.method.CMD_PRIVMSG import CMD_PRIVMSG
        method = CMD_PRIVMSG()
        method._irc_prefix = 'gizmore!user@host'
        method._irc_params = ['#test', '$ping']
        method._env_server = self.server
        method._env_reply_to = None
        method.irc_user = AsyncMock(return_value=self.user)
        method.irc_channel = MagicMock(return_value=MagicMock())
        method.empty = MagicMock(return_value='held')
        message = MagicMock()
        message.env_copy.return_value = message
        with patch('gdo.irc.method.CMD_PRIVMSG.GDO_Session.for_user'), \
             patch('gdo.irc.method.CMD_PRIVMSG.Message', return_value=message), \
             patch.object(CMD_PRIVMSG, 'should_probe_autologin', return_value=True), \
             patch('gdo.irc.method.CMD_PRIVMSG.autologin') as factory:
            factory.PENDING = {}
            factory.return_value.env_copy.return_value.maybe_probe = AsyncMock(return_value=True)
            self.assertEqual('held', await method.gdo_execute())
        message.execute.assert_not_called()

    async def test_cooldown_skips_probe_until_expiry(self):
        from gdo.irc.method.CMD_PRIVMSG import CMD_PRIVMSG
        self.user.is_type.return_value = False
        method = CMD_PRIVMSG()
        method._irc_prefix = 'gizmore!user@host'
        method._irc_params = ['#test', '$ping']
        method._env_server = self.server
        method.irc_user = AsyncMock(return_value=self.user)
        method.irc_channel = MagicMock(return_value=MagicMock())
        method.empty = MagicMock(return_value='held')
        message = MagicMock()
        message.env_copy.return_value = message
        message.execute.return_value = 'executed'
        autologin.FAILED_UNTIL['gizmore{euirc}'] = 1900
        with patch('gdo.irc.method.CMD_PRIVMSG.GDO_Session.for_user'), \
             patch('gdo.irc.method.CMD_PRIVMSG.Message', return_value=message), \
             patch.object(CMD_PRIVMSG, 'should_probe_autologin', return_value=True), \
             patch.object(autologin, 'maybe_probe', new_callable=AsyncMock) as probe, \
             patch.object(Application, 'TIME', 1899):
            self.assertEqual('executed', await method.gdo_execute())
            self.assertFalse(message._platform_authenticated)
            probe.assert_not_awaited()
        with patch('gdo.irc.method.CMD_PRIVMSG.GDO_Session.for_user'), \
             patch('gdo.irc.method.CMD_PRIVMSG.Message', return_value=message), \
             patch.object(CMD_PRIVMSG, 'should_probe_autologin', return_value=True), \
             patch.object(autologin, 'maybe_probe', new_callable=AsyncMock) as probe, \
             patch.object(Application, 'TIME', 1900):
            self.assertEqual('held', await method.gdo_execute())
            probe.assert_awaited_once()

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

    async def test_germanleets_307_confirms_identified_pending_probe(self):
        from gdo.irc.method.CMD_307 import CMD_307
        self.server.get_name.return_value = 'germanleets'
        self.user.get_name_sid.return_value = 'gizmore{germanleets}'
        autologin.PROBES['gizmore{germanleets}'] = (1030, self.original)
        method = CMD_307()
        method._env_server = self.server
        method._env_user = method._env_channel = method._env_session = method._env_reply_to = None
        method._env_http = False
        method._env_mode = Mode.render_irc
        method._irc_prefix = 'Armida.german-elite.net'
        method._irc_params = ['Mira', 'gizmore', 'is identified for this nick']
        method.empty = MagicMock()
        queue = MagicMock()
        with patch.object(Application, 'TIME', 1000), patch.object(Application, 'MESSAGES', queue):
            await method.gdo_execute()
        self.user.authenticate.assert_awaited_once_with(None)
        self.assertTrue(queue.put.call_args.args[0]._platform_authenticated)

    async def test_germanleets_307_rejects_wrong_text_or_target(self):
        from gdo.irc.method.CMD_307 import CMD_307
        self.server.get_name.return_value = 'germanleets'
        method = CMD_307()
        method._env_server = self.server
        method._env_user = method._env_channel = method._env_session = method._env_reply_to = None
        method._env_http = False
        method._env_mode = Mode.render_irc
        method._irc_prefix = 'Armida.german-elite.net'
        method.empty = MagicMock()
        for params in (['Mira', 'gizmore', 'is a registered nick'],
                       ['Other', 'gizmore', 'is identified for this nick'],
                       ['Mira', 'gizmore']):
            method._irc_params = params
            await method.gdo_execute()
        self.user.authenticate.assert_not_awaited()

    async def test_rizon_307_requires_matching_pending_probe(self):
        from gdo.irc.method.CMD_307 import CMD_307
        self.server.get_name.return_value = 'rizon'
        self.user.get_name_sid.return_value = 'gizmore{rizon}'
        method = CMD_307()
        method._env_server = self.server
        method._env_user = method._env_channel = method._env_session = method._env_reply_to = None
        method._env_http = False
        method._env_mode = Mode.render_irc
        method._irc_prefix = 'irc.mufff.in'
        method.empty = MagicMock()
        queue = MagicMock()
        with patch.object(Application, 'TIME', 1000), patch.object(Application, 'MESSAGES', queue):
            method._irc_params = ['Mira', 'gizmore', 'has identified for this nick']
            await method.gdo_execute()  # no pending Rizon probe
            autologin.PROBES['gizmore{rizon}'] = (1030, self.original)
            for params in (['Other', 'gizmore', 'has identified for this nick'],
                           ['Mira', 'gizmore', 'is a registered nick'],
                           ['Mira', 'gizmore', 'is identified for this nick']):
                method._irc_params = params
                await method.gdo_execute()
            method._irc_prefix = 'attacker!user@host'
            method._irc_params = ['Mira', 'gizmore', 'has identified for this nick']
            await method.gdo_execute()
            self.user.authenticate.assert_not_awaited()
            method._irc_prefix = 'irc.mufff.in'
            await method.gdo_execute()
        self.user.authenticate.assert_awaited_once_with(None)
        self.assertTrue(queue.put.call_args.args[0]._platform_authenticated)

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

    async def test_probe_preserves_origin_when_dispatched_message_changes(self):
        original = Message('$user.approve example', Mode.render_irc)
        original._env_server = self.server
        original._env_user = self.user
        original._env_session = original._env_reply_to = None
        autologin.PROBES.clear()
        queue = MagicMock()
        with patch.object(Application, 'TIME', 1000), patch.object(Application, 'MESSAGES', queue):
            self.assertTrue(await self.method.maybe_probe(self.user, original))
            original._env_user = MagicMock()
            self.assertTrue(await self.method.confirm_probe(self.user))
        self.user.authenticate.assert_awaited_once_with(None)
        self.assertTrue(queue.put.call_args.args[0]._platform_authenticated)

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
