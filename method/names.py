from gdo.base.GDT import GDT
from gdo.base.Util import html
from gdo.core.GDT_Channel import GDT_Channel
from gdo.irc.IRCCommand import IRCCommand


class names(IRCCommand):
    """List the member snapshot of a connected IRC channel."""

    @classmethod
    def gdo_trigger(cls) -> str:
        return 'irc.names'

    def gdo_method_hidden(self) -> bool:
        return True

    def gdo_parameters(self) -> list[GDT]:
        return [
            GDT_Channel('channel').connectors('irc').default_current().not_null(),
        ]

    async def gdo_execute(self) -> GDT:
        channel = self.target_irc_channel(self.param_value('channel'))
        names = sorted((user.get_name() for user in channel.online_users()), key=str.casefold)
        return self.reply('msg_irc_names', (html(channel.get_name()), html(', '.join(names) or '-')))
