import logging
from db.db_connection import db_connection, get_model
from utils.ColorScheme import ColorScheme
from utils.menu import safe_input
from utils.cli_handlers import (
    display_menu, handle_pdf_upload, handle_manual_insert, 
    handle_deletion, handle_search, console
)

cs = ColorScheme()

def main():
    logging.basicConfig(filename='activity.log', level=logging.INFO)
    
    with console.status("[bold green]Initializing AI Engine..."):
        model = get_model()
    
    if not model: return

    while True:
        display_menu(cs)
        choice = safe_input(f"{cs.GREEN}Action -> {cs.RESET}").lower()
        
        if choice == "q": break
        if not choice: continue

        # Database Context Management
        conn = db_connection()
        if not conn: continue
        cursor = conn.cursor()

        try:
            if choice == "u":   handle_pdf_upload(conn, cursor, cs)
            elif choice == "i": handle_manual_insert(conn, cursor, model, cs)
            elif choice == "d": handle_deletion(conn, cursor, model, cs)
            elif choice == "h": handle_search(conn, cursor, model, cs)
            else: print(f"{cs.RED}Invalid option.{cs.RESET}")
        finally:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    main()