
🔐 VANTA CHAT
<p align="center"> <b>Real-Time Private Chat Application</b><br/> <i>Private conversations. Simple connection.</i> </p> <p align="center"> <img alt="Python" src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white"> <img alt="GUI" src="https://img.shields.io/badge/GUI-Tkinter-4B8BBE"> <img alt="Networking" src="https://img.shields.io/badge/Networking-TCP-2563EB"> <img alt="Database" src="https://img.shields.io/badge/Database-SQLite-003B57"> <img alt="Protocol" src="https://img.shields.io/badge/Protocol-JSON%20over%20TCP-7C3AED"> <img alt="Testing" src="https://img.shields.io/badge/Testing-Manual%20%2B%20Automated-16a34a"> <img alt="License" src="https://img.shields.io/badge/License-Educational-lightgrey"> <img alt="Status" src="https://img.shields.io/badge/Status-Complete-16a34a"> </p>
🔗 Project Repository
https://github.com/shailajakunchala09/OIBSIP

Project: Python-Task5-ChatApplication

VANTA CHAT is a desktop Tkinter application using a threaded TCP server and SQLite database. It is designed for local or trusted-network use rather than public web hosting.

📖 Project Overview

VANTA CHAT is a real-time desktop chat application built for the OASIS INFOBYTE Python Programming Internship — Task 5: Chat Application.

The project provides a complete client-server messaging experience with user accounts, chat rooms, real-time message delivery, persistent message history, online presence, typing indicators, unread message badges, desktop notifications, search, themes, and automatic reconnection.

The application is built using Python's standard library, with Tkinter for the graphical interface, TCP sockets for networking, and SQLite for persistent server-side data.

The project focuses on demonstrating practical Python concepts including:

Client-server architecture
TCP socket programming
Multi-threading
JSON-based communication
GUI development with Tkinter
SQLite database integration
Password hashing
Real-time event handling
Error handling
Automated testing
🎯 Why This Project?

Many basic chat applications demonstrate only a simple socket connection and message exchange.

VANTA CHAT approaches the same problem as a complete desktop application by combining:

👤 User authentication
💬 Real-time messaging
🏠 Multiple chat rooms
🗄 Persistent message history
🟢 Online presence
✍️ Typing indicators
🔔 Desktop notifications
🔎 Message and room search
🌙 Dark and light themes
🔄 Automatic reconnection
🛡 Password security

The project separates the networking, database, and interface layers so each part can be maintained and tested independently.

✨ Key Features
👤 User accounts with sign-in and registration
🔐 PBKDF2 salted password hashing
💬 Real-time messaging over TCP
🏠 Multiple chat rooms
➕ Create new rooms
🚪 Join and leave rooms
🕘 Persistent message history
📅 Message timestamps and date separators
🟢 Online presence indicators
✍️ Live typing indicator
🔔 Unread message badges
🖥️ Desktop notifications
🔊 Notification sound settings
🔎 Room search
🔍 Message search
😊 Emoji picker
🌙 Dark and light themes
⚙️ Application settings
🔄 Automatic reconnect
❤️ Heartbeat connection monitoring
⏱️ Idle connection timeout
🚦 Message rate limiting
🚪 Graceful logout
⌨️ Keyboard shortcuts
📜 Last 100 messages available as room history
🛡 Security Features
Feature	Detail
Password protection	Passwords are stored using PBKDF2 salted hashes
Password storage	Plain-text passwords are not stored
Rate limiting	Helps prevent excessive message requests
Input validation	Server validates incoming requests
Graceful logout	Client closes the connection cleanly
Connection monitoring	Heartbeat mechanism detects inactive connections
Idle timeout	Inactive connections can be closed automatically
Database storage	SQLite is used for structured persistent data
Protocol validation	Client/server communicate using structured JSON messages

Security note: VANTA CHAT uses unencrypted TCP communication and stores chat messages as plain text in SQLite. It is intended for localhost or trusted-network educational use and should not be treated as a production secure messaging system.

💬 Chat Application Logic

VANTA CHAT follows a client-server communication model.

Message Flow
User
  │
  ▼
Tkinter Client
  │
  │ JSON over TCP
  ▼
Threaded Chat Server
  │
  ├── Authentication
  ├── Room Management
  ├── Message Processing
  ├── Presence
  └── Rate Limiting
  │
  ▼
SQLite Database
  │
  └── Users / Rooms / Messages / History

When a user sends a message:

The Tkinter client collects the message.
The message is converted into a JSON request.
The request is sent through the TCP connection.
The server validates and processes the request.
The server stores the message in SQLite.
Connected clients receive the new message.
The GUI updates the conversation in real time.
🗄 Database & Persistence

The server uses SQLite to maintain application data.

The database manages information required for:

👤 User accounts
🏠 Chat rooms
💬 Messages
🕘 Message history
🟢 User presence-related state

The server maintains persistent room history, allowing users to see previous messages after leaving and rejoining a room.

The application limits displayed room history to the last 100 messages.

🧠 Architecture

