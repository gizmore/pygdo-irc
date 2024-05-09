from gdo.irc.IRCCommand import IRCCommand


class CMD_433(IRCCommand):

    def gdo_execute(self):
        self._env_server.get_connector().send_nick_cmd()
