# This is my flask app web.py
import re

from flask import Flask, render_template, request

from db.db_connection import db_connection, get_model
from db.operations.DocumentManager import DocumentManager
from hybrid.hybrid_search import search_hybrid
from utils.analytics.bert_topic import get_bert_topics, predict_bert_topic, predict_bert_topics_batch
from utils.analytics.topic_modeling import (
    find_best_k,
    get_topics,
    plot_coherence,
    predict_topic,
)
from utils.cli_handlers import handle_search

# The main connection to the database
app = Flask(__name__, template_folder='templates', static_folder='static')
get_model()  # Pre-warm the AI model at startup so first request isn't slow

# Helper function to parse LDA topic string
def parse_lda_keywords(topic_string, top_k=5, min_weight=0.01):
    """
    Parse LDA topic string like '0.045*"word1" + 0.032*"word2"'
    into a dictionary of keywords, filtered by weight and limited to top_k
    """
    keywords = {}
    # Pattern: weight*"word"
    pattern = r'([\d.]+)\*"([^"]+)"'
    matches = re.findall(pattern, topic_string)

    for weight, word in matches:
        weight_float = float(weight)
        # Filter: only include keywords with significant weight
        if weight_float >= min_weight and len(word) > 2 and word.isalpha():
            keywords[word] = weight_float

    # Sort by weight (descending) and limit to top_k
    sorted_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:top_k]
    return dict(sorted_keywords)

# Helper function to extract BERT keywords
def parse_bert_keywords(bert_topic_tuple, top_k=5):
    """
    Extract keywords from BERT topic tuple (id, keywords_string)
    Filters out short words and numbers, limits to top_k
    """
    try:
        if isinstance(bert_topic_tuple, (tuple, list)) and len(bert_topic_tuple) > 1:
            keywords_str = bert_topic_tuple[1]
            if isinstance(keywords_str, str):
                # Parse "word1, word2, word3" format
                words = [w.strip() for w in keywords_str.split(',') if w.strip()]
                # Filter: only keep words that are alphabetic and have length > 2
                filtered_words = [w for w in words if len(w) > 2 and w.isalpha()]
                # Limit to top_k
                filtered_words = filtered_words[:top_k]
                return {word: 1.0 for word in filtered_words}
            elif isinstance(keywords_str, dict):
                return keywords_str
    except Exception as e:
        print(f"Error in parse_bert_keywords: {e}")
    return {}
API_URL= 'http://localhost:5000'  # fast api backend



# home page

@app.route('/', methods=['GET', 'POST'])
def home():
    query = (request.form.get('query') or request.args.get('query') or '').strip()
    # start connection
    conn = db_connection()


    if not conn:
        return 'Error: Could not connect to the database.'
    cursor = conn.cursor()
    # This is for foreground
    manager = DocumentManager(conn, cursor, get_model())
    results = manager.select(limit=10)


    if results:
        # Extract content for topic modeling
        cursor.execute('SELECT content FROM document ORDER BY random() LIMIT 10')
        training_data = [r[0] for r in cursor.fetchall()]
        _,lda_model, dictionary = get_topics(training_data, num_topics=10)

        # Tagging documents with topics
        for doc in results:
            # Add default relevance score for home page results
            doc['relevance_score'] = 'N/A'

            # We can use LDA for now, or BERT if preferred. Let's use LDA as default tag.
            topic_id = predict_topic(doc['content'], lda_model, dictionary)
            doc['tag'] = f'LDA Topic {topic_id + 1}'

            # Optional: Add BERT tag too
            # _, bert_model = get_bert_topics(training_data, get_model(), num_topics=10)
            # bert_topic_id = predict_bert_topic(doc['content'], get_model(), bert_model)
            # doc['bert_tag'] = f'BERT Topic {bert_topic_id + 1}'
    else:
        results =[]

    cursor.close()
    conn.close()
    return render_template('static/content.html',
    results=results, query=query)

# show single post
@app.route('/show/<int:doc_id>')
def show(doc_id):
    conn = db_connection()
    if conn:
        cursor = conn.cursor()
        manager = DocumentManager(conn, cursor, get_model())
        result = manager.show(doc_id)
        cursor.close()
        conn.close()
        return render_template('static/show.html', result=result)
    return 'Error: Could not connect to the database.'
