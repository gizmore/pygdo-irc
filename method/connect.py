import asyncio

from gdo.base.Application import Application
from gdo.base.Method import Method
from gdo.core.GDO_Server import GDO_Server
from gdo.core.GDT_Name import GDT_Name
from gdo.core.GDT_Bool import GDT_Bool
from gdo.core.method.launch import launch
from gdo.net.GDT_Url import GDT_Url


class connect(Method):
    """Connect once; persist only after the IRC welcome, then adopt the loop."""

    PENDING = set()
    TIMEOUT = 60

    @classmethod
    def gdo_trigger(cls):
        return 'irc.connect'

    def gdo_user_permission(self):
        return 'staff'

    def gdo_transactional(self):
        return False

    def gdo_parameters(self):
        return [GDT_Name('name').not_null().positional(),
                GDT_Url('url').schemes(['tcp', 'tcps']).in_and_external().not_null().positional(),
                GDT_Bool('cert').not_null().initial('1')]

    async def gdo_execute(self):
        name, url = self.param_val('name'), self.param_val('url')
        key = name.casefold()
        if key in self.PENDING or GDO_Server.table().get_by_vals({'serv_name': name}):
            return self.err('err_irc_connect_exists')
        server = GDO_Server.blank({'serv_name': name, 'serv_url': url, 'serv_connector': 'irc',
                                   'serv_tls_validate': self.param_val('cert')})
        connector = server.get_connector()
        self.PENDING.add(key)
        worker = None
        registered = None
        adopted = False
        try:
            async def run():
                await connector.connect()
                if server.is_persisted():
                    await server.loop()

            server._has_loop = True
            worker = asyncio.create_task(run(), name=f'IRC connect {name}')
            server._loop_task = worker
            Application.TASKS.append(worker)
            registered = asyncio.create_task(connector._registration_complete.wait())
            done, _ = await asyncio.wait([worker, registered], timeout=self.TIMEOUT,
                                         return_when=asyncio.FIRST_COMPLETED)
            if registered not in done or not server.is_persisted():
                return self.err('err_irc_connect_failed')
            launch.SERVERS.append(server)
            adopted = True
            return self.msg('msg_irc_connect_success', (
                name, server.get_id(), connector._own_nick,
                connector._own_nick, server.get_trigger(),
            ))
        finally:
            self.PENDING.discard(key)
            if registered:
                registered.cancel()
                await asyncio.gather(registered, return_exceptions=True)
            if not adopted:
                if worker:
                    worker.cancel()
                    await asyncio.gather(worker, return_exceptions=True)
                    if worker in Application.TASKS:
                        Application.TASKS.remove(worker)
                connector.disconnected()
                server._has_loop = False
                server._loop_task = None
