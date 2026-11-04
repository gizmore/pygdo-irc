from gdo.core.GDT_UserType import GDT_UserType
from gdo.irc.IRCCommand import IRCCommand


class CMD_335(IRCCommand):
    """Recognize IRCv3 RPL_WHOISBOT for the user named in the WHOIS reply."""

    async def gdo_execute(self):
        if (len(self._irc_params) != 3 or not self._irc_params[1]
                or self._env_server.get_connector().bot_mode_supported is not True):
            return self.empty()
        user = await self._env_server.get_or_create_user(self._irc_params[1])
        if user.get_user_type() != GDT_UserType.BOT:
            user.save_val('user_type', GDT_UserType.BOT)
        return self.empty()
