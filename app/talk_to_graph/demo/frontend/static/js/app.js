// demo/frontend/static/js/app.js

const sparqlEndpoint = 'http://localhost:5001/sparql'; // SPARQL endpoint
const llmEndpoint = 'http://localhost:5002/llm'; // LLM endpoint

document.getElementById('sparqlForm').addEventListener('submit', async (event) => {
    event.preventDefault();
    const query = document.getElementById('sparqlQuery').value;
    const response = await fetch(sparqlEndpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
    });
    const data = await response.json();
    displayResults(data, 'sparqlResults');
});

document.getElementById('llmForm').addEventListener('submit', async (event) => {
    event.preventDefault();
    const query = document.getElementById('llmQuery').value;
    const response = await fetch(llmEndpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
    });
    const data = await response.json();
    displayResults(data, 'llmResults');
});

// Load stats on page load
document.addEventListener('DOMContentLoaded', function() {
    loadStats();
});

async function loadStats() {
    try {
        const response = await fetch('/api/llm/stats');
        const data = await response.json();
        
        if (data.success) {
            const stats = data.stats;
            const statsElement = document.getElementById('stats');
            if (statsElement) {
                let statsHtml = `📊 ${stats.total_items} items in vector database | Status: ${stats.status}`;
                if (stats.collections && stats.collections.length > 0) {
                    statsHtml += '<br><small>';
                    stats.collections.forEach(col => {
                        statsHtml += `${col.name}: ${col.vectors} vectors | `;
                    });
                    statsHtml += '</small>';
                }
                statsElement.innerHTML = statsHtml;
            }
        }
    } catch (error) {
        console.error('Error loading stats:', error);
        const statsElement = document.getElementById('stats');
        if (statsElement) {
            statsElement.innerHTML = '⚠️ Could not load statistics';
        }
    }
}

async function embedDocuments() {
    const button = document.getElementById('embedButton');
    const status = document.getElementById('embedStatus');
    
    if (!button || !status) return;
    
    button.disabled = true;
    button.textContent = '⏳ Embedding...';
    status.textContent = 'This may take a minute...';
    
    try {
        const response = await fetch('/api/llm/embed', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const data = await response.json();
        
        if (data.success) {
            status.innerHTML = `✅ Success! Embedded ${data.result.total_stakeholders} stakeholders from ${data.result.files_processed} files`;
            status.style.color = '#90EE90';
            
            // Reload stats
            setTimeout(loadStats, 1000);
            
            // Clear status after 5 seconds
            setTimeout(() => {
                status.textContent = '';
            }, 5000);
        } else {
            status.innerHTML = `❌ Error: ${data.error}`;
            status.style.color = '#FFB6C1';
        }
        
    } catch (error) {
        status.innerHTML = `❌ Error: ${error.message}`;
        status.style.color = '#FFB6C1';
    } finally {
        button.disabled = false;
        button.textContent = '📦 Embed Documents';
    }
}

function askExample(question) {
    const input = document.getElementById('questionInput');
    if (input) {
        input.value = question;
        sendQuestion();
    }
}

function handleKeyPress(event) {
    if (event.key === 'Enter') {
        sendQuestion();
    }
}

async function sendQuestion() {
    const input = document.getElementById('questionInput');
    const button = document.getElementById('sendButton');
    
    if (!input || !button) {
        console.error('Input or button element not found');
        return;
    }
    
    const question = input.value.trim();
    
    if (!question) {
        alert('Please enter a question');
        return;
    }
    
    // Disable input
    input.disabled = true;
    button.disabled = true;
    button.textContent = 'Processing...';
    
    // Clear previous results and show loading
    const sparqlResults = document.getElementById('sparqlResults');
    const llmResults = document.getElementById('llmResults');
    
    if (sparqlResults) {
        sparqlResults.innerHTML = '<div class="loading">Querying SPARQL graph database</div>';
    }
    if (llmResults) {
        llmResults.innerHTML = '<div class="loading">Querying vector database with LLM</div>';
    }
    
    // Query both endpoints simultaneously
    try {
        await Promise.all([
            querySPARQL(question),
            queryLLM(question)
        ]);
    } catch (error) {
        console.error('Error querying:', error);
    } finally {
        // Re-enable input
        input.disabled = false;
        button.disabled = false;
        button.textContent = 'Ask Both';
        input.focus();
    }
}

async function querySPARQL(question) {
    try {
        const response = await fetch('/api/sparql/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question })
        });
        
        const data = await response.json();
        displaySPARQLResults(data);
        
    } catch (error) {
        console.error('SPARQL query error:', error);
        displaySPARQLError(error.message);
    }
}

