import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import nltk
from gensim import corpora
from gensim.models import CoherenceModel, LdaModel
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

# Download necessary data quietly if not present
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet', quiet=True)


def find_best_k(documents, k_range=range(2, 8), timeout=30):
    """
    Find the best number of topics (k) based on coherence score.

    Args:
        documents: List of documents
        k_range: Range of k values to test (default: 2-7 for speed)
        timeout: Max seconds to spend (not strictly enforced, but limits k_range)

    Returns:
        best_k: Optimal number of topics
        coherence_scores: Dictionary with {k: coherence_score}
    """
    print("Finding best k value using coherence scores...")
    try:
        texts = [preprocess(doc) for doc in documents]
        if not texts:
            print("  No texts to analyze, using k=5")
            return 5, {5: 0.0}

        dictionary = corpora.Dictionary(texts)
        corpus = [dictionary.doc2bow(text) for text in texts]

        if not corpus:
            print("  No corpus, using k=5")
            return 5, {5: 0.0}

        coherence_scores = {}

        for k in k_range:
            try:
                print(f"  Testing k={k}...", end=" ", flush=True)
                lda = LdaModel(corpus=corpus, id2word=dictionary, num_topics=k, passes=5, random_state=42)
                # Use u_mass instead of c_v. u_mass is incredibly fast, does not use multiprocessing, and won't crash your server!
                coherence_model = CoherenceModel(model=lda, corpus=corpus, dictionary=dictionary, coherence='u_mass')
                coherence_score = coherence_model.get_coherence()
                coherence_scores[k] = coherence_score
                print(f"coherence={coherence_score:.4f}")
            except Exception as e:
                print(f"Error at k={k}: {e}")
                continue

        if not coherence_scores:
            print("  Could not calculate coherence, using k=5")
            return 5, {5: 0.0}

        # --- ELBOW DETECTION METHOD ---
        k_vals = list(coherence_scores.keys())
        scores = list(coherence_scores.values())
        
        best_k = k_vals[-1] # Default to max k if no elbow is clear
        
        if len(scores) >= 3:
            max_drop = -float('inf')
            elbow_k = k_vals[0]
            
            # Calculate the second derivative (where the slope flattens the most)
            for i in range(1, len(scores) - 1):
                slope_before = scores[i] - scores[i-1]
                slope_after = scores[i+1] - scores[i]
                drop = slope_before - slope_after
                
                if drop > max_drop:
                    max_drop = drop
                    elbow_k = k_vals[i]
                    
            if max_drop > 0: # Ensures it's a real plateau
                best_k = elbow_k
        else:
            best_k = max(coherence_scores, key=coherence_scores.get)

        print(f"\n✓ Best k={best_k} (Elbow Method) with coherence score: {coherence_scores[best_k]:.4f}\n")
        return best_k, coherence_scores

    except Exception as e:
        print(f"Error in find_best_k: {e}, using k=5")
        return 5, {5: 0.0}


def plot_coherence(coherence_scores, best_k=None):
    """Plot coherence scores across different k values."""
    try:
        k_values = list(coherence_scores.keys())
        scores = list(coherence_scores.values())

        if not k_values or not scores:
            print("No coherence scores to plot")
            return

        if best_k is None:
            best_k = max(coherence_scores, key=coherence_scores.get)
        best_score = coherence_scores[best_k]

        # Make the graph shorter and more beautiful
        plt.figure(figsize=(8, 2.5))
        plt.plot(k_values, scores, marker='o', linestyle='-', color='#4F46E5', linewidth=2.5, markersize=8)
        
        # Highlight the best k value
        plt.plot(best_k, best_score, marker='*', color='#10B981', markersize=14, label=f'Best k = {best_k}')
        
        plt.xlabel('Number of Topics (k)', fontsize=11, fontweight='500', color='#374151')
        plt.ylabel('Coherence Score (u_mass)', fontsize=11, fontweight='500', color='#374151')
        plt.title(f'Optimal Topic Count: k = {best_k}', fontsize=14, fontweight='bold', color='#1F2937', pad=15)
        
        # Clean up borders and add grid
        plt.grid(True, linestyle='--', alpha=0.6, color='#E5E7EB')
        plt.gca().spines['top'].set_visible(False)
        plt.gca().spines['right'].set_visible(False)
        plt.legend(loc='best', frameon=False)

        import os
        os.makedirs('static', exist_ok=True)
        plt.savefig('static/coherence_scores.png', dpi=100, bbox_inches='tight')
        print("✓ Coherence plot saved as 'static/coherence_scores.png'")
        plt.close()
    except Exception as e:
        print(f"Error plotting coherence: {e}")
        plt.close()


