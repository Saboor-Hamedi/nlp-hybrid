Name: Abdul Saboor Hamedi
NIM: 241012050123
Class: Regular B
Subject: ADVANCED NLP
Analysis Report: Evolution of Text Representation and Embedding Techniques
1. Introduction
Natural Language Processing (NLP) is a research field where language is processed to understand its syntactic, semantic, and sentimental aspects. The advancement of NLP has facilitated solutions in domains such as Neural Machine Translation, Sentiment Analysis, and Chatbots. Broadly, NLP consists of two main steps: the representation of input text (raw data) into a numerical format, such as vectors or matrices, and the design of models for processing that numerical data. This report surveys the evolution from rule-based and statistical methods to more context-sensitive learned representations.

2. Rule-Based and Statistical Encoding
Early NLP began with exact matching techniques like Context-Free Grammar (CFG), which relied on complex, hand-composed logical rules. However, these were often rigid, time-consuming, and error-prone due to the ambiguous nature of natural language.
2.1 Discrete Space Representations
Statistical approaches emerged to address these limitations by focusing on word frequency to reduce arbitrary text into fixed-length lists of numbers.
•	One-Hot Encoding (OHE): Represents words in a "word-term" matrix where only one index is marked as '1' to indicate a word's presence. While it retains word order and allows for original text reconstruction, it ignores context and results in sparse, high-dimensional matrices.
•	Bag of Words (BoW): A concise representation where each row is a sentence and columns represent unique vocabulary words. It enables document similarity scoring but ignores word order and fails to comprehend semantic information like synonyms.
•	N-Grams: Captures multi-word tokens within a fixed "window" to retain meaning implicit in word ordering (e.g., "not playing" vs. "not" and "playing" separately).
•	TF-IDF (Term Frequency-Inverse Document Frequency): This metric upscales unique, important words that help classify a document while penalizing common words prevalent across the corpus.

3. Dimensionality Reduction Techniques (DRT)
To overcome the "curse of dimensionality" and data sparsity in discrete representations, DRTs find a new space where data is expressed with fewer features and minimal information loss.
•	Feature Selection: Terms are sorted based on criteria like Document Frequency (DF), Term-Frequency Variance (TFV), or Information Gain (IG), and non-influential terms are discarded.
•	Feature Transformation: Linear transformations map original dimensions to a lower space.
o	Latent Semantic Indexing (LSI): Uses Singular Value Decomposition (SVD) to derive "topic vectors" from co-occurring words, effectively resolving synonym issues.
o	Probabilistic LSI (PLSI): A generative model that accounts for polysemy by associating latent context variables with word occurrences.
o	Latent Dirichlet Allocation (LDA): A non-linear statistical algorithm that models documents as random mixtures of latent topics, generalizing better to unseen data than PLSI.
________________________________________
4. Case Study: The TF-IDF Digital Fingerprint
The following implementation demonstrates how a collection of words (corpus) is translated into a mathematical map. Each list represents the unique "weight" of the vocabulary [bird, cat, dog, mouse].
4.1 Corpus and Numerical Scores
Document Content	TF-IDF Numeric Vector
cat dog mouse	[0.0, 0.5386, 0.5958, 0.5958]
dog dog cat	[0.0, 0.4119, 0.9112, 0.0]
mouse bird	[0.6706, 0.0, 0.0, 0.7418]
bird cat	[0.7071, 0.7071, 0.0, 0.0]
dog mouse bird	[0.5386, 0.0, 0.5958, 0.5958]
cat bird	[0.7071, 0.7071, 0.0, 0.0]
mouse cat	[0.0, 0.6706, 0.0, 0.7418]
dog dog	[0.0, 0.0, 1.0, 0.0]
bird bird	[1.0, 0.0, 0.0, 0.0]
cat dog mouse bird	[0.4742, 0.4742, 0.5245, 0.5245]
4.2 Resultant Matrix Representation
Python
[[0.0, 0.5386, 0.5958, 0.5958],
 [0.0, 0.4119, 0.9112, 0.0],
 [0.6706, 0.0, 0.0, 0.7418],
 [0.7071, 0.7071, 0.0, 0.0],
 [0.5386, 0.0, 0.5958, 0.5958],
 [0.7071, 0.7071, 0.0, 0.0],
 [0.0, 0.6706, 0.0, 0.7418],
 [0.0, 0.0, 1.0, 0.0],
 [1.0, 0.0, 0.0, 0.0],
 [0.4742, 0.4742, 0.5245, 0.5245]]
docs
= [

  "Artificial intelligence is transforming the modern world.",

  "Machine learning algorithms require large amounts of data.",

  "Natural language processing helps computers understand human
text.",

  "Feature extraction is a critical step in data science.",

  "Python is the most popular language for AI development.",

  "Neural networks are inspired by the human brain structure.",

  "Data scientists use statistics to find patterns in
datasets.",

  "Large language models can generate realistic human
conversation.",

  "Deep learning is a subset of machine learning technology.",

  "The future of technology depends on responsible AI
development."
]

