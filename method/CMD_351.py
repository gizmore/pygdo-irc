from gdo.base.GDT import GDT
from gdo.irc.IRCCommand import IRCCommand
from gdo.irc.method.version import version


class CMD_351(IRCCommand):
    """Refresh the daemon identity after an IRC VERSION request."""

    def gdo_execute(self) -> GDT:
        # RPL_VERSION: <client> <version> <server> :<comments>
        if len(self._irc_params) < 2:
            return self.empty()
        # Persist through the version method's server-scoped config.  A 351
        # numeric has no user/channel context, so only copy its server.
        target = version()
        target._env_server = self._env_server
        target.save_server_version(self._irc_params[1])
        return self.empty()
