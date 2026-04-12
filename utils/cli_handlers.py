from utils.helper_functions import check_if_empty_input
import os 
import sys 
from rich.console import Console
from rich.progress import track 
from utils.menu import safe_input, is_back, MENU
from ingestion.insert_pdf_chunks import insert_pdf
from hybrid.hybrid_search import search_hybrid 
from db.operations.DocumentManager import DocumentManager

console = Console() 

def display_menu(cs):
    print("\n" + "=" * 60)
    print(f"{cs.BOLD}   HYBRID SEARCH ENGINE   {cs.RESET}")
    print("=" * 60)
    for key, (title, desc) in MENU.items():
        print(f"  {cs.BOLD}[{key.upper()}]{cs.RESET} {title:<18} : {desc}")
    print("=" * 60)


def handle_pdf_upload(conn, cursor, cs):
    path = safe_input("Enter PDF path (or 'b' to go back): ").strip('"').strip("'")
    if check_if_empty_input(path):
        print(f'{cs.RED}❌ Document path cannot be empty.{cs.RESET}')
        return
    elif is_back(path): return
    
    if os.path.isdir(path):
        files = [f for f in os.listdir(path) if f.lower().endswith('.pdf')]
        if not files:
            console.print(f"[yellow]No PDFs found in {path}[/yellow]")
            return
        
        success = 0
        for filename in track(files, description="Ingesting..."):
            if insert_pdf(os.path.join(path, filename), conn, cursor):
                success += 1
        console.print(f"[bold green]Complete: {success}/{len(files)} successful.[/bold green]")
    elif os.path.isfile(path):
        insert_pdf(path, conn, cursor)
    else:
        console.print(f"[red]Path not found.[/red]")

def handle_manual_insert(conn, cursor, model, cs):
    text = safe_input('Enter document text: ')
    if check_if_empty_input(text):
        print(f'{cs.RED}❌ Document text cannot be empty.{cs.RESET}')
        return
    elif is_back(text):
        return
    else:
        manager = DocumentManager(conn, cursor, model)
        manager.insert(text)

def handle_deletion(conn, cursor, model, cs):
    doc_id = safe_input('Enter document ID: ')
    if check_if_empty_input(doc_id):
        print(f'{cs.RED}❌ Document ID cannot be empty.{cs.RESET}')
        return
    elif is_back(doc_id):
        return
    if doc_id.isdigit():
        manager = DocumentManager(conn, cursor, model)
        manager.delete(int(doc_id))

def handle_search(conn, cursor, model, cs):
    query = safe_input("Search query: ")
    if check_if_empty_input(query):
        print(f"{cs.RED}❌ Query cannot be empty.{cs.RESET}")
        return
    elif is_back(query):
        return
    else:
        search_hybrid(query, conn, cursor, model)