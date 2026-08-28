import asyncio
import os
import re
import unittest
from unittest.mock import AsyncMock, MagicMock, call, patch

from gdo.base.Application import Application
from gdo.base.Message import Message
from gdo.base.ModuleLoader import ModuleLoader
from gdo.base.Render import Mode
from gdo.base.Logger import Logger
from gdo.core.GDO_Server import GDO_Server
from gdo.irc.connector.IRCReader import IRCReader
from gdo.irc.connector.IRC import IRC
from gdo.irc.connector.IRCWriter import IRCWriter
from gdo.irc.IRCUtil import IRCUtil
from gdo.irc.method.CMD_JOIN import CMD_JOIN
from gdo.irc.method.CMD_PART import CMD_PART
from gdo.irc.method.CMD_QUIT import CMD_QUIT
from gdo.irc.method.CMD_PRIVMSG import CMD_PRIVMSG
from gdo.irc.method.signup import signup
from gdo.message.GDT_HTML import GDT_HTML
from gdo.core.method.launch import launch
from gdotest.TestUtil import reinstall_module, cli_plug, web_gizmore, install_module, GDOTestCase


class IRCPlug:
    _msg: str

    def message(self, msg: str):
        self._msg = msg
        return self

    def exec(self):
        connector = IRCTestCase.IRC_SERVER.get_connector()
        connector.process_message(self._msg)


class IRCWriterTest(unittest.IsolatedAsyncioTestCase):

    async def test_immediate_chunks_respect_prefix_and_utf8_line_limit(self):
        """Chunks preserve content and fit the complete IRC line in UTF-8."""
        Application.mode(Mode.render_irc)
        prefix = 'PRIVMSG #dog :Dog: '
        text = 'wechall.defcon, wechall.import_wc5 🙂🙂🙂🙂🙂'
        line_limit = len(prefix.encode('utf-8')) + IRCWriter.SERVER_PREFIX_RESERVE + 18
        sent = []

        class Queue:
            def get_next_sleep_time(self):
                return 0

        class Writer(IRCWriter):
            async def write_now(self, message):
                sent.append(message)

        writer = object.__new__(Writer)
        writer._queue = Queue()
        message = Message('test', Mode.render_irc).result(text)
        message._env_server = None
        message._env_user = None

        with (
            patch.object(CMD_PRIVMSG, 'get_max_msg_len', return_value=line_limit),
            patch.object(Logger, 'debug'),
        ):
            await writer.write(prefix, message)

        self.assertGreater(len(sent), 1)
        self.assertTrue(all(chunk.startswith(prefix) for chunk in sent))
        self.assertEqual(text, ''.join(chunk[len(prefix):] for chunk in sent))
        self.assertTrue(all(
            len((chunk + '\r\n').encode('utf-8')) + IRCWriter.SERVER_PREFIX_RESERVE <= line_limit
            for chunk in sent
        ))


class IRCUtilTest(unittest.TestCase):

    def test_strip_owner_prefix(self):
        self.assertEqual('Founder', IRCUtil.strip_permission('~Founder'))


class IRCReaderTest(unittest.IsolatedAsyncioTestCase):

    async def test_eof_marks_connector_disconnected(self):
        """A remote EOF must release the server loop for reconnect + auto-join."""
        class Connector:
            def __init__(self):
                self.disconnected_called = False
                self._server = type('Server', (), {'get_name': lambda self: 'test'})()

            def is_connected(self):
                return True

            def disconnected(self):
                self.disconnected_called = True

        class Socket:
            async def readline(self):
                return b''

        connector = Connector()
        reader = IRCReader(connector)
        reader.sock = Socket()
        with patch.object(Application, 'RUNNING', True), patch.object(Logger, 'debug'):
            await reader.run_()
        self.assertTrue(connector.disconnected_called)


class IRCPingTest(unittest.TestCase):

    def test_ping_timeout_after_one_learned_interval(self):
        connector = IRC()
        connector.got_ping(100.0)
        connector.got_ping(160.0)
        self.assertFalse(connector.ping_timed_out(220.0))
        self.assertTrue(connector.ping_timed_out(221.0))


