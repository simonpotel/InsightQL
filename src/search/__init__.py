"""document indexing and search engine using sqlite"""

from .engine import SearchEngine
from .loader import load_documents

__all__ = ['SearchEngine', 'load_documents'] 