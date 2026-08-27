from gdo.base.Application import Application
from gdo.base.GDT import GDT
from gdo.irc.IRCCommand import IRCCommand


class CMD_001(IRCCommand):

    async def gdo_execute(self) -> GDT:
        connector = self.irc_connector()
        nickname = self._irc_params[0]
        await connector.setup_dog_user(nickname)
        # A 433 fallback changes the active nick. Never identify that fallback
        # nick with credentials belonging to the configured original nick.
        password = self._env_server.gdo_val('serv_password')
        if password and nickname.casefold() == self._env_server.get_username().casefold():
            await connector.send_raw(f'PRIVMSG NickServ :IDENTIFY {password}')
        await Application.EVENTS.publish(f'irc_connected', self._env_server, self)
        return self.empty()
