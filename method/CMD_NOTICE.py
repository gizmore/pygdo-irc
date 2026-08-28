from gdo.irc.method.CMD_PRIVMSG import CMD_PRIVMSG


class CMD_NOTICE(CMD_PRIVMSG):

    async def gdo_execute(self):
        sender = (self._irc_prefix or '').split('!', 1)[0]
        if sender.casefold() == 'nickserv' and len(self._irc_params) > 1:
            from gdo.irc.method.signup import signup
            await signup().env_copy(self).on_nickserv_notice(self._irc_params[1])
            return self.empty()
        return await super().gdo_execute()
