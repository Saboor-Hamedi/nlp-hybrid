import os
import sys
sys.path.append(os.getcwd())
from db.db_connection import db_connection, get_model
from utils.analytics.topic_modeling import get_topics, plot_lda_topics, plot_tfidf
from utils.analytics.bert_topic import get_bert_topics, plot_bert_clusters

def generate_report():
    print("\n" + "="*50)
    print("AI ANALYSIS REPORT GENERATOR")
    print("="*50)
    
    conn = db_connection()
    if not conn:
        print("Failed to connect to database.")
        return
        
    cursor = conn.cursor()
    cursor.execute('SELECT content FROM document ORDER BY id DESC LIMIT 100')
    docs = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    
    if not docs:
        print("No documents found.")
        return
        
    print(f"Analyzing {len(docs)} documents...")
    
    # LDA
    num_topics = 5
    lda_results, lda_model, dictionary = get_topics(docs, num_topics=num_topics)
    print("\n--- LDA TOPICS ---")
    for topic_id, words in lda_results:
        print(f"Topic #{topic_id + 1}: {words}")
        
    # BERT
    bert_results, bert_kmeans = get_bert_topics(docs, get_model(), num_topics=num_topics)
    print("\n--- BERT TOPICS ---")
    for topic_id, words in bert_results:
        print(f"Topic #{topic_id + 1}: {words}")
        
    # TF-IDF (We'll just run it to get the console output if we add prints there, 
    # or we can just look at the return value if we updated it)
    print("\n--- TOP TF-IDF TERMS ---")
    # Since I'm in a script, I can just calculate it here or call the function
    # Let's call the function I just modified (if it worked)
    tfidf_data = plot_tfidf(docs)
    for item in tfidf_data[:10]:
        print(f"{item['term']}: {item['rank']:.4f}")

    print("\n" + "="*50)

if __name__ == "__main__":
    generate_report()
