from gdo.base.GDT import GDT
from gdo.irc.IRCCommand import IRCCommand
from gdo.irc.method.CMD_PRIVMSG import CMD_PRIVMSG


class CMD_005(IRCCommand):
    """
    Save IRC Settings from a line like:
    :irc.local 005 Dog AWAYLEN=200 CASEMAPPING=rfc1459 CHANLIMIT=#:20 CHANMODES=b,k,l,imnpst CHANNELLEN=64 CHANTYPES=# ELIST=CMNTU HOSTLEN=64 KEYLEN=32 KICKLEN=255 LINELEN=512 MAXLIST=b:100 :are supported by this server
    """

    def gdo_execute(self) -> GDT:
        for setting in self._irc_params[1:]:
            try:
                key, val = setting.split('=')
                if key == 'LINELEN':
                    CMD_PRIVMSG().env_copy(self).save_config_server('max_msg_len', val)
            except:
                pass
        return self.empty()
