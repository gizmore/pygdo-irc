from pygments.lexers import q

from gdo.base.Application import Application
from gdo.base.GDO_Module import GDO_Module
from gdo.base.Message import Message
from gdo.core.Connector import Connector
from gdo.core.GDO_Server import GDO_Server
from gdo.irc.connector.IRC import IRC


class module_irc(GDO_Module):

    def __init__(self):
        super().__init__()

    def gdo_dependencies(self) -> list:
        return [
            'login',
            'recovery',
            'register',
        ]

    def gdo_init(self):
        Connector.register(IRC)

    def gdo_user_settings(self):
        return [
        ]

    def gdo_subscribe_events(self):
        Application.EVENTS.subscribe('irc_registered', self.on_registered)
        Application.EVENTS.subscribe('irc_connected', self.on_connected)
        # Application.EVENTS.subscribe('irc_joined', self.on_joined)
        # Application.EVENTS.subscribe('irc_parted', self.on_parted)

    async def on_registered(self, server: GDO_Server):
        # Synchronous insert before user creation; the unique server name also
        # guards against competing processes. Reconnects never insert again.
        if not server.is_persisted():
            server.insert()

    async def on_connected(self, server: GDO_Server, message: Message):
        # Logger.debug(f"IRC Server {server.render_name()} connected!")
        from gdo.irc.method.join import join
        await join().env_copy(message).on_connected()

    # async def on_joined(self, channel: GDO_Channel, user: GDO_User, message: Message):
    #     from gdo.irc.method.join import join
    #     join().env_copy(message).on_bot_joined()
    #
    # async def on_parted(self, channel: GDO_Channel, user: GDO_User, message: Message):
    #     del message._env_server._channels[channel.get_name()]
