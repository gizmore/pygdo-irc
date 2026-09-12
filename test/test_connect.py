import asyncio
import unittest
from unittest.mock import AsyncMock, Mock, patch

from gdo.base.Application import Application
from gdo.base.Events import Events
from gdo.base.Render import Mode
from gdo.core.method.launch import launch
from gdo.irc.method.connect import connect
from gdo.irc.method.CMD_001 import CMD_001
from gdo.irc.module_irc import module_irc


class ConnectTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        Application.EVENTS = Events()
        Application.mode(Mode.render_irc)
        self.old_tasks, self.old_servers = Application.TASKS, launch.SERVERS
        Application.TASKS, launch.SERVERS = [], []
        connect.PENDING.clear()

    async def asyncTearDown(self):
        for task in Application.TASKS:
            task.cancel()
        await asyncio.gather(*Application.TASKS, return_exceptions=True)
        Application.TASKS, launch.SERVERS = self.old_tasks, self.old_servers
        connect.PENDING.clear()

    async def test_registered_event_inserts_once(self):
        server = Mock()
        server.is_persisted.side_effect = [False, True]
        module = module_irc()
        await module.on_registered(server)
        await module.on_registered(server)
        server.insert.assert_called_once()

    async def test_welcome_persists_before_user_creation(self):
        order = []
        module = module_irc()
        Application.EVENTS.subscribe('irc_registered', module.on_registered)
        server = Mock()
        server.is_persisted.return_value = False
        server.insert.side_effect = lambda: order.append('insert')
        server.gdo_val.return_value = None
        connector = Mock()
        connector._registration_complete = asyncio.Event()
        connector.setup_dog_user = AsyncMock(side_effect=lambda _: order.append('user'))
        method = CMD_001()
        method._env_server = server
        method._irc_params = ['Dog']
        method.irc_connector = Mock(return_value=connector)
        method.empty = Mock()
        await method.gdo_execute()
        self.assertEqual(['insert', 'user'], order)
        self.assertTrue(connector._registration_complete.is_set())

    def method(self):
        method = connect()
        method.param_val = lambda key: {'name':'example', 'url':'tcps://example.test:6697', 'cert':'1'}[key]
        method.msg, method.err = Mock(), Mock()
        return method

    async def test_duplicate_name_does_not_connect(self):
        method = self.method()
        with patch('gdo.irc.method.connect.GDO_Server.table') as table, patch('gdo.irc.method.connect.GDO_Server.blank') as blank:
            table.return_value.get_by_vals.return_value = Mock()
            await method.gdo_execute()
            blank.assert_not_called()
            method.err.assert_called_once_with('err_irc_connect_exists')

    async def test_pending_name_does_not_start_second_connection(self):
        connect.PENDING.add('example')
        method = self.method()
        with patch('gdo.irc.method.connect.GDO_Server.blank') as blank:
            await method.gdo_execute()
            blank.assert_not_called()
            method.err.assert_called_once_with('err_irc_connect_exists')

    async def attempt(self, successful=False, timeout=False, cert='1'):
        method = self.method()
        values = method.param_val
        method.param_val = lambda key: cert if key == 'cert' else values(key)
        method.TIMEOUT = .01
        server, connector = Mock(), Mock()
        server.get_connector.return_value = connector
        server.is_persisted.return_value = False
        connector._registration_complete = asyncio.Event()
        async def establish():
            if successful:
                server.is_persisted.return_value = True
                connector._registration_complete.set()
            if successful or timeout:
                await asyncio.Event().wait()
        connector.connect = AsyncMock(side_effect=establish)
        connector._own_nick = 'Dog_42'
        server.get_id.return_value = '7'
        server.get_trigger.return_value = '$'
        with patch('gdo.irc.method.connect.GDO_Server.table') as table, patch('gdo.irc.method.connect.GDO_Server.blank', return_value=server) as blank:
            table.return_value.get_by_vals.return_value = None
            await method.gdo_execute()
            self.assertEqual(cert, blank.call_args.args[0]['serv_tls_validate'])
        self.assertFalse(connect.PENDING)
        if successful:
            self.assertEqual([server], launch.SERVERS)
            connector.disconnected.assert_not_called()
            method.msg.assert_called_once_with('msg_irc_connect_success', (
                'example', '7', 'Dog_42', 'Dog_42', '$',
            ))
        else:
            self.assertEqual([], launch.SERVERS)
            self.assertEqual([], Application.TASKS)
            connector.disconnected.assert_called_once()
            server.insert.assert_not_called()
            method.err.assert_called_once_with('err_irc_connect_failed')

    async def test_failed_connect_is_cleaned_up(self):
        await self.attempt()

    async def test_registration_timeout_is_cleaned_up(self):
        await self.attempt(timeout=True)

    async def test_success_adopts_live_server(self):
        await self.attempt(successful=True)

    async def test_certificate_check_can_be_disabled_explicitly(self):
        await self.attempt(successful=True, cert='0')
