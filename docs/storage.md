# Document Storage in InsightQL

This document explains how InsightQL stores and manages files.

## The Storage Process

When adding documents to InsightQL, the system:

1. Reads files from your specified resources directory
2. Processes each file and potentially breaks it into smaller chunks
3. Stores documents and metadata in a SQLite database
4. Indexes terms for searching

By default, InsightQL looks for files with the `.llm` extension, but this is customizable.

## File Loading

InsightQL's file loading system:

- Recursively scans directories to find documents
- Uses pattern matching to identify relevant files
- Supports customizable file types through glob patterns
- Tracks the source of each document

To load only text files, specify the pattern `**/*.txt` when initializing the system.

## Chunking

Large documents are broken down into smaller chunks, providing:

- More precise search results targeting specific sections
- Better context for question answering
- Improved performance with large documents

The default chunk size is 2000 characters and is adjustable.

## The Database

InsightQL uses SQLite for:

- Fast document retrieval
- Minimal setup and configuration
- Portable database files that can be easily backed up
- Support for full-text search

The database file is created in the `data` directory by default.

## Tracking Document Origins

For each document chunk, InsightQL stores metadata including:

- Original file path
- Filename
- File extension
- Parent directory
- Chunk number and total chunks

This enables tracing any search result back to its source document. 