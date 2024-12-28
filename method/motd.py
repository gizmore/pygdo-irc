from gdo.base.GDT import GDT
from gdo.core.GDT_Text import GDT_Text
from gdo.irc.IRCCommand import IRCCommand


class motd(IRCCommand):
    MOTDS: dict[str, str] = {}  # MOTD in progress.

    def gdo_method_config_server(self) -> [GDT]:
        return [
            GDT_Text('irc_motd'),
        ]

    def save_motd(self):
        sid = self._env_server.get_id()
        self.save_config_server('irc_motd', self.__class__.MOTDS[sid])
        del self.MOTDS[sid]

    def gdo_execute(self) -> GDT:
        return self.reply('%s', [self.get_config_server_val('irc_motd')])

