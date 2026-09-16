from gdo.base.GDT import GDT
from gdo.base.Util import html
from gdo.core.GDT_Bool import GDT_Bool
from gdo.core.GDT_Channel import GDT_Channel
from gdo.irc.IRCCommand import IRCCommand


class join(IRCCommand):

    @classmethod
    def gdo_trigger(cls) -> str:
        return 'irc.join'

    def gdo_user_permission(self) -> str | None:
        return 'staff'

    def gdo_parameters(self) -> list[GDT]:
        return [
            GDT_Channel('channel').connectors('irc').not_null(),
        ]

    @classmethod
    def gdo_method_config_channel(cls) -> list[GDT]:
        return [
            GDT_Bool('auto_join'),
        ]

    async def gdo_execute(self) -> GDT:
        channel = self.target_irc_channel(self.param_value('channel'))
        name = channel.get_name()
        self.msg('msg_irc_join_channel', (html(name),))
        await self.irc_connector().send_raw(f"JOIN {name}")
        return self.empty()

    def on_bot_joined(self):
        state = self.get_config_channel_val('auto_join')
        if state is None:
            self.save_config_channel('auto_join', '1')

    async def on_connected(self):
        channels = self.channels_with_setting('auto_join', '1', self._env_server)
        for channel in channels:
            await self.irc_connector().send_raw(f"JOIN {channel.get_name()}")
