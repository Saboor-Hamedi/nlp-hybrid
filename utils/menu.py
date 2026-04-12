from utils.ColorScheme import ColorScheme

cs = ColorScheme()
MENU = {
    "u": ("Upload PDF", "Bulk ingest folder or single PDF."),
    "i": ("Insert Document", "Insert a document manually."),
    "d": ("Delete Document", "Delete a document by ID."),
    "h": ("Hybrid Search", "Search using semantic + keyword (BM25)."),
    "b": ("Back", "Go back to the main menu."),
    "q": ("Quit", "Exit the program."),
}

def safe_input(promt)-> str:
    try:
        return input(promt).strip()
    except (EOFError, KeyboardInterrupt):
        print(f"\n{cs.YELLOW}Operation cancelled.{cs.RESET}")
        return ""

def safe_int_input(prompt: str) -> int | None:
    """Return int or None on error / cancel."""
    raw = safe_input(prompt)
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        print(f"{cs.RED}Please enter a valid integer.{cs.RESET}")
        return None

def is_back(text: str) -> bool:
    from utils.helper_functions import go_back
    return go_back(text)


