# 🔐 VANTA CHAT

<p align="center">
  <b>Real-Time Private Chat Application</b><br/>
  <i>Private conversations. Simple connection.</i>
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white">
  <img alt="GUI" src="https://img.shields.io/badge/GUI-Tkinter-4B8BBE">
  <img alt="Networking" src="https://img.shields.io/badge/Networking-TCP-2563EB">
  <img alt="Database" src="https://img.shields.io/badge/Database-SQLite-003B57">
  <img alt="Protocol" src="https://img.shields.io/badge/Protocol-JSON%20over%20TCP-7C3AED">
  <img alt="License" src="https://img.shields.io/badge/License-Educational-lightgrey">
  <img alt="Status" src="https://img.shields.io/badge/Status-Complete-16a34a">
</p>

---

## 📖 Project Overview

**VANTA CHAT** is a real-time desktop chat application built for **OASIS INFOBYTE's Python Programming Internship — Task 5: Chat Application**.

It provides a complete client-server messaging experience with user accounts, chat rooms, real-time messages, persistent chat history, online presence, typing indicators, unread badges, desktop notifications, search, themes, and connection management.

The application is built using **Python's standard library**, with **Tkinter** for the graphical interface, **TCP sockets** for networking, and **SQLite** for persistent server-side storage.

The project demonstrates practical Python concepts including:

- Client-server architecture
- TCP socket programming
- Multi-threading
- JSON-based communication
- GUI development with Tkinter
- SQLite database integration
- Password hashing
- Real-time event handling
- Connection management
- Error handling

## 🎯 Why This Project?

Basic chat applications often demonstrate only a simple socket connection and message exchange.

**VANTA CHAT** extends that concept into a complete desktop application by combining real-time communication with authentication, chat rooms, persistent history, notifications, search, presence, and connection management.

The project is designed to demonstrate how different Python components can work together as a practical application while keeping the networking, database, and user-interface responsibilities separated.

## ✨ Key Features

- 👤 **User accounts** with sign-in and authentication
- 🔐 **PBKDF2 salted password hashing**
- 💬 **Real-time messaging** over TCP
- 🏠 **Multiple chat rooms**
- ➕ **Create new rooms**
- 🚪 **Join and leave rooms**
- 🕘 **Persistent message history**
- 📅 **Message timestamps and date separators**
- 🟢 **Online presence**
- ✍️ **Live typing indicator**
- 🔔 **Unread message badges**
- 🖥️ **Desktop notifications**
- 🔊 **Notification sound settings**
- 🔎 **Room search**
- 🔍 **Message search**
- 😊 **Emoji picker**
- 🌙 **Dark and light themes**
- ⚙️ **Application settings**
- 🔄 **Automatic reconnect**
- ❤️ **Heartbeat connection monitoring**
- ⏱️ **Idle connection timeout**
- 🚦 **Message rate limiting**
- 🚪 **Graceful logout**
- 📜 **Chat history with the latest 100 messages**

## 🛡 Security Features

| Feature | Detail |
|---|---|
| Password security | Passwords are protected using PBKDF2 salted hashes |
| Authentication | Users must authenticate before using the chat application |
| Request validation | Server validates client requests before processing |
| Rate limiting | Helps prevent excessive message requests |
| Connection management | Heartbeat and idle timeout handling |
| Graceful logout | Connections are closed cleanly |
| Database storage | SQLite provides structured persistent storage |

> **Security note:** VANTA CHAT uses TCP communication without TLS encryption and stores chat messages as plain text in SQLite. It is intended for localhost or trusted-network educational use and should not be considered a production secure messaging platform.

## 💬 Chat Application Logic

The application follows a client-server communication model.

```text
Tkinter Client
      │
      │ Newline-delimited JSON over TCP
      ▼
Threaded Chat Server
      │
      ├── Authentication
      ├── Room Management
      ├── Message Processing
      ├── Presence
      ├── Typing Events
      └── Rate Limiting
      │
      ▼
SQLite Database
      │
      ├── Users
      ├── Rooms
      └── Messages
```

## 🧠 Client-Server Architecture

VANTA CHAT uses a threaded TCP server and a Tkinter client.

### Server

The server is responsible for:

- Managing client connections
- Authenticating users
- Managing chat rooms
- Processing messages
- Maintaining presence
- Storing chat history
- Handling typing events
- Applying rate limits
- Managing connection timeouts

### Client

The client is responsible for:

- Login and account access
- Displaying chat rooms
- Sending messages
- Receiving messages
- Displaying notifications
- Showing unread counts
- Searching rooms and messages
- Managing themes and settings

### Threading

The server uses one thread per client connection.

The client uses background reader threads to receive incoming messages without blocking the Tkinter interface.

Incoming events are passed into a queue and processed by the GUI.

## 🗄 Database & Persistence

VANTA CHAT uses **SQLite** for server-side persistence.

The database stores information required for:

- User accounts
- Chat rooms
- Messages
- Chat history