class IRCNickTest(unittest.IsolatedAsyncioTestCase):

    async def test_permanent_nick_is_persisted_only_after_server_confirmation(self):
        server = MagicMock()
        server.get_username.return_value = 'Dog'
        connector = IRC()
        connector._server = server
        connector.send_raw = AsyncMock()

        await connector.change_nick('mira', True)

        connector.send_raw.assert_awaited_once_with('NICK mira')
        server.save_val.assert_not_called()

        await connector.nick_changed('mira')

        self.assertEqual('mira', connector._own_nick)
        self.assertEqual(
            [('serv_username', 'mira'), ('serv_password', None)],
            [call.args for call in server.save_val.call_args_list],
        )

    async def test_pending_nick_ignores_another_nick_confirmation(self):
        server = MagicMock()
        server.get_username.return_value = 'Dog'
        connector = IRC()
        connector._server = server
        connector.send_raw = AsyncMock()
        await connector.change_nick('mira', True)

        self.assertFalse(await connector.nick_changed('someone_else'))
        server.save_val.assert_not_called()
        self.assertEqual('mira', connector._pending_nick)

    async def test_real_configured_nick_identifies_after_confirmation(self):
        server = MagicMock()
        server.get_username.return_value = 'mira'
        server.gdo_val.return_value = 'nickserv-password'
        connector = IRC()
        connector._server = server
        connector.send_raw = AsyncMock()

        await connector.nick_changed('mira')

        connector.send_raw.assert_awaited_once_with(
            'PRIVMSG NickServ :IDENTIFY nickserv-password'
        )


