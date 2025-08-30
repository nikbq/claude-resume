"""
Claude Resume - A web-based viewer for Claude chat history
"""

__version__ = "1.0.0"
__author__ = "Nik"

from .server import ChatHistoryHandler, main

__all__ = ["ChatHistoryHandler", "main"]