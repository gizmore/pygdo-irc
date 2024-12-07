from gdo.core.GDO_Permission import GDO_Permission


class IRCUtil:
    PERMISSIONS = {
        '@': GDO_Permission.ADMIN,
        '!': GDO_Permission.ADMIN,
        '%': GDO_Permission.STAFF,
        '+': None,
    }

    @classmethod
    def strip_permission(cls, username: str):
        if username[0] in cls.PERMISSIONS:
            return username[1:]
        return username
