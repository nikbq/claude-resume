# Claude Resume: Claude Code Chat History Viewer

A powerful Claude Code chat history viewer that allows you to search through your chat history and resume any conversation directly from your terminal.

## Features

- 🔍 **Search Through Chat History**: Search across all your Claude Code conversations
- 📁 **Multi-Project View**: Load and view chats from multiple projects at once - run from home directory to see all projects in one place
- 🎯 **Resume Any Chat**: Get the exact command to resume any conversation - just copy and paste into your terminal
- 🌐 **Web Interface**: Clean, responsive web UI accessible from any browser

## Quick Start - No Installation Required

These methods run directly without installation. The server starts immediately and opens your browser.

### Method 1: Using uvx (Recommended if you have uv)
```bash
uvx --from git+https://github.com/nikbq/claude-resume.git claude-resume
```

### Method 2: One-liner with curl
```bash
curl -s https://raw.githubusercontent.com/nikbq/claude-resume/main/run.py | python3
```

That's it! The browser will open automatically with your chat history.

## Installation Method

If you want to install Claude Resume permanently for repeated use, follow these steps:

### Install Options

#### Using pip
```bash
pip install git+https://github.com/nikbq/claude-resume.git
```

#### Using uv
```bash
uv pip install git+https://github.com/nikbq/claude-resume.git
```

#### Using pipx (for isolated installation)
```bash
pipx install git+https://github.com/nikbq/claude-resume.git
```

### Usage After Installation

Once installed, you can run:
```bash
claude-resume
```

This will:
1. Start the web server
2. Open your browser automatically
3. Display all Claude chat history from `~/.claude/projects/`

### Command Line Options (for installed version only)

```bash
claude-resume [options]

Options:
  -p, --port PORT       Port to run server on (default: auto-finds available)
  --no-browser         Don't automatically open browser
  -h, --help           Show help message
```

## Tips for Both Methods
- Run from your home directory to view all projects at once
- Use the search bar to find specific conversations
- Click on any chat to view full conversation and get the resume command

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