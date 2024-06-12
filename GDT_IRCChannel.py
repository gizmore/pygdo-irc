from gdo.core.GDT_Name import GDT_Name


class GDT_IRCChannel(GDT_Name):

    def __init__(self, name):
        super().__init__(name)
        self.pattern('/[#@][a-z][a-z_0-9]/i')
