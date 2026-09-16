import regex

from gdo.base.GDT import GDT
from gdo.base.Util import html
from gdo.core.GDT_Bool import GDT_Bool
from gdo.core.GDT_String import GDT_String
from gdo.irc.IRCCommand import IRCCommand


class join(IRCCommand):

    @classmethod
    def gdo_trigger(cls) -> str:
        return 'irc.join'

    def gdo_user_permission(self) -> str | None:
        return 'staff'

    def gdo_parameters(self) -> list[GDT]:
        return [
            GDT_String('channel').pattern(r'^#{1,2}[a-z][-_a-z0-9]*$', regex.IGNORECASE).not_null().positional(),
        ]

    @classmethod
    def gdo_method_config_channel(cls) -> list[GDT]:
        return [
            GDT_Bool('auto_join'),
        ]

    async def gdo_execute(self) -> GDT:
        name = self.param_val('channel')
        channel = self.target_irc_channel(self.irc_channel(name))
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
