import asyncio
from collections import deque
import time

from gdo.base.Message import Message
from gdo.base.Method import Method
from gdo.core.GDO_User import GDO_User


class IRCSendQueue():
    """
    Do not send messages too fast.
    Each user gets a list of replies for whom to sent.
    Keep the queues sorted by uid, so newer users are untrusted
    """

    _connector: 'IRC'
    _queues: dict[str, asyncio.Queue[Message]]  # queue for each originated user with the executed method to reply
    _queue_order: deque[str]
    _has_messages: asyncio.Event
    _tokens: int|None
    _last_refill: float

    def __init__(self, connector: 'IRC'):
        self._connector = connector
        self._queues = {}
        self._queue_order = deque()
        self._has_messages = asyncio.Event()
        self._tokens = None
        self._last_refill = time.monotonic()

    def queue_for_user(self, user: GDO_User | object):
        uid = user.get_id()
        if uid not in self._queues:
            self._queues[uid] = asyncio.Queue()
            self._queue_order.append(uid)
        return self._queues[uid]

    async def append(self, message: Message):
        queue = self.queue_for_user(message._env_user)
        queue.put_nowait(message)
        self._has_messages.set()

    async def get_next_message_to_process(self) -> Message | None:
        """Return one reply per origin in round-robin order.

        A long reply such as ``$help`` must not monopolise the flood window:
        after one line the next waiting user gets a turn.  A finite wait keeps
        the writer responsive to a disconnect while it is otherwise idle.
        """
        while not self._queue_order:
            self._has_messages.clear()
            try:
                await asyncio.wait_for(self._has_messages.wait(), timeout=0.25)
            except asyncio.TimeoutError:
                return None

        uid = self._queue_order.popleft()
        queue = self._queues[uid]
        message = queue.get_nowait()
        if queue.empty():
            del self._queues[uid]
        else:
            self._queue_order.append(uid)
        return message

    def get_rate_limit(self) -> tuple[float, int]:
        """Return the configured (refill period, burst size) for this server."""
        from gdo.irc.method.CMD_PRIVMSG import CMD_PRIVMSG
        method = CMD_PRIVMSG().env_server(self._connector._server)
        period = float(method.get_config_server_value('flood_period'))
        burst = int(method.get_config_server_value('flood_burst'))
        return max(0.0, period), max(1, burst)

    async def wait_for_send_slot(self):
        """Consume one server-wide IRC flood token.

        The bucket permits a small configurable burst after idle time, then
        refills one line per configured period.  Raw IRC protocol traffic is
        intentionally sent outside this queue by ``IRC.send_raw()``.
        """
        while True:
            period, burst = self.get_rate_limit()
            if period == 0:
                return

            now = time.monotonic()
            if self._tokens is None:
                self._tokens = burst
                self._last_refill = now
            else:
                elapsed = now - self._last_refill
                tokens = int(elapsed / period)
                if tokens:
                    self._tokens = min(burst, self._tokens + tokens)
                    self._last_refill += tokens * period
                else:
                    self._tokens = min(burst, self._tokens)

            if self._tokens:
                self._tokens -= 1
                return

            await asyncio.sleep(max(0.0, period - (now - self._last_refill)))