class IRCSignupTest(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        Application.mode(Mode.render_irc)
        Application.STORAGE.lang = 'en'

    async def test_registers_unregistered_nickname_and_saves_password(self):
        server = MagicMock()
        server.gdo_val.return_value = ''
        server.get_username.return_value = 'Dog'
        connector = MagicMock()
        connector.send_raw = AsyncMock()
        method = signup()
        method._env_server = server

        with (
            patch.object(method, 'param_value', side_effect=lambda key, default=False: default),
            patch.object(method, 'get_config_server_val', return_value=''),
            patch.object(method, 'get_config_server_value', return_value=False),
            patch.object(method, 'save_config_server'),
            patch.object(method, 'irc_connector', return_value=connector),
            patch.object(method, 'reply', return_value=GDT_HTML()),
        ):
            await method.gdo_execute()

        command = connector.send_raw.await_args.args[0]
        self.assertTrue(command.startswith('PRIVMSG NickServ :REGISTER '))
        self.assertTrue(command.endswith(' mira@mira-gpt.org'))
        password = command.split()[3]
        self.assertEqual(32, len(password))
        server.save_val.assert_not_called()

    async def test_does_not_register_nickname_with_a_saved_password(self):
        server = MagicMock()
        server.gdo_val.return_value = 'already-registered'
        server.get_username.return_value = 'Dog'
        connector = MagicMock()
        connector.send_raw = AsyncMock()
        method = signup()
        method._env_server = server

        with (
            patch.object(method, 'param_value', side_effect=lambda key, default=False: default),
            patch.object(method, 'irc_connector', return_value=connector),
            patch.object(method, 'reply', return_value=GDT_HTML()),
        ):
            await method.gdo_execute()

        connector.send_raw.assert_not_awaited()
        server.save_val.assert_not_called()

    async def test_force_identifies_the_pending_registration(self):
        server = MagicMock()
        server.gdo_val.return_value = ''
        server.get_username.return_value = 'mira'
        connector = MagicMock()
        connector.send_raw = AsyncMock()
        method = signup()
        method._env_server = server

        with (
            patch.object(method, 'param_value', side_effect=lambda key, default=False: key == 'force'),
            patch.object(method, 'get_config_server_val', return_value='pending-secret'),
            patch.object(method, 'get_config_server_value', return_value=False),
            patch.object(method, 'irc_connector', return_value=connector),
            patch.object(method, 'reply', return_value=GDT_HTML()),
        ):
            await method.gdo_execute()

        self.assertEqual(
            'PRIVMSG NickServ :IDENTIFY pending-secret',
            connector.send_raw.await_args.args[0],
        )

    def test_recognises_identification_confirmation(self):
        self.assertTrue(signup.is_identification_confirmed(
            'mira-gpt', 'You are now identified for mira-gpt.'
        ))
        self.assertFalse(signup.is_identification_confirmed(
            'mira-gpt', 'You are now identified for another-nick.'
        ))

    async def test_promotes_pending_password_only_for_confirmed_nickname(self):
        server = MagicMock()
        server.get_username.return_value = 'Dog'
        method = signup()
        method._env_server = server

        with (
            patch.object(method, 'get_config_server_val', return_value='pending-secret'),
            patch.object(method, 'save_config_server') as save_pending,
        ):
            confirmed = await method.on_nickserv_notice(
                'Nickname Dog has been confirmed.'
            )

        self.assertTrue(confirmed)
        server.save_val.assert_called_once_with('serv_password', 'pending-secret')
        self.assertEqual(
            [
                ('pending_password', ''),
                ('known_registered', '1'),
            ],
            [call.args for call in save_pending.call_args_list],
        )

    def test_ignores_unconfirmed_or_other_nickserv_notices(self):
        self.assertFalse(signup.is_registration_confirmed(
            'Dog', 'An email containing activation instructions has been sent.'
        ))
        self.assertFalse(signup.is_registration_confirmed(
            'Dog', 'Nickname Cat has been confirmed.'
        ))

    def test_recognises_germanleets_password_confirmation(self):
        self.assertTrue(signup.is_registration_confirmed(
            'mira', 'Dein Passwort ist ein-registrierungs-passwort.'
        ))

    async def test_discards_pending_password_when_nickserv_reports_registered(self):
        server = MagicMock()
        server.get_username.return_value = 'Dog'
        method = signup()
        method._env_server = server

        with (
            patch.object(method, 'get_config_server_val', return_value='pending-secret'),
            patch.object(method, 'save_config_server') as save_config,
        ):
            confirmed = await method.on_nickserv_notice('Your nick is already registered.')

        self.assertFalse(confirmed)
        server.save_val.assert_not_called()
        self.assertEqual(
            [
                ("pending_password", ''),
                ("known_registered", '1'),
            ],
            [call.args for call in save_config.call_args_list],
        )


class IRCChannelLifecycleTest(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        Application.mode(Mode.render_irc)
        Application.STORAGE.lang = 'en'

    @staticmethod
    def user(server, name='mira'):
        user = MagicMock()
        user.get_name.return_value = name
        user.get_server.return_value = server
        return user

    async def test_own_join_marks_every_joined_channel_and_persists_auto_join(self):
        server = MagicMock()
        server.on_bot_joined = AsyncMock()
        user = self.user(server)
        first, second = MagicMock(), MagicMock()
        first.on_bot_joined = AsyncMock()
        second.on_bot_joined = AsyncMock()
        method = CMD_JOIN()
        method._irc_prefix = 'mira!user@host'
        method._irc_params = ['#one,#two']
        method._env_session = None
        method._env_reply_to = None

        with (
            patch.object(CMD_JOIN, 'irc_user', new=AsyncMock(return_value=user)),
            patch.object(CMD_JOIN, 'irc_channel', side_effect=[first, second]),
            patch.object(CMD_JOIN, 'is_own_user', return_value=True),
            patch('gdo.irc.method.join.join.on_bot_joined') as persist_auto_join,
        ):
            await method.gdo_execute()

        self.assertEqual(
            [call(user, first), call(user, second)],
            server.on_bot_joined.await_args_list,
        )
        self.assertEqual(
            [call(user), call(user)],
            [first.on_bot_joined.call_args, second.on_bot_joined.call_args],
        )
        self.assertEqual(2, persist_auto_join.call_count)

    async def test_foreign_join_never_changes_bot_auto_join_configuration(self):
        server = MagicMock()
        server.on_user_joined = AsyncMock()
        user = self.user(server, 'other')
        channel = MagicMock()
        channel.on_user_joined = AsyncMock()
        method = CMD_JOIN()
        method._irc_prefix = 'other!user@host'
        method._irc_params = ['#one']

        with (
            patch.object(CMD_JOIN, 'irc_user', new=AsyncMock(return_value=user)),
            patch.object(CMD_JOIN, 'irc_channel', return_value=channel),
            patch.object(CMD_JOIN, 'is_own_user', return_value=False),
            patch('gdo.irc.method.join.join.on_bot_joined') as persist_auto_join,
        ):
            await method.gdo_execute()

        server.on_user_joined.assert_awaited_once_with(user, channel)
        channel.on_user_joined.assert_awaited_once_with(user)
        persist_auto_join.assert_not_called()

    async def test_part_and_quit_use_the_matching_bot_lifecycle(self):
        server = MagicMock()
        server.on_bot_quit = AsyncMock()
        user = self.user(server)
        first, second = MagicMock(), MagicMock()
        first.on_bot_left = AsyncMock()
        second.on_bot_left = AsyncMock()
        part = CMD_PART()
        part._irc_prefix = 'mira!user@host'
        part._irc_params = ['#one,#two']

        with (
            patch.object(CMD_PART, 'irc_user', new=AsyncMock(return_value=user)),
            patch.object(CMD_PART, 'irc_channel', side_effect=[first, second]),
            patch.object(CMD_PART, 'is_own_user', return_value=True),
        ):
            await part.gdo_execute()

        first.on_bot_left.assert_awaited_once_with(user)
        second.on_bot_left.assert_awaited_once_with(user)

        quit_ = CMD_QUIT()
        quit_._irc_prefix = 'mira!user@host'
        with (
            patch.object(CMD_QUIT, 'irc_user', new=AsyncMock(return_value=user)),
            patch.object(CMD_QUIT, 'is_own_user', return_value=True),
        ):
            await quit_.gdo_execute()

        server.on_bot_quit.assert_awaited_once_with(user)


class IRCTestCase(GDOTestCase):
    IRC_SERVER: GDO_Server = None
    """
    For this test you need an IRC server on irc.giz.org:6667
    """

    async def asyncSetUp(self):
        await super().asyncSetUp()
        Application.init(os.path.dirname(__file__ + "/../../../../"))
        loader = ModuleLoader.instance()
        loader.load_modules_db(True)
        install_module('irc')
        loader.init_modules(True, True)
        Application.init_cli()
        loader.init_cli()
        if IRCTestCase.IRC_SERVER is None:
            num_servers = GDO_Server.table().count_where()
            cli_plug(web_gizmore(), f"$add_server wechall_irc_{num_servers + 1} irc ircs://irc.wechall.net:6697")
            IRCTestCase.IRC_SERVER = GDO_Server.table().select().where("serv_connector='irc'").order('serv_created DESC').first().exec().fetch_object()

    async def test_01_add_irc_server(self):
        num_servers = GDO_Server.table().count_where()
        out = cli_plug(web_gizmore(), f"$add_server wechall_irc_{num_servers + 1} irc ircs://irc.wechall.net:6697")
        self.assertIn('new irc server', out, "Cannot add IRC server")
        pattern = r'#(\d+)'
        match = re.search(pattern, out)
        self.assertIsNotNone(match, "Cannot extract server id from add_server message.")

    async def test_02_add_invalid_irc_server(self):
        num_servers = GDO_Server.table().count_where()
        out = cli_plug(web_gizmore(), f"$add_server wechall_irc_{num_servers + 1} irc irc://127.0.0.1:1")
        self.assertNotIn('new irc server', out, "Would have added an invalid IRC server")

    async def test_03_help_rendering(self):
        from gdo.core.method.help import help
        server = IRCTestCase.IRC_SERVER
        user = web_gizmore()
        out = help().env_server(server).env_user(user, True).gdo_execute()
        out = out.render_irc()
        self.assertIn('Core', out, 'IRC Help does not work.')

    async def test_04_connect_irc_server(self):
        server = IRCTestCase.IRC_SERVER
        method = launch()
        await method.mainloop_step_server(server)
        await asyncio.sleep(2)
        self.assertTrue(server.get_connector().is_connected(), "Cannot connect to irc server.")
        await server.stop_loop()

if __name__ == '__main__':
    unittest.main()
