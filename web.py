# This is my flask app web.py
from utils.analytics.topic_modeling import predict_topic
from db.operations.DocumentManager import DocumentManager
from hybrid.hybrid_search import search_hybrid
from utils.cli_handlers import handle_search
from db.db_connection import db_connection, get_model

from flask import Flask, render_template, request

# The main connection to the database 
app = Flask(__name__, template_folder='templates', static_folder='static')
MODEL = get_model()
API_URL= 'http://localhost:5000'  # fast api backend 



# home page 

@app.route('/', methods=['GET', 'POST'])
def home(): 
    query = request.form.get('query') or ''
    # start connection 
    conn = db_connection() 


    if not conn:
        return 'Error: Could not connect to the database.'
    cursor = conn.cursor()
    # This is for foreground
    manager = DocumentManager(conn, cursor, MODEL)
    results = manager.select(limit=10)


    if results:
        # Extract content for topic modeling
        cursor.execute('SELECT content FROM document ORDER BY random() LIMIT 100')
        training_data = [r[0] for r in cursor.fetchall()]
        _,lda_model, dictionary = get_topics(training_data, num_topics=10)

        # Tagging documents with topics

        for doc in results:
            topic_id = predict_topic(doc['content'], lda_model, dictionary)
            doc['tag'] = f'Topic {topic_id + 1}'
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
        manager = DocumentManager(conn, cursor, MODEL)
        result = manager.show(doc_id)
        cursor.close()
        conn.close()
        return render_template('static/show.html', result=result)
    return 'Error: Could not connect to the database.'
# search
@app.route('/search', methods=['GET','POST'])
def search(): 
    query = request.form.get('query') or ('').strip()

    # we validate the input 
    if not query or len(query) < 2:
        return render_template('static/search.html', 
        results=[], query=query, 
        error="Please enter at least 2 characters.")
        # start connection 
    conn = db_connection() 
    if conn: 
        cursor = conn.cursor()
        results, stats = search_hybrid(query, conn, cursor, MODEL)
        cursor.close()
        conn.close()

        # We need to convert the results to dicnationaries format 
        results_dict = []
        for r in results:
            results_dict.append({
                "id": r[0],
                "content": r[1],
                "relevance_score": r[2],
                "language": r[3],
                "created_at": r[4],
            })
        
        return render_template('static/search.html', results=results_dict)
    return 'Error: Could not connect to the database.'
    

#  Topic modeling 
# Add this import at the top
from utils.analytics.topic_modeling import get_topics
@app.route('/topics')
def show_topics():
    conn = db_connection()
    if conn:
        cursor = conn.cursor()
        # Fetch last 100 documents to analyze
        cursor.execute('SELECT content FROM document LIMIT 100')
        docs = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        
        if not docs:
            return "No documents found to analyze topics."

        # Run LDA
        lda_results, lda_model, dictionary = get_topics(docs, num_topics=10)


        # creating a list of dictionary that include the tag 
        documents_with_tags =[]
        for content in docs:
            topic_id = predict_topic(content, lda_model, dictionary)
            documents_with_tags.append({
                "content": content,
                "tag": f"Topic {topic_id + 1}"
            })


        
        return render_template('static/topics.html', 
            topics=lda_results,
            documents=documents_with_tags)
    
    return 'Database connection failed.'


if __name__ == '__main__':
    app.run(debug=True)