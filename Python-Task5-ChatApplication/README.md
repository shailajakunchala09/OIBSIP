# VANTA CHAT

**Private conversations. Simple connection.**

A multi-user desktop chat application written in Python. A threaded TCP server stores users, rooms and
message history in SQLite, and a Tkinter client gives each person a sign-in screen, chat rooms, live
messages, unread badges and desktop pop-ups. It uses the Python standard library only, with no packages to install.

Built for **OASIS INFOBYTE Python Programming Internship, Task 5: Chat Application**.

> **Please read the [Security & privacy](#security--privacy) section.** Passwords are hashed, but messages are
> stored as plain text and sent over unencrypted TCP. This is a learning project meant for localhost or a
> trusted network.

---

## Features

| Area | What it does |
|---|---|
| Accounts | Register and sign in. Passwords are stored as salted PBKDF2 hashes. Wrong-password and unknown-user errors are identical. |
| Rooms | Four rooms are seeded (General, Python, Technology, Random). Users can create rooms, join, and leave. Membership is saved. |
| Messaging | Real-time delivery to everyone in a room, with timestamps, date separators, and system lines such as "You joined #General". |
| History | The last 100 messages of a room are loaded when you open it. Everything is kept in SQLite across restarts. |
| Presence | Online and last-seen status per member, plus online counts per room. |
| Typing indicator | "alice is typing…" is shown to others in the room. |
| Unread badges | Rooms you are not looking at count new messages from other people. |
| Notifications | An always-on-top pop-up appears for new messages **only while the window is unfocused**. Optional sound. Clicking it opens the room. |
| Emoji | Shortcodes such as `:smile:` are converted on send. An emoji picker is built in. |
| Search | Find a room (Ctrl+K) or search the messages you have loaded in the current room (Ctrl+F). |
| Reliability | Heartbeat, idle timeout, automatic reconnect with session resume, graceful logout, abrupt-disconnect handling, per-user rate limit. |
| Interface | Splash screen, light and dark themes, settings, About dialog, keyboard shortcuts, confirmations, empty states, friendly error messages. |

### Emoji shortcodes

`:smile:` 😄 · `:heart:` ❤️ · `:thumbsup:` 👍 · `:laughing:` 😆 · `:fire:` 🔥 · `:rocket:` 🚀 · `:wave:` 👋 · `:joy:` 😂 ·
`:ok_hand:` 👌 · `:clap:` 👏 · `:star:` ⭐ · `:eyes:` 👀 · `:tada:` 🎉 · `:thinking:` 🤔 · `:pray:` 🙏 · `:100:` 💯

Unknown shortcodes are left as typed.

### Keyboard shortcuts

| Keys | Action |
|---|---|
| Ctrl+K | Find a room |
| Ctrl+F | Search messages in the current room |
| Ctrl+N | Create a room |
| Ctrl+E | Emoji picker |
| Ctrl+B | Show or hide the members panel |
| Ctrl+, | Settings |
| Enter / Shift+Enter | Send / new line |
| Esc | Clear the message box, or close search |

---

## How this maps to the OASIS task

| Requirement | Where |
|---|---|
| Server and client over sockets | `server/server.py`, `client/client.py` |
| Real-time messaging | `ChatServer._on_send_message` broadcasts to room members |
| Timestamps | Epoch seconds stored per message, formatted on the client (`client/state.py`) |
| Graceful disconnect | `logout` / `bye` frames, plus abrupt-drop cleanup in `ChatServer._disconnect` |
| Run on localhost | Default `127.0.0.1:5050` (`common/protocol.py`) |
| GUI | Tkinter, `client/` |
| Registration and login | `server/auth.py`, `server/server.py`, `client/login_view.py` |
| Multiple rooms | `rooms` and `room_members` tables, `ChatServer._join` / `_on_leave_room` |
| History on join | `Database.recent_messages`, sent inside the `joined` frame |
| Notifications when unfocused | `App._maybe_notify` and `ToastManager` in `client/gui.py` and `client/components.py` |
| Emoji | `common/emoji.py` (server conversion), picker in `client/chat_view.py` |

---

## Architecture

```
┌──────────────┐   newline-delimited JSON over TCP    ┌────────────────────────┐
│ Tkinter      │ ───────────────────────────────────▶ │ ChatServer             │
│ client (GUI) │ ◀─────────────────────────────────── │  one thread per client │
└──────────────┘                                      │  ├─ auth (PBKDF2)      │
  App (gui.py)                                        │  ├─ rooms + broadcast  │
  ├─ LoginView / ChatView                             │  └─ SQLite (WAL)       │
  ├─ ChatState  (pure Python)                         └────────────────────────┘
  └─ ChatClient (reader + heartbeat threads → queue)
```

**Threading on the client.** Tkinter is not thread-safe, so socket reads happen on background threads that
only put frames on a `queue.Queue`. The GUI drains that queue every 40 ms with `after()` and is the only code
that touches widgets.

**Threading on the server.** The accept loop starts one thread per connection. Shared state (online sessions,
session tokens) is guarded by a lock. Each session has its own send lock so two broadcasts cannot interleave bytes.
SQLite is accessed through one `Database` object that serialises access.

**Protocol.** Each frame is one UTF-8 JSON object followed by `\n`. Frames over a size limit or that are not valid
JSON are rejected. Examples:

```json
{"type": "login", "username": "alice", "password": "…"}
{"type": "send_message", "room_id": 1, "text": "hello :wave:"}
{"type": "message", "room_id": 1, "message": {"id": 12, "kind": "user", "username": "alice", "text": "hello 👋", "ts": 1767000000}}
```

Client to server: `register`, `login`, `resume`, `logout`, `list_rooms`, `create_room`, `join_room`, `leave_room`,
`send_message`, `typing`, `ping`.
Server to client: `auth_ok`, `rooms`, `joined`, `left`, `message`, `presence`, `typing`, `error`, `pong`, `bye`, `server_shutdown`.

**Message flow.** The client sends `send_message`. The server validates it, applies the rate limit, converts emoji
shortcodes, writes it to SQLite, then broadcasts a `message` frame to every online member of that room, including the
sender. The sender's own message appears when that broadcast comes back, so what you see is what was stored.

**Reconnect.** If the connection drops, the client retries up to 8 times with a growing delay and sends a `resume`
frame carrying an in-memory session token. If the server restarted, the token is gone and the user is returned to the
sign-in screen with a clear message.

### Database schema (`database/vanta_chat.db`)

| Table | Columns |
|---|---|
| `users` | `id`, `username` (unique, case-insensitive), `password_hash`, `created_at`, `last_seen` |
| `rooms` | `id`, `name` (unique, case-insensitive), `description`, `created_by`, `created_at` |
| `room_members` | `room_id`, `user_id`, `joined_at` (primary key on both ids) |
| `messages` | `id`, `room_id`, `user_id`, `kind` (`user` or `system`), `body`, `created_at` |

Foreign keys are enforced and the journal mode is WAL. The database file is created and seeded automatically on the
first server start.

### Project structure

```
Python-Task5-ChatApplication/
├── common/            protocol.py, emoji.py, validation.py   (shared by both sides)
├── server/            server.py, database.py, auth.py, config.py
├── client/            gui.py, client.py, state.py, chat_view.py, login_view.py,
│                      components.py, theme.py, settings.py
├── database/          created at runtime (the .db file is git-ignored)
├── assets/icons/      placeholder folder (no icon files are shipped)
├── screenshots/       see screenshots/README.md for the capture plan
├── docs/              DEMO_SCRIPT.md
├── tests/             test_server.py, test_client.py
├── run_server.bat
├── run_client.bat
├── requirements.txt
└── README.md
```

---

## Requirements

* **Python 3.10 or newer** (3.12 was used for development of the server and tests).
* **Tkinter.** It ships with the python.org Windows installer. If `import tkinter` fails, re-run the installer
  and make sure *tcl/tk and IDLE* is ticked.
* No third-party packages.

## Setup on Windows

Open PowerShell or Command Prompt in the project folder:

```bat
python -m venv .venv
.venv\Scripts\activate
```

The virtual environment is optional because nothing needs installing, but the `.bat` files use it automatically if it exists.

## Running

**1. Start the server** (leave this window open):

```bat
run_server.bat
```

or `python -m server.server`. Options: `--host`, `--port`, `--db`.

**2. Start one or more clients** (a new window each time):

```bat
run_client.bat
```

or `python -m client.gui`. Options: `--host`, `--port`, `--splash-seconds` (use `0` to skip the splash).

### Trying it with two users (Alice and Bob)

1. Start the server, then start a client. Choose **Create an account**, register `alice` with a password of 8 or more characters.
2. Start a second client. Register `bob`.
3. Both users land in **#General**. Send a message from Alice and watch it arrive for Bob with a timestamp.
4. Type `:tada:` or pick an emoji from the picker.
5. Minimise Bob's window and send from Alice. A pop-up should appear for Bob. Click it to jump to the room.
6. Create a room from Alice (Ctrl+N) and join it from Bob using the **BROWSE** list.
7. Close Alice's window, then reopen and sign in again. The history is still there.

Both clients can run on one machine. To use two machines on the same network, start the server with
`python -m server.server --host 0.0.0.0` and start clients with `--host <server-ip>`. Remember the traffic is not encrypted
(see below), and you may need to allow the port through the Windows firewall.

## Testing

```bat
python -m unittest discover -s tests -t .
```

There are 31 automated tests. They start a real server on a free local port with a temporary SQLite file and talk to it over real sockets.
They cover registration and login rules, password hashing and unique salts, duplicate users, malformed input, real-time delivery,
room isolation, history order, join and leave notices, room creation rules, the rate limit, typing events, abrupt disconnects and presence,
ten simultaneous clients, persistence across a server restart, the client state logic, and client connection failure and loss detection.

**What is not covered by automated tests:** the Tkinter windows themselves. See [Known limitations](#known-limitations).

---

## Security & privacy

This section describes exactly what the application does and does not protect.

**What is protected**

* Passwords are never stored. The server stores `pbkdf2_sha256$200000$<salt>$<hash>`: PBKDF2-HMAC-SHA256, 200,000 iterations, a random 16-byte salt per user.
* Hashes are compared in constant time. An unknown username takes the same verification work as a wrong password, and both return the same message.
* All database queries are parameterised.
* Input is validated on the server (usernames, room names, password length, message length, control characters removed) in addition to the client.
* A per-connection rate limit (10 messages per 5 seconds), a frame-size limit and an idle timeout reduce abuse and dead connections.
* A second sign-in to the same account is refused while it is already online.
* The client saves only theme, notification choices and the last username to `~/.vanta_chat/settings.json`. It never saves passwords or session tokens.

**What is NOT protected**

* **Messages are stored as plain text** in `database/vanta_chat.db`. The database holds usernames, password hashes, room names and descriptions,
  room membership, every message body with its timestamp, and last-seen times. Anyone with access to that file, and the server operator, can read all messages.
* **Traffic is unencrypted TCP.** There is no TLS. Anyone who can watch the network between client and server can read messages and the password at sign-in.
  This is not end-to-end encryption.
* The session token used for reconnect is held in server memory and in the client's memory. It is sent unencrypted like everything else.
* There is no account recovery, no password change, no email verification, no administrator role and no message deletion or moderation.
* The rate limit is the only abuse protection. It is not a defence against a determined attacker.

Use it on localhost or a network you trust, and do not share real passwords or sensitive conversations through it.
Adding TLS with `ssl.SSLContext.wrap_socket` would be the first step toward a safer version.

---

## Known limitations

* **The GUI was not visually run during development of this build.** The environment used to write the code had no Tkinter, so the windows were
  compile-checked and their controller logic was exercised against a stub, but layout, colours, hover states, the splash, pop-ups and
  the emoji picker have not been looked at on a real screen. Expect to adjust spacing or fonts after your first run, and please capture the
  screenshots from your own machine.
* There are no automated tests for the Tkinter widgets.
* Emoji rendering depends on the Tk build and font. Some systems draw them in monochrome.
* DPI awareness is not enabled, so text can look slightly soft on scaled Windows displays.
* Message search covers only messages loaded in the client (up to 100 on joining a room, plus new ones), not the full database history.
* Desktop pop-ups are in-app windows, not native Windows notifications, and appear only while the app is running.
* Rooms are public to everyone on the server. There are no private rooms or direct messages.
* One window per account at a time.
* The server runs in a console and has no admin interface.

## Future improvements

TLS, password change, direct messages, private rooms, full-history server-side search, message edit and delete, file sharing,
native notifications, a packaged Windows executable, and Tkinter widget tests.

---

## Author

**Kunchala Shailaja** · Python Programming Intern, OASIS INFOBYTE
GitHub: [shailajakunchala09](https://github.com/shailajakunchala09) · Repository: `OIBSIP`

Task 5: Chat Application
