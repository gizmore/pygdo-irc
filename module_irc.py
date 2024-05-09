from gdo.base.Application import Application
from gdo.base.GDO_Module import GDO_Module
from gdo.base.Logger import Logger
from gdo.base.Method import Method
from gdo.core.Connector import Connector
from gdo.irc.connector.IRC import IRC


class module_irc(GDO_Module):

    def __init__(self):
        super().__init__()

    def gdo_init(self):
        Connector.register(IRC)
        Application.EVENTS.subscribe('irc_connected', self.on_connected)

    def on_connected(self, method: Method):
        Logger.debug(f"IRC Server {method._env_server.render_name()} connected!")
