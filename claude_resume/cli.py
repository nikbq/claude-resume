#!/usr/bin/env python3
"""
Claude Resume CLI - Command line interface for Claude chat history viewer
"""

import argparse
import sys
from pathlib import Path
from .server import main as server_main


def main():
    """Main entry point for the claude-resume command"""
    parser = argparse.ArgumentParser(
        description="Claude Resume - View and search your Claude chat history",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  claude-resume                    # Start the server on default port 8888
  claude-resume --port 9000        # Start on custom port
  claude-resume --no-browser       # Don't auto-open browser
  claude-resume --help             # Show this help message

The viewer will read chat history from ~/.claude/projects/
and provide a web interface to browse, search, and resume conversations.
        """
    )
    
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=8888,
        help='Port to run the server on (default: 8888)'
    )
    
    parser.add_argument(
        '--no-browser',
        action='store_true',
        help="Don't automatically open the browser"
    )
    
    parser.add_argument(
        '--host',
        default='localhost',
        help='Host to bind the server to (default: localhost)'
    )
    
    parser.add_argument(
        '--version', '-v',
        action='version',
        version='%(prog)s 1.0.0'
    )
    
    args = parser.parse_args()
    
    # Check if Claude projects directory exists
    claude_dir = Path.home() / '.claude' / 'projects'
    if not claude_dir.exists():
        print(f"Error: Claude projects directory not found at {claude_dir}")
        print("Please ensure Claude Code is installed and has been used to create projects.")
        sys.exit(1)
    
    # Run the server with options
    try:
        import os
        os.environ['CLAUDE_RESUME_PORT'] = str(args.port)
        os.environ['CLAUDE_RESUME_HOST'] = args.host
        os.environ['CLAUDE_RESUME_NO_BROWSER'] = '1' if args.no_browser else '0'
        
        server_main()
    except KeyboardInterrupt:
        print("\nServer stopped")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()