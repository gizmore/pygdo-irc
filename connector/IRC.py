import socket
import ssl

from gdo.base.Logger import Logger
from gdo.core.Connector import Connector
from gdo.core.GDO_Server import GDO_Server
from gdo.irc.connector.IRCReader import IRCReader
from gdo.irc.connector.IRCWriter import IRCWriter


class IRC(Connector):
    """
    IRC Connector for the Dog Chatbot
    """

    _sock: object
    _recv_thread: object
    _send_thread: object

    def gdo_has_channels(self) -> bool:
        return True

    def gdo_connect(self) -> bool:
        try:
            url = self._server.get_url()
            host = url['host']
            port = url['port']

            # Create a socket object
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Wrap the socket with SSL/TLS
            context = ssl.create_default_context()
            if url['tls']:
                ssl_sock = context.wrap_socket(sock, server_hostname=host)
                ssl_sock.connect((host, port))
                self._sock = ssl_sock
            else:
                sock.connect((host, port))
                self._sock = sock

            # TODO: check if self._sock is connected
            self._recv_thread = IRCReader(self)
            self._recv_thread.daemon = True
            self._recv_thread.start()

            self._send_thread = IRCWriter(self)


            # TODO: Now create a reader thread with blocking socket
        except GDOException as ex:
            Logger.exception(ex)
            return False
        return True

    def gdo_disconnect(self, quit_message: str):
        pass

    def gdo_disconnected(self):
        """
        on a disconnect, stop and join all threads gracefully
        """
        if hasattr(self, '_sock'):
            self._sock.close()
            delattr(self, '_sock')
        if hasattr(self, '_recv_thread'):
            self._recv_thread.join()
            delattr(self, '_recv_thread')
        if hasattr(self, '_send_thread'):
            self._send_thread.join()
            delattr(self, '_send_thread')

    def process_message(self, irc_text):
        Logger.debug(irc_text)
        pass

