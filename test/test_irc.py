import os
import re
import time
import unittest

from gdo.base.Application import Application
from gdo.base.Exceptions import GDOParamError
from gdo.base.ModuleLoader import ModuleLoader
from gdo.core.GDO_Server import GDO_Server
from gdo.core.method.launch import launch
from gdotest.TestUtil import reinstall_module, cli_plug, get_gizmore, install_module


class IRCTestCase(unittest.TestCase):
    IRC_SERVER = None
    """
    For this test you need an IRC server on irc.giz.org:6667
    """

    def setUp(self):
        Application.init(os.path.dirname(__file__ + "/../../../../"))
        loader = ModuleLoader.instance()
        loader.load_modules_db(True)
        loader.init_modules()
        install_module('irc')
        Application.init_cli()
        loader.init_cli()
        if IRCTestCase.IRC_SERVER is None:
            num_servers = GDO_Server.table().count_where()
            cli_plug(get_gizmore(), f"add_server giz.org_{num_servers + 1} IRC irc://irc.giz.org:6667")
            IRCTestCase.IRC_SERVER = GDO_Server.table().select().where("serv_connector='IRC'").order('serv_created DESC').first().exec().fetch_object()

    def test_01_add_irc_server(self):
        num_servers = GDO_Server.table().count_where()
        out = cli_plug(get_gizmore(), f"add_server giz.org_{num_servers + 1} IRC irc://irc.giz.org:6667")
        self.assertIn('new IRC server', out, "Cannot add IRC server")
        pattern = r'#(\d+)'
        match = re.search(pattern, out)
        self.assertIsNotNone(match, "Cannot extract server id from add_server message.")

    def test_02_add_invalid_irc_server(self):
        num_servers = GDO_Server.table().count_where()
        with self.assertRaises(GDOParamError):
            out = cli_plug(get_gizmore(), f"add_server giz.org_{num_servers + 1} IRC irc://irc.giz.org:6668")
            self.assertNotIn('new IRC server', out, "Would have added an invalid IRC server")

    def test_03_connect_irc_server(self):
        server = IRCTestCase.IRC_SERVER
        method = launch()
        method.mainloop_step_server(server)
        time.sleep(15)  # sleep 5 seconds to let irc connect
        server.get_connector().disconnect('Disconnect automatically')

    def test_04_help(self):
        from gdo.core.method.help import help
        server = IRCTestCase.IRC_SERVER
        user = get_gizmore()
        out = help().env_server(server).env_user(user).gdo_execute().render_irc()
        self.assertIn('Core', out, 'IRC Help does not work.')


if __name__ == '__main__':
    unittest.main()