Messages remain available when a user leaves and later rejoins a room.

The application provides access to the latest **100 messages** of a room as history.

## 🧰 Technology Stack

| Layer | Technology |
|---|---|
| Language | Python 3.10+ |
| GUI | Tkinter |
| Networking | TCP Sockets |
| Communication | Newline-delimited JSON |
| Database | SQLite |
| Concurrency | Python threading |
| Password Security | PBKDF2 salted hashes |
| Testing | Python standard library |
| Dependencies | Python standard library |

> No third-party Python packages are required for VANTA CHAT.
>
## 🏗 Architecture

```text
                    ┌──────────────────────┐
                    │    Tkinter Client    │
                    │                      │
                    │ Login / Rooms / Chat │
                    │ Search / Settings    │
                    │ Notifications        │
                    └──────────┬───────────┘
                               │
                               │ TCP + JSON
                               ▼
                    ┌──────────────────────┐
                    │   Threaded Server    │
                    │                      │
                    │ Authentication       │
                    │ Room Management      │
                    │ Messaging            │
                    │ Presence             │
                    │ Rate Limiting        │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │       SQLite         │
                    │                      │
                    │ Users / Rooms /      │
                    │ Messages / History   │
                    └──────────────────────┘
```

## 📁 Project Structure

```text
Python-Task5-ChatApplication/
├── assets/
├── client/
├── common/
├── database/
├── docs/
├── screenshots/
├── server/
├── tests/
├── .gitignore
├── README.md
├── requirements.txt
├── run_client.bat
└── run_server.bat
```

## 🗂 File Overview

| File / Folder | Responsibility |
|---|---|
| `client/` | Tkinter desktop chat client |
| `server/` | Threaded TCP chat server |
| `common/` | Shared application components |
| `database/` | SQLite database functionality |
| `assets/` | Application assets |
| `docs/` | Project documentation |
| `screenshots/` | Application screenshots |
| `tests/` | Automated tests |
| `requirements.txt` | Project dependency information |
| `run_client.bat` | Windows client launcher |
| `run_server.bat` | Windows server launcher |
| `README.md` | Project documentation |

## 🖥 GUI / UX

VANTA CHAT provides a desktop interface built with Tkinter.

### Authentication

Users can access the application through the sign-in and account system.

### Chat Rooms

Users can:

- View available rooms
- Search rooms
- Join rooms
- Create rooms
- Leave rooms
- Rejoin rooms

### Conversation Area

The chat interface provides:

- Real-time messages
- Timestamps
- Date separators
- System messages
- Typing indicators
- Message history
- Online presence
- Unread message badges

### Notifications

The application supports:

- Desktop notifications
- Notification sounds
- Notification settings

### Themes

Users can switch between:

- Light theme
- Dark theme

- ## 🔎 Search

VANTA CHAT provides search functionality for both rooms and messages.

| Shortcut | Function |
|---|---|
| `Ctrl + K` | Search rooms |
| `Ctrl + F` | Search messages |

## 🔔 Notifications

VANTA CHAT supports desktop notifications for incoming messages.

Unread message badges indicate messages that have not yet been viewed.

Notification behavior can be controlled through the application settings.

## ✍️ Typing Indicator

The application provides a real-time typing indicator.

When a user starts typing, other connected users can see the typing activity before the message is sent.

## 🏠 Chat Rooms

The application includes seeded chat rooms and allows users to create additional rooms.

A user can:

1. Select a room.
2. Join the room.
3. Send messages.
4. Receive messages in real time.
5. Leave the room.
6. Rejoin the room.
7. View previous room history.

## 🔄 Connection Management

VANTA CHAT includes several connection-management features:

- ❤️ Heartbeat monitoring
- 🔄 Automatic reconnect
- ⏱️ Idle timeout
- 🚪 Graceful logout
- 🧵 Background reader threads
- 📥 Queue-based GUI event handling

These features help maintain a responsive client during normal connection interruptions.

## 🚦 Validation & Error Handling

The application handles common errors without unnecessarily crashing the GUI.

Examples include:

- Invalid authentication
- Invalid room operations
- Connection interruptions
- Invalid requests
- Empty messages
- Server-side validation errors
- Disconnected clients

The server validates incoming requests before processing them.

## 🔒 Security & Privacy Considerations

- Passwords are protected using salted PBKDF2 hashing.
- Plain-text passwords are not stored.
- Server-side validation is performed on client requests.
- Message rate limiting helps control excessive requests.
- Connection timeouts help manage inactive clients.
- Chat messages are stored in the SQLite database.
- The application does not claim to provide production-grade encrypted messaging.

### Important Limitation

The current application communicates using standard TCP without TLS encryption.

Therefore, it is intended for:

- Localhost use
- Trusted private networks
- Educational demonstrations
- Testing environments

Production deployment would require additional security measures such as encrypted communication, stronger deployment controls, and secure infrastructure.

## 🧪 Testing

VANTA CHAT was manually tested using multiple client sessions.

