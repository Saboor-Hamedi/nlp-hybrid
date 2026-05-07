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


def plot_bert_clusters(documents, embedder, kmeans_model):
    """Visualize BERT clusters using PCA for 2D dimensionality reduction."""
    try:
        import matplotlib.pyplot as plt
        from sklearn.decomposition import PCA
        import os
        
        # 1. Generate Embeddings
        embeddings = embedder.encode(documents, show_progress_bar=False)
        
        # 2. Reduce to 2D
        pca = PCA(n_components=2, random_state=42)
        reduced_embeddings = pca.fit_transform(embeddings)
        
        # 3. Get labels
        labels = kmeans_model.predict(embeddings)
        
        # 4. Plot
        plt.figure(figsize=(10, 7))
        scatter = plt.scatter(reduced_embeddings[:, 0], reduced_embeddings[:, 1], 
                            c=labels, cmap='viridis', alpha=0.6, s=50)
        
        plt.title('BERT Topic Clusters (PCA 2D Projection)', fontsize=14, fontweight='bold', color='#1F2937')
        plt.xlabel('Principal Component 1', fontsize=11, color='#4B5563')
        plt.ylabel('Principal Component 2', fontsize=11, color='#4B5563')
        
        # Add legend
        legend = plt.legend(*scatter.legend_elements(), title="Topics", loc="best")
        plt.gca().add_artist(legend)
        
        plt.grid(True, linestyle='--', alpha=0.3)
        plt.gca().spines['top'].set_visible(False)
        plt.gca().spines['right'].set_visible(False)
        
        plt.tight_layout()
        os.makedirs('static', exist_ok=True)
        plt.savefig('static/bert_clusters.png', dpi=100, bbox_inches='tight')
        print("✓ BERT cluster plot saved as 'static/bert_clusters.png'")
        plt.close()
    except Exception as e:
        print(f"Error plotting BERT clusters: {e}")
        if 'plt' in locals():
            plt.close()
