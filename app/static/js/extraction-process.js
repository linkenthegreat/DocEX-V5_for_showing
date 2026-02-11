/**
 * DocEX Extraction Process Management
 * Handles API calls, status polling, and result processing
 */

// Import utility functions if not already available
if (typeof window.getConfidenceClass === 'undefined') {
    console.warn('⚠️ getConfidenceClass not found, defining fallback');
    window.getConfidenceClass = function(score) {
        if (score >= 0.8) return 'confidence-high';
        if (score >= 0.6) return 'confidence-medium';
        if (score >= 0.4) return 'confidence-low';
        return 'confidence-very-low';
    };
}

if (typeof window.showNotification === 'undefined') {
    console.warn('⚠️ showNotification not found, defining fallback');
    window.showNotification = function(message, type = 'info') {
        console.log(`${type.toUpperCase()}: ${message}`);
        alert(`${message}`);
    };
}

if (typeof window.formatConfidence === 'undefined') {
    window.formatConfidence = function(score) {
        if (typeof score !== 'number' || isNaN(score)) return 'N/A';
        return `${Math.round(score * 100)}%`;
    };
}

/**
 * DocEX Extraction Process Functions
 * Handles the actual extraction workflow and API calls
 */

/**
 * Start the extraction process
 */
async function startExtraction() {
    const filename = window.ModalState.currentFilename;
    const priority = document.getElementById('extractionPriority')?.value || 'cost';
    const useContext = document.getElementById('useContext')?.checked || false;
    const detailedOutput = document.getElementById('detailedOutput')?.checked || false;
    
    if (!filename) {
        showErrorAlert('❌ No filename specified for extraction');
        return;
    }
    
    console.log(`🚀 Starting extraction: ${filename} (${priority})`);
    
    window.ModalState.extractionInProgress = true;
    window.ModalState.startTime = new Date();
    
    // Show progress phase
    showExtractionPhase('extractionProgress');
    
    try {
        // Start extraction job
        const startResponse = await fetch('/api/agent/extract', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                filename: filename,
                priority: priority,
                use_context: useContext,
                detailed_output: detailedOutput
            })
        });
        
        if (!startResponse.ok) {
            throw new Error(`Failed to start extraction: ${startResponse.statusText}`);
        }
        
        const startData = await startResponse.json();
        const jobId = startData.job_id;
        
        console.log(`✅ Extraction job started: ${jobId}`);
        window.ModalState.currentJobId = jobId;
        
        // Start polling for progress
        await pollExtractionProgress(jobId);
        
    } catch (error) {
        console.error('❌ Extraction failed:', error);
        displayExtractionError(`Failed to start extraction: ${error.message}`);
        window.ModalState.extractionInProgress = false;
        stopProgressAnimation();
    }
}

/**
 * Poll extraction progress until completion
 */
