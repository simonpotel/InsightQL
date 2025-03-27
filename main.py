import argparse
import os
import sys
from colorama import init, Fore, Style

from src.search import SearchEngine, load_documents
from src.client import ChatClient
from src.search.ui import interactive_chat, print_header


init(autoreset=True)


def parse_args():
    """parse command line arguments for application configuration"""
    parser = argparse.ArgumentParser(description="Local LLM Chat with document search")
    
    parser.add_argument("--resources", type=str, default="./resources",
                        help="Directory containing documents to load")
    
    parser.add_argument("--pattern", type=str, default="**/*.llm",
                        help="File pattern for document loading")
    
    parser.add_argument("--db", type=str, default=None,
                        help="SQLite database path for document index")
    
    parser.add_argument("--model", type=str, default="llama3.2",
                        help="Ollama model to use")
    
    parser.add_argument("--host", type=str, default="http://localhost:11434",
                        help="Ollama API host")
    
    parser.add_argument("--temperature", type=float, default=0.7,
                        help="Temperature for response generation")
    
    parser.add_argument("--system", type=str, default=None,
                        help="System prompt")
    
    parser.add_argument("--no-search", action="store_true",
                        help="Disable document search")
    
    parser.add_argument("--k-results", type=int, default=5,
                        help="Number of search results to use")
    
    return parser.parse_args()


def main():
    """main application entry point"""
    args = parse_args()
    
    # Clear screen and print header
    os.system('cls' if os.name == 'nt' else 'clear')
    print_header()
    
    search_engine = None
    
    # setup document search if enabled
    if not args.no_search:
        if not os.path.exists(args.resources):
            print(f"{Fore.RED}Error: Resources directory '{args.resources}' not found.{Style.RESET_ALL}")
            return 1
        
        # configure database location
        db_path = args.db
        if not db_path:
            # use a db file in data directory
            data_dir = "data"
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, "ressources.db")
            print(f"{Fore.CYAN}Using database: {db_path}{Style.RESET_ALL}")
        
        # load documents or use existing database
        if not os.path.exists(db_path):
            print(f"{Fore.YELLOW}Documents not found in database. Loading documents...{Style.RESET_ALL}")
            search_engine = load_documents(args.resources, db_path, args.pattern)
            
            if not search_engine:
                print(f"{Fore.RED}Failed to load documents.{Style.RESET_ALL}")
                return 1
            
            doc_count = search_engine.get_document_count()
            print(f"{Fore.GREEN}Loaded {doc_count} documents into the database.{Style.RESET_ALL}")
        else:
            print(f"{Fore.CYAN}Using existing database: {db_path}{Style.RESET_ALL}")
            search_engine = SearchEngine(db_path)
            doc_count = search_engine.get_document_count()
            print(f"{Fore.GREEN}Found {doc_count} documents in the database.{Style.RESET_ALL}")
        
        # confirm if database is empty
        if doc_count == 0:
            print(f"{Fore.YELLOW}Warning: No documents found in the database.{Style.RESET_ALL}")
            if input(f"{Fore.YELLOW}Continue without documents? (y/n): {Style.RESET_ALL}").lower() != "y":
                return 0
    
    print(f"\n{Fore.CYAN}{Style.BRIGHT}Initializing chat client with model: {Fore.GREEN}{args.model}{Style.RESET_ALL}")
    
    # create chat client with configured options
    chat_client = ChatClient(
        model=args.model,
        temperature=args.temperature,
        system_prompt=args.system,
        host=args.host,
        search_engine=search_engine,
        k_search=args.k_results
    )
    
    # start interactive session
    try:
        interactive_chat(chat_client)
    except Exception as e:
        print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 