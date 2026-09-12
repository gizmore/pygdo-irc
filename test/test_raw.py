import unittest
from unittest.mock import AsyncMock, Mock, patch

from gdo.base.Application import Application
from gdo.base.Events import Events
from gdo.base.Render import Mode
from gdo.irc.method.irc_raw import irc_raw


class RawTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        Application.EVENTS = Events()
        Application.mode(Mode.render_irc)

    def test_optional_server_keeps_command_remainder(self):
        for tokens, expected in [(['WHOIS', 'Dog'], None), (['3', 'WHOIS', 'Dog'], '3')]:
            method = irc_raw()
            method._raw_args.pargs = tokens
            with patch('gdo.ui.WithIcon.t', return_value='icon'), patch('gdo.core.GDO_Server.GDO_Server.table'):
                params = method.parameters()
            self.assertEqual(expected, params['server'].get_val())
            self.assertEqual('WHOIS Dog', params['cmd'].get_value())

    async def test_uses_current_message_server(self):
        method = irc_raw()
        server = Mock()
        server.get_connector_name.return_value = 'irc'
        server.get_connector.return_value.send_raw = AsyncMock()
        method._env_server = server
        method.parameter = Mock()
        method.parameter.return_value.get_val.return_value = None
        method.param_value = Mock(return_value='PRIVMSG #test :hello world')
        method.empty = Mock()
        await method.gdo_execute()
        server.get_connector.return_value.send_raw.assert_awaited_once_with('PRIVMSG #test :hello world')

    async def test_rejects_embedded_line_break(self):
        method = irc_raw()
        server = Mock()
        server.get_connector_name.return_value = 'irc'
        server.get_connector.return_value.send_raw = AsyncMock()
        method._env_server = server
        method.parameter = Mock()
        method.parameter.return_value.get_val.return_value = None
        method.param_value = Mock(return_value='PING x\r\nQUIT')
        method.err = Mock()
        await method.gdo_execute()
        method.err.assert_called_once_with('err_irc_raw_line')
        server.get_connector.return_value.send_raw.assert_not_awaited()
