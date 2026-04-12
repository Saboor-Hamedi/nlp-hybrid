from db.operations.document_management import insert_document

def handle_manual_insert(cnn, cursor, model):
    text = input("Enter the text you want to index: ").strip()
    if text:
        # insert_document, handles cleaning, embedding, and sql execution 
        doc_id = insert_document(text, cnn, cursor, model)
        if doc_id:
            print(f"Document inserted with ID: {doc_id}")
        else:
            print("Failed to insert document")