/**
 * Enhanced JSON-LD file viewing with agent integration
 * Updated to match API response format
 */

// Preview JSON-LD file
function previewJsonLdFile(filename) {
    console.log('🔍 Previewing JSON-LD file:', filename);
    
    // Encode filename for URL
    const encodedFilename = encodeURIComponent(filename);
    
    fetch(`/api/agent/preview_jsonld/${encodedFilename}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Preview failed: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('✅ Preview data received:', data);
            displayPreviewModal(data);
        })
        .catch(error => {
            console.error('❌ Error previewing JSON-LD file:', error);
            showNotification(`❌ Failed to preview file: ${error.message}`, 'error');
        });
}

// Preview TTL file
function previewTtlFile(filename) {
    console.log('🔍 Previewing TTL file:', filename);
    
    // Encode filename for URL
    const encodedFilename = encodeURIComponent(filename);
    
    fetch(`/api/agent/preview_ttl/${encodedFilename}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`TTL Preview failed: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('✅ TTL Preview data received:', data);
            displayTtlPreviewModal(data);
        })
        .catch(error => {
            console.error('❌ Error previewing TTL file:', error);
            showNotification(`❌ Failed to preview TTL file: ${error.message}`, 'error');
        });
}

// Display JSON-LD preview modal
function displayPreviewModal(data) {
    const modal = document.getElementById('previewModal') || createPreviewModal();
    
    // FIXED: Use correct data structure from API
    const metadata = data.metadata || {};
    const extraction_metadata = {
        extraction_strategy: metadata.extractionStrategy || metadata.extraction_strategy || 'Unknown',
        agent_model: metadata.agentModel || metadata.agent_model || 'Unknown',
        quality_score: metadata.qualityScore || metadata.quality_score || 0.0,
        extraction_confidence: metadata.extractionConfidence || metadata.extraction_confidence || 0.0
    };
    
    const modalContent = `
        <div class="modal-header">
            <h3>📄 ${data.filename}</h3>
            <span class="close-btn" onclick="closePreviewModal()">&times;</span>
        </div>
        <div class="modal-body">
            <!-- Preview Tabs -->
            <div class="preview-tabs">
                <button class="tab-btn active" onclick="switchTab('stakeholders')">
                    👥 Stakeholders (${data.stakeholder_count || 0})
                </button>
                <button class="tab-btn" onclick="switchTab('metadata')">
                    📊 Metadata
                </button>
                <button class="tab-btn" onclick="switchTab('turtle')">
                    🐢 Turtle
                </button>
                <button class="tab-btn" onclick="switchTab('jsonld')">
                    📋 JSON-LD
                </button>
            </div>
            
            <!-- Stakeholders Tab -->
            <div id="stakeholders-tab" class="preview-tab-content active">
                ${data.stakeholders && data.stakeholders.length > 0 ? `
                    <div class="stakeholders-preview-grid">
                        ${data.stakeholders.map((stakeholder, index) => `
                            <div class="stakeholder-preview-card">
                                <div class="stakeholder-name">${stakeholder.name || 'Unknown'}</div>
                                <div class="stakeholder-type">${stakeholder.stakeholderType || 'UNKNOWN'}</div>
                                <div class="stakeholder-details">
                                    <div><strong>Role:</strong> ${stakeholder.role || 'N/A'}</div>
                                    <div><strong>Organization:</strong> ${stakeholder.organization || 'N/A'}</div>
                                    ${stakeholder.confidenceScore ? `
                                        <div><strong>Confidence:</strong> ${(stakeholder.confidenceScore * 100).toFixed(0)}%</div>
                                    ` : ''}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                    ${data.stakeholder_count > data.stakeholders.length ? `
                        <div class="preview-note">
                            Showing ${data.stakeholders.length} of ${data.stakeholder_count} stakeholders.
                            <button onclick="viewFullFile('${data.filename}')" class="btn btn-info">View All</button>
                        </div>
                    ` : ''}
                ` : `
                    <div class="no-content">
                        ⚠️ No stakeholders found in this file
                    </div>
                `}
            </div>
            
            <!-- Metadata Tab -->
            <div id="metadata-tab" class="preview-tab-content">
                <div class="preview-info">
                    <div class="info-grid">
                        <div class="info-item">
                            <strong>Format:</strong> ${data.format || 'JSON-LD'}
                        </div>
                        <div class="info-item">
                            <strong>Triples:</strong> ${data.triple_count || 'Unknown'}
                        </div>
                        <div class="info-item">
                            <strong>Extraction Strategy:</strong> ${extraction_metadata.extraction_strategy}
                        </div>
                        <div class="info-item">
                            <strong>Agent Model:</strong> ${extraction_metadata.agent_model}
                        </div>
                        <div class="info-item">
                            <strong>Quality Score:</strong> 
                            <span class="quality-badge ${getQualityClass(extraction_metadata.quality_score)}">
                                ${(extraction_metadata.quality_score * 100).toFixed(0)}%
                            </span>
                        </div>
                        <div class="info-item">
                            <strong>Has Metadata:</strong> ${data.has_metadata ? '✅ Yes' : '❌ No'}
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Turtle Tab -->
            <div id="turtle-tab" class="preview-tab-content">
                <pre class="code-preview"><code class="language-turtle">${data.turtle_preview || 'No Turtle preview available'}</code></pre>
            </div>
            
            <!-- JSON-LD Tab -->
            <div id="jsonld-tab" class="preview-tab-content">
                <pre class="code-preview"><code class="language-json">${data.jsonld_preview || 'No JSON-LD preview available'}</code></pre>
            </div>
        </div>
        <div class="modal-footer">
            <button onclick="viewFullFile('${data.filename}')" class="btn btn-info">
                📄 View Full Content
            </button>
            <button onclick="downloadFile('${data.filename}')" class="btn btn-success">
                💾 Download
            </button>
            <button onclick="closePreviewModal()" class="btn btn-secondary">
                ✖️ Close
            </button>
        </div>
    `;
    
    modal.innerHTML = modalContent;
    modal.style.display = 'block';
}

// Display TTL preview modal
function displayTtlPreviewModal(data) {
    const modal = document.getElementById('previewModal') || createPreviewModal();
    
    const modalContent = `
        <div class="modal-header">
            <h3>🐢 ${data.filename}</h3>
            <span class="close-btn" onclick="closePreviewModal()">&times;</span>
        </div>
        <div class="modal-body">
            <div class="preview-info">
                <div class="info-grid">
                    <div class="info-item">
                        <strong>📁 Size:</strong> ${data.file_size}
                    </div>
                    <div class="info-item">
                        <strong>🕒 Modified:</strong> ${new Date(data.modified).toLocaleString()}
                    </div>
                    <div class="info-item">
                        <strong>🔗 Triples:</strong> ${data.triple_count}
                    </div>
                    <div class="info-item">
                        <strong>📋 Namespaces:</strong> ${data.namespace_count || 0}
                    </div>
                </div>
            </div>
            
            <div class="content-preview">
                <h4>🐢 Turtle Content Preview</h4>
                <pre class="code-preview"><code class="language-turtle">${data.content_preview}</code></pre>
                <button onclick="viewFullFile('${data.filename}')" class="btn btn-info">
                    View Full Content
                </button>
            </div>
        </div>
        <div class="modal-footer">
            <button onclick="viewFullFile('${data.filename}')" class="btn btn-info">
                📄 View Full Content
            </button>
            <button onclick="closePreviewModal()" class="btn btn-secondary">
                ✖️ Close
            </button>
        </div>
    `;
    
    modal.innerHTML = modalContent;
    modal.style.display = 'block';
}

// Switch between tabs
function switchTab(tabName) {
    // Hide all tab contents
    const tabContents = document.querySelectorAll('.preview-tab-content');
    tabContents.forEach(content => {
        content.classList.remove('active');
    });
    
    // Remove active class from all tab buttons
    const tabButtons = document.querySelectorAll('.tab-btn');
    tabButtons.forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab content
    const selectedTab = document.getElementById(`${tabName}-tab`);
    if (selectedTab) {
        selectedTab.classList.add('active');
    }
    
    // Add active class to clicked tab button
    event.target.classList.add('active');
}

// Create preview modal if it doesn't exist
function createPreviewModal() {
    const modal = document.createElement('div');
    modal.id = 'previewModal';
    modal.className = 'modal extraction-modal';
    modal.style.cssText = `
        display: none;
        position: fixed;
        z-index: 1000;
        left: 0;
        top: 0;
        width: 100%;
        height: 100%;
        overflow: auto;
        background-color: rgba(0,0,0,0.8);
    `;
    
    document.body.appendChild(modal);
    
    // Close modal when clicking outside
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closePreviewModal();
        }
    });
    
    return modal;
}