async function queryLLM(question) {
    try {
        const response = await fetch('/api/llm/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question })
        });
        
        const data = await response.json();
        displayLLMResults(data);
        
    } catch (error) {
        console.error('LLM query error:', error);
        displayLLMError(error.message);
    }
}

function displayResults(data, resultElementId) {
    const resultElement = document.getElementById(resultElementId);
    resultElement.innerHTML = ''; // Clear previous results
    if (data.results) {
        data.results.forEach(result => {
            const div = document.createElement('div');
            div.textContent = JSON.stringify(result);
            resultElement.appendChild(div);
        });
    } else {
        const div = document.createElement('div');
        div.textContent = 'No results found.';
        resultElement.appendChild(div);
    }
}

function displaySPARQLResults(data) {
    const container = document.getElementById('sparqlResults');
    if (!container) return;
    
    if (!data.success) {
        container.innerHTML = `<div class="error">❌ Error: ${escapeHtml(data.error)}</div>`;
        return;
    }
    
    let html = '<div class="answer">';
    html += `<strong>Answer:</strong><br>${escapeHtml(data.answer)}`;
    html += '<div class="metadata">';
    html += `⏱️ Execution time: ${data.execution_time.toFixed(3)}s<br>`;
    html += `📊 Results: ${data.results ? data.results.length : 0} items`;
    html += '</div></div>';
    
    if (data.sparql_query) {
        html += '<div class="sources">';
        html += '<strong>Generated SPARQL Query:</strong><br>';
        html += `<pre style="overflow-x: auto; padding: 10px; background: white; border-radius: 4px; font-size: 12px;">${escapeHtml(data.sparql_query)}</pre>`;
        html += '</div>';
    }
    
    if (data.thought_process && data.thought_process.length > 0) {
        html += '<div class="sources">';
        html += '<strong>💭 Thought Process:</strong><br>';
        data.thought_process.forEach(thought => {
            html += `<div style="padding: 5px 0;">• ${escapeHtml(thought)}</div>`;
        });
        html += '</div>';
    }
    
    container.innerHTML = html;
}

function displayLLMResults(data) {
    const container = document.getElementById('llmResults');
    if (!container) return;
    
    if (!data.success) {
        container.innerHTML = `<div class="error">❌ Error: ${escapeHtml(data.error)}</div>`;
        return;
    }
    
    let html = '<div class="answer">';
    html += `<strong>Answer:</strong><br>${escapeHtml(data.answer).replace(/\n/g, '<br>')}`;
    html += '<div class="metadata">';
    html += `⏱️ Execution time: ${data.execution_time.toFixed(3)}s<br>`;
    html += `📊 Context used: ${data.context_used} items`;
    html += '</div></div>';
    
    if (data.sources && data.sources.length > 0) {
        html += '<div class="sources">';
        html += '<strong>📚 Sources:</strong><br>';
        data.sources.forEach(source => {
            html += `<div class="source-item">`;
            html += `<strong>${escapeHtml(source.name || source.type)}</strong>`;
            if (source.role) {
                html += ` - ${escapeHtml(source.role)}`;
            }
            html += ` from ${escapeHtml(source.doc_title)} (${escapeHtml(source.relevance)} relevant)<br>`;
            html += `<small>${escapeHtml(source.snippet)}</small>`;
            html += `</div>`;
        });
        html += '</div>';
    }
    
    container.innerHTML = html;
}

function displaySPARQLError(message) {
    const container = document.getElementById('sparqlResults');
    if (container) {
        container.innerHTML = `<div class="error">❌ Error: ${escapeHtml(message)}</div>`;
    }
}

function displayLLMError(message) {
    const container = document.getElementById('llmResults');
    if (container) {
        container.innerHTML = `<div class="error">❌ Error: ${escapeHtml(message)}</div>`;
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}