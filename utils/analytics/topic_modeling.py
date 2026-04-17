from gensim import corpora 
from gensim.models import LdaModel
from nltk.corpus import stopwords 
from nltk.tokenize import word_tokenize
import nltk 
# Download ncesssary data 
nltk.download('punkt')
nltk.download('stopwords')
def get_topics(documents, num_topics = 10):
    # Pre-processing 
    stop_words = set(stopwords.words('english'))
    texts = [preprocess(doc) for doc in documents]
    # Create dictionary and corpus (Bag of Words)
    dictionary  = corpora.Dictionary(texts)
    corpus = [dictionary.doc2bow(text) for text in texts]
    # Train the LDA model 
    lda_model = LdaModel(corpus=corpus, id2word=dictionary, num_topics=num_topics, passes=10)
    # Get the topics 
    topics = lda_model.print_topics()
    return topics, lda_model, dictionary


def predict_topic(text, lda_model, dictionary):
    # Predict the topic ID FOR  new piece of texst 
    processed_text = preprocess(text)
    # Convert to Bag of Words
    bow = dictionary.doc2bow(processed_text)
    # Get the topic distribution
    topics  = lda_model.get_document_topics(bow)
    # Sort by probability 
    topics.sort(key=lambda x: x[1], reverse=True)
    return topics[0][0] if topics else 0 # return the most probable topic ID 


def preprocess(text):
    stop_words = set(stopwords.words('english'))
    return [
        word for word in word_tokenize(text.lower())
        if word.isalnum() and word not in stop_words
    ]