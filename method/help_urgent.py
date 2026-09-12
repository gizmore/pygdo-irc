import time

from gdo.base.Method import Method
from gdo.core.GDT_RestOfText import GDT_RestOfText
from gdo.core.GDO_User import GDO_User


class help_urgent(Method):
    """Forward a bounded support request privately to online staff."""
    RECENT = {}

    @classmethod
    def gdo_trigger(cls):
        return 'urgent'

    def gdo_connectors(self):
        return 'irc'

    def gdo_method_hidden(self):
        return True

    def gdo_needs_authentication(self):
        return False

    def gdo_parameters(self):
        return [GDT_RestOfText('message').not_null()]

    async def gdo_execute(self):
        text = self.param_value('message')
        if not text or not text.strip() or len(text) > 500 or any(c in text for c in '\r\n\0'):
            return self.err('err_help_urgent_text')
        server = self._env_server
        contacts = {contact.get_id(): contact for contact in GDO_User.staff()
                    if contact.get_server().get_connector().is_connected() and contact.is_online()}
        if not contacts:
            return self.err('err_help_urgent_unavailable')
        now = time.monotonic()
        type(self).RECENT = {key: value for key, value in self.RECENT.items() if now - value < 60}
        user = self._env_reply_to or self._env_user
        key = (server.get_id(), user.get_id())
        network_key = (server.get_id(), None)
        if key in self.RECENT or now - self.RECENT.get(network_key, float('-inf')) < 10:
            return self.err('err_help_urgent_wait')
        self.RECENT[key] = self.RECENT[network_key] = now
        origin = '%s / %s' % (server.get_name(), self._env_channel.get_name() if self._env_channel else 'private message')
        sent = 0
        for contact in contacts.values():
            try:
                await contact.get_server().send_to_user(contact, 'msg_help_urgent_request', (user.get_name(), origin, text))
                sent += 1
            except Exception:
                continue
        if not sent:
            return self.err('err_help_urgent_unavailable')
        return self.msg('msg_help_urgent_sent', (sent, len(contacts)))
