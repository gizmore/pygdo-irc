from gdo.base.GDT import GDT
from gdo.base.Util import html
from gdo.irc.GDT_IRCChannel import GDT_IRCChannel
from gdo.irc.IRCCommand import IRCCommand
from gdo.irc.method.join import join


class part(IRCCommand):

    @classmethod
    def gdo_trigger(cls) -> str:
        return 'irc.part'

    def gdo_in_private(self) -> bool:
        return False

    def gdo_user_permission(self) -> str | None:
        return 'staff'

    def gdo_parameters(self) -> list[GDT]:
        # In a channel, `$irc.part` parts that channel. An explicit name still
        # allows staff to remove another channel on the same IRC server.
        return [
            GDT_IRCChannel('channel').initial(self._env_channel.get_name()).not_null(),
        ]

    async def gdo_execute(self) -> GDT:
        name = self.param_val('channel')
        channel = self.target_irc_channel(name)

        # auto_join belongs to the join method's channel configuration.
        join().env_copy(self).env_channel(channel).save_config_channel('auto_join', '0')
        await self.irc_connector().send_raw(f'PART {name}')
        return self.reply('msg_irc_part_channel', (html(name),))
