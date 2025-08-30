#!/usr/bin/env python3
"""
Claude Chat History Server
Serves Claude chat history from ~/.claude/projects/ with a web interface
"""

import json
import os
import glob
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse
import webbrowser
import threading
import time

# Configuration
CLAUDE_PROJECTS_DIR = Path.home() / '.claude' / 'projects'
PORT = 8888

class ChatHistoryHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        
        if parsed_path.path == '/':
            self.serve_html()
        elif parsed_path.path == '/api/chats':
            self.serve_chats()
        else:
            super().do_GET()
    
    def serve_html(self):
        """Serve the main HTML interface"""
        html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Claude Chat History Viewer</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        h1 { color: #333; margin-bottom: 20px; }
        
        .controls { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .search-box { width: 100%; padding: 12px; font-size: 16px; border: 2px solid #ddd; border-radius: 6px; margin-bottom: 15px; }
        .search-box:focus { outline: none; border-color: #4CAF50; }
        
        .stats { display: flex; gap: 20px; margin-bottom: 15px; }
        .stat-card { background: #f8f9fa; padding: 10px 15px; border-radius: 6px; }
        .stat-label { font-size: 12px; color: #666; }
        .stat-value { font-size: 24px; font-weight: bold; color: #333; }
        
        .filters { display: flex; gap: 10px; flex-wrap: wrap; }
        .filter-btn { padding: 8px 16px; background: #e0e0e0; border: none; border-radius: 4px; cursor: pointer; transition: all 0.3s; }
        .filter-btn:hover { background: #d0d0d0; }
        .filter-btn.active { background: #4CAF50; color: white; }
        
        .chat-list { background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .chat-item { border-bottom: 1px solid #eee; padding: 15px; cursor: pointer; transition: background 0.2s; position: relative; }
        .chat-item:hover { background: #f8f9fa; }
        .chat-item:last-child { border-bottom: none; }
        
        .chat-header { display: flex; justify-content: space-between; align-items: start; margin-bottom: 10px; }
        .chat-id { font-family: monospace; color: #666; font-size: 12px; }
        .chat-time { color: #999; font-size: 12px; }
        .chat-project { color: #4CAF50; font-weight: 500; margin-bottom: 5px; }
        .chat-preview { color: #333; line-height: 1.5; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
        .chat-stats { margin-top: 8px; font-size: 11px; color: #999; }
        
        .copy-icon { display: inline-block; margin-left: 8px; padding: 4px 6px; background: #e0e0e0; color: #666; border: none; border-radius: 3px; font-size: 14px; cursor: pointer; transition: all 0.2s; vertical-align: middle; }
        .copy-icon:hover { background: #4CAF50; color: white; transform: scale(1.1); }
        .copy-icon.copied { background: #2196F3; color: white; }
        
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1000; }
        .modal.active { display: flex; align-items: center; justify-content: center; }
        .modal-content { background: white; width: 90%; max-width: 900px; max-height: 80vh; border-radius: 12px; overflow: hidden; display: flex; flex-direction: column; }
        .modal-header { padding: 20px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; }
        .modal-body { padding: 20px; overflow-y: auto; flex: 1; }
        .modal-close { background: none; border: none; font-size: 24px; cursor: pointer; color: #999; }
        
        .message { margin-bottom: 20px; padding: 15px; border-radius: 8px; }
        .message.user { background: #e3f2fd; border-left: 4px solid #2196F3; }
        .message.assistant { background: #f3e5f5; border-left: 4px solid #9C27B0; }
        .message-role { font-weight: bold; margin-bottom: 8px; color: #666; }
        .message-content { white-space: pre-wrap; word-wrap: break-word; font-family: monospace; font-size: 13px; }
        .message-time { font-size: 11px; color: #999; margin-top: 8px; }
        
        .loading { text-align: center; padding: 40px; color: #666; }
        .error { background: #fee; color: #c00; padding: 15px; border-radius: 6px; margin: 20px 0; }
        
        .notification { position: fixed; bottom: 20px; right: 20px; background: #4CAF50; color: white; padding: 15px 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.2); z-index: 2000; animation: slideIn 0.3s ease-out; }
        @keyframes slideIn { from { transform: translateX(400px); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
        @keyframes slideOut { from { transform: translateX(0); opacity: 1; } to { transform: translateX(400px); opacity: 0; } }
        .notification.hiding { animation: slideOut 0.3s ease-out; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Claude Chat History Viewer</h1>
        
        <div class="controls">
            <input type="text" class="search-box" id="search" placeholder="Search chats by content, ID, or project name...">
            
            <div class="stats" id="stats">
                <div class="stat-card">
                    <div class="stat-label">Total Chats</div>
                    <div class="stat-value" id="total-chats">0</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Projects</div>
                    <div class="stat-value" id="total-projects">0</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Messages</div>
                    <div class="stat-value" id="total-messages">0</div>
                </div>
            </div>
            
            <div class="filters" id="project-filters">
                <button class="filter-btn active" data-project="all" onclick="setProjectFilter('all')">All Projects</button>
            </div>
        </div>
        
        <div class="chat-list" id="chat-list">
            <div class="loading">Loading chats...</div>
        </div>
    </div>
    
    <div class="modal" id="chat-modal">
        <div class="modal-content">
            <div class="modal-header">
                <div>
                    <h2 id="modal-title">Chat Details</h2>
                    <div class="chat-id" id="modal-chat-id"></div>
                </div>
                <button class="modal-close" onclick="closeModal()">×</button>
            </div>
            <div class="modal-body" id="modal-body"></div>
        </div>
    </div>
    
    <script>
        let allChats = [];
        let filteredChats = [];
        let activeProject = 'all';
        let projects = new Set();
        
        // Load chats on page load
        loadChats();
        
        document.getElementById('search').addEventListener('input', filterChats);
        
        async function loadChats() {
            try {
                const response = await fetch('/api/chats');
                const data = await response.json();
                
                allChats = data.chats;
                projects = new Set(data.projects);
                
                updateStats();
                updateProjectFilters();
                filterChats();
            } catch (error) {
                document.getElementById('chat-list').innerHTML = 
                    '<div class="error">Error loading chats: ' + error.message + '</div>';
            }
        }
        
        function updateStats() {
            document.getElementById('total-chats').textContent = allChats.length;
            document.getElementById('total-projects').textContent = projects.size;
            const totalMessages = allChats.reduce((sum, chat) => sum + chat.messageCount, 0);
            document.getElementById('total-messages').textContent = totalMessages.toLocaleString();
        }
        
        function updateProjectFilters() {
            const filtersDiv = document.getElementById('project-filters');
            filtersDiv.innerHTML = '';
            
            // Create All Projects button with onclick
            const allBtn = document.createElement('button');
            allBtn.className = 'filter-btn active';
            allBtn.dataset.project = 'all';
            allBtn.textContent = 'All Projects';
            allBtn.onclick = () => setProjectFilter('all');
            filtersDiv.appendChild(allBtn);
            
            Array.from(projects).sort().forEach(project => {
                const btn = document.createElement('button');
                btn.className = 'filter-btn';
                btn.dataset.project = project;
                btn.textContent = project;
                btn.onclick = () => setProjectFilter(project);
                filtersDiv.appendChild(btn);
            });
        }
        
        function setProjectFilter(project) {
            activeProject = project;
            document.querySelectorAll('.filter-btn').forEach(btn => {
                btn.classList.toggle('active', btn.dataset.project === project);
            });
            filterChats();
        }
        
        function filterChats() {
            const searchTerm = document.getElementById('search').value.toLowerCase();
            
            filteredChats = allChats.filter(chat => {
                const projectMatch = activeProject === 'all' || chat.project === activeProject;
                const searchMatch = !searchTerm || 
                    chat.id.toLowerCase().includes(searchTerm) ||
                    chat.project.toLowerCase().includes(searchTerm) ||
                    chat.firstMessage.toLowerCase().includes(searchTerm) ||
                    chat.cwd.toLowerCase().includes(searchTerm);
                
                return projectMatch && searchMatch;
            });
            
            filteredChats.sort((a, b) => new Date(b.startTime) - new Date(a.startTime));
            displayChats();
        }
        
        function displayChats() {
            const listDiv = document.getElementById('chat-list');
            
            if (filteredChats.length === 0) {
                listDiv.innerHTML = '<div class="loading">No chats found</div>';
                return;
            }
            
            listDiv.innerHTML = filteredChats.map(chat => `
                <div class="chat-item" onclick="showChatDetails('${chat.id}')">
                    <div class="chat-header">
                        <div>
                            <div class="chat-project">${escapeHtml(chat.project)}</div>
                            <div class="chat-id">
                                ID: ${chat.id}
                                <button class="copy-icon" onclick="event.stopPropagation(); copyResumeCommand('${chat.id}', '${escapeHtml(chat.cwd).replace(/'/g, "\\'")}', this)" title="Copy resume command">📋</button>
                            </div>
                        </div>
                        <div class="chat-time">${formatDate(chat.startTime)}</div>
                    </div>
                    <div class="chat-preview">${escapeHtml(chat.firstMessage)}</div>
                    <div class="chat-stats">
                        ${chat.messageCount} messages • ${formatDuration(chat.startTime, chat.endTime)}
                    </div>
                </div>
            `).join('');
        }
        
        function showChatDetails(chatId) {
            const chat = allChats.find(c => c.id === chatId);
            if (!chat) return;
            
            document.getElementById('modal-title').textContent = chat.project;
            document.getElementById('modal-chat-id').innerHTML = 'Session: ' + chat.id + 
                ` <button class="copy-icon" onclick="event.stopPropagation(); copyResumeCommand('${chat.id}', '${escapeHtml(chat.cwd).replace(/'/g, "\\'")}', this)" title="Copy resume command">📋</button>`;
            
            const modalBody = document.getElementById('modal-body');
            modalBody.innerHTML = `
                <div style="margin-bottom: 20px; padding: 15px; background: #f5f5f5; border-radius: 6px;">
                    <strong>Working Directory:</strong> ${escapeHtml(chat.cwd)}<br>
                    <strong>Start Time:</strong> ${formatDate(chat.startTime)}<br>
                    <strong>End Time:</strong> ${formatDate(chat.endTime)}<br>
                    <strong>Duration:</strong> ${formatDuration(chat.startTime, chat.endTime)}<br>
                    <strong>Total Messages:</strong> ${chat.messageCount}
                </div>
                ${chat.messages.map(msg => {
                    if (msg.message && msg.message.content) {
                        const role = msg.message.role;
                        let content = '';
                        
                        if (typeof msg.message.content === 'string') {
                            content = msg.message.content;
                        } else if (Array.isArray(msg.message.content)) {
                            content = msg.message.content
                                .map(c => c.text || '')
                                .join('');
                        }
                        
                        return `
                            <div class="message ${role}">
                                <div class="message-role">${role.toUpperCase()}</div>
                                <div class="message-content">${escapeHtml(content)}</div>
                                <div class="message-time">${formatDate(msg.timestamp)}</div>
                            </div>
                        `;
                    }
                    return '';
                }).join('')}
            `;
            
            document.getElementById('chat-modal').classList.add('active');
        }
        
        function closeModal() {
            document.getElementById('chat-modal').classList.remove('active');
        }
        
        function formatDate(dateStr) {
            if (!dateStr || dateStr === 'Unknown') return 'Unknown';
            const date = new Date(dateStr);
            return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
        }
        
        function formatDuration(start, end) {
            if (!start || !end || start === 'Unknown' || end === 'Unknown') return 'Unknown duration';
            const duration = new Date(end) - new Date(start);
            const hours = Math.floor(duration / 3600000);
            const minutes = Math.floor((duration % 3600000) / 60000);
            if (hours > 0) return hours + 'h ' + minutes + 'm';
            return minutes + 'm';
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text || '';
            return div.innerHTML;
        }
        
        function copyResumeCommand(sessionId, cwd, button) {
            const command = `cd "${cwd}" && claude --resume ${sessionId}`;
            
            const copySuccess = () => {
                button.classList.add('copied');
                button.innerHTML = '✓';
                
                // Show notification
                showNotification('✅ Command copied! Paste it in your terminal to continue this chat.');
                
                setTimeout(() => {
                    button.classList.remove('copied');
                    button.innerHTML = '📋';
                }, 2000);
            };
            
            navigator.clipboard.writeText(command).then(copySuccess).catch(err => {
                // Fallback for older browsers
                const textarea = document.createElement('textarea');
                textarea.value = command;
                textarea.style.position = 'fixed';
                textarea.style.opacity = '0';
                document.body.appendChild(textarea);
                textarea.select();
                document.execCommand('copy');
                document.body.removeChild(textarea);
                copySuccess();
            });
        }
        
        function showNotification(message) {
            // Remove any existing notification
            const existing = document.querySelector('.notification');
            if (existing) existing.remove();
            
            const notification = document.createElement('div');
            notification.className = 'notification';
            notification.textContent = message;
            document.body.appendChild(notification);
            
            setTimeout(() => {
                notification.classList.add('hiding');
                setTimeout(() => notification.remove(), 300);
            }, 3500);
        }
        
        // Allow closing modal with Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') closeModal();
        });
        
        // Click outside modal to close
        document.getElementById('chat-modal').addEventListener('click', (e) => {
            if (e.target.id === 'chat-modal') closeModal();
        });
    </script>
</body>
</html>'''
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html_content.encode())
    
    def serve_chats(self):
        """Serve chat data as JSON"""
        try:
            chats = []
            projects = set()
            
            # Find all JSONL files in projects directory
            for project_dir in CLAUDE_PROJECTS_DIR.iterdir():
                if project_dir.is_dir():
                    project_name = project_dir.name.replace('-Users-', '').replace('-', ' ')
                    project_name = ' '.join(project_name.split()[-2:]) if len(project_name.split()) > 2 else project_name
                    
                    for jsonl_file in project_dir.glob('*.jsonl'):
                        try:
                            with open(jsonl_file, 'r', encoding='utf-8') as f:
                                lines = f.readlines()
                                if not lines:
                                    continue
                                
                                messages = []
                                for line in lines:
                                    try:
                                        msg = json.loads(line.strip())
                                        messages.append(msg)
                                    except json.JSONDecodeError:
                                        continue
                                
                                if messages:
                                    first_msg = messages[0]
                                    last_msg = messages[-1]
                                    user_messages = [m for m in messages if m.get('message', {}).get('role') == 'user']
                                    first_user_msg = ''
                                    
                                    if user_messages:
                                        content = user_messages[0].get('message', {}).get('content', '')
                                        if isinstance(content, str):
                                            first_user_msg = content
                                        elif isinstance(content, list) and content:
                                            first_user_msg = content[0].get('text', '') if isinstance(content[0], dict) else str(content[0])
                                    
                                    projects.add(project_name)
                                    chats.append({
                                        'id': first_msg.get('sessionId', jsonl_file.stem),
                                        'fileName': jsonl_file.name,
                                        'project': project_name,
                                        'startTime': first_msg.get('timestamp', 'Unknown'),
                                        'endTime': last_msg.get('timestamp', 'Unknown'),
                                        'messageCount': len(messages),
                                        'firstMessage': first_user_msg or 'No user message',
                                        'messages': messages,
                                        'cwd': first_msg.get('cwd', 'Unknown')
                                    })
                        except Exception as e:
                            print(f"Error processing {jsonl_file}: {e}")
            
            response_data = {
                'chats': chats,
                'projects': list(projects)
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())

def open_browser():
    """Open the browser after a short delay"""
    time.sleep(1)
    webbrowser.open(f'http://localhost:{PORT}')

def main():
    if not CLAUDE_PROJECTS_DIR.exists():
        print(f"Error: Claude projects directory not found at {CLAUDE_PROJECTS_DIR}")
        print("Please ensure Claude Code is installed and has been used to create projects.")
        return
    
    # Count available chats
    jsonl_files = list(CLAUDE_PROJECTS_DIR.glob('*/*.jsonl'))
    print(f"Found {len(jsonl_files)} chat files in {CLAUDE_PROJECTS_DIR}")
    
    # Start the server
    server = HTTPServer(('localhost', PORT), ChatHistoryHandler)
    print(f"\nStarting Claude Chat History Viewer...")
    print(f"Server running at http://localhost:{PORT}")
    print("Press Ctrl+C to stop the server\n")
    
    # Open browser in a separate thread
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")
        server.server_close()

if __name__ == '__main__':
    main()