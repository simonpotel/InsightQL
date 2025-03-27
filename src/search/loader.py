import os
import glob
import time
from typing import Optional

from .engine import SearchEngine


def load_documents(resources_dir: str, db_path: str = ":memory:", pattern: str = "**/*.llm", chunk_size: int = 2000) -> Optional[SearchEngine]:
    """load documents from files and create search engine index
    
    args:
        resources_dir: directory containing document files
        db_path: path to sqlite database file
        pattern: glob pattern for matching files
        chunk_size: size of document chunks
        
    returns:
        search engine instance or None if loading fails
    """
    if not os.path.exists(resources_dir):
        print(f"Error: Resources directory '{resources_dir}' not found.")
        return None
    
    try:
        start_time = time.time()
        
        # create appropriate database path
        if db_path == ":memory:":
            # use a db file in data directory
            data_dir = "data"
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, "ressources.db")
            search_engine = SearchEngine(db_path)
        else:
            search_engine = SearchEngine(db_path)
        
        file_paths = glob.glob(os.path.join(resources_dir, pattern), recursive=True)
        count = 0
        
        def chunk_text(text, size=chunk_size, overlap=200):
            """split text into overlapping chunks with intelligent breaks
            
            args:
                text: source text to split
                size: maximum chunk size in characters
                overlap: overlap between chunks in characters
                
            returns:
                list of text chunks
            """
            if len(text) <= size:
                return [text]
            
            chunks = []
            start = 0
            while start < len(text):
                end = min(start + size, len(text))
                
                # try to break at paragraph boundary
                if end < len(text):
                    paragraph_break = text.rfind('\n\n', start, end)
                    if paragraph_break > start + size // 2:
                        end = paragraph_break + 2
                
                # try to break at sentence boundary
                if end < len(text) and end == start + size:
                    sentence_end = max(
                        text.rfind('. ', start, end),
                        text.rfind('! ', start, end),
                        text.rfind('? ', start, end)
                    )
                    if sentence_end > start + size // 2:
                        end = sentence_end + 2
                
                # fallback to word boundary
                if end < len(text) and end == start + size:
                    space_pos = text.rfind(' ', start, end)
                    if space_pos > start:
                        end = space_pos + 1
                
                chunks.append(text[start:end])
                
                # ensure proper overlap between chunks
                start = max(start + 1, end - overlap)
                
                # special case for small remaining content
                if start > end - 50 and end < len(text):
                    start = end
            
            return chunks
        
        # process each file and add to search engine
        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                chunks = chunk_text(content)
                
                for i, chunk in enumerate(chunks):
                    metadata = {
                        "source": file_path,
                        "filename": os.path.basename(file_path),
                        "extension": os.path.splitext(file_path)[1],
                        "directory": os.path.dirname(file_path),
                        "chunk": i,
                        "total_chunks": len(chunks)
                    }
                    
                    search_engine.add_document(chunk, metadata)
                    count += 1
                    
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
        
        elapsed_time = time.time() - start_time
        print(f"Loaded {count} document chunks in {elapsed_time:.2f} seconds.")
        
        return search_engine
    except Exception as e:
        import traceback
        print(f"Error loading documents: {e}")
        print(traceback.format_exc())
        return None 