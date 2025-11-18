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
from gdo.core.GDO_Permission import GDO_Permission
from gdo.core.GDO_User import GDO_User
from gdo.core.GDO_UserPermission import GDO_UserPermission
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
        return Mode.irc

    def gdo_has_channels(self) -> bool:
        return True

    async def gdo_connect(self) -> bool:
        try:
            url = self._server.get_url()
            host = url['host']
            port = url['port']
            self._own_nick = self.get_nickname()
            Logger.debug(f"Connecting to {url['raw']}")

            ssl_ctx = None
            if url['tls']:
                ssl_ctx = ssl.create_default_context()
                # Optionally:
                # ssl_ctx.check_hostname = True
                # ssl_ctx.verify_mode = ssl.CERT_REQUIRED

            self._recv_thread = IRCReader(self)
            self._send_thread = IRCWriter(self)

            recv, send = await asyncio.open_connection(
                host,
                port,
                ssl=ssl_ctx,
                server_hostname=host if url['tls'] else None,
            )
            self._recv_thread.sock = recv
            self._send_thread.sock = send
            if recv and send:
                self._connected = True
                reader_task = asyncio.create_task(self._recv_thread.run_(), name=self._server.get_name()+"_IRC_READ")
                writer_task = asyncio.create_task(self._send_thread.run_(), name=self._server.get_name()+"_IRC_WRITE")
                Application.TASKS[self._server.get_name()+"_IRC_READ"] = reader_task
                Application.TASKS[self._server.get_name()+"_IRC_WRITE"] = writer_task
                await self.send_user_cmd()
                await asyncio.wait([reader_task, writer_task])
                Logger.debug('connected!')
            return self._connected

        except Exception as ex:
            Logger.exception(ex)
            self.connect_failed()
            return False

    async def gdo_disconnect(self, quit_message: str):
        await self.send_quit(quit_message)
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
            return mod.get_method(f"CMD_{name}").env_mode(Mode.irc).env_server(self._server).env_channel(None).env_user(None, False).env_session(None)
        except GDOMethodException as ex:
            Logger.debug(f'Unknown IRC Command {name}')
            return module_irc.instance().get_method("CMD_NA")

    async def process_message(self, message: str):
        Application.tick()
        Application.mode(Mode.irc)

        Logger.debug(message)

        prefix, command, params = self.parse_message(message)

        cmd = self.get_command(command)
        cmd._message = message
        cmd._irc_prefix = prefix
        cmd._irc_params = params

        result = cmd.gdo_execute()
        while asyncio.iscoroutine(result):
            result = await result
        return result

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

    async def send_user_cmd(self, stub: Method = None):
        nickname = self.get_nickname()
        await self.send_raw(f"USER {nickname} {nickname} {nickname} :{nickname}")
        await self.send_raw(f"NICK {nickname}")

    async def send_nick_cmd(self):
        nickname = f"{self.get_nickname()}_{Random.mrand(1, 99):02d}"
        self._own_nick = nickname
        await self.send_raw(f"NICK {nickname}")

    async def send_quit(self, message: str):
        await self.send_raw(f"QUIT {message}")

    ########
    # Send #
    ########
    async def send_raw(self, message: str):
        await self._send_thread.write_now(message)

    async def gdo_send_to_channel(self, message: Message):
        channel = message._env_channel
        server = message._env_server
        text = message._result
        for line in text.splitlines():
            if line:
                msg = message.message_copy().result(line)
                prefix = f'{message._env_user.render_name()}: ' if not message._thread_user else ''
                Logger.debug(f"{server.get_name()} >> {channel.render_name()} >> {line}")
                prefix = f'PRIVMSG {channel.get_name()} :{prefix}'
                await self._send_thread.write(prefix, msg)

    async def gdo_send_to_user(self, message: Message, notice: bool=False):
        server = message._env_server
        user = message._env_user
        text = message._result
        for line in text.splitlines():
            if line:
                msg = message.message_copy().result(line)
                Logger.debug(f"{server.get_name()} >> {user.render_name()} >> {line}")
                prefix = f'NOTICE {user.get_name()} :' if notice else f'PRIVMSG {user.get_name()} :'
                await self._send_thread.write(prefix, msg)

    def gdo_get_dog_user(self) -> GDO_User:
        return self._own_user

    def setup_dog_user(self, dog_name: str) -> GDO_User:
        self._own_nick = dog_name
        self._own_user = self._server.get_or_create_user(dog_name)
        self._own_user.save_val('user_type', GDT_UserType.CHAPPY)
        GDO_UserPermission.grant(self._own_user, GDO_Permission.ADMIN)
        GDO_UserPermission.grant(self._own_user, GDO_Permission.STAFF)
        GDO_UserPermission.grant(self._own_user, GDO_Permission.VOICE)
        self._own_user._authenticated = True
        return self._own_user