# search
@app.route('/search', methods=['GET','POST'])
@app.route('/search', methods=['GET','POST'])
def search():
    # Support both POST form data and GET URL parameters
    query = (request.form.get('query') or request.args.get('query') or '').strip()

    # we validate the input
    if not query or len(query) < 2:
        return render_template('static/search.html',
        results=[], query=query,
        error="Please enter at least 2 characters.")
        # start connection
    conn = db_connection()
    if conn:
        cursor = conn.cursor()
        results, stats = search_hybrid(query, conn, cursor, get_model())

        # ========== TRAIN TOPIC MODELS ON SEARCH RESULTS ==========
        training_data = [r[1] for r in results]

        # Use up to 5 topics, but no more than the number of search results we actually have
        dynamic_k = max(1, min(5, len(training_data)))

        lda_topics = []
        lda_model = None
        dictionary = None
        bert_topics = []
        bert_kmeans = None

        if training_data:
            try:
                lda_topics, lda_model, dictionary = get_topics(training_data, num_topics=dynamic_k)
            except Exception as e:
                print(f"Error training LDA: {e}")
                lda_topics = []

            try:
                bert_topics, bert_kmeans = get_bert_topics(training_data, get_model(), num_topics=dynamic_k)
            except Exception as e:
                print(f"Error training BERT: {e}")
                bert_topics = []
        # ========================================

        cursor.close()
        conn.close()

        # Convert results to dictionary format with topic predictions
        # Batch predict BERT topics for all results at once (much faster)
        bert_topic_ids = (
            predict_bert_topics_batch([r[1] for r in results], get_model(), bert_kmeans)
            if bert_kmeans else [0] * len(results)
        )

        results_dict = []
        for i, r in enumerate(results):
            lda_topic_id = 0
            bert_topic_id = bert_topic_ids[i]

            # Predict LDA topic for this result (safely)
            if lda_model and dictionary:
                try:
                    lda_topic_id = predict_topic(r[1], lda_model, dictionary)
                except:
                    lda_topic_id = 0

            # Parse LDA keywords from topic string with type checking
            lda_keywords = {}
            if lda_topics and lda_topic_id < len(lda_topics):
                try:
                    topic_tuple = lda_topics[lda_topic_id]
                    # Check if topic_tuple is a tuple or list with at least 2 elements
                    if isinstance(topic_tuple, (tuple, list)) and len(topic_tuple) > 1:
                        # Check if the second element is a string
                        if isinstance(topic_tuple[1], str):
                            lda_keywords = parse_lda_keywords(topic_tuple[1])
                        elif isinstance(topic_tuple[1], dict):
                            # If it's already a dictionary, use it directly
                            lda_keywords = topic_tuple[1]
                        else:
                            lda_keywords = {}
                    elif isinstance(topic_tuple, dict):
                        # If topic_tuple itself is a dictionary
                        lda_keywords = topic_tuple
                    else:
                        lda_keywords = {}
                except Exception as e:
                    print(f"Error parsing LDA keywords: {e}")
                    lda_keywords = {}

            # Parse BERT keywords from topic tuple with type checking
            bert_keywords = {}
            if bert_topics and bert_topic_id < len(bert_topics):
                try:
                    bert_topic_tuple = bert_topics[bert_topic_id]
                    # Check if bert_topic_tuple is a tuple or list with at least 2 elements
                    if isinstance(bert_topic_tuple, (tuple, list)) and len(bert_topic_tuple) > 1:
                        # Check if the second element is a string
                        if isinstance(bert_topic_tuple[1], str):
                            bert_keywords = parse_bert_keywords(bert_topic_tuple)
                        elif isinstance(bert_topic_tuple[1], dict):
                            # If it's already a dictionary, use it directly
                            bert_keywords = bert_topic_tuple[1]
                        else:
                            bert_keywords = {}
                    elif isinstance(bert_topic_tuple, dict):
                        # If bert_topic_tuple itself is a dictionary
                        bert_keywords = bert_topic_tuple
                    else:
                        bert_keywords = {}
                except Exception as e:
                    print(f"Error parsing BERT keywords: {e}")
                    bert_keywords = {}

            results_dict.append({
                "id": r[0],
                "content": r[1],
                "relevance_score": r[2],
                "language": r[3],
                "created_at": r[4],
                "lda_topic_id": lda_topic_id,
                "lda_topic_label": f"LDA Topic {lda_topic_id + 1}" if lda_topics else "N/A",
                "bert_topic_id": bert_topic_id,
                "bert_topic_label": f"BERT Topic {bert_topic_id + 1}" if bert_topics else "N/A",
                "lda_keywords": lda_keywords,
                "bert_keywords": bert_keywords
            })

        return render_template('static/search.html',
            results=results_dict,
            query=query,
            lda_topics=lda_topics,
            bert_topics=bert_topics,
            stats=stats)
    return 'Error: Could not connect to the database.'

