# pygdo-irc
[PyGDO](https://github.com/gizmore/pygdo) module to add an IRC connector. Basic IRC functionality.

## Installation

```
cd pygdo
./gdo_adm.sh provide -y irc
pygdo add_server name01 IRC tcps://irc.wechall.net:6697
```


#### License

This is proprietary software licensed under the PyGDOv8 License
# Connecting a new server

Staff can use `$irc.connect <name> <tcp://host:port|tcps://host:port>`.
Certificate verification is enabled by default (`--cert=1`). For a trusted
test server, `--cert=0` disables TLS certificate and hostname verification;
this setting is saved with that server after registration and applies to its
reconnects as well. TLS encryption remains enabled for `tcps://`, but without
verification the peer's identity is not authenticated.
The server is initially temporary: IRC `001` publishes `irc_registered`,
which persists it before any bot user is created. Existing persisted servers
are not inserted again on reconnect. Existing or pending names are rejected.

The initial connection has a 60-second registration timeout. Failed attempts
are disconnected and discarded. Successful connections become managed Dog
servers, and the caller receives the actual nickname plus a `/msg <nick> $ping`
example using the server's command prefix. Use this in the running Dog for a
long-lived connection; a one-shot CLI process cannot retain a live socket.
`add_server` remains available to save configuration without connecting first.
# Raw IRC commands

Admins can send `$irc.raw [<server ID>] <command...>`. Omit the numeric server
ID to use the current message's server, or use `--server=<ID>` explicitly.
For example: `$irc.raw WHOIS Dog` or `$irc.raw 3 WHOIS Dog`.
Only connected IRC servers accept commands; embedded line breaks are rejected.

## Support requests

`$urgent <message>` privately forwards one line (up to 500 characters) to all
staff users currently known to be online on connected servers, including other
networks. Only the supplied text, sender name, and source server/channel are
forwarded, not conversation history. No recipient configuration is necessary.
The reply reports how many sends were queued; it does not confirm receipt or
promise an immediate answer. This is not an emergency service.
Requests are limited to one per user per minute and one per source server every
ten seconds. With no online staff, the command reports that forwarding is unavailable.
