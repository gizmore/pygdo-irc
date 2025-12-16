import regex

from gdo.core.GDT_Name import GDT_Name


class GDT_IRCChannel(GDT_Name):

    def __init__(self, name):
        super().__init__(name)
        self.pattern(r'^[#@]{1,2}[a-z][-a-z_0-9]*$', regex.IGNORECASE)
