from gdo.base.Application import Application
from gdo.base.GDO_Module import GDO_Module
from gdo.base.Logger import Logger
from gdo.base.Message import Message
from gdo.core.Connector import Connector
from gdo.core.GDO_Channel import GDO_Channel
from gdo.core.GDO_Server import GDO_Server
from gdo.core.GDO_User import GDO_User
from gdo.irc.connector.IRC import IRC
from gdo.irc.method.autologin import autologin


class module_irc(GDO_Module):

    def __init__(self):
        super().__init__()

    def gdo_init(self):
        Connector.register(IRC)

    def gdo_subscribe_events(self):
        Application.EVENTS.subscribe('irc_connected', self.on_connected)
        Application.EVENTS.subscribe('irc_joined', self.on_joined)

    def on_connected(self, server: GDO_Server, message: Message):
        Logger.debug(f"IRC Server {server.render_name()} connected!")
        from gdo.irc.method.join import join
        join().env_copy(message).on_connected()

    def on_joined(self, channel: GDO_Channel, user: GDO_User, message: Message):
        from gdo.irc.method.join import join
        join().env_copy(message).on_bot_joined()
