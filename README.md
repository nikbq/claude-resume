# Claude Resume 🚀

A powerful web-based viewer for Claude chat history with the ability to resume conversations directly from your terminal.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey.svg)

## ✨ Features

- 📖 **Browse Chat History**: View all your Claude conversations in one place
- 🔍 **Smart Search**: Search through chats by content, project name, or session ID
- 🏷️ **Project Filtering**: Filter chats by project for better organization
- 📊 **Statistics Dashboard**: See total chats, projects, and message counts
- 📋 **Resume Commands**: Copy resume commands with one click to continue any conversation
- 🎯 **Real-time Updates**: Automatically detects new chat sessions
- 🌐 **Web Interface**: Clean, responsive web UI accessible from any browser
- ⚡ **Fast & Lightweight**: Built with Python's standard library - no heavy dependencies

## 📸 Screenshots

### Main Dashboard
View all your Claude chats with search and filtering capabilities:
- Search by content, ID, or project name
- Filter by specific projects
- View chat statistics
- See message previews

### Chat Details
Click on any chat to view:
- Complete conversation history
- Message timestamps
- Working directory information
- One-click resume command copying

## 🚀 Quick Start

### Instant Run (No Installation Required!)

#### Method 1: One-liner with curl
```bash
curl -s https://raw.githubusercontent.com/nikbq/claude-resume/main/run.py | python3
```

#### Method 2: Using uvx (if you have uv installed)
```bash
uvx --from git+https://github.com/nikbq/claude-resume.git claude-resume
```

### Installation (Optional)

If you want to install permanently:

#### Using pip
```bash
pip install git+https://github.com/nikbq/claude-resume.git
```

#### Using uv (recommended)
```bash
uv pip install git+https://github.com/nikbq/claude-resume.git
```

#### Using pipx (for isolated installation)
```bash
pipx install git+https://github.com/nikbq/claude-resume.git
```

### Usage

Simply run:
```bash
claude-resume
```

This will:
1. Start the web server on port 8888
2. Automatically open your browser
3. Display all your Claude chat history from `~/.claude/projects/`

## 🎮 Command Line Options

```bash
claude-resume [options]

Options:
  -p, --port PORT       Port to run the server on (default: 8888)
  --host HOST          Host to bind the server to (default: localhost)
  --no-browser         Don't automatically open the browser
  -v, --version        Show version information
  -h, --help           Show help message

Examples:
  claude-resume                    # Start on default port with auto-browser
  claude-resume --port 9000        # Use custom port
  claude-resume --no-browser       # Don't open browser automatically
  claude-resume --host 0.0.0.0     # Allow external connections
```

## 🔧 Development Setup

### Clone the repository
```bash
git clone https://github.com/nikbq/claude-resume.git
cd claude-resume
```

### Install in development mode
```bash
pip install -e .
```

### Run tests (if available)
```bash
python -m pytest tests/
```

## 📦 Project Structure

```
claude-resume/
├── claude_resume/
│   ├── __init__.py       # Package initialization
│   ├── cli.py            # Command-line interface
│   └── server.py         # HTTP server and web interface
├── pyproject.toml        # Package configuration
├── README.md            # This file
├── LICENSE              # MIT License
└── .gitignore          # Git ignore rules
```

## 🌟 Features in Detail

### Smart Search
- Search across all chat content
- Filter by project name
- Find chats by session ID
- Search in working directories

### Resume Functionality
Each chat displays a copy button that generates the exact command needed to resume that conversation:
```bash
cd "/path/to/project" && claude --resume session-id
```

### Project Organization
- Automatically groups chats by project
- Shows project statistics
- Quick project filtering

### Message Viewer
- Color-coded messages (User/Assistant)
- Timestamp for each message
- Full conversation context
- Syntax highlighting for code blocks

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 🐛 Known Issues

- The viewer requires Claude Code to be installed and have existing chat history
- Chat history location is hardcoded to `~/.claude/projects/`
- Some older chat formats might not be fully compatible

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built for the Claude Code community
- Inspired by the need for better chat history management
- Thanks to all contributors and users

## 📮 Support

If you encounter any issues or have questions:
- Open an issue on [GitHub](https://github.com/nikbq/claude-resume/issues)
- Check existing issues for solutions
- Provide detailed information about your environment and the issue

## 🔮 Future Plans

- [ ] Export chats to markdown/PDF
- [ ] Advanced search with regex support
- [ ] Chat analytics and insights
- [ ] Backup and restore functionality
- [ ] Integration with Claude API for direct resuming
- [ ] Dark mode theme
- [ ] Keyboard shortcuts
- [ ] Multi-language support

---

Made with ❤️ for the Claude community