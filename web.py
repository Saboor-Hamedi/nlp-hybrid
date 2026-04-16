# This is my flask app web.py
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
    if conn: 
        cursor = conn.cursor()
        cursor.execute('SELECT id, content, created_at, language FROM document ORDER BY RANDOM() LIMIT 10')
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('static/search.html', results=results, query=query)
    return 'Error: Could not connect to the database.'


@app.route('/search', methods=['GET','POST'])

def search(): 
    query = request.form.get('query') or ''
    # start connection 
    conn = db_connection() 
    if conn: 
        cursor = conn.cursor()
        results, stats = search_hybrid(query, conn, cursor, MODEL)

        cursor.close()
        conn.close()
        
        return render_template('static/search.html', results=results)
    return 'Error: Could not connect to the database.'
    


if __name__ == '__main__':
    app.run(debug=True)