def plot_lda_topics(lda_model, num_topics=5):
    """Generate a beautiful bar chart visualization for LDA topics."""
    try:
        topics = lda_model.show_topics(num_topics=num_topics, num_words=10, formatted=False)
        
        # Calculate grid size
        cols = 2
        rows = (num_topics + 1) // cols
        
        plt.figure(figsize=(12, rows * 4))
        
        for i, (topic_id, words) in enumerate(topics):
            plt.subplot(rows, cols, i + 1)
            
            word_names = [w[0] for w in words]
            word_weights = [w[1] for w in words]
            
            # Sort for better visualization
            sorted_indices = np.argsort(word_weights)
            word_names = [word_names[j] for j in sorted_indices]
            word_weights = [word_weights[j] for j in sorted_indices]
            
            plt.barh(word_names, word_weights, color='#6366F1', alpha=0.8)
            plt.title(f'LDA Topic {topic_id + 1}', fontsize=12, fontweight='bold', color='#1F2937')
            plt.grid(axis='x', linestyle='--', alpha=0.4)
            plt.gca().spines['top'].set_visible(False)
            plt.gca().spines['right'].set_visible(False)
        
        plt.tight_layout()
        os.makedirs('static', exist_ok=True)
        plt.savefig('static/lda_topics.png', dpi=100, bbox_inches='tight')
        print("✓ LDA topic plot saved as 'static/lda_topics.png'")
        plt.close()
    except Exception as e:
        print(f"Error plotting LDA topics: {e}")
        plt.close()


def plot_tfidf(documents, top_n=15):
    """Generate a bar chart for the top TF-IDF words across the corpus."""
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        import pandas as pd
        
        # We need a custom tokenizer that uses our preprocess function
        vectorizer = TfidfVectorizer(tokenizer=lambda x: preprocess(x), token_pattern=None)
        tfidf_matrix = vectorizer.fit_transform(documents)
        
        # Sum tfidf weights for each word across all documents
        sums = tfidf_matrix.sum(axis=0)
        
        # Get feature names
        features = vectorizer.get_feature_names_out()
        
        # Create a list of (word, score) tuples
        data = []
        for col, term in enumerate(features):
            data.append((term, sums[0, col]))
            
        ranking = pd.DataFrame(data, columns=['term', 'rank'])
        ranking = ranking.sort_values('rank', ascending=False).head(top_n)
        
        # Plotting
        plt.figure(figsize=(10, 6))
        plt.barh(ranking['term'], ranking['rank'], color='#EC4899', alpha=0.7)
        plt.gca().invert_yaxis()
        plt.title(f'Top {top_n} Terms by TF-IDF Score', fontsize=14, fontweight='bold', color='#1F2937', pad=20)
        plt.xlabel('Cumulative TF-IDF Weight', fontsize=11, color='#4B5563')
        plt.grid(axis='x', linestyle='--', alpha=0.3)
        plt.gca().spines['top'].set_visible(False)
        plt.gca().spines['right'].set_visible(False)
        
        plt.tight_layout()
        os.makedirs('static', exist_ok=True)
        plt.savefig('static/tfidf_scores.png', dpi=100, bbox_inches='tight')
        print("✓ TF-IDF plot saved as 'static/tfidf_scores.png'")
        plt.close()
        plt.close()
        return ranking.to_dict('records')
    except Exception as e:
        print(f"Error plotting TF-IDF: {e}")
        plt.close()
        return []


def get_topics(documents, num_topics=10):
    """Train LDA model and return topics."""
    # Pre-processing
    texts = [preprocess(doc) for doc in documents]
    # Create dictionary and corpus (Bag of Words)
    dictionary = corpora.Dictionary(texts)
    corpus = [dictionary.doc2bow(text) for text in texts]
    # Train the LDA model
    lda_model = LdaModel(corpus=corpus, id2word=dictionary, num_topics=num_topics, passes=10, random_state=42)
    # Get the topics
    topics = lda_model.print_topics()
    return topics, lda_model, dictionary


def predict_topic(text, lda_model, dictionary):
    """Predict the topic ID for a new piece of text."""
    processed_text = preprocess(text)
    # Convert to Bag of Words
    bow = dictionary.doc2bow(processed_text)
    # Get the topic distribution
    topics = lda_model.get_document_topics(bow)
    # Sort by probability
    topics.sort(key=lambda x: x[1], reverse=True)
    return topics[0][0] if topics else 0  # return the most probable topic ID


# Initialize lemmatizer globally for performance
lemmatizer = WordNetLemmatizer()

# Custom academic stop words that add noise to topics
ACADEMIC_STOP_WORDS = {
    'paper', 'study', 'results', 'method', 'conclusion', 'figure', 'table', 
    'et', 'al', 'data', 'using', 'used', 'based', 'approach', 'model', 
    'performance', 'analysis', 'proposed', 'two', 'also', 'one', 'new',
    'different', 'show', 'well', 'may', 'time', 'first', 'research',
    'work', 'can', 'this', 'that', 'we', 'our', 'fig', 'section', 'system'
}

def preprocess(text):
    """Preprocess text for topic modeling (runs strictly in memory)."""
    stop_words = set(stopwords.words('english')).union(ACADEMIC_STOP_WORDS)
    
    processed_words = []
    for word in word_tokenize(text.lower()):
        # Keep words that are alphabetic, >2 chars, and not stop words
        if word.isalpha() and len(word) > 2 and word not in stop_words:
            # Lemmatize (e.g. "computing" -> "compute", "results" -> "result")
            lemma = lemmatizer.lemmatize(word)
            
            # Double check the lemmatized form isn't a stop word
            if lemma not in stop_words:
                processed_words.append(lemma)
                
    return processed_words