async function pollExtractionProgress(jobId) {
    const pollInterval = 2000; // Poll every 2 seconds
    let polling = true;
    
    while (polling && window.ModalState.extractionInProgress) {
        try {
            const response = await fetch(`/api/agent/extract/${jobId}/status`);
            
            if (!response.ok) {
                throw new Error(`Failed to get status: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            // Update progress UI
            updateProgressDisplay(data);
            
            // Check if job is complete
            if (data.status === 'complete') {
                polling = false;
                await handleExtractionComplete(jobId);
            } else if (data.status === 'error') {
                polling = false;
                displayExtractionError(data.error || 'Unknown extraction error');
            }
            
            // Wait before next poll
            if (polling) {
                await new Promise(resolve => setTimeout(resolve, pollInterval));
            }
            
        } catch (error) {
            console.error('❌ Error polling extraction status:', error);
            polling = false;
            displayExtractionError(`Status polling error: ${error.message}`);
        }
    }
}

/**
 * Update progress display with real data
 */
function updateProgressDisplay(data) {
    // Update progress bar
    const progressFill = document.getElementById('progressBarFill');
    const progressPercentage = document.getElementById('progressPercentage');
    
    if (progressFill && progressPercentage) {
        progressFill.style.width = `${data.progress || 0}%`;
        progressPercentage.textContent = `${data.progress || 0}%`;
    }
    
    // Update step text
    const progressText = document.getElementById('progressText');
    const progressSubtext = document.getElementById('progressSubtext');
    
    if (progressText) {
        progressText.textContent = data.current_step || 'Processing...';
    }
    
    if (progressSubtext) {
        progressSubtext.textContent = data.substep || '';
    }
    
    // Update live info
    const liveStrategy = document.getElementById('liveStrategy');
    const liveModel = document.getElementById('liveModel');
    const liveCost = document.getElementById('liveCost');
    
    if (liveStrategy) {
        liveStrategy.textContent = data.job_id ? 'Running' : 'Initializing';
    }
    
    if (liveModel) {
        liveModel.textContent = data.model_used || 'Loading...';
    }
    
    if (liveCost) {
        liveCost.textContent = `$${(data.cost_estimate || 0).toFixed(4)}`;
    }
    
    // Update timer
    if (data.elapsed_time) {
        const minutes = Math.floor(data.elapsed_time / 60);
        const seconds = Math.floor(data.elapsed_time % 60);
        const progressTime = document.getElementById('progressTime');
        if (progressTime) {
            progressTime.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }
    }
}

/**
 * Handle extraction completion
 */
async function handleExtractionComplete(jobId) {
    try {
        // Get detailed results
        const response = await fetch(`/api/agent/extract/${jobId}/results`);
        
        if (!response.ok) {
            throw new Error(`Failed to get results: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // Store job ID for approval
        window.ModalState.currentJobId = jobId;
        
        // Display results
        displayExtractionResults(data);
        
        window.ModalState.extractionInProgress = false;
        stopProgressAnimation();
        
        console.log('✅ Extraction completed successfully');
        
    } catch (error) {
        console.error('❌ Error getting extraction results:', error);
        displayExtractionError(`Failed to get results: ${error.message}`);
    }
}

/**
 * Display real extraction results from API
 */
function displayExtractionResults(apiData) {
    showExtractionPhase('extractionResults');
    
    const resultsDiv = document.getElementById('extractionResults');
    if (!resultsDiv) {
        console.error('❌ Results div not found');
        return;
    }
    
    const results = apiData.results;
    const metadata = apiData.metadata || results.metadata;
    
    let resultsHTML = `
        <div class="results-container">
            <div class="results-header">
                <h4>✅ Extraction Complete!</h4>
                <div class="results-summary">
                    <div class="summary-grid">
                        <div class="summary-item">
                            <span class="summary-label">Stakeholders:</span>
                            <span class="summary-value">${results.stakeholders?.length || 0}</span>
                        </div>
                        <div class="summary-item">
                            <span class="summary-label">Strategy:</span>
                            <span class="summary-value">${metadata.extraction_strategy || 'Unknown'}</span>
                        </div>
                        <div class="summary-item">
                            <span class="summary-label">Model:</span>
                            <span class="summary-value">${metadata.agent_model || 'Unknown'}</span>
                        </div>
                        <div class="summary-item">
                            <span class="summary-label">Time:</span>
                            <span class="summary-value">${(metadata.processing_time || 0).toFixed(1)}s</span>
                        </div>
                        <div class="summary-item">
                            <span class="summary-label">Cost:</span>
                            <span class="summary-value">$${(metadata.cost_estimate || 0).toFixed(4)}</span>
                        </div>
                        <div class="summary-item">
                            <span class="summary-label">Quality:</span>
                            <span class="summary-value">${((metadata.quality_score || 0) * 100).toFixed(0)}%</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="stakeholders-section">
                <h5>📋 Extracted Stakeholders</h5>
                <div class="stakeholders-grid">
    `;
    
    // Display stakeholders from API results
    if (results.stakeholders && results.stakeholders.length > 0) {
        results.stakeholders.forEach((stakeholder, index) => {
            resultsHTML += `
                <div class="stakeholder-card">
                    <div class="stakeholder-header">
                        <div class="stakeholder-name">${stakeholder.name || 'Unknown'}</div>
                        <div class="stakeholder-type">${stakeholder.stakeholderType || 'UNKNOWN'}</div>
                    </div>
                    <div class="stakeholder-details">
                        <div class="detail-row">
                            <span class="detail-label">Role:</span>
                            <span class="detail-value">${stakeholder.role || 'Not specified'}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Organization:</span>
                            <span class="detail-value">${stakeholder.organization || 'Not specified'}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Confidence:</span>
                            <span class="detail-value confidence-${getConfidenceClass(stakeholder.confidenceScore || 0)}">
                                ${((stakeholder.confidenceScore || 0) * 100).toFixed(0)}%
                            </span>
                        </div>
                        ${stakeholder.contact ? `
                        <div class="detail-row">
                            <span class="detail-label">Contact:</span>
                            <span class="detail-value">${stakeholder.contact}</span>
                        </div>
                        ` : ''}
                    </div>
                </div>
            `;
        });
    } else {
        resultsHTML += `
            <div class="no-stakeholders">
                <p>⚠️ No stakeholders were extracted from this document.</p>
            </div>
        `;
    }
    
    resultsHTML += `
                </div>
            </div>
            
            <div class="results-actions">
                <button class="btn btn-success btn-large" onclick="approveExtraction()">
                    ✅ Approve & Save
                </button>
                <button class="btn btn-warning" onclick="editExtraction()">
                    ✏️ Edit Results
                </button>
                <button class="btn btn-danger" onclick="rejectExtraction()">
                    ❌ Reject
                </button>
                <button class="btn btn-secondary" onclick="closeExtractionModal()">
                    Close
                </button>
            </div>
        </div>
    `;
    
    resultsDiv.innerHTML = resultsHTML;
}

/**
 * Approve extraction and optionally open review
 */
async function approveExtraction() {
    if (!window.ModalState.currentJobId) {
        showErrorAlert('❌ No job ID available for approval');
        return;
    }
    
    try {
        const choice = confirm('✅ Approve extraction results?\n\nClick OK to approve and save immediately\nClick Cancel to review and edit first');
        
        if (choice) {
            // Direct approval - save immediately
            const response = await fetch(`/api/agent/extract/${window.ModalState.currentJobId}/approve`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            if (!response.ok) {
                throw new Error(`Failed to approve extraction: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            alert(`✅ Extraction approved and saved!\n\nSaved to: ${data.saved_to}`);
            closeExtractionModal();
            
            // Refresh the file list to show new JSON-LD file
            window.location.reload();
            
        } else {
            // Open review modal for detailed review
            console.log('🔄 Opening review system for detailed approval...');
            
            // First save the extraction results temporarily
            const response = await fetch(`/api/agent/extract/${window.ModalState.currentJobId}/approve`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                const savedFilename = data.saved_to.split('/').pop(); // Get just the filename
                
                closeExtractionModal();
                
                // Wait for modal to close, then open review
                setTimeout(() => {
                    if (typeof window.openDetailedReviewModal === 'function') {
                        window.openDetailedReviewModal(savedFilename);
                    } else {
                        alert('Review system not loaded. Please refresh the page.');
                    }
                }, 500);
            } else {
                throw new Error(`Failed to save for review: ${response.statusText}`);
            }
        }
        
    } catch (error) {
        console.error('❌ Error in approveExtraction:', error);
        showErrorAlert(`Failed to approve extraction: ${error.message}`);
    }
}

// Export functions to global scope
window.startExtraction = startExtraction;
window.pollExtractionProgress = pollExtractionProgress;
window.updateProgressDisplay = updateProgressDisplay;
window.handleExtractionComplete = handleExtractionComplete;
window.displayExtractionResults = displayExtractionResults;
window.approveExtraction = approveExtraction;

console.log('⚙️ Extraction Process loaded');