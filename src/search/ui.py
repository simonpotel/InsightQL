import os
import json
import time
from colorama import Fore, Style

from src.client import ChatClient


def print_header():
    """display application header with formatting"""
    header = """
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                                 InsightQL Chat                                ┃
┃                Document-based conversations using local LLMs                  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
    """
    print(f"{Fore.MAGENTA}{Style.BRIGHT}{header}{Style.RESET_ALL}")


def interactive_chat(
        chat_client: ChatClient,
        exit_commands = None,
        help_commands = None,
        clear_commands = None,
        docs_commands = None,
        save_commands = None,
        load_commands = None
    ):
    """run interactive chat session with command handling
    
    args:
        chat_client: initialized chat client instance
        exit_commands: commands to exit the session
        help_commands: commands to show help
        clear_commands: commands to clear conversation
        docs_commands: commands to show document references
        save_commands: commands to save conversation
        load_commands: commands to load conversation
    """
    exit_commands = exit_commands or ["/exit", "/quit", "exit", "quit"]
    help_commands = help_commands or ["/help", "help", "?"]
    clear_commands = clear_commands or ["/clear", "clear"]
    docs_commands = docs_commands or ["/docs", "docs"]
    save_commands = save_commands or ["/save", "save"]
    load_commands = load_commands or ["/load", "load"]
    
    os.system('cls' if os.name == 'nt' else 'clear')
    print_header()
    
    print(f"{Style.BRIGHT}Interactive chat session using {Fore.YELLOW}{chat_client.model}{Style.RESET_ALL}")
    print(f"Type {Fore.YELLOW}{', '.join(exit_commands)}{Style.RESET_ALL} to exit")
    print(f"Type {Fore.YELLOW}{', '.join(help_commands)}{Style.RESET_ALL} for help")
    
    def show_help():
        """display available commands and their descriptions"""
        help_text = f"""
{Fore.MAGENTA}{Style.BRIGHT}Available Commands:{Style.RESET_ALL}
  {Fore.YELLOW}{', '.join(exit_commands)}{Style.RESET_ALL} - Exit the interactive session
  {Fore.YELLOW}{', '.join(help_commands)}{Style.RESET_ALL} - Show this help message
  {Fore.YELLOW}{', '.join(clear_commands)}{Style.RESET_ALL} - Clear the conversation history
  {Fore.YELLOW}{', '.join(docs_commands)}{Style.RESET_ALL} - Show document references for the last response
  {Fore.YELLOW}{', '.join(save_commands)} [filename]{Style.RESET_ALL} - Save conversation to a file
  {Fore.YELLOW}{', '.join(load_commands)} [filename]{Style.RESET_ALL} - Load conversation from a file
"""
        print(help_text)
    
    def print_stream(text):
        """print streaming response text"""
        print(f"{Fore.WHITE}{text}", end="")
    
    while True:
        try:
            user_input = input(f"\n{Fore.MAGENTA}{Style.BRIGHT}You > {Style.RESET_ALL}")
            
            if user_input.lower() in exit_commands:
                print(f"{Fore.YELLOW}Exiting interactive session.{Style.RESET_ALL}")
                break
            
            elif user_input.lower() in help_commands:
                show_help()
            
            elif user_input.lower() in clear_commands:
                chat_client.clear_conversation()
                os.system('cls' if os.name == 'nt' else 'clear')
                print_header()
                print(f"{Fore.YELLOW}Conversation history cleared.{Style.RESET_ALL}")
            
            elif user_input.lower() in docs_commands or user_input.lower().startswith(tuple(d + " " for d in docs_commands)):
                show_document_references(chat_client)
            
            elif user_input.lower() in save_commands or user_input.lower().startswith(tuple(s + " " for s in save_commands)):
                save_conversation(chat_client, user_input)
            
            elif user_input.lower() in load_commands or user_input.lower().startswith(tuple(l + " " for l in load_commands)):
                load_conversation(chat_client, user_input)
            
            else:
                print(f"\n{Fore.YELLOW}{Style.BRIGHT}MODEL > {Style.RESET_ALL}", end="")
                response = chat_client.ask(user_input, print_stream)
                
                if chat_client.doc_references:
                    print(f"\n{Style.DIM}(Type {Fore.YELLOW}/docs{Style.RESET_ALL}{Style.DIM} to see document references){Style.RESET_ALL}")
        
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Exiting interactive session.{Style.RESET_ALL}")
            break
        
        except Exception as e:
            print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")


def show_document_references(chat_client):
    """display document references used in the last response
    
    args:
        chat_client: chat client instance with references to display
    """
    doc_refs = chat_client.get_doc_references()
    
    if not doc_refs:
        print(f"{Fore.YELLOW}No document references available for the last response.{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.MAGENTA}{Style.BRIGHT}Document references:{Style.RESET_ALL}")
        for i, doc in enumerate(doc_refs):
            source = doc.get("source", "Unknown")
            chunk = doc.get("chunk", 0)
            total_chunks = doc.get("total_chunks", 1)
            print(f"  {Fore.WHITE}[{i+1}] {Fore.YELLOW}{source} {Style.DIM}(chunk {chunk+1}/{total_chunks}){Style.RESET_ALL}")


def save_conversation(chat_client, command_input):
    """save conversation history to json file
    
    args:
        chat_client: chat client with conversation to save
        command_input: command string that may include filename
    """
    parts = command_input.split(" ", 1)
    filename = parts[1] if len(parts) > 1 else f"chat_{int(time.time())}.json"
    
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(chat_client.conversation, f, ensure_ascii=False, indent=2)
        
        print(f"{Fore.MAGENTA}Conversation saved to {Fore.YELLOW}{filename}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Error saving conversation: {e}{Style.RESET_ALL}")


def load_conversation(chat_client, command_input):
    """load conversation history from json file
    
    args:
        chat_client: chat client to load conversation into
        command_input: command string that may include filename
    """
    parts = command_input.split(" ", 1)
    
    if len(parts) < 2:
        print(f"{Fore.RED}Please specify a filename to load.{Style.RESET_ALL}")
        return
    
    filename = parts[1]
    
    if not os.path.exists(filename):
        print(f"{Fore.RED}File not found: {filename}{Style.RESET_ALL}")
        return
    
    try:
        with open(filename, "r", encoding="utf-8") as f:
            conversation = json.load(f)
        
        chat_client.conversation = conversation
        print(f"{Fore.MAGENTA}Conversation loaded from {Fore.YELLOW}{filename}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Error loading conversation: {e}{Style.RESET_ALL}") 