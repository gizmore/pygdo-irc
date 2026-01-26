import os
import re
import time
import unittest

from gdo.base.Application import Application
from gdo.base.Exceptions import GDOParamError
from gdo.base.ModuleLoader import ModuleLoader
from gdo.core.GDO_Server import GDO_Server
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
            cli_plug(web_gizmore(), f"$add_server giz.org_{num_servers + 1} irc irc://irc.giz.org:6667")
            IRCTestCase.IRC_SERVER = GDO_Server.table().select().where("serv_connector='irc'").order('serv_created DESC').first().exec().fetch_object()

    async def test_01_add_irc_server(self):
        num_servers = GDO_Server.table().count_where()
        out = cli_plug(web_gizmore(), f"$add_server giz.org_{num_servers + 1} irc irc://irc.giz.org:6667")
        self.assertIn('new irc server', out, "Cannot add IRC server")
        pattern = r'#(\d+)'
        match = re.search(pattern, out)
        self.assertIsNotNone(match, "Cannot extract server id from add_server message.")

    async def test_02_add_invalid_irc_server(self):
        num_servers = GDO_Server.table().count_where()
        with self.assertRaises(GDOParamError):
            out = cli_plug(web_gizmore(), f"$add_server giz.org_{num_servers + 1} irc irc://irc.giz.org:6668")
            self.assertNotIn('new IRC server', out, "Would have added an invalid IRC server")

    async def test_03_help_rendering(self):
        from gdo.core.method.help import help
        server = IRCTestCase.IRC_SERVER
        user = web_gizmore()
        out = await help().env_server(server).env_user(user, True).gdo_execute()
        out = out.render_irc()
        self.assertIn('Core', out, 'IRC Help does not work.')

    async def test_04_connect_irc_server(self):
        server = IRCTestCase.IRC_SERVER
        method = launch()
        await method.mainloop_step_server(server)
        time.sleep(12)  # sleep 5 seconds to let irc connect
        self.assertTrue(server.get_connector().is_connected(), "Cannot connect to irc server.")
        await server.get_connector().disconnect('Disconnect automatically')

if __name__ == '__main__':
    unittest.main()
    