VANTA CHAT uses a layered client-server architecture.

┌─────────────────────────────┐
│       Tkinter Client        │
│                             │
│  Login / Rooms / Chat UI    │
│  Notifications / Search     │
└──────────────┬──────────────┘
               │
               │ JSON over TCP
               ▼
┌─────────────────────────────┐
│       Threaded Server       │
│                             │
│ Authentication              │
│ Room Management             │
│ Messaging                   │
│ Presence                    │
│ Rate Limiting               │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│          SQLite             │
│                             │
│ Users / Rooms / Messages    │
└─────────────────────────────┘
Threading Model

The server creates a separate thread for each client connection.

The client also uses background reader threads so that incoming messages do not block the Tkinter GUI.

Incoming events are passed into a queue and processed by the GUI safely.

🧰 Technology Stack
Layer	Technology
Language	Python 3.10+
GUI	Tkinter
Networking	TCP Sockets
Communication	Newline-delimited JSON
Database	SQLite
Concurrency	Python threading
Password Security	PBKDF2 salted hashes
Testing	Python standard library
Dependencies	Python standard library

No third-party Python packages are required for the VANTA CHAT application.

🏗 Project Architecture
Client
  │
  ├── GUI
  ├── Network Reader
  ├── Event Queue
  └── User Interaction
          │
          ▼
      TCP Socket
          │
          ▼
Server
  │
  ├── Client Threads
  ├── Authentication
  ├── Room Management
  ├── Message Handling
  ├── Presence
  ├── Rate Limiting
  └── Database Layer
          │
          ▼
       SQLite
📁 Project Structure
Python-Task5-ChatApplication/
│
├── assets/
│
├── client/
│   └── gui.py
│
├── common/
│
├── database/
│
├── docs/
│
├── screenshots/
│
├── server/
│   └── server.py
│
├── tests/
│
├── .gitignore
├── README.md
├── requirements.txt
├── run_client.bat
└── run_server.bat
🗂 File Overview
File / Folder	Responsibility
client/	Tkinter desktop client
server/	TCP chat server and connection handling
common/	Shared communication and application components
database/	SQLite database-related functionality
assets/	Application assets
docs/	Project documentation
screenshots/	Application screenshots
tests/	Automated test files
requirements.txt	Project dependency information
run_client.bat	Windows client launcher
run_server.bat	Windows server launcher
README.md	Project documentation
🖥 GUI / UX

VANTA CHAT provides a desktop interface designed around common messaging workflows.

Login / Account Access

Users can sign in and access the chat application through their account.

Chat Rooms

The application provides:

Room list
Room creation
Join room
Leave room
Room search
Unread message indicators
Chat Area

The conversation interface provides:

Real-time messages
Timestamps
Date separators
System messages
Typing indicators
Message history
Online presence
Notifications

Users can configure:

Desktop notifications
Notification sounds
Themes

The application supports:

☀️ Light theme
🌙 Dark theme
🔎 Search

VANTA CHAT provides separate search functionality.

Room Search
Ctrl + K

Allows users to search available chat rooms.

Message Search
Ctrl + F

Allows users to search messages in the chat interface.

🔔 Notifications & Unread Messages

When a new message arrives while the user is not actively viewing the relevant conversation:

An unread badge can appear.
The unread count is updated.
Desktop notification support can alert the user.

Notification behavior can be controlled from the application settings.

✍️ Typing Indicator

VANTA CHAT provides a real-time typing indicator.

When another user is typing, the chat interface can indicate that activity before the message is sent.

This demonstrates real-time event communication beyond ordinary message delivery.

🏠 Chat Rooms

The application includes seeded rooms and supports creating additional rooms.

Users can:

View available rooms.
Search for rooms.
Join a room.
Send messages.
Leave a room.
Rejoin later.
View previous room history.
🔄 Connection Reliability

VANTA CHAT includes several connection-management features:

❤️ Heartbeat monitoring
⏱️ Idle timeout
🔄 Automatic reconnect
🚪 Graceful logout
🧵 Background reader threads
📥 Event queue for GUI updates

These features help the client remain responsive during normal connection interruptions.

🚦 Error Handling

The application handles common errors without unnecessarily crashing the GUI.

Examples include:

Invalid login information
Invalid room operations
Connection interruptions
Invalid requests
Empty messages
Server-side validation errors
Disconnected clients

The server also performs request validation before processing client operations.

🧪 Testing

VANTA CHAT was manually tested using multiple client sessions.

Tested Functionality
Test	Result
Server startup	✅ Passed
Client startup	✅ Passed
Tkinter availability	✅ Passed
User registration/login	✅ Passed
Room joining	✅ Passed
Message sending	✅ Passed
Real-time two-user messaging	✅ Passed
Leave and rejoin room	✅ Passed
Message history	✅ Passed
Room creation	✅ Passed
Typing indicator	✅ Passed
Unread message badge	✅ Passed
Desktop notification	✅ Passed
Room search	✅ Passed
Message search	✅ Passed
Dark theme	✅ Passed
Light theme	✅ Passed
Notification settings	✅ Passed
Run Tests
python -m unittest discover -s tests -v
📸 Screenshots

