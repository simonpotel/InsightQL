# Search Functionality

This document explains how InsightQL's search system works.

## Search Philosophy

InsightQL uses a multi-strategy approach to find information. The system automatically chooses the best strategy based on your query and available search capabilities.

## Search Strategies

InsightQL uses a three-tier approach:

### Full-Text Search

The primary search method uses SQLite's FTS5 extension, which provides:

- Speed: Searches happen in milliseconds even with thousands of documents
- Relevance: Results are ranked by how well they match your query
- Accuracy: The system finds the most relevant documents first

This approach excels at finding documents containing exact terms.

### Term-Based Search

If full-text search isn't available or finds no results, the system falls back to term-based search that:

- Counts how many search terms appear in each document
- Considers term frequency
- Weights documents containing more of your search terms higher

### Fuzzy Matching

As a last resort, InsightQL can use fuzzy matching to find documents when:
- You might have typos in your query
- You only know part of a word
- The exact term isn't in the database

This works by looking for document terms that start with the same characters as your search terms.

## How Results Are Scored

Documents are scored based on:

- How many search terms appear in the document
- Term frequency
- Term position within the document
- Whether the document contains all search terms or only some

The system calculates a relevance score for each document, presenting the most relevant matches first.

## Search Integration

InsightQL's search functionality is integrated throughout the system:

- The chat client uses document search to provide context for answering questions
- API endpoints allow direct access to search functionality
- Search results include full metadata for tracing information back to sources

## Customizing Search

You can customize search behavior by:

- Adjusting the number of results returned (`top_k` parameter)
- Using different search patterns to match specific file types
- Modifying document chunking size to change search granularity 