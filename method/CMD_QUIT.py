from gdo.base.GDT import GDT
from gdo.irc.IRCCommand import IRCCommand


class CMD_QUIT(IRCCommand):

    async def gdo_execute(self) -> GDT:
        self._env_user = await self.irc_user(self._irc_prefix)
        self._env_server = self._env_user.get_server()
        if self.is_own_user():
            await self._env_server.on_bot_quit(self._env_user)
        else:
            # QUIT is the authoritative end of an IRC connection.  Do this
            # before the server lifecycle removes the user from its rooms, so
            # Fun can still announce an eligible new record there.
            from gdo.fun.module_fun import module_fun
            if fun := module_fun.for_irc():
                await fun.remember_quit(self._env_user)
            await self._env_server.on_user_quit(self._env_user)
        return self.empty()
