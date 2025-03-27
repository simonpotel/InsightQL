import re
import sqlite3
import json
import uuid
from typing import List, Dict, Any, Tuple


class SearchEngine:
    """lightweight search engine using sqlite for document storage and retrieval"""
    
    def __init__(self, db_path: str = ":memory:"):
        """initialize search engine with database connection
        
        args:
            db_path: path to sqlite database file or :memory: for in-memory db
        """
        self.conn = sqlite3.connect(db_path)
        self.conn.enable_load_extension(True)
        try:
            self.conn.load_extension("fts5")
            self.has_fts = True
        except:
            self.has_fts = False
        self.conn.enable_load_extension(False)
        
        self.cursor = self.conn.cursor()
        self._create_tables()
    
    def _create_tables(self):
        """create database tables and indices for documents and term index"""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                content TEXT,
                metadata TEXT
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS terms (
                term TEXT,
                doc_id TEXT,
                frequency INTEGER,
                positions TEXT,
                UNIQUE(term, doc_id)
            )
        ''')
        
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_terms_term ON terms(term)
        ''')
        
        if self.has_fts:
            try:
                self.cursor.execute('''
                    CREATE VIRTUAL TABLE IF NOT EXISTS fts_documents USING fts5(
                        content,
                        doc_id UNINDEXED
                    )
                ''')
            except:
                self.has_fts = False
        
        self.conn.commit()
    
    def _tokenize(self, text: str) -> List[str]:
        """extract meaningful terms from text for indexing or searching
        
        args:
            text: source text to tokenize
            
        returns:
            list of lowercase terms with length > 1
        """
        text = text.lower()
        terms = re.findall(r'\w+', text)
        return [term for term in terms if len(term) > 1]
    
    def add_document(self, content: str, metadata: Dict[str, Any]) -> str:
        """add document to database with content and metadata
        
        args:
            content: text content of document
            metadata: additional information about document
            
        returns:
            generated document id
        """
        doc_id = str(uuid.uuid4())
        
        self.cursor.execute(
            "INSERT INTO documents (id, content, metadata) VALUES (?, ?, ?)",
            (doc_id, content, json.dumps(metadata))
        )
        
        if self.has_fts:
            try:
                self.cursor.execute(
                    "INSERT INTO fts_documents (doc_id, content) VALUES (?, ?)",
                    (doc_id, content)
                )
            except:
                self.has_fts = False
        
        terms = self._tokenize(content)
        term_counts = {}
        term_positions = {}
        
        # track term frequencies and positions
        for pos, term in enumerate(terms):
            term_counts[term] = term_counts.get(term, 0) + 1
            if term not in term_positions:
                term_positions[term] = []
            term_positions[term].append(pos)
        
        # store term data in index
        for term, count in term_counts.items():
            positions = json.dumps(term_positions[term])
            self.cursor.execute(
                "INSERT INTO terms (term, doc_id, frequency, positions) VALUES (?, ?, ?, ?)",
                (term, doc_id, count, positions)
            )
        
        self.conn.commit()
        return doc_id
    
    def search(self, query: str, top_k: int = 5) -> List[Tuple[str, Dict[str, Any], float]]:
        """search documents using multi-strategy approach
        
        args:
            query: search query text
            top_k: maximum number of results to return
            
        returns:
            list of tuples with (doc_id, metadata, score)
        """
        query_terms = self._tokenize(query)
        
        if not query_terms:
            return []
        
        results = []
        
        # strategy 1: full-text search (fastest and most accurate)
        if self.has_fts:
            try:
                fts_query = " OR ".join(query_terms)
                self.cursor.execute("""
                    SELECT d.id, d.metadata, fts.rank
                    FROM fts_documents fts
                    JOIN documents d ON fts.doc_id = d.id
                    WHERE fts.content MATCH ?
                    ORDER BY fts.rank
                    LIMIT ?
                """, (fts_query, top_k))
                
                for row in self.cursor.fetchall():
                    doc_id, metadata_json, score = row
                    metadata = json.loads(metadata_json)
                    results.append((doc_id, metadata, score))
                
                if results:
                    return results
            except:
                self.has_fts = False
        
        # strategy 2: term index search (more detailed matching)
        if not results:
            query_terms_set = set(query_terms)
            if query_terms_set:
                term_placeholders = ','.join(['?'] * len(query_terms_set))
                
                self.cursor.execute(f"""
                    SELECT doc_id, term, frequency, positions
                    FROM terms
                    WHERE term IN ({term_placeholders})
                """, list(query_terms_set))
                
                doc_matches = {}
                for doc_id, term, freq, positions_json in self.cursor.fetchall():
                    if doc_id not in doc_matches:
                        doc_matches[doc_id] = {
                            'term_matches': {},
                            'total_matches': 0,
                            'total_freq': 0
                        }
                    
                    doc_matches[doc_id]['term_matches'][term] = {
                        'freq': freq,
                        'positions': json.loads(positions_json) if positions_json else []
                    }
                    doc_matches[doc_id]['total_matches'] += 1
                    doc_matches[doc_id]['total_freq'] += freq
                
                # score documents based on term coverage and frequency
                scored_docs = []
                for doc_id, match_data in doc_matches.items():
                    term_count_score = match_data['total_matches'] / len(query_terms_set)
                    freq_score = match_data['total_freq']
                    
                    final_score = term_count_score * 3 + freq_score
                    scored_docs.append((doc_id, final_score))
                
                if scored_docs:
                    scored_docs.sort(key=lambda x: x[1], reverse=True)
                    top_docs = scored_docs[:top_k]
                    
                    for doc_id, score in top_docs:
                        self.cursor.execute(
                            "SELECT metadata FROM documents WHERE id = ?",
                            (doc_id,)
                        )
                        metadata_json = self.cursor.fetchone()[0]
                        metadata = json.loads(metadata_json)
                        results.append((doc_id, metadata, score))
        
        # strategy 3: fuzzy/prefix matching (fallback for inexact matches)
        if not results and query_terms:
            like_patterns = []
            like_params = []
            
            for term in query_terms:
                if len(term) > 3:
                    like_patterns.append("term LIKE ?")
                    like_params.append(f"{term[:3]}%")
            
            if like_patterns:
                like_query = " OR ".join(like_patterns)
                query_sql = f"""
                    SELECT doc_id, COUNT(*) as score
                    FROM terms
                    WHERE {like_query}
                    GROUP BY doc_id
                    ORDER BY score DESC
                    LIMIT ?
                """
                
                self.cursor.execute(query_sql, like_params + [top_k])
                
                for doc_id, score in self.cursor.fetchall():
                    self.cursor.execute(
                        "SELECT metadata FROM documents WHERE id = ?",
                        (doc_id,)
                    )
                    metadata_json = self.cursor.fetchone()[0]
                    metadata = json.loads(metadata_json)
                    results.append((doc_id, metadata, score))
        
        return results
    
    def get_document(self, doc_id: str) -> Tuple[str, Dict[str, Any]]:
        """retrieve document content and metadata by id
        
        args:
            doc_id: document identifier
            
        returns:
            tuple of (content, metadata)
        """
        self.cursor.execute(
            "SELECT content, metadata FROM documents WHERE id = ?",
            (doc_id,)
        )
        content, metadata_json = self.cursor.fetchone()
        return content, json.loads(metadata_json)
    
    def get_document_count(self) -> int:
        """get total number of documents in database"""
        self.cursor.execute("SELECT COUNT(*) FROM documents")
        return self.cursor.fetchone()[0]
    
    def close(self):
        """close database connection"""
        self.conn.close()
    
    def __del__(self):
        """ensure database connection is closed on object destruction"""
        try:
            self.conn.close()
        except:
            pass 