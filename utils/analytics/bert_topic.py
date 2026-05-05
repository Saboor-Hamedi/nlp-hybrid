from sklearn.cluster import KMeans
import numpy as np
from collections import Counter
from utils.analytics.topic_modeling import preprocess

def get_bert_topics(documents, embedder, num_topics=10):
    """
    Performs topic modeling using BERT embeddings and KMeans clustering.
    Returns:
        - topic_summaries: List of strings describing each topic
        - kmeans_model: The trained KMeans model
    """
    if not documents:
        return [], None

    # 1. Generate Embeddings
    embeddings = embedder.encode(documents, show_progress_bar=False)
    
    # 2. Cluster Embeddings
    kmeans = KMeans(n_clusters=min(num_topics, len(documents)), random_state=42, n_init='auto')
    cluster_labels = kmeans.fit_predict(embeddings)
    
    # 3. Extract Topic Keywords (Simple most frequent words in cluster)
    topic_summaries = []
    for i in range(kmeans.n_clusters):
        # Get documents in this cluster
        cluster_docs = [documents[j] for j, label in enumerate(cluster_labels) if label == i]
        
        # Tokenize and count words
        all_words = []
        for doc in cluster_docs:
            all_words.extend(preprocess(doc))
        
        most_common = Counter(all_words).most_common(5)
        keywords = ", ".join([word for word, count in most_common])
        topic_summaries.append((i, keywords))
        
    return topic_summaries, kmeans

def predict_bert_topic(text, embedder, kmeans_model):
    """Predicts the topic ID for a new piece of text using BERT embeddings."""
    if not kmeans_model:
        return 0
    embedding = embedder.encode([text], show_progress_bar=False)
    prediction = kmeans_model.predict(embedding)
    return int(prediction[0])
