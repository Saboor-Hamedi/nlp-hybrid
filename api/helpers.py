import re

def parse_lda_keywords(topic_string, top_k=5, min_weight=0.01):
    keywords = {}
    pattern = r'([\d.]+)\*"([^"]+)"'
    for weight, word in re.findall(pattern, topic_string):
        weight_float = float(weight)
        if weight_float >= min_weight and len(word) > 2 and word.isalpha():
            keywords[word] = weight_float
    return dict(sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:top_k])

def parse_bert_keywords(bert_topic_tuple, top_k=5):
    try:
        if isinstance(bert_topic_tuple, (tuple, list)) and len(bert_topic_tuple) > 1:
            keywords_str = bert_topic_tuple[1]
            if isinstance(keywords_str, str):
                words = [w.strip() for w in keywords_str.split(',') if w.strip()]
                filtered_words = [w for w in words if len(w) > 2 and w.isalpha()][:top_k]
                return {word: 1.0 for word in filtered_words}
            elif isinstance(keywords_str, dict):
                return keywords_str
    except Exception as e:
        print(f"Error parsing BERT keywords: {e}")
    return {}
