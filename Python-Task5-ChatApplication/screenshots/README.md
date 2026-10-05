# Screenshot capture plan

Capture these from your own machine, running the real app. Do not mock or edit them.
Use the Windows Snipping Tool (Win+Shift+S) and save as PNG with exactly these names in this folder.
A window width of about 1180 px (the default) looks best.

Before you start: delete `database/vanta_chat.db` for a clean database, start `run_server.bat`, and open two clients.
Register `alice` in the first and `bob` in the second. Use obviously fake passwords.

| File | What to capture |
|---|---|
| `01-splash.png` | The splash screen. Run `python -m client.gui --splash-seconds 8` to give yourself time. |
| `02-login.png` | The sign-in screen, empty, in dark theme. |
| `03-register.png` | The "Create your account" screen with a username typed and the password hidden. |
| `04-chat-room.png` | Alice in #General with a short conversation between Alice and Bob (include a timestamp and a date chip). |
| `05-multiple-rooms.png` | The sidebar showing YOUR ROOMS and BROWSE, with an unread badge on a room Alice is not viewing. |
| `06-emoji.png` | The emoji picker open, or a message that contains converted shortcodes such as `:tada:` and `:rocket:`. |
| `07-notification.png` | A pop-up toast in the bottom-right corner while Bob's window is unfocused or minimised, after Alice sends a message. |
| `08-settings-light.png` | The Settings dialog, or the whole app in the light theme. Light theme is the better choice because dark is shown elsewhere. |
| `09-members-history.png` | The members panel showing online and last-seen status, in a room that has history from an earlier session (close and reopen a client first). |
| `10-error-handling.png` | An error state: sign in with a wrong password, or start the client with the server stopped and capture the "Could not reach the server" message. |

Check each image before committing: no real passwords, no personal paths, no other private windows in the frame.
