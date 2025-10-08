from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import json
import re
from collections import defaultdict
import math

app = Flask(__name__)
CORS(app)

# Simple stopwords list
STOPWORDS = {
    'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
    'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
    'to', 'was', 'will', 'with', 'this', 'but', 'they', 'have', 'had'
}

# Sample document collection
DOCUMENTS = [
    {
        "id": 1,
        "title": "Introduction to Information Retrieval",
        "author": "Manning, Raghavan, Schütze",
        "year": 2008,
        "category": "Computer Science",
        "tags": ["IR", "NLP", "Search"],
        "description": "Comprehensive guide to information retrieval covering indexing, query processing, and ranking algorithms. Topics include boolean retrieval, vector space model, probabilistic models, and evaluation metrics."
    },
    {
        "id": 2,
        "title": "Modern Information Retrieval",
        "author": "Baeza-Yates, Ribeiro-Neto",
        "year": 2011,
        "category": "Computer Science",
        "tags": ["IR", "Web Search", "Data Mining"],
        "description": "Advanced topics in information retrieval including web search, multimedia retrieval, and machine learning approaches. Covers crawling, indexing, and ranking at scale."
    },
    {
        "id": 3,
        "title": "Search Engines: Information Retrieval in Practice",
        "author": "Croft, Metzler, Strohman",
        "year": 2015,
        "category": "Computer Science",
        "tags": ["Search Engines", "Web", "Algorithms"],
        "description": "Practical approach to building and understanding search engines. Discusses evaluation methods, query optimization, and user interaction with search systems."
    },
    {
        "id": 4,
        "title": "The Art of Computer Programming",
        "author": "Donald Knuth",
        "year": 1968,
        "category": "Computer Science",
        "tags": ["Algorithms", "Programming", "Classic"],
        "description": "Fundamental algorithms and computer science concepts. Covers sorting, searching, and data structures with mathematical analysis."
    },
    {
        "id": 5,
        "title": "Natural Language Processing with Python",
        "author": "Bird, Klein, Loper",
        "year": 2009,
        "category": "Computer Science",
        "tags": ["NLP", "Python", "NLTK"],
        "description": "Introduction to NLP using Python and NLTK. Covers text processing, classification, tokenization, and information extraction techniques."
    }
]

class IRSystem:
    def __init__(self, documents):
        self.documents = documents
        self.inverted_index = {}
        self.doc_tokens = {}
        self.vocabulary = set()
        self.build_index()
    
    def tokenize(self, text):
        """Simple tokenization"""
        return re.findall(r'\w+', text.lower())
    
    def stem(self, word):
        """Simple stemming"""
        if len(word) <= 3:
            return word
        if word.endswith('ing'):
            return word[:-3]
        if word.endswith('ed'):
            return word[:-2]
        if word.endswith('s'):
            return word[:-1]
        return word
    
    def preprocess(self, text):
        """Tokenize, remove stopwords, and stem"""
        tokens = self.tokenize(text)
        tokens = [self.stem(token) for token in tokens if token not in STOPWORDS]
        return tokens
    
    def build_index(self):
        """Build inverted index"""
        for doc in self.documents:
            content = f"{doc['title']} {doc['description']} {' '.join(doc['tags'])}"
            tokens = self.preprocess(content)
            self.doc_tokens[doc['id']] = tokens
            
            for token in set(tokens):
                self.vocabulary.add(token)
                if token not in self.inverted_index:
                    self.inverted_index[token] = []
                self.inverted_index[token].append(doc['id'])
    
    def calculate_tf(self, term, tokens):
        """Calculate term frequency"""
        count = tokens.count(term)
        return count / len(tokens) if tokens else 0
    
    def calculate_idf(self, term):
        """Calculate inverse document frequency"""
        docs_with_term = len(self.inverted_index.get(term, []))
        return math.log((len(self.documents) + 1) / (docs_with_term + 1)) + 1
    
    def calculate_tfidf_vector(self, tokens):
        """Calculate TF-IDF vector for tokens"""
        vector = {}
        for term in self.vocabulary:
            tf = self.calculate_tf(term, tokens)
            idf = self.calculate_idf(term)
            vector[term] = tf * idf
        return vector
    
    def cosine_similarity(self, vec1, vec2):
        """Calculate cosine similarity between two vectors"""
        dot_product = sum(vec1.get(term, 0) * vec2.get(term, 0) for term in self.vocabulary)
        mag1 = math.sqrt(sum(val ** 2 for val in vec1.values()))
        mag2 = math.sqrt(sum(val ** 2 for val in vec2.values()))
        
        if mag1 == 0 or mag2 == 0:
            return 0
        return dot_product / (mag1 * mag2)
    
    def bm25_score(self, query_tokens, doc_id, k1=1.5, b=0.75):
        """Calculate BM25 score"""
        doc_tokens = self.doc_tokens[doc_id]
        doc_length = len(doc_tokens)
        avg_doc_length = sum(len(tokens) for tokens in self.doc_tokens.values()) / len(self.doc_tokens)
        
        score = 0
        for term in query_tokens:
            if term not in doc_tokens:
                continue
            
            term_freq = doc_tokens.count(term)
            docs_with_term = len(self.inverted_index.get(term, []))
            idf = math.log((len(self.documents) - docs_with_term + 0.5) / (docs_with_term + 0.5) + 1)
            
            numerator = term_freq * (k1 + 1)
            denominator = term_freq + k1 * (1 - b + b * (doc_length / avg_doc_length))
            score += idf * (numerator / denominator)
        
        return score
    
    def search(self, query, method='tfidf', category='all'):
        """Search documents using specified ranking method"""
        query_tokens = self.preprocess(query)
        
        if not query_tokens:
            return []
        
        # Get candidate documents
        candidate_ids = set()
        for token in query_tokens:
            if token in self.inverted_index:
                candidate_ids.update(self.inverted_index[token])
        
        # Score documents
        results = []
        for doc_id in candidate_ids:
            doc = next((d for d in self.documents if d['id'] == doc_id), None)
            if not doc:
                continue
            
            if category != 'all' and doc['category'] != category:
                continue
            
            if method == 'tfidf':
                query_vec = self.calculate_tfidf_vector(query_tokens)
                doc_vec = self.calculate_tfidf_vector(self.doc_tokens[doc_id])
                score = self.cosine_similarity(query_vec, doc_vec)
            else:  # bm25
                score = self.bm25_score(query_tokens, doc_id)
            
            matched_terms = [token for token in query_tokens if token in self.doc_tokens[doc_id]]
            
            results.append({
                'document': doc,
                'score': score,
                'matched_terms': matched_terms
            })
        
        # Sort by score
        results.sort(key=lambda x: x['score'], reverse=True)
        return results

