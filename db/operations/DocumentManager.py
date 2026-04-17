
import os 
import sys  
import psycopg2
from utils.helper_functions import check_if_empty_input, measure_time
from utils.languages import detect_language
from utils.text_properties import normalize_content
from utils.ColorScheme import ColorScheme


class DocumentManager:
    def __init__(self, conn, cursor, model):
        """
        Initialize the DocumentManager with database connection, cursor, and model.
        """
        self.conn = conn
        self.cursor = cursor
        self.model = model
        self.cs = ColorScheme()

    def insert(self, content,commit=True, silent=False, preserve_fidelity=False):

        # Check for empty input -> no empty input is allowed 
        if check_if_empty_input(content):
            if not silent:
                print(f"{self.cs.RED}❌ Input cannot be empty.{self.cs.RESET}")
            return False

        get_elapsed = measure_time()


        # Logic: Preserve exact text for Scholar/AI data
        nor_content = content.strip() if preserve_fidelity else normalize_content(content)
        language = detect_language(nor_content)
        
        try:
            # Generate embedding
            emb = self.model.encode(nor_content).tolist()

            # 1. Insert content and FTS vector
            self.cursor.execute(
                "INSERT INTO document (content, language, content_tsvector) VALUES (%s, %s, to_tsvector('simple', %s)) RETURNING id;",
                (nor_content, language, nor_content),
            )
            result = self.cursor.fetchone()
            if result is None:
                if not silent:
                    print(f"{self.cs.RED}❌ INSERT failed - no ID returned{self.cs.RESET}")
                return False
            doc_id = result[0]

            # 2. Insert embedding (pgvector)
            self.cursor.execute(
                "INSERT INTO document_embedding (doc_id, embedding) VALUES (%s, %s)",
                (doc_id, emb),
            )

            if commit:
                self.conn.commit()
                if not silent:
                    print(f"{self.cs.GREEN}✅ Inserted document (language: {language}). Time: {get_elapsed()}s {self.cs.RESET}")
            else:
                if not silent:
                    print(f"{self.cs.YELLOW}📝 Queued for batch (language: {language}). Time: {get_elapsed()}s {self.cs.RESET}")
            
            return doc_id

        except Exception as e:
            print(f"{self.cs.RED}❌ Error after {get_elapsed()}s. Error: {e}{self.cs.RESET}")
            self.conn.rollback()
            return False

    def select(self, doc_id=None, limit=10, offset=0):
        get_elapsed = measure_time()
        try:
        
            # This block fetches your list of documents for the home page
            query = """
                SELECT d.id, d.content, d.language, d.created_at, e.embedding 
                FROM document d
                LEFT JOIN document_embedding e ON d.id = e.doc_id
                ORDER BY random() 
                LIMIT %s OFFSET %s;
            """
            self.cursor.execute(query, (limit, offset))
            rows = self.cursor.fetchall()
            
            results = []
            for row in rows:
                results.append({
                    "id": row[0],
                    "content": row[1],
                    "language": row[2],
                    "created_at": row[3],
                    "embedding": row[4]
                })
            
            print(f"{self.cs.GREEN}✅ Selected {len(results)} documents. Time: {get_elapsed()}s {self.cs.RESET}")
            return results

        except Exception as e:

            print(f"{self.cs.RED}❌ Error in select: {e}{self.cs.RESET}")
            self.conn.rollback()
            return False

    def show(self, doc_id):
        query = """
                    SELECT d.id, d.content, d.language, d.created_at, e.embedding 
                    FROM document d
                    LEFT JOIN document_embedding e ON d.id = e.doc_id
                    WHERE d.id = %s;
                """
        try:
            self.cursor.execute(query, (doc_id,))
            row = self.cursor.fetchone()

            if row: 
                return {
                    "id": row[0],
                    "content": row[1],
                    "language": row[2],
                    "created_at": row[3],
                    "embedding": row[4]
                }
            return None
        except Exception as e:
            print(f"{self.cs.RED}❌ Error in show: {e}{self.cs.RESET}")
            self.conn.rollback()
            return False
    def update(self, content, doc_id):
        pass

    def delete(self, doc_id):
        if not isinstance(doc_id, int):
            print(f"{self.cs.RED}❌ Document ID must be an integer.{self.cs.RESET}")
            return False
        try:

            # Start a transaction delete both entries
            self.cursor.execute("BEGIN;")
            # Delete from document_embedding first due to foreign key constraint
            self.cursor.execute("DELETE FROM document_embedding WHERE doc_id = %s;", (doc_id,))
            self.cursor.execute("DELETE FROM document WHERE id = %s;", (doc_id,))
            self.cursor.execute("COMMIT;")

            # Check if any rows were deleted
            if self.cursor.rowcount == 0:
                self.cursor.execute("ROLLBACK;")
                print(f"{self.cs.RED}❌ No document found with ID {doc_id}.{self.cs.RESET}")
                return True
            self.conn.commit()

            # Notify BM25 utility to update its index
            print(f"{self.cs.GREEN}✅ Document with ID {doc_id} deleted successfully.{self.cs.RESET}")

        except psycopg2.Error as e:
            # Rollback on any database error
            self.cursor.execute("ROLLBACK")
            print(f"{self.cs.RED}❌ Database error during deletion: {e}{self.cs.RESET}")
            return False
        except Exception as e:
            self.cursor.execute("ROLLBACK")
            print(f"{self.cs.RED}❌ Unexpected error during deletion: {e}{self.cs.RESET}")
            return False