Doc 2
Dictionary:
{'ai': np.float64(0.0), 'algorithms':
np.float64(0.39922678978566695), 'amounts': np.float64(0.39922678978566695),
'are': np.float64(0.0), 'artificial': np.float64(0.0), 'brain':
np.float64(0.0), 'by': np.float64(0.0), 'can': np.float64(0.0), 'computers':
np.float64(0.0), 'conversation': np.float64(0.0), 'critical': np.float64(0.0),
'data': np.float64(0.29691673564864024), 'datasets': np.float64(0.0), 'deep':
np.float64(0.0), 'depends': np.float64(0.0), 'development': np.float64(0.0),
'extraction': np.float64(0.0), 'feature': np.float64(0.0), 'find':
np.float64(0.0), 'for': np.float64(0.0), 'future': np.float64(0.0), 'generate':
np.float64(0.0), 'helps': np.float64(0.0), 'human': np.float64(0.0), 'in':
np.float64(0.0), 'inspired': np.float64(0.0), 'intelligence': np.float64(0.0),
'is': np.float64(0.0), 'language': np.float64(0.0), 'large':
np.float64(0.3393792446687549), 'learning': np.float64(0.3393792446687549),
'machine': np.float64(0.3393792446687549), 'models': np.float64(0.0), 'modern':
np.float64(0.0), 'most': np.float64(0.0), 'natural': np.float64(0.0),
'networks': np.float64(0.0), 'neural': np.float64(0.0), 'of':
np.float64(0.29691673564864024), 'on': np.float64(0.0), 'patterns':
np.float64(0.0), 'popular': np.float64(0.0), 'processing': np.float64(0.0),
'python': np.float64(0.0), 'realistic': np.float64(0.0), 'require':
np.float64(0.39922678978566695), 'responsible': np.float64(0.0), 'science':
np.float64(0.0), 'scientists': np.float64(0.0), 'statistics': np.float64(0.0),
'step': np.float64(0.0), 'structure': np.float64(0.0), 'subset':
np.float64(0.0), 'technology': np.float64(0.0), 'text': np.float64(0.0), 'the':
np.float64(0.0), 'to': np.float64(0.0), 'transforming': np.float64(0.0),
'understand': np.float64(0.0), 'use': np.float64(0.0), 'world': np.float64(0.0)}
Key
Takeaways from the Scores
·       The "Heavy Hitters" (Score ~0.40):
Words like 'algorithms', 'amounts', and 'require' have the highest scores
(0.3992). This is because they are unique to this document. They are the
"keywords" that define what this specific sentence is about.
·       The "Shared" Words (Score ~0.30):
Words like 'learning' and 'large' have slightly lower scores (0.3393). This
happens because these words likely appear in other sentences in 10-document
set. Since they aren’t "exclusive" to this sentence, the computer
gives them a little less credit.
·       The "Background Noise" (Score 0.0):
The vast majority of the dictionary is 0.0. This simply means those words (like
'brain', 'python', or 'networks')

5. Feature Extraction in Technology Datasets
Extending this to a modern technology corpus provides deeper insight into feature weighting and dictionary mapping.
5.1 Document Example
Document 2: "Machine learning algorithms require large amounts of data."
Dictionary Result:
{'ai': 0.0, 'algorithms': 0.3992, 'amounts': 0.3992, 'data': 0.2969, 'large': 0.3394, 'learning': 0.3394, 'machine': 0.3394, 'of': 0.2969, ...}
5.2 Score Interpretations
•	The "Heavy Hitters" (Score ~0.40): Words such as 'algorithms', 'amounts', and 'require' define the specific theme of this document.
•	The "Shared" Words (Score ~0.30): Words like 'learning' and 'large' appear in other sentences in the 10-document set, receiving less credit because they are not exclusive.
•	Background Noise (Score 0.0): Words not appearing in this sentence (e.g., 'brain', 'python') receive no weight.
•	Precision (np.float64): High-precision decimal numbers are used to ensure mathematical accuracy when calculating differences between similar sentences.


6. Neural Network and Contextual Representations
Neural network-based techniques automatically deduce features, alleviating the need for manual feature engineering. These mappings occur in a continuous vector space where word meanings (literal and implied) are represented using dense floating-point values.
•	Static Embeddings: Models like Word2Vec, GloVe, and FastText provide fixed representations regardless of context.
•	Dynamic (Contextual) Embeddings: Advanced models like ELMo, GPT, and BERT generate dynamic embeddings that change based on surrounding words, successfully modeling polysemy.
•	Fine-Tuning Approaches: Models are pre-trained on large-scale general corpora and then refined for specific tasks. This includes Cross-Lingual, Knowledge-Enriched (integrating external facts like Wikidata), Domain-Specific (e.g., BioBERT), and Multi-Modal (integrating audio or visual data) embeddings.

7. Conclusion
The field of text representation has progressed from simple keyword matching to high-dimensional contextual maps. While current embeddings capture deep semantic and syntactic relationships, challenges remain regarding task-specific performance, bias, and interpretability.