# Initialize IR system
ir_system = IRSystem(DOCUMENTS)

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/api/documents', methods=['GET'])
def get_documents():
    """Get all documents"""
    return jsonify({
        'documents': DOCUMENTS,
        'total': len(DOCUMENTS)
    })

@app.route('/api/search', methods=['POST'])
def search():
    """Search documents"""
    data = request.json
    query = data.get('query', '')
    method = data.get('method', 'tfidf')
    category = data.get('category', 'all')
    
    if not query:
        # Return all documents if no query
        filtered = DOCUMENTS if category == 'all' else [d for d in DOCUMENTS if d['category'] == category]
        return jsonify({
            'results': [{'document': d, 'score': 0, 'matched_terms': []} for d in filtered],
            'total': len(filtered),
            'preprocessed_query': []
        })
    
    results = ir_system.search(query, method, category)
    preprocessed = ir_system.preprocess(query)
    
    return jsonify({
        'results': results,
        'total': len(results),
        'preprocessed_query': preprocessed
    })

@app.route('/api/documents', methods=['POST'])
def add_document():
    """Add a new document"""
    data = request.json
    new_id = max(doc['id'] for doc in DOCUMENTS) + 1
    
    new_doc = {
        'id': new_id,
        'title': data['title'],
        'author': data['author'],
        'year': int(data['year']),
        'category': data['category'],
        'tags': [tag.strip() for tag in data.get('tags', '').split(',') if tag.strip()],
        'description': data['description']
    }
    
    DOCUMENTS.append(new_doc)
    
    # Rebuild index
    global ir_system
    ir_system = IRSystem(DOCUMENTS)
    
    return jsonify({'success': True, 'document': new_doc})

@app.route('/api/documents/<int:doc_id>', methods=['DELETE'])
def delete_document(doc_id):
    """Delete a document"""
    global DOCUMENTS
    DOCUMENTS = [d for d in DOCUMENTS if d['id'] != doc_id]
    
    # Rebuild index
    global ir_system
    ir_system = IRSystem(DOCUMENTS)
    
    return jsonify({'success': True})

@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """Get system metrics"""
    return jsonify({
        'total_documents': len(DOCUMENTS),
        'vocabulary_size': len(ir_system.vocabulary),
        'indexed_terms': len(ir_system.inverted_index),
        'categories': list(set(doc['category'] for doc in DOCUMENTS))
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)