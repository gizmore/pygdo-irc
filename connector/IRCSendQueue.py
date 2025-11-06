import asyncio
from queue import Queue

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

    def __init__(self, connector: 'IRC'):
        self._connector = connector
        self._queues = {}

    def sort_queues(self):
        self._queues = {k: self._queues[k] for k in sorted(self._queues)}

    def queue_for_user(self, user: GDO_User | object):
        uid = user.get_id()
        if uid not in self._queues:
            self._queues[uid] = asyncio.Queue()
            self.sort_queues()
        return self._queues[uid]

    async def append(self, message: Message):
        queue = self.queue_for_user(message._env_user)
        await queue.put(message)

    async def get_next_message_to_process(self) -> Message | None:
        for queue in self._queues.values():
            if queue.qsize() > 0:
                return await queue.get()
        return None

    def get_next_sleep_time(self) -> float:
        return 1
