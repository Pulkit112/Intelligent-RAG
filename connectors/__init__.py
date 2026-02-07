"""Pluggable connectors: file, web, API, DB, chat. No parsing logic."""

from connectors.base import BaseConnector
from connectors.file_connector import FileConnector

__all__ = ["BaseConnector", "FileConnector"]
