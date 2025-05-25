from flask import Flask, render_template, request, jsonify, url_for
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()

app = Flask(__name__, static_folder='static')
engine = create_engine('sqlite:///search_engine.db')
Session = sessionmaker(bind=engine)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search')
def search():
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    
    session = Session()
    # Простой поиск по содержимому и заголовку
    search_query = text("""
        SELECT url, title, content, 
               (CASE 
                   WHEN title LIKE :query THEN 2
                   WHEN content LIKE :query THEN 1
                   ELSE 0
               END) as score
        FROM webpages
        WHERE title LIKE :query OR content LIKE :query
        ORDER BY score DESC
    """)
    
    results = []
    for row in session.execute(search_query, {'query': f'%{query}%'}):
        result = {
            'url': row.url,
            'title': row.title,
            'content': row.content[:200] + '...',  # Показываем только первые 200 символов
            'score': row.score
        }
        results.append(result)
    
    session.close()
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True) 