import asyncio
import socket
import ssl
import time

from gdo.base.Application import Application
from gdo.base.Exceptions import GDOException, GDOMethodException
from gdo.base.Logger import Logger
from gdo.base.Message import Message
from gdo.base.Method import Method
from gdo.base.Render import Mode
from gdo.base.Util import Random
from gdo.core.Connector import Connector
from gdo.core.GDO_User import GDO_User
from gdo.core.GDT_UserType import GDT_UserType
from gdo.irc.connector.IRCReader import IRCReader
from gdo.irc.connector.IRCWriter import IRCWriter


class IRC(Connector):
    """
    IRC Connector for the Dog Chatbot
    """

    _socket: object
    _recv_thread: IRCReader
    _send_thread: IRCWriter
    _event_loop: object
    _own_nick: str
    _own_user: GDO_User

    def __init__(self):
        super().__init__()
        self._socket = None
        self._recv_thread = None
        self._send_thread = None
        self._own_nick = 'Dog'
        self._own_user = None

    def get_render_mode(self) -> Mode:
        return Mode.IRC

    def gdo_has_channels(self) -> bool:
        return True

    def gdo_connect(self) -> bool:
        try:
            url = self._server.get_url()
            host = url['host']
            port = url['port']
            self._own_nick = self.get_nickname()
            Logger.debug(f"Connecting to {url['raw']}")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            context = ssl.create_default_context()
            if url['tls']:
                ssl_sock = context.wrap_socket(sock, server_hostname=host)
                ssl_sock.connect((host, port))
                self._socket = ssl_sock
            else:
                sock.connect((host, port))
                self._socket = sock

            self._connected = True

            self._event_loop = asyncio.get_event_loop()

            self._recv_thread = IRCReader(self)
            self._recv_thread.daemon = True
            self._recv_thread.start()

            self._send_thread = IRCWriter(self)
            self._send_thread.daemon = True
            self._send_thread.start()

            self.send_user_cmd()

            Logger.debug('connected!')
            return True

        except Exception as ex:
            Logger.exception(ex)
            self.connect_failed()
            return False

    def gdo_disconnect(self, quit_message: str):
        self.send_quit(quit_message)
        time.sleep(0.5)
        # self.gdo_disconnected()

    def gdo_disconnected(self):
        """
        on a disconnect, stop and join all threads gracefully
        """
        if hasattr(self, '_sock'):
            self._socket.close()
            delattr(self, '_sock')

    #########
    # Parse #
    #########

    def get_command(self, name: str) -> Method:
        from gdo.irc.module_irc import module_irc
        mod = module_irc.instance()
        try:
            return mod.get_method(f"CMD_{name}").env_mode(Mode.IRC).env_server(self._server).env_channel(None).env_user(None)
        except GDOMethodException as ex:
            Logger.debug(f'Unknown IRC Command {name}')
            return module_irc.instance().get_method("CMD_NA")

    def process_message(self, message: str):
        Application.tick()

        Logger.debug(message)

        prefix, command, params = self.parse_message(message)

        cmd = self.get_command(command)
        cmd._message = message
        cmd._irc_prefix = prefix
        cmd._irc_params = params

        cmd.gdo_execute()

    def parse_message(self, message: str):
        prefix = None
        command = None
        params = []

        tokens = message.split(' ')

        if tokens[0].startswith(':'):
            prefix = tokens[0][1:]
            tokens = tokens[1:]

        command = tokens[0]
        tokens = tokens[1:]

        if len(tokens) > 0 and tokens[0].startswith(':'):
            params.append(' '.join(tokens)[1:])
        else:
            while len(tokens) > 0:
                if tokens[0].startswith(':'):
                    params.append(' '.join(tokens)[1:])
                    break
                else:
                    params.append(tokens[0])
                    tokens = tokens[1:]

        return prefix, command, params

    ###########
    # Connect #
    ###########

    def get_nickname(self):
        return self._server.get_username()

    def send_user_cmd(self, stub: Method = None):
        nickname = self.get_nickname()
        self.send_raw(f"USER {nickname} {nickname} {nickname} :{nickname}")
        self.send_raw(f"NICK {nickname}")

    def send_nick_cmd(self):
        nickname = f"{self.get_nickname()}_{Random.mrand(1, 99):02d}"
        self._own_nick = nickname
        self.send_raw(f"NICK {nickname}")

    def send_quit(self, message: str):
        self.send_raw(f"QUIT {message}")

    ########
    # Send #
    ########
    def send_raw(self, message: str):
        self._send_thread.write_now(message)

    async def gdo_send_to_channel(self, message: Message):
        channel = message._env_channel
        server = message._env_server
        text = message._result
        for line in text.splitlines():
            msg = message.message_copy().result(line)
            prefix = f'{message._env_user.render_name()}: ' if not message._thread_user else ''
            Logger.debug(f"{server.get_name()} >> {channel.render_name()} >> {line}")
            prefix = f'PRIVMSG {channel.get_name()} :{prefix}'
            self._send_thread.write(prefix, msg)

    async def gdo_send_to_user(self, message: Message):
        server = message._env_server
        user = message._env_user
        text = message._result
        for line in text.splitlines():
            msg = message.message_copy().result(line)
            Logger.debug(f"{server.get_name()} >> {user.render_name()} >> {line}")
            prefix = f'PRIVMSG {user.get_name()} :'
            self._send_thread.write(prefix, msg)

    def gdo_get_dog_user(self) -> GDO_User:
        return self._own_user

    def setup_dog_user(self, dog_name: str) -> GDO_User:
        self._own_nick = dog_name
        self._own_user = self._server.get_or_create_user(dog_name, dog_name)
        self._own_user.save_val('user_type', GDT_UserType.CHAPPY)
        return self._own_user
