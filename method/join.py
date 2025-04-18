from gdo.base.GDT import GDT
from gdo.base.Util import html
from gdo.core.GDT_Bool import GDT_Bool
from gdo.irc.GDT_IRCChannel import GDT_IRCChannel
from gdo.irc.IRCCommand import IRCCommand


class join(IRCCommand):

    @classmethod
    def gdo_trigger(cls) -> str:
        return 'irc.join'

    def gdo_user_permission(self) -> str | None:
        return 'staff'

    def gdo_parameters(self) -> [GDT]:
        return [
            GDT_IRCChannel('channel').not_null(),
        ]

    @classmethod
    def gdo_method_config_channel(cls) -> [GDT]:
        return [
            GDT_Bool('auto_join'),
        ]

    def gdo_execute(self) -> GDT:
        name = self.param_val('channel')
        self.msg('msg_irc_join_channel', (html(name),))
        self.irc_connector().send_raw(f"JOIN {name}")
        return self.empty()

    def on_bot_joined(self):
        state = self.get_config_channel_val('auto_join')
        if state is None:
            self.save_config_channel('auto_join', '1')

    def on_connected(self):
        channels = self.channels_with_setting('auto_join', '1', self._env_server)
        for channel in channels:
            self.irc_connector().send_raw(f"JOIN {channel.get_name()}")
