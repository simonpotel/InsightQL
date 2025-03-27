import json
import requests
from typing import List, Dict, Any, Optional, Callable
from colorama import init, Fore, Style

init(autoreset=True)


class ChatClient:
    """chat client interface for ollama api with document search capabilities"""
    
    def __init__(
            self,
            model: str = "llama3.2",
            temperature: float = 0.7,
            system_prompt: str = None,
            max_tokens: int = 2000,
            host: str = "http://localhost:11434",
            search_engine = None,
            k_search: int = 5
        ):
        """initialize chat client with model settings and search engine
        
        args:
            model: ollama model name
            temperature: response randomness (0.0-1.0)
            system_prompt: initial system instructions
            max_tokens: maximum tokens in response
            host: ollama api endpoint
            search_engine: optional search engine instance
            k_search: number of results to retrieve from search
        """
        self.model = model
        self.temperature = temperature
        self.system_prompt = system_prompt or "You are a helpful assistant."
        self.max_tokens = max_tokens
        self.host = host
        self.search_engine = search_engine
        self.k_search = k_search
        
        self.conversation = []
        self.doc_references = []
        
        if not self._check_ollama_available():
            print(f"{Fore.MAGENTA}Warning: Cannot connect to Ollama at {host}{Style.RESET_ALL}")
    
    def _check_ollama_available(self) -> bool:
        """verify connection to ollama api"""
        try:
            response = requests.get(f"{self.host}/api/tags")
            return response.status_code == 200
        except:
            return False
    
    def _generate_response(self, prompt: str, stream_handler: Optional[Callable[[str], None]] = None) -> str:
        """generate response from model, with document context if available
        
        args:
            prompt: user question
            stream_handler: optional callback for streaming responses
            
        returns:
            model response as string
        """
        prompt_with_docs = prompt
        
        if self.search_engine:
            search_results = self.search_engine.search(prompt, self.k_search)
            
            if search_results:
                docs_content = []
                self.doc_references = []
                
                for doc_id, metadata, _ in search_results:
                    content, _ = self.search_engine.get_document(doc_id)
                    doc_source = metadata.get("source", "unknown")
                    
                    docs_content.append(f"[Document: {doc_source}]\n{content}\n")
                    self.doc_references.append(metadata)
                
                docs_text = "\n".join(docs_content)
                prompt_with_docs = f"Available documents:\n{docs_text}\n\nUser question: {prompt}\n\nPlease use the information from the documents to answer the question."
        
        url = f"{self.host}/api/chat"
        
        payload = {
            "model": self.model,
            "messages": self.conversation + [{"role": "user", "content": prompt_with_docs}],
            "stream": stream_handler is not None,
            "temperature": self.temperature,
            "options": {
                "num_predict": self.max_tokens
            }
        }
        
        if self.system_prompt:
            payload["system"] = self.system_prompt
        
        if stream_handler:
            response_text = ""
            response = requests.post(url, json=payload, stream=True)
            
            for line in response.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line)
                        if "message" in chunk and "content" in chunk["message"]:
                            content = chunk["message"]["content"]
                            response_text += content
                            stream_handler(content)
                    except:
                        pass
            
            return response_text
        else:
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                return result["message"]["content"]
            else:
                error_message = f"Error: {response.status_code} - {response.text}"
                print(f"{Fore.RED}{error_message}{Style.RESET_ALL}")
                return f"API error: {error_message}"
    
    def ask(self, prompt: str, stream_handler: Optional[Callable[[str], None]] = None) -> str:
        """send question to the model and get response
        
        args:
            prompt: user question
            stream_handler: optional callback for streaming responses
            
        returns:
            model response as string
        """
        self.conversation.append({"role": "user", "content": prompt})
        
        try:
            response = self._generate_response(prompt, stream_handler)
            self.conversation.append({"role": "assistant", "content": response})
            return response
        except Exception as e:
            error_message = f"Error generating response: {e}"
            print(f"{Fore.RED}{error_message}{Style.RESET_ALL}")
            return error_message
    
    def get_doc_references(self) -> List[Dict[str, Any]]:
        """get document references used in last response"""
        return self.doc_references
    
    def clear_conversation(self):
        """reset conversation history and document references"""
        self.conversation = []
        self.doc_references = [] 