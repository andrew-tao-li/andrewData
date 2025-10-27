"""Data storage modules"""

from .sqlite_storage import HealthDatabase

try:
    from .google_sheets_storage import GoogleSheetsStorage
    GOOGLE_SHEETS_AVAILABLE = True
except ImportError:
    GoogleSheetsStorage = None
    GOOGLE_SHEETS_AVAILABLE = False

__all__ = ['HealthDatabase', 'GoogleSheetsStorage', 'GOOGLE_SHEETS_AVAILABLE']