// Close preview modal
function closePreviewModal() {
    const modal = document.getElementById('previewModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// View full file content
function viewFullFile(filename) {
    console.log('🔍 Requesting full content for:', filename);
    
    const encodedFilename = encodeURIComponent(filename);
    
    fetch(`/api/agent/get_file_content/${encodedFilename}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Content retrieval failed: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            displayFullContentModal(data);
        })
        .catch(error => {
            console.error('❌ Error getting full file content:', error);
            showNotification(`❌ Failed to load full content: ${error.message}`, 'error');
        });
}

// Download file
function downloadFile(filename) {
    console.log('💾 Downloading file:', filename);
    
    const encodedFilename = encodeURIComponent(filename);
    const downloadUrl = `/api/agent/load_jsonld/${encodedFilename}`;
    
    // Create temporary download link
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    showNotification(`💾 Downloading ${filename}...`, 'info');
}

// Display full content modal (keep existing implementation)
function displayFullContentModal(data) {
    const modal = document.getElementById('fullContentModal') || createFullContentModal();
    
    const modalContent = `
        <div class="modal-header">
            <h3>📄 ${data.filename} - Full Content</h3>
            <span class="close-btn" onclick="closeFullContentModal()">&times;</span>
        </div>
        <div class="modal-body full-content">
            <div class="content-info">
                ${data.content_type === 'json' ? `
                    <span class="info-badge">📊 ${data.stakeholder_count} Stakeholders</span>
                ` : data.content_type === 'turtle' ? `
                    <span class="info-badge">🔗 ${data.triple_count} Triples</span>
                ` : ''}
                <button onclick="copyToClipboard('fullContentText')" class="btn btn-info">
                    📋 Copy Content
                </button>
            </div>
            <pre id="fullContentText"><code class="language-${data.content_type}">${data.content}</code></pre>
        </div>
        <div class="modal-footer">
            <button onclick="copyToClipboard('fullContentText')" class="btn btn-info">
                📋 Copy to Clipboard
            </button>
            <button onclick="closeFullContentModal()" class="btn btn-secondary">
                ✖️ Close
            </button>
        </div>
    `;
    
    modal.innerHTML = modalContent;
    modal.style.display = 'block';
}

// Create full content modal (keep existing implementation)
function createFullContentModal() {
    const modal = document.createElement('div');
    modal.id = 'fullContentModal';
    modal.className = 'modal extraction-modal full-content-modal';
    modal.style.cssText = `
        display: none;
        position: fixed;
        z-index: 1001;
        left: 0;
        top: 0;
        width: 100%;
        height: 100%;
        overflow: auto;
        background-color: rgba(0,0,0,0.8);
    `;
    
    document.body.appendChild(modal);
    
    // Close modal when clicking outside
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeFullContentModal();
        }
    });
    
    return modal;
}

// Close full content modal
function closeFullContentModal() {
    const modal = document.getElementById('fullContentModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Get quality class for styling (keep existing)
function getQualityClass(score) {
    if (score >= 0.8) return 'quality-high';
    if (score >= 0.6) return 'quality-medium';
    return 'quality-low';
}

// Copy content to clipboard (keep existing)
function copyToClipboard(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        navigator.clipboard.writeText(element.textContent).then(() => {
            showNotification('✅ Content copied to clipboard!', 'success');
        }).catch(err => {
            console.error('❌ Failed to copy content:', err);
            showNotification('❌ Failed to copy content', 'error');
        });
    }
}

// Show notification (keep existing)
function showNotification(message, type = 'info') {
    let container = document.getElementById('notificationContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notificationContainer';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 2000;
        `;
        document.body.appendChild(container);
    }
    
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.style.cssText = `
        background: ${type === 'error' ? '#ff6b6b' : type === 'success' ? '#51cf66' : '#339af0'};
        color: white;
        padding: 12px 20px;
        border-radius: 4px;
        margin-bottom: 10px;
        max-width: 300px;
        word-wrap: break-word;
    `;
    notification.textContent = message;
    
    container.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closePreviewModal();
        closeFullContentModal();
    }
});

console.log('✅ Enhanced JSON-LD viewer loaded with API integration');