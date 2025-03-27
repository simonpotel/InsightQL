# Database Structure

This document explains the internal database structure of InsightQL.

## Database Tables

InsightQL uses three main tables to store and index documents:

### Documents Table

```sql
CREATE TABLE documents (
    id TEXT PRIMARY KEY,
    content TEXT,
    metadata TEXT
)
```

Each row represents either a complete document or a chunk of a larger document. The content field contains the actual text, while metadata (stored as JSON) holds information about the source file.

### Terms Table

```sql
CREATE TABLE terms (
    term TEXT,
    doc_id TEXT,
    frequency INTEGER,
    positions TEXT,
    UNIQUE(term, doc_id)
)
```

This table enables searching by recording which terms appear in which documents, tracking frequency, storing positions within documents, and supporting partial and fuzzy matching.

### FTS Documents Table

When available, InsightQL creates a virtual table using SQLite's FTS5 (Full-Text Search) extension:

```sql
CREATE VIRTUAL TABLE fts_documents USING fts5(
    content,
    doc_id UNINDEXED
)
```

This table dramatically speeds up text searches using specialized indexing techniques.

## Data Examples

### Document Record Example

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "content": "This is the text content of the document...",
  "metadata": {
    "source": "/path/to/original/file.llm",
    "filename": "file.llm",
    "extension": ".llm",
    "directory": "/path/to/original",
    "chunk": 0,
    "total_chunks": 3
  }
}
```

### Term Index Record Example

```json
{
  "term": "database",
  "doc_id": "550e8400-e29b-41d4-a716-446655440000",
  "frequency": 5,
  "positions": [3, 17, 42, 56, 72]
}
```

This record shows that the term "database" appears 5 times in the document at the specified word positions.
