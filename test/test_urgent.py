import unittest
from unittest.mock import AsyncMock, Mock, patch

from gdo.base.Application import Application
from gdo.base.Events import Events
from gdo.base.Render import Mode
from gdo.irc.method.help_urgent import help_urgent


class UrgentTest(unittest.IsolatedAsyncioTestCase):
    def test_hidden_but_directly_addressable(self):
        self.assertTrue(self.method.gdo_method_hidden())
        self.assertEqual('urgent', self.method.gdo_trigger())

    def setUp(self):
        Application.EVENTS = Events()
        Application.mode(Mode.render_irc)
        help_urgent.RECENT = {}
        self.method = help_urgent()
        self.method._env_server = Mock()
        self.method._env_server.get_id.return_value = '3'
        self.method._env_server.get_name.return_value = 'mogwai'
        self.method._env_user = Mock()
        self.method._env_user.get_id.return_value = '12'
        self.method._env_user.get_name.return_value = 'requester'
        self.method._env_reply_to = None
        self.method._env_channel = None
        self.method.param_value = Mock(return_value='Please help')
        self.method.msg = Mock()
        self.method.err = Mock()

    def contact(self, uid, online=True, connected=True):
        user = Mock()
        user.get_id.return_value = uid
        user.is_online.return_value = online
        user.get_server.return_value.get_connector.return_value.is_connected.return_value = connected
        user.get_server.return_value.send_to_user = AsyncMock()
        return user

    async def test_all_online_staff_on_their_own_servers_once(self):
        a, b, offline, disconnected = self.contact('1'), self.contact('2'), self.contact('3', False), self.contact('4', connected=False)
        with patch('gdo.irc.method.help_urgent.GDO_User.staff', return_value=[a, b, a, offline, disconnected]):
            await self.method.gdo_execute()
        for user in (a, b):
            user.get_server().send_to_user.assert_awaited_once_with(user, 'msg_help_urgent_request', ('requester', 'mogwai / private message', 'Please help'))
        offline.get_server().send_to_user.assert_not_awaited()
        disconnected.get_server().send_to_user.assert_not_awaited()
        self.method.msg.assert_called_once_with('msg_help_urgent_sent', (2, 2))

    async def test_partial_failure_does_not_stop_other_recipients(self):
        a, b = self.contact('1'), self.contact('2')
        a.get_server().send_to_user.side_effect = RuntimeError('failed')
        with patch('gdo.irc.method.help_urgent.GDO_User.staff', return_value=[a, b]):
            await self.method.gdo_execute()
        b.get_server().send_to_user.assert_awaited_once()
        self.method.msg.assert_called_once_with('msg_help_urgent_sent', (1, 2))

    async def test_no_staff_does_not_confirm_delivery(self):
        with patch('gdo.irc.method.help_urgent.GDO_User.staff', return_value=[]):
            await self.method.gdo_execute()
        self.method.err.assert_called_once_with('err_help_urgent_unavailable')
        self.method.msg.assert_not_called()

    async def test_rate_limit(self):
        a = self.contact('1')
        with patch('gdo.irc.method.help_urgent.GDO_User.staff', return_value=[a]):
            await self.method.gdo_execute()
            await self.method.gdo_execute()
        a.get_server().send_to_user.assert_awaited_once()
        self.method.err.assert_called_once_with('err_help_urgent_wait')

    async def test_invalid_text(self):
        for text in ('', ' ', 'x' * 501, 'one\ntwo', 'a\0b'):
            self.method.param_value.return_value = text
            with patch('gdo.irc.method.help_urgent.GDO_User.staff') as staff:
                await self.method.gdo_execute()
                staff.assert_not_called()
        self.assertEqual('urgent', help_urgent.gdo_trigger())
