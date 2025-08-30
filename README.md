# Claude Resume: Claude Code Chat History Viewer

A powerful Claude Code chat history viewer that allows you to search through your chat history and resume any conversation directly from your terminal.

## Features

- 🔍 **Search Through Chat History**: Search across all your Claude Code conversations
- 📁 **Multi-Project View**: Load and view chats from multiple projects at once - run from home directory to see all projects in one place
- 🎯 **Resume Any Chat**: Get the exact command to resume any conversation - just copy and paste into your terminal
- ⚡ **Smart Filtering**: Filter by project, search by content, or find specific sessions
- 🌐 **Web Interface**: Clean, responsive web UI accessible from any browser

## Quick Start

### Installation

#### Method 1: Using uvx (Recommended)
```bash
uvx --from git+https://github.com/nikbq/claude-resume.git claude-resume
```

#### Method 2: One-liner with curl
```bash
curl -s https://raw.githubusercontent.com/nikbq/claude-resume/main/run.py | python3
```

#### Method 3: Using pip
```bash
pip install git+https://github.com/nikbq/claude-resume.git
```

## Usage

Simply run:
```bash
claude-resume
```

This will:
1. Start the web server
2. Open your browser automatically
3. Display all Claude chat history from `~/.claude/projects/`

### Tips
- Run from your home directory to view all projects at once
- Use the search bar to find specific conversations
- Click on any chat to view full conversation and get the resume command

## Command Line Options

```bash
claude-resume [options]

Options:
  -p, --port PORT       Port to run server on (default: auto-finds available)
  --no-browser         Don't automatically open browser
  -h, --help           Show help message
```

## Resume Functionality

Each chat displays a copy button that generates the exact command to resume that conversation:
```bash
cd "/path/to/project" && claude --resume session-id
```

## Requirements

- Python 3.8+
- Claude Code installed with existing chat history

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

For issues or questions, please open an issue on [GitHub](https://github.com/nikbq/claude-resume/issues).