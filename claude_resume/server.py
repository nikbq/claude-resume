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
import socket
from .utils import clean_message_content, should_show_chat, filter_messages, extract_summary

# Configuration
CLAUDE_PROJECTS_DIR = Path.home() / '.claude' / 'projects'

def find_free_port(start_port=8888, max_tries=100):
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + max_tries):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"Could not find a free port in range {start_port}-{start_port + max_tries}")

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
        
        mark { background-color: yellow; padding: 0 2px; border-radius: 2px; }
        mark.current { background-color: #ff9800; color: white; }
        .search-snippet { background: #fffde7; padding: 8px; border-radius: 4px; margin-top: 8px; border-left: 3px solid #ffc107; }
        
        .chat-header { display: flex; align-items: start; margin-bottom: 10px; }
        .chat-id { font-family: monospace; color: #666; font-size: 12px; }
        .chat-heading { color: #333; font-weight: 500; margin-bottom: 5px; font-size: 15px; }
        .no-summary { color: #999; font-style: italic; font-weight: 400; font-size: 13px; }
        .chat-preview { color: #666; line-height: 1.4; font-size: 13px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
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
        
        .modal-search-bar { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
        .modal-search-input { flex: 1; padding: 8px; border: 2px solid #ddd; border-radius: 4px; font-size: 14px; }
        .modal-search-input:focus { outline: none; border-color: #4CAF50; }
        .search-nav-btn { padding: 6px 10px; background: #f0f0f0; border: 1px solid #ddd; border-radius: 4px; cursor: pointer; transition: all 0.2s; }
        .search-nav-btn:hover:not(:disabled) { background: #e0e0e0; }
        .search-nav-btn:disabled { opacity: 0.5; cursor: not-allowed; }
        .match-counter { font-size: 13px; color: #666; min-width: 80px; text-align: center; }
        
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
        let currentSearchTerm = '';
        let modalSearchMatches = [];
        let currentMatchIndex = -1;
        
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
        
        // Utility function to extract context around search term
        function extractSearchContext(text, searchTerm, maxWords = 50) {
            if (!text || !searchTerm) return '';
            
            const lowerText = text.toLowerCase();
            const index = lowerText.indexOf(searchTerm.toLowerCase());
            
            if (index === -1) return '';
            
            // If the message is short enough, return the whole thing
            const words = text.split(/\\s+/);
            if (words.length <= maxWords) {
                return text;
            }
            
            // Find word boundaries around the match
            const before = text.substring(0, index).split(/\\s+/);
            const after = text.substring(index + searchTerm.length).split(/\\s+/);
            
            const wordsBeforeCount = Math.floor(maxWords / 2);
            const wordsAfterCount = Math.floor(maxWords / 2);
            
            const startWords = before.slice(-wordsBeforeCount);
            const endWords = after.slice(0, wordsAfterCount);
            
            let result = '';
            if (before.length > wordsBeforeCount) result = '...';
            result += startWords.join(' ') + ' ' + text.substring(index, index + searchTerm.length) + ' ' + endWords.join(' ');
            if (after.length > wordsAfterCount) result += '...';
            
            return result.trim();
        }
        
        // Utility function to highlight search terms
        function highlightText(text, searchTerm, isCurrent = false) {
            if (!text || !searchTerm) return escapeHtml(text);
            
            const escaped = escapeHtml(text);
            const regex = new RegExp('(' + escapeRegex(searchTerm) + ')', 'gi');
            return escaped.replace(regex, isCurrent ? '<mark class="current">$1</mark>' : '<mark>$1</mark>');
        }
        
        function escapeRegex(str) {
            return str.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&');
        }
        
        function filterChats() {
            const searchTerm = document.getElementById('search').value.toLowerCase();
            currentSearchTerm = searchTerm;
            
            filteredChats = allChats.filter(chat => {
                const projectMatch = activeProject === 'all' || chat.project === activeProject;
                
                // First check basic fields for quick matches
                let searchMatch = !searchTerm || 
                    chat.id.toLowerCase().includes(searchTerm) ||
                    chat.project.toLowerCase().includes(searchTerm) ||
                    chat.firstMessage.toLowerCase().includes(searchTerm) ||
                    (chat.summary && chat.summary.toLowerCase().includes(searchTerm)) ||
                    chat.cwd.toLowerCase().includes(searchTerm);
                
                // If not found in basic fields and we have a search term, search through all messages
                if (!searchMatch && searchTerm && chat.messages) {
                    for (let i = 0; i < chat.messages.length; i++) {
                        const msg = chat.messages[i];
                        if (msg.message && msg.message.content) {
                            let content = '';
                            
                            // Handle different content formats
                            if (typeof msg.message.content === 'string') {
                                content = msg.message.content;
                            } else if (Array.isArray(msg.message.content)) {
                                content = msg.message.content
                                    .map(c => c.text || '')
                                    .join(' ');
                            }
                            
                            if (content.toLowerCase().includes(searchTerm)) {
                                // Store the matched content and index for preview
                                chat.searchMatch = {
                                    content: content,
                                    messageIndex: i,
                                    snippet: extractSearchContext(content, searchTerm)
                                };
                                searchMatch = true;
                                break;
                            }
                        }
                    }
                }
                
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
            
            listDiv.innerHTML = filteredChats.map(chat => {
                let previewContent = '';
                
                // If there's a search match in messages, show that snippet
                if (currentSearchTerm && chat.searchMatch && chat.searchMatch.snippet) {
                    previewContent = `<div class="search-snippet">${highlightText(chat.searchMatch.snippet, currentSearchTerm)}</div>`;
                } else {
                    // Otherwise show the regular first message
                    previewContent = `<div class="chat-preview">${escapeHtml(chat.firstMessage)}</div>`;
                }
                
                return `
                    <div class="chat-item" onclick="showChatDetails('${chat.id}')">
                        <div class="chat-header">
                            <div style="width: 100%;">
                                <div class="chat-heading">${chat.summary ? escapeHtml(chat.summary) : '<span class="no-summary">No summary available</span>'}</div>
                                <div class="chat-id">
                                    ID: ${chat.id}
                                    <button class="copy-icon" onclick="event.stopPropagation(); copyResumeCommand('${chat.id}', '${escapeHtml(chat.cwd).replace(/'/g, "\\'")}', this)" title="Copy resume command">📋</button>
                                </div>
                            </div>
                        </div>
                        ${previewContent}
                        <div class="chat-stats">
                            ${chat.messageCount} messages • ${formatRelativeTime(chat.endTime)} • ${escapeHtml(chat.project)}
                        </div>
                    </div>
                `;
            }).join('');
        }
        
        function showChatDetails(chatId) {
            const chat = allChats.find(c => c.id === chatId);
            if (!chat) return;
            
            document.getElementById('modal-title').textContent = chat.project;
            document.getElementById('modal-chat-id').innerHTML = `
                <div>
                    <div>Session: ${chat.id} 
                        <button class="copy-icon" onclick="event.stopPropagation(); copyResumeCommand('${chat.id}', '${escapeHtml(chat.cwd).replace(/'/g, "\\'")}', this)" title="Copy resume command">📋</button>
                    </div>
                    <div class="modal-search-bar">
                        <input type="text" class="modal-search-input" id="modal-search" placeholder="Search in this chat..." value="${escapeHtml(currentSearchTerm)}">
                        <button class="search-nav-btn" onclick="navigateMatch('prev')" title="Previous match (Shift+Enter)">↑</button>
                        <button class="search-nav-btn" onclick="navigateMatch('next')" title="Next match (Enter)">↓</button>
                        <span class="match-counter" id="match-counter"></span>
                    </div>
                </div>
            `;
            
            const modalBody = document.getElementById('modal-body');
            modalBody.innerHTML = `
                <div style="margin-bottom: 20px; padding: 15px; background: #f5f5f5; border-radius: 6px;">
                    <strong>Working Directory:</strong> ${escapeHtml(chat.cwd)}<br>
                    <strong>Duration:</strong> ${formatDuration(chat.startTime, chat.endTime)}<br>
                    <strong>Total Messages:</strong> ${chat.messageCount}<br>
                    <strong>Last Active:</strong> ${formatRelativeTime(chat.endTime)}
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
                                <div class="message-time">${formatRelativeTime(msg.timestamp)}</div>
                            </div>
                        `;
                    }
                    return '';
                }).join('')}
            `;
            
            document.getElementById('chat-modal').classList.add('active');
            
            // Set up modal search
            const modalSearchInput = document.getElementById('modal-search');
            modalSearchInput.addEventListener('input', () => searchInModal(chat));
            modalSearchInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    if (e.shiftKey) {
                        navigateMatch('prev');
                    } else {
                        navigateMatch('next');
                    }
                }
            });
            
            // Auto-search if there's a current search term
            if (currentSearchTerm) {
                searchInModal(chat);
                // Auto-scroll to first match after DOM updates
                if (modalSearchMatches.length > 0) {
                    // Use requestAnimationFrame to ensure DOM is ready
                    requestAnimationFrame(() => {
                        navigateMatch('next');
                    });
                }
            }
        }
        
        function closeModal() {
            document.getElementById('chat-modal').classList.remove('active');
        }
        
        function formatDate(dateStr) {
            if (!dateStr || dateStr === 'Unknown') return 'Unknown';
            const date = new Date(dateStr);
            return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
        }
        
        function formatRelativeTime(dateStr) {
            if (!dateStr || dateStr === 'Unknown') return 'Unknown';
            
            const date = new Date(dateStr);
            const now = new Date();
            const diffMs = now - date;
            const diffSecs = Math.floor(diffMs / 1000);
            const diffMins = Math.floor(diffSecs / 60);
            const diffHours = Math.floor(diffMins / 60);
            const diffDays = Math.floor(diffHours / 24);
            const diffWeeks = Math.floor(diffDays / 7);
            const diffMonths = Math.floor(diffDays / 30);
            const diffYears = Math.floor(diffDays / 365);
            
            if (diffSecs < 60) return 'just now';
            if (diffMins === 1) return '1 minute ago';
            if (diffMins < 60) return diffMins + ' minutes ago';
            if (diffHours === 1) return '1 hour ago';
            if (diffHours < 24) return diffHours + ' hours ago';
            if (diffDays === 1) return 'yesterday';
            if (diffDays < 7) return diffDays + ' days ago';
            if (diffWeeks === 1) return '1 week ago';
            if (diffWeeks < 4) return diffWeeks + ' weeks ago';
            if (diffMonths === 1) return '1 month ago';
            if (diffMonths < 12) return diffMonths + ' months ago';
            if (diffYears === 1) return '1 year ago';
            return diffYears + ' years ago';
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
        
        // Function to search within the modal
        function searchInModal(chat) {
            const searchTerm = document.getElementById('modal-search').value.toLowerCase();
            modalSearchMatches = [];
            currentMatchIndex = -1;
            
            if (!searchTerm) {
                // Clear highlights
                updateModalContent(chat, '');
                document.getElementById('match-counter').textContent = '';
                return;
            }
            
            // Update content with highlights FIRST
            updateModalContent(chat, searchTerm);
            
            // THEN find all matches in the newly created DOM
            const messages = document.querySelectorAll('.message');
            messages.forEach((msgElement, index) => {
                const marks = msgElement.querySelectorAll('mark');
                if (marks.length > 0) {
                    modalSearchMatches.push({
                        element: msgElement,
                        marks: marks,
                        index: index
                    });
                }
            });
            
            updateMatchCounter();
        }
        
        // Function to update modal content with highlights
        function updateModalContent(chat, searchTerm) {
            const modalBody = document.getElementById('modal-body');
            modalBody.innerHTML = `
                <div style="margin-bottom: 20px; padding: 15px; background: #f5f5f5; border-radius: 6px;">
                    <strong>Working Directory:</strong> ${escapeHtml(chat.cwd)}<br>
                    <strong>Duration:</strong> ${formatDuration(chat.startTime, chat.endTime)}<br>
                    <strong>Total Messages:</strong> ${chat.messageCount}<br>
                    <strong>Last Active:</strong> ${formatRelativeTime(chat.endTime)}
                </div>
                ${chat.messages.map((msg, idx) => {
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
                        
                        // Highlight search term if present
                        const highlightedContent = searchTerm ? 
                            highlightText(content, searchTerm) : 
                            escapeHtml(content);
                        
                        return `
                            <div class="message ${role}" data-message-index="${idx}">
                                <div class="message-role">${role.toUpperCase()}</div>
                                <div class="message-content">${highlightedContent}</div>
                                <div class="message-time">${formatRelativeTime(msg.timestamp)}</div>
                            </div>
                        `;
                    }
                    return '';
                }).join('')}
            `;
        }
        
        // Function to navigate between matches
        function navigateMatch(direction) {
            if (modalSearchMatches.length === 0) return;
            
            // Remove current highlight
            const currentMarks = document.querySelectorAll('mark.current');
            currentMarks.forEach(mark => mark.classList.remove('current'));
            
            if (direction === 'next') {
                currentMatchIndex = (currentMatchIndex + 1) % modalSearchMatches.length;
            } else {
                currentMatchIndex = currentMatchIndex - 1;
                if (currentMatchIndex < 0) currentMatchIndex = modalSearchMatches.length - 1;
            }
            
            // Scroll to and highlight current match
            const match = modalSearchMatches[currentMatchIndex];
            if (match.marks && match.marks.length > 0) {
                match.marks[0].classList.add('current');
                match.marks[0].scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
            
            updateMatchCounter();
        }
        
        // Function to update match counter
        function updateMatchCounter() {
            const counter = document.getElementById('match-counter');
            if (modalSearchMatches.length > 0) {
                counter.textContent = `${currentMatchIndex + 1} of ${modalSearchMatches.length}`;
            } else if (document.getElementById('modal-search').value) {
                counter.textContent = 'No matches';
            } else {
                counter.textContent = '';
            }
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
                    # Extract project name from directory name
                    # Directory format: -Users-username-Projects-project-name
                    dir_name = project_dir.name
                    
                    # Remove leading dash if present
                    if dir_name.startswith('-'):
                        dir_name = dir_name[1:]
                    
                    # Split by -Projects- to get the project part
                    if 'Projects-' in dir_name:
                        # Everything after 'Projects-' is the project name
                        project_name = dir_name.split('Projects-', 1)[-1]
                    else:
                        # Fallback: take everything after the username
                        parts = dir_name.split('-')
                        if len(parts) > 2 and parts[0] == 'Users':
                            project_name = '-'.join(parts[2:])
                        else:
                            project_name = dir_name
                    
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
                                    # Try to extract summary BEFORE filtering
                                    summary = extract_summary(messages)
                                    
                                    # Filter out empty messages
                                    messages = filter_messages(messages)
                                    if not messages:
                                        continue
                                    
                                    first_msg = messages[0]
                                    last_msg = messages[-1]
                                    
                                    # Try to find first sensible message (user or assistant)
                                    first_user_msg = ''
                                    for msg in messages[:20]:  # Look at first 20 messages
                                        if msg.get('message'):
                                            role = msg['message'].get('role', '')
                                            content = msg['message'].get('content', '')
                                            if role in ['user', 'assistant'] and content:
                                                cleaned_content = clean_message_content(content)
                                                if cleaned_content and len(cleaned_content) > 5:  # Lower threshold for technical messages
                                                    first_user_msg = cleaned_content
                                                    break
                                    
                                    # If still no sensible message found, default to empty
                                    if not first_user_msg:
                                        first_user_msg = 'No message content'
                                    
                                    cwd = first_msg.get('cwd', 'Unknown')
                                    
                                    chat_data = {
                                        'id': first_msg.get('sessionId', jsonl_file.stem),
                                        'fileName': jsonl_file.name,
                                        'project': project_name,
                                        'startTime': first_msg.get('timestamp', 'Unknown'),
                                        'endTime': last_msg.get('timestamp', 'Unknown'),
                                        'messageCount': len(messages),
                                        'firstMessage': first_user_msg or 'No user message',
                                        'summary': summary,
                                        'messages': messages,
                                        'cwd': cwd
                                    }
                                    
                                    # Get current directory context
                                    current_dir = os.getcwd()
                                    
                                    # Only add chat if it matches current directory context
                                    if should_show_chat(chat_data, current_dir):
                                        projects.add(project_name)
                                        chats.append(chat_data)
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

def open_browser(host, port):
    """Open the browser after a short delay"""
    time.sleep(1)
    webbrowser.open(f'http://{host}:{port}')

def main():
    if not CLAUDE_PROJECTS_DIR.exists():
        print(f"Error: Claude projects directory not found at {CLAUDE_PROJECTS_DIR}")
        print("Please ensure Claude Code is installed and has been used to create projects.")
        return
    
    # Get configuration from environment or defaults
    HOST = os.environ.get('CLAUDE_RESUME_HOST', 'localhost')
    NO_BROWSER = os.environ.get('CLAUDE_RESUME_NO_BROWSER', '0') == '1'
    
    # Try to use specified port or find an available one
    requested_port = int(os.environ.get('CLAUDE_RESUME_PORT', 8888))
    try:
        PORT = find_free_port(requested_port, 1)  # Try exact port first
    except RuntimeError:
        # If requested port is busy, find another
        PORT = find_free_port(requested_port + 1)
        print(f"Port {requested_port} is busy, using port {PORT} instead")
    
    # Count available chats
    jsonl_files = list(CLAUDE_PROJECTS_DIR.glob('*/*.jsonl'))
    print(f"Found {len(jsonl_files)} chat files in {CLAUDE_PROJECTS_DIR}")
    
    # Start the server
    server = HTTPServer((HOST, PORT), ChatHistoryHandler)
    print(f"\nStarting Claude Chat History Viewer...")
    print(f"Server running at http://{HOST}:{PORT}")
    print("Press Ctrl+C to stop the server\n")
    
    # Open browser in a separate thread if not disabled
    if not NO_BROWSER:
        browser_thread = threading.Thread(target=open_browser, args=(HOST, PORT))
        browser_thread.daemon = True
        browser_thread.start()
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")
        server.server_close()

if __name__ == '__main__':
    main()