Application screenshots are available in:

screenshots/

Recommended screenshots include:

01. Login
screenshots/01-login.png
02. Chat Dashboard
screenshots/02-chat-dashboard.png
03. Real-Time Conversation
screenshots/03-chat-conversation.png
04. Chat Rooms
screenshots/04-chat-rooms.png
05. Typing Indicator
screenshots/05-typing-indicator.png
06. Notifications
screenshots/06-notification.png
07. Dark Theme
screenshots/07-dark-theme.png

Rename the screenshot filenames above if your actual screenshots folder uses different names.

▶️ How to Run
Start the Server

From the project directory:

python -m server.server

The default server address is:

127.0.0.1:5050

You should see:

VANTA CHAT server listening on 127.0.0.1:5050
Start the Client

Open another terminal in the project directory:

python -m client.gui

The VANTA CHAT desktop application will open.

⚙️ Installation

Clone the OIBSIP repository:

git clone https://github.com/shailajakunchala09/OIBSIP.git

Move into the Task 5 project:

cd OIBSIP/Python-Task5-ChatApplication

Check Python:

python --version

VANTA CHAT requires:

Python 3.10+

No third-party packages are required.

Run the server:

python -m server.server

Open another terminal and run the client:

python -m client.gui
🪟 Windows Launchers

Windows users can also use the included batch files.

Server
run_server.bat
Client
run_client.bat
🕹 Usage
1. Start the Server

Start the server before launching the client.

2. Open the Client

Launch the Tkinter application.

3. Create or Sign In to an Account

Use the authentication interface to access the application.

4. Select a Room

Choose an existing room or create a new one.

5. Send Messages

Type a message and send it to the current room.

6. Chat in Real Time

Other connected users in the same room receive messages immediately.

7. Search

Use room or message search when needed.

8. Customize Settings

Change:

Theme
Desktop notifications
Notification sound
9. Logout

Use the application's logout functionality to close the session gracefully.

⌨️ Keyboard Shortcuts
Shortcut	Action
Ctrl + K	Search chat rooms
Ctrl + F	Search messages

Additional application shortcuts are available through the application's shortcut/settings interface.

🧪 Manual Testing Scenario

A basic two-user test can be performed using two client windows.

Client 1
User: shailaja_16
Client 2
User: shailaja_17

Both users can:

Connect to the same server.
Join the same room.
Send messages.
Receive messages in real time.
Leave the room.
Rejoin the room.
Verify that previous messages remain available.

This verifies the main client-server messaging workflow.

🔒 Security & Privacy Considerations

VANTA CHAT includes several security-oriented design choices:

Passwords are protected using salted PBKDF2 hashing.
Generated authentication data is not stored as plain-text passwords.
Server-side validation is performed on client requests.
Message rate limiting helps control excessive requests.
Connection timeouts help manage inactive clients.
The application does not claim to provide production-grade encrypted messaging.
Important Limitation

The current educational implementation uses:

TCP

without TLS encryption.

Therefore, it should be used on:

localhost
A trusted private network
Educational/testing environments

It should not be presented as a secure production messaging platform without additional encryption and deployment hardening.

🚀 Future Enhancements

Possible future improvements include:

🔐 TLS-encrypted communication
📎 File and image sharing
🖼️ Image messages
👥 Private one-to-one conversations
🔔 More advanced notification controls
🟢 Richer presence states
🛡️ Additional server-side security controls
🌐 Web-based client
📱 Mobile client
☁️ Secure cloud deployment
🔑 Password reset functionality
👤 User profile customization
🎓 Learning Outcomes

Building VANTA CHAT reinforced practical Python development skills including:

TCP socket programming
Client-server architecture
Python threading
Tkinter GUI development
SQLite database management
JSON communication
Authentication workflows
Password hashing
Real-time event handling
Queue-based GUI updates
Connection management
Error handling
Application testing
Software architecture and separation of concerns

The project also provided practical experience in designing a complete Python application rather than only implementing an isolated programming exercise.

📌 OASIS INFOBYTE Internship

Program: Python Programming Internship
Organization: OASIS INFOBYTE
Task: Task 5 – Chat Application

VANTA CHAT was developed as part of the OASIS INFOBYTE Python Programming Internship.

👩‍💻 Developer

Kunchala Shailaja

Python Programming Internship — OASIS INFOBYTE

GitHub: shailajakunchala09

Repository: OIBSIP

📌 Project Status

✅ Complete

VANTA CHAT Task 5 has been implemented and manually verified for its core client-server functionality, including:

User accounts
Chat rooms
Real-time messaging
Message history
Room creation
Typing indicators
Unread badges
Desktop notifications
Search
Dark/light themes
Settings
Connection handling

The project is available in the public OIBSIP GitHub repository under:

Python-Task5-ChatApplication/
<p align="center"> <b>🔐 VANTA CHAT</b><br/> Private conversations. Simple connection. </p>
