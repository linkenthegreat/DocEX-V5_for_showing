// Add this to the main.py or create a separate preview.js file:

/**
 * Preview JSON-LD file content
 * @param {string} filename - The JSON-LD filename to preview
 */
async function previewJsonLdFile(filename) {
    console.log(`👁️ Previewing JSON-LD file: ${filename}`);
    
    try {
        // Call the preview API
        const response = await fetch(`/api/agent/preview_jsonld/${encodeURIComponent(filename)}`);
        
        if (!response.ok) {
            throw new Error(`Preview failed: ${response.statusText}`);
        }
        
        const previewData = await response.json();
        
        // Open preview modal
        openPreviewModal(previewData);
        
    } catch (error) {
        console.error('❌ Error previewing JSON-LD file:', error);
        alert(`❌ Failed to preview file: ${error.message}`);
    }
}

/**
 * Open preview modal with JSON-LD data
 */
function openPreviewModal(previewData) {
    // Create modal HTML
    const modalHTML = `
        <div id="previewModal" class="extraction-modal show" style="display: flex;">
            <div class="modal-content" style="max-width: 90vw; max-height: 90vh; width: 1000px;">
                <div class="modal-header">
                    <h3>👁️ JSON-LD Preview: ${previewData.filename}</h3>
                    <span class="close-btn" onclick="closePreviewModal()">&times;</span>
                </div>
                
                <div class="modal-body" style="overflow-y: auto;">
                    <!-- File Info -->
                    <div class="preview-info">
                        <div class="info-grid">
                            <div class="info-item">
                                <strong>Format:</strong> ${previewData.format}
                            </div>
                            <div class="info-item">
                                <strong>Triples:</strong> ${previewData.triple_count}
                            </div>
                            <div class="info-item">
                                <strong>Stakeholders:</strong> ${previewData.stakeholder_count}
                            </div>
                            <div class="info-item">
                                <strong>Has Metadata:</strong> ${previewData.has_metadata ? 'Yes' : 'No'}
                            </div>
                        </div>
                    </div>
                    
                    <!-- Tabs -->
                    <div class="preview-tabs">
                        <button class="tab-btn active" onclick="showPreviewTab('stakeholders')">📋 Stakeholders</button>
                        <button class="tab-btn" onclick="showPreviewTab('metadata')">📊 Metadata</button>
                        <button class="tab-btn" onclick="showPreviewTab('turtle')">🐢 Turtle</button>
                        <button class="tab-btn" onclick="showPreviewTab('jsonld')">📄 JSON-LD</button>
                    </div>
                    
                    <!-- Stakeholders Tab -->
                    <div id="stakeholdersTab" class="preview-tab-content active">
                        <h4>📋 Stakeholders Preview</h4>
                        ${generateStakeholdersPreview(previewData.stakeholders)}
                    </div>
                    
                    <!-- Metadata Tab -->
                    <div id="metadataTab" class="preview-tab-content">
                        <h4>📊 Extraction Metadata</h4>
                        <pre class="code-preview">${JSON.stringify(previewData.metadata, null, 2)}</pre>
                    </div>
                    
                    <!-- Turtle Tab -->
                    <div id="turtleTab" class="preview-tab-content">
                        <h4>🐢 RDF Turtle Format</h4>
                        <pre class="code-preview">${previewData.turtle_preview}${previewData.turtle_preview.length >= 2000 ? '\n\n... (truncated)' : ''}</pre>
                    </div>
                    
                    <!-- JSON-LD Tab -->
                    <div id="jsonldTab" class="preview-tab-content">
                        <h4>📄 JSON-LD Source</h4>
                        <pre class="code-preview">${previewData.jsonld_preview}${previewData.jsonld_preview.length >= 2000 ? '\n\n... (truncated)' : ''}</pre>
                    </div>
                </div>
                
                <div class="modal-footer">
                    <button class="btn btn-info" onclick="openDetailedReviewModal('${previewData.filename}')">
                        ✏️ Edit & Review
                    </button>
                    <button class="btn btn-success" onclick="downloadJsonLd('${previewData.filename}')">
                        💾 Download
                    </button>
                    <button class="btn btn-secondary" onclick="closePreviewModal()">
                        Close
                    </button>
                </div>
            </div>
        </div>
    `;
    
    // Add modal to page
    document.body.insertAdjacentHTML('beforeend', modalHTML);
}

/**
 * Generate stakeholders preview HTML
 */
function generateStakeholdersPreview(stakeholders) {
    if (!stakeholders || stakeholders.length === 0) {
        return '<p class="no-content">No stakeholders found in this document.</p>';
    }
    
    let html = '<div class="stakeholders-preview-grid">';
    
    stakeholders.forEach((stakeholder, index) => {
        html += `
            <div class="stakeholder-preview-card">
                <div class="stakeholder-name">${stakeholder.name || 'Unknown'}</div>
                <div class="stakeholder-type">${stakeholder.stakeholderType || stakeholder.type || 'Unknown'}</div>
                <div class="stakeholder-details">
                    <div><strong>Role:</strong> ${stakeholder.role || 'Not specified'}</div>
                    <div><strong>Organization:</strong> ${stakeholder.organization || 'Not specified'}</div>
                    ${stakeholder.confidenceScore ? `<div><strong>Confidence:</strong> ${(stakeholder.confidenceScore * 100).toFixed(0)}%</div>` : ''}
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    
    if (stakeholders.length >= 5) {
        html += '<p class="preview-note">Showing first 5 stakeholders. Use Edit & Review for full list.</p>';
    }
    
    return html;
}

/**
 * Show specific preview tab
 */
function showPreviewTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.preview-tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active from all buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab
    const targetTab = document.getElementById(`${tabName}Tab`);
    if (targetTab) {
        targetTab.classList.add('active');
    }
    
    // Activate button
    event.target.classList.add('active');
}

/**
 * Close preview modal
 */
function closePreviewModal() {
    const modal = document.getElementById('previewModal');
    if (modal) {
        modal.remove();
    }
}

/**
 * Download JSON-LD file
 */
function downloadJsonLd(filename) {
    const link = document.createElement('a');
    link.href = `/api/agent/load_jsonld/${encodeURIComponent(filename)}`;
    link.download = filename;
    link.click();
}

// Make preview functions globally available
window.previewJsonLdFile = previewJsonLdFile;
window.openPreviewModal = openPreviewModal;
window.showPreviewTab = showPreviewTab;
window.closePreviewModal = closePreviewModal;
window.downloadJsonLd = downloadJsonLd;

console.log('👁️ JSON-LD preview functionality loaded');