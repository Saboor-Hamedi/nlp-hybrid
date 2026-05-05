from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk

# Ensure VADER lexicon is downloaded
try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    nltk.download('vader_lexicon', quiet=True)

def get_sentiment_modeling(documents):
    """
    Analyzes the sentiment of a list of documents.
    Returns a summary of sentiment distribution.
    """
    sia = SentimentIntensityAnalyzer()
    results = {
        "positive": 0,
        "neutral": 0,
        "negative": 0,
        "details": []
    }
    
    for doc in documents:
        score = sia.polarity_scores(doc)
        compound = score['compound']
        
        if compound >= 0.05:
            label = "Positive"
            results["positive"] += 1
        elif compound <= -0.05:
            label = "Negative"
            results["negative"] += 1
        else:
            label = "Neutral"
            results["neutral"] += 1
            
        results["details"].append({
            "content": doc,
            "score": compound,
            "label": label
        })
        
    return results
