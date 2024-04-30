import os
import re
import unittest

from gdo.base.Application import Application
from gdo.base.ModuleLoader import ModuleLoader
from gdo.core.GDO_Server import GDO_Server
from gdo.core.method.launch import launch
from gdotest.TestUtil import reinstall_module, cli_plug, get_gizmore


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
        reinstall_module('irc')
        Application.init_cli()
        loader.init_cli()
        IRCTestCase.IRC_SERVER = GDO_Server.table().select().where("serv_connector='IRC'").order('serv_created DESC').first().exec().fetch_object()

    def test_01_add_server(self):
        out = cli_plug(get_gizmore(), "add_server giz.org IRC irc://irc.giz.org:6667")
        self.assertIn('new IRC server', out, "Cannot add IRC server")
        pattern = r'#(\d+)'
        match = re.search(pattern, out)
        self.assertIsNotNone(match, "Cannot extract server id from add_server message.")
        sid = match.group(1)
        IRCTestCase.IRC_SERVER = GDO_Server.table().get_by_id(sid)

    def test_02_connect_irc(self):
        server = IRCTestCase.IRC_SERVER
        method = launch()
        method.mainloop_step_server(IRCTestCase.IRC_SERVER)




if __name__ == '__main__':
    unittest.main()
