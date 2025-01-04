from gdo.base.Application import Application
from gdo.base.Message import Message
from gdo.base.Method import Method
from gdo.core.GDO_User import GDO_User


class autologin(Method):

    PROBES: dict[str, tuple[float, Message]] = {}

    def gdo_trigger(self) -> str:
        return ''

    def maybe_probe(self, user: GDO_User, original_message: Message):
        username = user.get_name_sid()
        if username in self.__class__.PROBES:
            probe = self.__class__.PROBES[username]
            if probe[0] < Application.TIME:
                pass
            else:
                return
        self.__class__.PROBES[username] = (Application.TIME + 300, original_message)
        self._env_server.get_connector().send_raw(f"WHOIS {username}")
