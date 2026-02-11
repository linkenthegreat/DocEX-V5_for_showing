// demo/frontend/static/js/comparison.js

document.addEventListener('DOMContentLoaded', function() {
    const sparqlButton = document.getElementById('sparql-query-button');
    const llmButton = document.getElementById('llm-query-button');
    const sparqlResultContainer = document.getElementById('sparql-results');
    const llmResultContainer = document.getElementById('llm-results');

    sparqlButton.addEventListener('click', async function() {
        const query = document.getElementById('sparql-query-input').value;
        const response = await fetch('/api/sparql_query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query }),
        });
        const data = await response.json();
        displayResults(data, sparqlResultContainer);
    });

    llmButton.addEventListener('click', async function() {
        const query = document.getElementById('llm-query-input').value;
        const response = await fetch('/api/llm_query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query }),
        });
        const data = await response.json();
        displayResults(data, llmResultContainer);
    });

    function displayResults(data, container) {
        container.innerHTML = ''; // Clear previous results
        if (data.error) {
            container.innerHTML = `<p>Error: ${data.error}</p>`;
        } else {
            const resultsList = document.createElement('ul');
            data.results.forEach(result => {
                const listItem = document.createElement('li');
                listItem.textContent = JSON.stringify(result);
                resultsList.appendChild(listItem);
            });
            container.appendChild(resultsList);
        }
    }
});