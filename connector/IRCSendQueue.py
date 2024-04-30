from gdo.base.Method import Method
from gdo.core.GDO_User import GDO_User


class IRCSendQueue:
    """
    Do not send messages too fast.
    Each user gets a list of replies for whom to sent.
    Keep the queues sorted by uid, so newer users are untrusted
    """

    _connector: 'IRC'
    _queues: dict[str, list[Method]]  # queue for each originated user with the executed method to reply

    def __init__(self, connector: 'IRC'):
        self._connector = connector
        self._queues = {}

    def sort_queues(self):
        # TODO: sort queues by uid (dict key)
        pass

    def queue_for_user(self, user: GDO_User):
        uid = user.get_id()
        if uid not in self._queues:
            self._queues[uid] = []
            self.sort_queues()
        return self._queues[uid]

    def get_next_method_to_process(self) -> Method|None:
        for queue in self._queues:
            if len(queue) > 0:
                pass
                # TODO: unshift a method from beginning of the queue
        return None

    def get_next_method_sleep_time(self) -> float:
        # TODO: calculate how long to sleep for not flooding a server
        pass
