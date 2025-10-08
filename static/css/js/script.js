let currentQuery = '';

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadMetrics();
    loadDocuments();
    
    document.getElementById('search-input').addEventListener('input', debounce(performSearch, 300));
    document.getElementById('ranking-method').addEventListener('change', performSearch);
    document.getElementById('category-filter').addEventListener('change', performSearch);
});

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

async function loadMetrics() {
    try {
        const response = await fetch('/api/metrics');
        const data = await response.json();
        
        document.getElementById('total-docs').textContent = data.total_documents;
        document.getElementById('vocab-size').textContent = data.vocabulary_size;
        document.getElementById('indexed-terms').textContent = data.indexed_terms;
        
        // Update category filter
        const categoryFilter = document.getElementById('category-filter');
        categoryFilter.innerHTML = '<option value="all">All</option>';
        data.categories.forEach(cat => {
            const option = document.createElement('option');
            option.value = cat;
            option.textContent = cat;
            categoryFilter.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading metrics:', error);
    }
}

async function loadDocuments() {
    await performSearch();
}

async function performSearch() {
    const query = document.getElementById('search-input').value;
    const method = document.getElementById('ranking-method').value;
    const category = document.getElementById('category-filter').value;
    
    try {
        const response = await fetch('/api/search', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ query, method, category })
        });
        
        const data = await response.json();
        displayResults(data.results);
        
        document.getElementById('results-count').textContent = data.total;
        document.getElementById('results-text').textContent = `${data.total} document(s) found`;
        
        // Show preprocessed query
        const preprocessedDiv = document.getElementById('preprocessed-query');
        if (query && data.preprocessed_query.length > 0) {
            preprocessedDiv.textContent = `Preprocessed Query: ${data.preprocessed_query.join(', ')}`;
            preprocessedDiv.classList.add('show');
        } else {
            preprocessedDiv.classList.remove('show');
        }
    } catch (error) {
        console.error('Error searching:', error);
    }
}

function displayResults(results) {
    const container = document.getElementById('results');
    
    if (results.length === 0) {
        container.innerHTML = `
            <div class="no-results">
                <h2>📭 No documents found</h2>
                <p>Try different keywords or add more documents</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = results.map(result => {
        const doc = result.document;
        const score = result.score.toFixed(4);
        const matched = result.matched_terms.slice(0, 3).join(', ');
        
        return `
            <div class="result-card">
                <div class="result-header">
                    <div>
                        <div class="result-title">${doc.title}</div>
                        ${score > 0 ? `
                            <div class="result-scores">
                                <span class="score-badge">Score: ${score}</span>
                                ${matched ? `<span class="matched-badge">Matched: ${matched}</span>` : ''}
                            </div>
                        ` : ''}
                    </div>
                    <button class="btn-delete" onclick="deleteDocument(${doc.id})">Delete</button>
                </div>
                
                <div class="result-meta">
                    <span>👤 ${doc.author}</span>
                    <span>📅 ${doc.year}</span>
                    <span>📁 ${doc.category}</span>
                </div>
                
                <div class="result-description">${doc.description}</div>
                
                <div class="result-tags">
                    ${doc.tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
                </div>
            </div>
        `;
    }).join('');
}

function addDocument() {
    document.getElementById('add-form').classList.remove('hidden');
}

function cancelAdd() {
    document.getElementById('add-form').classList.add('hidden');
    clearForm();
}

function clearForm() {
    document.getElementById('new-title').value = '';
    document.getElementById('new-author').value = '';
    document.getElementById('new-year').value = '';
    document.getElementById('new-category').value = '';
    document.getElementById('new-tags').value = '';
    document.getElementById('new-description').value = '';
}

async function submitDocument() {
    const doc = {
        title: document.getElementById('new-title').value,
        author: document.getElementById('new-author').value,
        year: document.getElementById('new-year').value,
        category: document.getElementById('new-category').value,
        tags: document.getElementById('new-tags').value,
        description: document.getElementById('new-description').value
    };
    
    if (!doc.title || !doc.author || !doc.year || !doc.category || !doc.description) {
        alert('Please fill in all required fields');
        return;
    }
    
    try {
        await fetch('/api/documents', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(doc)
        });
        
        cancelAdd();
        loadMetrics();
        performSearch();
    } catch (error) {
        console.error('Error adding document:', error);
    }
}

async function deleteDocument(id) {
    if (!confirm('Are you sure you want to delete this document?')) return;
    
    try {
        await fetch(`/api/documents/${id}`, { method: 'DELETE' });
        loadMetrics();
        performSearch();
    } catch (error) {
        console.error('Error deleting document:', error);
    }
}