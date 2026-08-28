from gdo.base.GDT import GDT
from gdo.core.GDO_Permission import GDO_Permission
from gdo.core.GDT_Bool import GDT_Bool
from gdo.core.GDT_String import GDT_String
from gdo.irc.IRCCommand import IRCCommand


class nick(IRCCommand):
    """Change the bot nickname on the current IRC server."""

    @classmethod
    def gdo_trigger(cls) -> str:
        return 'irc.nick'

    def gdo_user_permission(self) -> str | None:
        return GDO_Permission.STAFF

    def gdo_parameters(self) -> list[GDT]:
        return [
            GDT_Bool('permanent').not_null().initial('0'),
            GDT_String('new_nick').ascii().minlen(1).maxlen(64).pattern(r'^[^\x00\r\n :]+$').not_null().positional(),
        ]

    async def gdo_execute(self) -> GDT:
        nickname = self.param_val('new_nick')
        connector = self.irc_connector()
        configured = self._env_server.get_username()
        if nickname.casefold() == connector._own_nick.casefold():
            if nickname.casefold() == configured.casefold():
                if password := self._env_server.gdo_val('serv_password'):
                    await connector.send_raw(f'PRIVMSG NickServ :IDENTIFY {password}')
                    return self.reply('msg_irc_nick_identifying', (nickname,))
            return self.reply('msg_irc_nick_current', (nickname,))
        await connector.change_nick(nickname, self.param_value('permanent'))
        return self.reply('msg_irc_nick_sent', (nickname,))