| Test | Result |
|---|---|
| Tkinter startup | ✅ Passed |
| Server startup | ✅ Passed |
| Client startup | ✅ Passed |
| User registration/login | ✅ Passed |
| Room joining | ✅ Passed |
| Message sending | ✅ Passed |
| Real-time two-user messaging | ✅ Passed |
| Leave and rejoin | ✅ Passed |
| Message history | ✅ Passed |
| Room creation | ✅ Passed |
| Typing indicator | ✅ Passed |
| Unread badge | ✅ Passed |
| Desktop notification | ✅ Passed |
| Room search | ✅ Passed |
| Message search | ✅ Passed |
| Dark theme | ✅ Passed |
| Light theme | ✅ Passed |
| Notification settings | ✅ Passed |

### Run Tests

```bash
python -m unittest discover -s tests -v

## 📸 Screenshots

Application screenshots are included in the project's `screenshots/` directory.

```text
screenshots/
```

The screenshots demonstrate the main VANTA CHAT interface and its functionality, including chat rooms, conversations, notifications, and themes.

## ▶️ How to Run

### Start the Server

From the project directory:

```bash
python -m server.server
```

The default server address is:

```text
127.0.0.1:5050
```

The server displays:

```text
VANTA CHAT server listening on 127.0.0.1:5050
```

### Start the Client

Open another terminal in the project directory:

```bash
python -m client.gui
```

The VANTA CHAT desktop application will open.

## ⚙️ Installation

Clone the OIBSIP repository:

```bash
git clone https://github.com/shailajakunchala09/OIBSIP.git
```

Move into the Task 5 project:

```bash
cd OIBSIP/Python-Task5-ChatApplication
```

Check your Python version:

```bash
python --version
```

VANTA CHAT requires:

```text
Python 3.10+
```

No third-party packages are required.

### Start the Server

```bash
python -m server.server
```

### Start the Client

Open another terminal:

```bash
python -m client.gui
```

## 🪟 Windows Launchers

Windows users can also use the included batch files.

### Server

```text
run_server.bat
```

### Client

```text
run_client.bat
```
## 🕹 Usage

1. Start the VANTA CHAT server.
2. Launch the desktop client.
3. Create an account or sign in.
4. Select a chat room.
5. Join the room.
6. Send and receive messages in real time.
7. Create additional rooms when required.
8. Use room and message search.
9. View typing indicators and unread badges.
10. Configure notification and theme settings.
11. Leave rooms or log out when finished.

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl + K` | Search rooms |
| `Ctrl + F` | Search messages |

## 🧪 Manual Testing Workflow

VANTA CHAT was tested using multiple client sessions.

A two-user test can be performed by connecting two clients to the same server and joining the same room.

The testing workflow includes:

1. Start the server.
2. Open the first client.
3. Sign in with the first account.
4. Open a second client.
5. Sign in with another account.
6. Join the same room.
7. Send messages between both users.
8. Verify real-time delivery.
9. Leave and rejoin the room.
10. Verify that message history remains available.
11. Test typing indicators.
12. Test unread badges and desktop notifications.
13. Test room and message search.
14. Test light and dark themes.

## 🚀 Future Enhancements

Possible future improvements include:

- 🔐 TLS-encrypted communication
- 📎 File sharing
- 🖼️ Image sharing
- 👥 Private one-to-one conversations
- 👤 User profile customization
- 🔑 Password reset functionality
- 🌐 Web-based client
- 📱 Mobile client
- ☁️ Secure cloud deployment
- 🛡️ Additional server security controls

  ## 🎓 Learning Outcomes

Building VANTA CHAT reinforced:

- Client-server architecture
- TCP socket programming
- Python threading
- Tkinter GUI development
- SQLite database management
- JSON communication
- Authentication workflows
- Password hashing
- Real-time event handling
- Queue-based GUI updates
- Connection management
- Error handling
- Application testing
- Separation of concerns

The project provided practical experience in building a complete Python application that combines networking, database management, GUI development, and real-time communication.

## 🎓 OASIS INFOBYTE Internship

**Program:** Python Programming Internship  
**Organization:** **OASIS INFOBYTE**  
**Task:** **Task 5 – Chat Application**

VANTA CHAT was developed as part of the OASIS INFOBYTE Python Programming Internship.

## 👩‍💻 Developer

**Kunchala Shailaja**

Python Programming Internship — **OASIS INFOBYTE**

GitHub: **shailajakunchala09**

Repository: **OIBSIP**

## 📌 Project Status

✅ **Complete**

All major VANTA CHAT Task 5 functionality has been implemented and manually verified, including:

- User accounts
- Authentication
- Chat rooms
- Real-time messaging
- Persistent message history
- Room creation
- Typing indicators
- Unread badges
- Desktop notifications
- Room search
- Message search
- Dark/light themes
- Settings
- Connection management

The project is available in the public **OIBSIP GitHub repository** under:

```text
Python-Task5-ChatApplication/
