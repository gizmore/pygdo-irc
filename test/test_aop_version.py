from unittest.mock import AsyncMock, MagicMock, patch

from gdo.base.Application import Application
from gdo.base.Render import Mode
from gdo.irc.method.CMD_004 import CMD_004
from gdo.irc.method.CMD_351 import CMD_351
from gdo.irc.method.aop import aop
from gdo.irc.method.nick import nick
from gdo.irc.method.version import version
from gdotest.TestUtil import GDOTestCase


class IRCAOPTest(GDOTestCase):

    def setUp(self):
        Application.mode(Mode.render_irc)

    async def test_aop_sends_chanserv_request_for_same_server_user(self):
        connector = MagicMock()
        connector.is_connected.return_value = True
        connector.send_raw = AsyncMock()
        server = MagicMock()
        server.get_connector_name.return_value = 'irc'
        server.get_connector.return_value = connector
        server.get_id.return_value = 7
        channel = MagicMock()
        channel.get_server.return_value = server
        channel.get_name.return_value = '#test'
        user = MagicMock()
        user.get_server_id.return_value = 7
        user.get_name.return_value = 'Alice'
        method = aop()
        method.param_value = MagicMock(side_effect=lambda name: {'channel': channel, 'user': user}[name])
        method.get_ircd_version = MagicMock(return_value='inspircd')
        method.reply = MagicMock(return_value='ok')

        self.assertEqual('ok', await method.gdo_execute())
        connector.send_raw.assert_awaited_once_with('PRIVMSG ChanServ :AOP #test ADD Alice')
        method.reply.assert_called_once_with('msg_irc_aop_sent', ('Alice', '#test'))

    async def test_aop_rejects_user_from_another_server(self):
        server = MagicMock()
        server.get_connector_name.return_value = 'irc'
        server.get_id.return_value = 7
        channel = MagicMock()
        channel.get_server.return_value = server
        user = MagicMock()
        user.get_server_id.return_value = 8
        method = aop()
        method.param_value = MagicMock(side_effect=lambda name: {'channel': channel, 'user': user}[name])
        method.err = MagicMock(return_value='error')

        self.assertEqual('error', await method.gdo_execute())
        method.err.assert_called_once_with('err_irc_aop_other_server')

    async def test_aop_allows_normal_channel_and_nick(self):
        connector = MagicMock()
        connector.is_connected.return_value = True
        connector.send_raw = AsyncMock()
        server = MagicMock()
        server.get_connector_name.return_value = 'irc'
        server.get_connector.return_value = connector
        server.get_id.return_value = 7
        channel = MagicMock()
        channel.get_server.return_value = server
        channel.get_name.return_value = '#wechall'
        user = MagicMock()
        user.get_server_id.return_value = 7
        user.get_name.return_value = 'rayaseiren'
        method = aop()
        method.param_value = MagicMock(side_effect=lambda name: {'channel': channel, 'user': user}[name])
        method.get_ircd_version = MagicMock(return_value='inspircd')
        method.reply = MagicMock(return_value='ok')

        self.assertEqual('ok', await method.gdo_execute())
        connector.send_raw.assert_awaited_once_with(
            'PRIVMSG ChanServ :AOP #wechall ADD rayaseiren')

    def test_aop_syntax_uses_atheme_flags_for_solanum_style_ircds(self):
        self.assertEqual(
            'FLAGS #test Alice +O',
            aop.aop_command('solanum', '#test', 'Alice'),
        )

    def test_aop_syntax_defaults_to_anope_aop(self):
        self.assertEqual(
            'AOP #test ADD Alice',
            aop.aop_command('inspircd', '#test', 'Alice'),
        )

    def test_nick_is_declared_as_an_irc_command(self):
        self.assertEqual('irc', nick().gdo_connectors())

class IRCVersionTest(GDOTestCase):

    def setUp(self):
        Application.mode(Mode.render_irc)

    async def test_version_requests_rpl_351_from_selected_server(self):
        connector = MagicMock()
        connector.is_connected.return_value = True
        connector.send_raw = AsyncMock()
        server = MagicMock()
        server.get_name.return_value = 'testnet'
        server.get_connector_name.return_value = 'irc'
        server.get_connector.return_value = connector
        method = version()
        method._env_server = server
        method.param_value = MagicMock(return_value=server)
        method.reply = MagicMock(return_value='ok')

        self.assertEqual('ok', await method.gdo_execute())
        connector.send_raw.assert_awaited_once_with('VERSION')
        method.reply.assert_called_once_with('msg_irc_version_requested', ('testnet',))


class IRC351Test(GDOTestCase):

    def setUp(self):
        Application.mode(Mode.render_irc)

    def test_stores_software_and_revision(self):
        server = MagicMock()
        method = CMD_351()
        method._env_server = server
        method._irc_params = ['Dog', 'UnrealIRCd-6.1.1.1', 'irc.example', 'unrealircd.org']
        method.empty = MagicMock(return_value='ok')

        with patch.object(version, 'save_server_version') as save:
            self.assertEqual('ok', method.gdo_execute())
        save.assert_called_once_with('UnrealIRCd-6.1.1.1')

    def test_keeps_unknown_version_token_intact(self):
        server = MagicMock()
        method = CMD_351()
        method._env_server = server
        method._irc_params = ['Dog', 'custom-ircd', 'irc.example', 'custom']
        method.empty = MagicMock(return_value='ok')

        with patch.object(version, 'save_server_version') as save:
            method.gdo_execute()
        save.assert_called_once_with('custom-ircd')


class IRCStartupVersionTest(GDOTestCase):

    def setUp(self):
        Application.mode(Mode.render_irc)

    def test_myinfo_startup_event_stores_ircd_identity(self):
        server = MagicMock()
        method = CMD_004()
        method._env_server = server
        method._irc_params = ['Dog', 'irc.example', 'InspIRCd-2.8.4.r3', 'iw', 'biklmnopstveI']
        method.empty = MagicMock(return_value='ok')

        with patch.object(version, 'save_server_version') as save:
            self.assertEqual('ok', method.gdo_execute())
        save.assert_called_once_with('InspIRCd-2.8.4.r3')

    def test_splits_startup_token_into_daemon_and_complete_revision(self):
        method = version()
        method.save_config_server = MagicMock()

        method.save_server_version('InspIRCd-2.8.4.r3')

        method.save_config_server.assert_any_call('irc_version', 'inspircd')
        method.save_config_server.assert_any_call('irc_revision', 'inspircd-2.8.4.r3')
