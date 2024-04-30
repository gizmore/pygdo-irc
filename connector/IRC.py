import socket

from gdo.core.Connector import Connector
from gdo.core.GDO_Server import GDO_Server


class IRC(Connector):
    _sock: object
    _recv_thread: object
    _send_thread: object

    def gdo_connect(self) -> bool:
        host = self._server.get_host()
        port = self._server.get_port()
        ssl = self._server.is_tls()

        # Create a socket object
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Wrap the socket with SSL/TLS
        context = ssl.create_default_context()
        if ssl:
            ssl_sock = context.wrap_socket(sock, server_hostname=host)
            ssl_sock.connect((host, port))
            self._sock = ssl_sock
        else:
            sock.connect((host, port))
            self._sock = sock
