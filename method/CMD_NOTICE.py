from gdo.core.GDT_UserType import GDT_UserType
from gdo.irc.method.CMD_PRIVMSG import CMD_PRIVMSG


class CMD_NOTICE(CMD_PRIVMSG):

    def gdo_is_notice(self) -> bool:
        return True

    async def gdo_execute(self):
        if not self._irc_prefix or len(self._irc_params) < 2:
            return self.empty()
        # IRC NOTICE is normally used by services, network announcements and
        # other automated actors.  Persist that fact so these users do not
        # become ordinary chat participants on later messages either.
        user = await self.irc_user(self._irc_prefix)
        if user.get_user_type() != GDT_UserType.BOT:
            user.save_val('user_type', GDT_UserType.BOT)
        sender = (self._irc_prefix or '').split('!', 1)[0]
        if sender.casefold() == 'nickserv':
            from gdo.irc.method.signup import signup
            await signup().env_copy(self).on_nickserv_notice(self._irc_params[1])
        return self.empty()
