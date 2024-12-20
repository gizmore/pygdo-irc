from gdo.base.GDT import GDT
from gdo.irc.IRCCommand import IRCCommand


class part(IRCCommand):

    def gdo_trigger(self) -> str:
        return 'irc.part'

    def gdo_connectors(self) -> str:
        return 'irc'

    def gdo_user_permission(self) -> str | None:
        return 'staff'

    async def gdo_execute(self) -> GDT:
        name = self._env_channel.get_name()
        self.irc_connector().send_raw(f"PART {name}")
        return self.empty()
