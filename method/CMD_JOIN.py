from gdo.base.GDT import GDT
from gdo.irc.IRCCommand import IRCCommand


class CMD_JOIN(IRCCommand):

    async def gdo_execute(self) -> GDT:
        self._env_user = await self.irc_user(self._irc_prefix)
        self._env_server = self._env_user.get_server()
        for name in self._irc_params[0].split(','):
            self._env_channel = self.irc_channel(name)
            if self.is_own_user():
                await self._env_server.on_bot_joined(self._env_user, self._env_channel)
                await self._env_channel.on_bot_joined(self._env_user)
                from gdo.irc.method.join import join
                join().env_copy(self).on_bot_joined()
            else:
                # Record this at the IRC protocol boundary as well as via the
                # generic server event.  In particular this catches a JOIN
                # immediately after a reconnect, before a later channel
                # lifecycle update can obscure its timestamp.
                from gdo.fun.module_fun import module_fun
                if fun := module_fun.for_irc():
                    fun.remember_join(self._env_user)
                await self._env_server.on_user_joined(self._env_user, self._env_channel)
                await self._env_channel.on_user_joined(self._env_user)
        return self.empty()
