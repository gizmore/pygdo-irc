from gdo.base.GDO_Module import GDO_Module
from gdo.core.Connector import Connector
from gdo.irc.connector.IRC import IRC


class module_irc(GDO_Module):

    def __init__(self):
        super().__init__()

    def gdo_init(self):
        Connector.register(IRC)
