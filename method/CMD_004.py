from gdo.base.GDT import GDT
from gdo.irc.IRCCommand import IRCCommand
from gdo.irc.method.version import version


class CMD_004(IRCCommand):
    """Store the daemon identity advertised during IRC registration.

    RPL_MYINFO has the form ``<nick> <server> <version> ...`` and arrives as
    part of every successful IRC startup.
    """

    def gdo_execute(self) -> GDT:
        if len(self._irc_params) >= 3:
            target = version()
            target._env_server = self._env_server
            target.save_server_version(self._irc_params[2])
        return self.empty()