#  Topic modeling
# Add this import at the top
from utils.analytics.bert_topic import get_bert_topics, plot_bert_clusters
from utils.analytics.sentiment import get_sentiment_modeling
from utils.analytics.topic_modeling import (
    get_topics,
    plot_lda_topics,
    plot_tfidf,
    predict_topic,
    preprocess,
)


@app.route('/topics')
def show_topics():
    try:
        conn = db_connection()
        if conn:
            cursor = conn.cursor()
            # Fetch last 50 documents to analyze (fewer docs = faster page load)
            cursor.execute('SELECT content FROM document ORDER BY id DESC LIMIT 50')

            docs = [row[0] for row in cursor.fetchall()]
            cursor.close()
            conn.close()

            if not docs:
                return "No documents found to analyze topics."

            print("Starting topic analysis...")
            # Find best k value (fewer iterations = faster)
            best_k, coherence_scores = find_best_k(docs, k_range=range(2, 5))
            print(f"Best k found (Elbow Method): {best_k}")

            plot_coherence(coherence_scores, best_k=best_k)
            coherence_image = "/static/coherence_scores.png"

            print(f"Training LDA with k={best_k}...")
            # Run LDA with best k
            lda_results, lda_model, dictionary = get_topics(docs, num_topics=best_k)

            print("Training BERT...")
            # Run BERT (returns embeddings too, for reuse downstream)
            bert_results, bert_kmeans, bert_embeddings = get_bert_topics(docs, get_model(), num_topics=best_k)

            print("Generating Figures...")
            # Generate the new figures
            plot_lda_topics(lda_model, num_topics=best_k)
            tfidf_ranking = plot_tfidf(docs)
            plot_bert_clusters(docs, get_model(), bert_kmeans, embeddings=bert_embeddings)

            print("\n" + "="*60)
            print("🚀 LIVE ANALYSIS REPORT")
            print("="*60)
            print("\n--- TOP TF-IDF KEYWORDS ---")
            for item in tfidf_ranking[:10]:
                print(f"  • {item['term']}: {item['rank']:.4f}")

            print("\n--- LDA TOPIC FINGERPRINTS ---")
            for topic_id, words in lda_results:
                print(f"  • Topic #{topic_id + 1}: {words}")

            print("\n--- BERT CONTEXTUAL CLUSTERS ---")
            for topic_id, words in bert_results:
                print(f"  • Topic #{topic_id + 1}: {words}")
            print("\n" + "="*60 + "\n")

            lda_image = "/static/lda_topics.png"
            tfidf_image = "/static/tfidf_scores.png"
            bert_image = "/static/bert_clusters.png"

            # creating a list of dictionary that include the tag
            # Batch predict BERT topics (much faster than 50 individual encode calls)
            bert_ids = predict_bert_topics_batch(docs, get_model(), bert_kmeans)
            documents_with_tags = []
            for i, content in enumerate(docs):
                lda_id = predict_topic(content, lda_model, dictionary)
                tokens = preprocess(content)
                documents_with_tags.append({
                    "content": content,
                    "tokens": " ".join(tokens),
                    "lda_tag": f"LDA {lda_id + 1}",
                    "bert_tag": f"BERT {bert_ids[i] + 1}"
                })

            print("Rendering template...")
            return render_template('static/topics.html',
                lda_topics=lda_results,
                bert_topics=bert_results,
                documents=documents_with_tags,
                coherence_image=coherence_image,
                lda_image=lda_image,
                tfidf_image=tfidf_image,
                bert_image=bert_image)
    except Exception as e:
        print(f"Error in show_topics: {e}")
        return f'Error: {e}'

    return 'Database connection failed.'

@app.route('/modeling')
def show_modeling():
    conn = db_connection()
    if conn:
        cursor = conn.cursor()
        # Fetch last 50 documents for modeling
        cursor.execute('SELECT content FROM document ORDER BY created_at DESC LIMIT 10')
        docs = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()

        if not docs:
            return "No documents found to analyze."

        # Run Sentiment Modeling
        sentiment_results = get_sentiment_modeling(docs)

        return render_template('static/modeling.html',
            sentiment=sentiment_results,
            total_docs=len(docs))

    return 'Database connection failed.'


if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
