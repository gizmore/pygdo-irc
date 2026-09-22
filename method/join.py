import regex

from gdo.base.GDT import GDT
from gdo.base.Util import html
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

    async def gdo_execute(self) -> GDT:
        name = self.param_val('channel')
        self.msg('msg_irc_join_channel', (html(name),))
        await self.irc_connector().send_raw(f"JOIN {name}")
        return self.empty()

    def on_bot_joined(self):
        self._env_channel.save_val('chan_autojoin', '1')

    async def on_connected(self):
        for channel in self._env_server.query_channels():
            if channel.gdo_val('chan_autojoin') != '1':
                continue
            await self.irc_connector().send_raw(f"JOIN {channel.get_name()}")
