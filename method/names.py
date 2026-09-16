from gdo.base.GDT import GDT
from gdo.base.Util import html
from gdo.irc.GDT_IRCChannel import GDT_IRCChannel
from gdo.irc.IRCCommand import IRCCommand


class names(IRCCommand):
    """List the member snapshot of a connected IRC channel."""

    @classmethod
    def gdo_trigger(cls) -> str:
        return 'irc.names'

    def gdo_parameters(self) -> list[GDT]:
        return [
            GDT_IRCChannel('channel').initial(self._env_channel.get_name()).not_null(),
        ]

    async def gdo_execute(self) -> GDT:
        channel = self.target_irc_channel(self.param_val('channel'))
        names = sorted((user.get_name() for user in channel.online_users()), key=str.casefold)
        return self.reply('msg_irc_names', (html(channel.get_name()), html(', '.join(names) or '-')))
