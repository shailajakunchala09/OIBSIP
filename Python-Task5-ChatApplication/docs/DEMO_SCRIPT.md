# Demo video script (target 3 minutes, range 2 to 4)

Record with two client windows side by side and the server console visible in the corner.
Start with a clean database. Speak slowly; keep the mouse movements deliberate.

## 0:00  Title card (5 seconds, text on a plain background)

```
Kunchala Shailaja
Python Programming
Task 5 — Chat Application
```

## 0:05  Introduction (15 s)
"This is VANTA CHAT, a multi-user chat application built with Python, Tkinter, sockets, threading and SQLite,
using only the standard library."

## 0:20  Start the server (15 s)
Double-click `run_server.bat`. Point at the console line that says the server is listening on 127.0.0.1:5050.

## 0:35  Splash and registration (25 s)
Launch the first client with `run_client.bat`. Show the splash, then the sign-in screen.
Click **Create an account**, try a short password to show the validation message, then register `alice`.

## 1:00  Second user and rooms (25 s)
Launch a second client and register `bob`. Both are in #General. Show the system line "joined".
Open **Python** from the sidebar in one client to show multiple rooms.

## 1:25  Real-time chat (30 s)
Send messages in both directions. Point out the timestamps. Show the typing indicator while one user types.
Send `:tada: :rocket:` to show emoji conversion, then open the emoji picker.

## 1:55  Notifications and unread badges (25 s)
Put Bob in another room, send from Alice in #General, and show the unread badge.
Minimise Bob's window, send again from Alice, and show the pop-up. Click it to jump to the room.

## 2:20  History and persistence (20 s)
Close Alice's window, reopen the client and sign in. Show that the earlier messages are still there.

## 2:40  Resilience (15 s)
Stop the server (Ctrl+C). Show the "Reconnecting" status in a client. Start the server again and show it reconnect.

## 2:55  Wrap-up (15 s)
Briefly show Settings (light theme) and say one honest line:
"Passwords are hashed, but messages are stored as plain text and the connection is not encrypted,
so this is for localhost and learning use."

## Before you record
* Run the automated tests once: `python -m unittest discover -s tests -t .`
* Close other windows, hide personal desktop items, and use fake passwords.
