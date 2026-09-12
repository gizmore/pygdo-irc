import unittest
from unittest.mock import Mock, AsyncMock

from gdo.base.Application import Application
from gdo.base.Events import Events
from gdo.base.Render import Mode
from gdo.irc.method.CMD_PRIVMSG import CMD_PRIVMSG
from gdo.irc.method.CMD_NOTICE import CMD_NOTICE


class PrefixGuardTest(unittest.IsolatedAsyncioTestCase):
    async def test_malformed_messages_do_not_resolve_users(self):
        Application.EVENTS = Events()
        Application.mode(Mode.render_irc)
        for cls in (CMD_PRIVMSG, CMD_NOTICE):
            for prefix, params in ((None, ['*', 'notice']), ('nick!u@h', [])):
                method = cls()
                method._irc_prefix = prefix
                method._irc_params = params
                method.empty = Mock()
                method.irc_user = AsyncMock()
                await method.gdo_execute()
                method.irc_user.assert_not_awaited()
                method.empty.assert_called_once()
