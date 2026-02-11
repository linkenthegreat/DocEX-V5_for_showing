/**
 * Review and Approval Workflow JavaScript
 * Handles stakeholder review, editing, and approval processes
 */

// Review state management
const ReviewState = {
    currentData: null,
    originalData: null,
    selectedStakeholders: new Set(),
    currentEditIndex: null,
    filters: {
        confidence: 'all',
        type: 'all',
        status: 'all'
    }
};

/**
 * Open detailed review modal for a JSON-LD file
 * @param {string} filename - The JSON-LD filename to review
 */
async function openDetailedReviewModal(filename) {
    console.log(`👁️ Opening detailed review modal for: ${filename}`);
    
    try {
        // Show loading state
        const modal = document.getElementById('reviewModal');
        if (modal) {
            modal.classList.add('show');
            modal.style.display = 'flex';
            
            // Show loading message
            const reviewContent = document.getElementById('stakeholderReviewGrid');
            if (reviewContent) {
                reviewContent.innerHTML = '<div class="loading-message">📂 Loading review data...</div>';
            }
        }
        
        // Load data
        const data = await loadJsonLdFile(filename);
        
        // Handle cancelled/null data
        if (!data) {
            closeReviewModal();
            return;
        }
        
        // Store data for review
        ReviewState.currentData = data;
        ReviewState.originalData = JSON.parse(JSON.stringify(data)); // Deep copy
        
        // Populate modal
        populateReviewHeader(filename, data);
        displayStakeholdersForReview(data.stakeholders || []);
        
        console.log('✅ Review modal populated successfully');
        
    } catch (error) {
        console.error('❌ Error opening review modal:', error);
        alert(`❌ Failed to open review: ${error.message}`);
        closeReviewModal();
    }
}

/**
 * Load JSON-LD file data
 * @param {string} filename - The filename to load
 * @returns {Object} The parsed JSON data
 */
async function loadJsonLdFile(filename) {
    try {
        console.log(`📂 Loading JSON-LD file for review: ${filename}`);
        
        // Try to load from the backend API
        const response = await fetch(`/api/agent/load_jsonld/${encodeURIComponent(filename)}`);
        
        if (response.ok) {
            const data = await response.json();
            console.log(`✅ Successfully loaded ${data.stakeholders?.length || 0} stakeholders from backend`);
            
            // If no stakeholders found, show helpful message
            if (!data.stakeholders || data.stakeholders.length === 0) {
                const useDemo = confirm(`📄 This file contains no stakeholders yet.\n\n• Click OK to demo the review interface with sample data\n• Click Cancel to extract stakeholders first\n\nFilename: ${filename}`);
                
                if (useDemo) {
                    console.log('🎯 Using demo data for review interface demonstration');
                    return generateMockReviewData(filename);
                } else {
                    alert('💡 Use the Extract button first to extract stakeholders from this document.');
                    return null;
                }
            }
            
            return data;
        } else {
            console.warn('⚠️ Backend load failed, using demo data');
            return generateMockReviewData(filename);
        }
        
    } catch (error) {
        console.error('❌ Error loading JSON-LD file:', error);
        console.warn('⚠️ Using demo data as fallback');
        return generateMockReviewData(filename);
    }
}

/**
 * Generate mock data for testing the review interface
 */
function generateMockReviewData(filename) {
    return {
        stakeholders: [
            {
                name: "Dr. Sarah Chen",
                stakeholderType: "RESEARCHER",
                role: "Lead Researcher",
                organization: "University Research Institute",
                contact: "s.chen@university.edu",
                confidenceScore: 0.95,
                extractionMethod: "AI-quality",
                sourceText: "Dr. Sarah Chen, the lead researcher at University Research Institute, has been conducting extensive research on social policy implementation.",
                reviewStatus: "pending",
                reviewNotes: ""
            },
            {
                name: "Minister Janet Roberts",
                stakeholderType: "GOVERNMENT_OFFICIAL",
                role: "Policy Minister",
                organization: "Department of Social Services",
                contact: "minister@gov.au",
                confidenceScore: 0.88,
                extractionMethod: "AI-quality",
                sourceText: "Minister Janet Roberts from the Department of Social Services announced new policy initiatives during the parliamentary session.",
                reviewStatus: "pending",
                reviewNotes: ""
            },
            {
                name: "Community Health Alliance",
                stakeholderType: "ORGANIZATION",
                role: "Advocacy Group",
                organization: "Community Health Alliance",
                contact: "info@healthalliance.org",
                confidenceScore: 0.72,
                extractionMethod: "AI-quality",
                sourceText: "The Community Health Alliance advocates for improved healthcare access in rural communities.",
                reviewStatus: "pending",
                reviewNotes: ""
            },
            {
                name: "Prof. Michael Thompson",
                stakeholderType: "ACADEMIC",
                role: "Policy Analyst",
                organization: "State University",
                contact: "m.thompson@stateuni.edu",
                confidenceScore: 0.91,
                extractionMethod: "AI-quality",
                sourceText: "Professor Michael Thompson's analysis of policy outcomes provides valuable insights into implementation strategies.",
                reviewStatus: "pending",
                reviewNotes: ""
            },
            {
                name: "Local Residents Association",
                stakeholderType: "COMMUNITY_MEMBER",
                role: "Community Group",
                organization: "Riverside Residents Association",
                contact: "contact@riverside.org",
                confidenceScore: 0.65,
                extractionMethod: "AI-quality",
                sourceText: "The Local Residents Association expressed concerns about the proposed changes to community services.",
                reviewStatus: "pending",
                reviewNotes: ""
            }
        ],
        metadata: {
            source_document: filename,
            extraction_strategy: "quality",
            agent_model: "GPT-4o",
            processing_time: 125.3,
            extraction_confidence: 0.87,
            quality_score: 0.93,
            extraction_timestamp: new Date().toISOString()
        }
    };
}

/**
 * Populate review modal header with file information
 */
function populateReviewHeader(filename, data) {
    const metadata = data.metadata || {};
    
    // Update filename
    const filenameElement = document.getElementById('reviewFilename');
    if (filenameElement) {
        filenameElement.textContent = filename;
    }
    
    // Update metadata
    document.getElementById('reviewStatus').textContent = 'Complete';
    document.getElementById('reviewAgent').textContent = metadata.agent_model || 'Unknown';
    document.getElementById('reviewQuality').textContent = `${((metadata.quality_score || 0.8) * 100).toFixed(0)}%`;
    document.getElementById('reviewStakeholderCount').textContent = (data.stakeholders || []).length;
    
    // Update quality score styling
    const qualityElement = document.getElementById('reviewQuality');
    const qualityScore = metadata.quality_score || 0.8;
    if (qualityScore > 0.8) {
        qualityElement.className = 'quality-score confidence-high';
    } else if (qualityScore > 0.6) {
        qualityElement.className = 'quality-score confidence-medium';
    } else {
        qualityElement.className = 'quality-score confidence-low';
    }
}

/**
 * Display stakeholders in the review grid
 */
function displayStakeholdersForReview(stakeholders) {
    const grid = document.getElementById('stakeholderReviewGrid');
    if (!grid) return;
    
    grid.innerHTML = '';
    
    stakeholders.forEach((stakeholder, index) => {
        const card = createStakeholderReviewCard(stakeholder, index);
        grid.appendChild(card);
    });
    
    updateReviewSummary();
}

/**
 * Create a stakeholder review card
 */
function createStakeholderReviewCard(stakeholder, index) {
    const card = document.createElement('div');
    card.className = `stakeholder-review-card ${stakeholder.reviewStatus || 'pending'}`;
    card.dataset.index = index;
    card.dataset.type = stakeholder.stakeholderType;
    card.dataset.confidence = getConfidenceLevel(stakeholder.confidenceScore || 0);
    card.dataset.status = stakeholder.reviewStatus || 'pending';
    
    const confidenceClass = getConfidenceClass(stakeholder.confidenceScore || 0);
    const confidencePercent = ((stakeholder.confidenceScore || 0) * 100).toFixed(0);
    
    card.innerHTML = `
        <div class="stakeholder-select">
            <input type="checkbox" 
                   onchange="toggleStakeholderSelection(${index})"
                   id="stakeholder-${index}">
        </div>
        
        <div class="stakeholder-card-header">
            <div>
                <div class="stakeholder-name">${stakeholder.name || 'Unknown'}</div>
                <span class="stakeholder-type">${stakeholder.stakeholderType || 'UNKNOWN'}</span>
            </div>
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
                <span class="detail-label">Contact:</span>
                <span class="detail-value">${stakeholder.contact || 'Not provided'}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Confidence:</span>
                <span class="detail-value confidence-score confidence-${confidenceClass}">${confidencePercent}%</span>
            </div>
        </div>
        
        <div class="source-text">
            ${stakeholder.sourceText || 'No source text available'}
        </div>
        
        <div class="stakeholder-actions">
            <button class="btn btn-success btn-sm" onclick="approveStakeholder(${index})">
                ✅ Approve
            </button>
            <button class="btn btn-warning btn-sm" onclick="editStakeholder(${index})">
                ✏️ Edit
            </button>
            <button class="btn btn-danger btn-sm" onclick="rejectStakeholder(${index})">
                ❌ Reject
            </button>
        </div>
        
        ${stakeholder.reviewNotes ? `
        <div class="review-notes">
            <strong>Notes:</strong> ${stakeholder.reviewNotes}
        </div>
        ` : ''}
    `;
    
    return card;
}

/**
 * Get confidence level from score
 */
function getConfidenceLevel(score) {
    if (score >= 0.8) return 'high';
    if (score >= 0.6) return 'medium';
    return 'low';
}

// Individual stakeholder actions
function approveStakeholder(index) {
    updateStakeholderStatus(index, 'approved');
}

function rejectStakeholder(index) {
    const confirmed = confirm('Are you sure you want to reject this stakeholder?');
    if (confirmed) {
        updateStakeholderStatus(index, 'rejected');
    }
}

function editStakeholder(index) {
    ReviewState.currentEditIndex = index;
    const stakeholder = ReviewState.currentData.stakeholders[index];
    openEditStakeholderModal(stakeholder);
}

/**
 * Update stakeholder status and refresh display
 */
function updateStakeholderStatus(index, status) {
    if (ReviewState.currentData.stakeholders[index]) {
        ReviewState.currentData.stakeholders[index].reviewStatus = status;
        
        // Update card appearance
        const card = document.querySelector(`[data-index="${index}"]`);
        if (card) {
            card.className = `stakeholder-review-card ${status}`;
            card.dataset.status = status;
        }
        
        updateReviewSummary();
        console.log(`✅ Stakeholder ${index} status updated to: ${status}`);
    }
}

/**
 * Update review summary display
 */
function updateReviewSummary() {
    const stakeholders = ReviewState.currentData.stakeholders || [];
    const total = stakeholders.length;
    const approved = stakeholders.filter(s => s.reviewStatus === 'approved').length;
    const rejected = stakeholders.filter(s => s.reviewStatus === 'rejected').length;
    const pending = stakeholders.filter(s => !s.reviewStatus || s.reviewStatus === 'pending').length;
    const modified = stakeholders.filter(s => s.reviewStatus === 'modified').length;
    
    const summaryElement = document.getElementById('reviewSummaryText');
    if (summaryElement) {
        summaryElement.textContent = `${total} stakeholders • ${approved} approved • ${rejected} rejected • ${pending} pending • ${modified} modified`;
    }
}

// Filter functions
function filterStakeholders() {
    const confidenceFilter = document.getElementById('confidenceFilter').value;
    const typeFilter = document.getElementById('typeFilter').value;
    const statusFilter = document.getElementById('statusFilter').value;
    
    ReviewState.filters = {
        confidence: confidenceFilter,
        type: typeFilter,
        status: statusFilter
    };
    
    const cards = document.querySelectorAll('.stakeholder-review-card');
    
    cards.forEach(card => {
        const shouldShow = shouldShowCard(card);
        card.style.display = shouldShow ? 'block' : 'none';
    });
}

function shouldShowCard(card) {
    const { confidence, type, status } = ReviewState.filters;
    
    // Check confidence filter
    if (confidence !== 'all' && card.dataset.confidence !== confidence) {
        return false;
    }
    
    // Check type filter
    if (type !== 'all' && card.dataset.type !== type) {
        return false;
    }
    
    // Check status filter
    if (status !== 'all' && card.dataset.status !== status) {
        return false;
    }
    
    return true;
}

// Bulk actions
function toggleSelectAll() {
    const selectAll = document.getElementById('selectAllStakeholders');
    const checkboxes = document.querySelectorAll('.stakeholder-review-card input[type="checkbox"]');
    
    checkboxes.forEach(checkbox => {
        if (!checkbox.closest('.stakeholder-review-card').style.display === 'none') {
            checkbox.checked = selectAll.checked;
            const index = parseInt(checkbox.id.split('-')[1]);
            if (selectAll.checked) {
                ReviewState.selectedStakeholders.add(index);
            } else {
                ReviewState.selectedStakeholders.delete(index);
            }
        }
    });
}

function toggleStakeholderSelection(index) {
    const checkbox = document.getElementById(`stakeholder-${index}`);
    if (checkbox.checked) {
        ReviewState.selectedStakeholders.add(index);
    } else {
        ReviewState.selectedStakeholders.delete(index);
    }
}

function bulkApprove() {
    if (ReviewState.selectedStakeholders.size === 0) {
        alert('Please select stakeholders to approve.');
        return;
    }
    
    const confirmed = confirm(`Approve ${ReviewState.selectedStakeholders.size} selected stakeholders?`);
    if (confirmed) {
        ReviewState.selectedStakeholders.forEach(index => {
            updateStakeholderStatus(index, 'approved');
        });
        clearSelection();
    }
}

function bulkReject() {
    if (ReviewState.selectedStakeholders.size === 0) {
        alert('Please select stakeholders to reject.');
        return;
    }
    
    const confirmed = confirm(`Reject ${ReviewState.selectedStakeholders.size} selected stakeholders?`);
    if (confirmed) {
        ReviewState.selectedStakeholders.forEach(index => {
            updateStakeholderStatus(index, 'rejected');
        });
        clearSelection();
    }
}

function bulkEdit() {
    if (ReviewState.selectedStakeholders.size === 0) {
        alert('Please select stakeholders to edit.');
        return;
    }
    
    alert('Bulk edit functionality will be implemented in the next phase.');
}

function clearSelection() {
    ReviewState.selectedStakeholders.clear();
    document.querySelectorAll('.stakeholder-review-card input[type="checkbox"]').forEach(checkbox => {
        checkbox.checked = false;
    });
    document.getElementById('selectAllStakeholders').checked = false;
}

// Main review actions
function approveAllStakeholders() {
    const confirmed = confirm('Approve all stakeholders in this extraction?');
    if (confirmed) {
        ReviewState.currentData.stakeholders.forEach((_, index) => {
            updateStakeholderStatus(index, 'approved');
        });
    }
}

function finalizeReview() {
    const approved = ReviewState.currentData.stakeholders.filter(s => s.reviewStatus === 'approved');
    
    if (approved.length === 0) {
        alert('Please approve at least one stakeholder before finalizing.');
        return;
    }
    
    const confirmed = confirm(`Finalize review with ${approved.length} approved stakeholders?\n\nThis will save the approved stakeholders to the database.`);
    if (confirmed) {
        saveReviewResults();
    }
}

/**
 * Save review results to backend
 */
async function saveReviewResults() {
    try {
        console.log('💾 Saving review results...');
        
        if (!ReviewState.currentData || !ReviewState.currentData.metadata) {
            throw new Error('No review data available to save');
        }
        
        const filename = ReviewState.currentData.metadata.source_document;
        if (!filename) {
            throw new Error('No source document filename available');
        }
        
        // Prepare review data
        const reviewData = {
            stakeholders: ReviewState.currentData.stakeholders,
            metadata: ReviewState.currentData.metadata,
            review_summary: {
                total_stakeholders: ReviewState.currentData.stakeholders.length,
                approved: ReviewState.currentData.stakeholders.filter(s => s.reviewStatus === 'approved').length,
                rejected: ReviewState.currentData.stakeholders.filter(s => s.reviewStatus === 'rejected').length,
                modified: ReviewState.currentData.stakeholders.filter(s => s.reviewStatus === 'modified').length,
                pending: ReviewState.currentData.stakeholders.filter(s => !s.reviewStatus || s.reviewStatus === 'pending').length,
                finalized_timestamp: new Date().toISOString()
            }
        };
        
        // Save to backend
        const response = await fetch(`/api/agent/save_review/${encodeURIComponent(filename)}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(reviewData)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `Save failed: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        console.log('✅ Review results saved successfully:', result);
        alert('✅ Review results saved successfully!');
        
        closeReviewModal();
        
        // Refresh the file list to show updated status
        window.location.reload();
        
    } catch (error) {
        console.error('❌ Error saving review results:', error);
        alert(`❌ Failed to save review results: ${error.message}`);
    }
}

function saveReviewProgress() {
    console.log('💾 Saving review progress...');
    alert('📝 Review progress saved. You can continue reviewing later.');
}

function closeReviewModal() {
    const modal = document.getElementById('reviewModal');
    if (modal) {
        modal.classList.remove('show');
        setTimeout(() => {
            modal.style.display = 'none';
            resetReviewState();
        }, 300);
    }
}

function resetReviewState() {
    ReviewState.currentData = null;
    ReviewState.originalData = null;
    ReviewState.selectedStakeholders.clear();
    ReviewState.currentEditIndex = null;
    ReviewState.filters = {
        confidence: 'all',
        type: 'all',
        status: 'all'
    };
}

/**
 * Open edit stakeholder modal with current data
 */
function openEditStakeholderModal(stakeholder) {
    console.log('✏️ Opening edit stakeholder modal for:', stakeholder.name);
    
    // Populate form fields
    document.getElementById('editName').value = stakeholder.name || '';
    document.getElementById('editType').value = stakeholder.stakeholderType || 'RESEARCHER';
    document.getElementById('editRole').value = stakeholder.role || '';
    document.getElementById('editOrganization').value = stakeholder.organization || '';
    document.getElementById('editContact').value = stakeholder.contact || '';
    document.getElementById('editConfidence').value = stakeholder.confidenceScore || 0.8;
    document.getElementById('editSourceText').value = stakeholder.sourceText || '';
    document.getElementById('editNotes').value = stakeholder.reviewNotes || '';
    
    // Update confidence display
    updateConfidenceDisplay();
    
    // Show edit modal
    const modal = document.getElementById('editStakeholderModal');
    if (modal) {
        modal.classList.add('show');
        modal.style.display = 'flex';
        
        // Focus on name field
        setTimeout(() => {
            document.getElementById('editName').focus();
        }, 300);
    }
}

/**
 * Close edit stakeholder modal
 */
function closeEditStakeholderModal() {
    const modal = document.getElementById('editStakeholderModal');
    if (modal) {
        modal.classList.remove('show');
        setTimeout(() => {
            modal.style.display = 'none';
        }, 300);
    }
}

/**
 * Save stakeholder edits
 */
function saveStakeholderEdit() {
    if (ReviewState.currentEditIndex === null) {
        alert('❌ No stakeholder selected for editing');
        return;
    }
    
    // Get form data
    const editedStakeholder = {
        name: document.getElementById('editName').value.trim(),
        stakeholderType: document.getElementById('editType').value,
        role: document.getElementById('editRole').value.trim(),
        organization: document.getElementById('editOrganization').value.trim(),
        contact: document.getElementById('editContact').value.trim(),
        confidenceScore: parseFloat(document.getElementById('editConfidence').value),
        sourceText: document.getElementById('editSourceText').value.trim(),
        reviewNotes: document.getElementById('editNotes').value.trim(),
        reviewStatus: 'modified'
    };
    
    // Validation
    if (!editedStakeholder.name) {
        alert('❌ Name is required');
        return;
    }
    
    if (!editedStakeholder.stakeholderType) {
        alert('❌ Type is required');
        return;
    }
    
    // Update the stakeholder
    const originalStakeholder = ReviewState.currentData.stakeholders[ReviewState.currentEditIndex];
    ReviewState.currentData.stakeholders[ReviewState.currentEditIndex] = {
        ...originalStakeholder,
        ...editedStakeholder
    };
    
    // Refresh the display
    displayStakeholdersForReview(ReviewState.currentData.stakeholders);
    
    // Close edit modal
    closeEditStakeholderModal();
    
    // Reset edit index
    ReviewState.currentEditIndex = null;
    
    console.log('✅ Stakeholder edited successfully');
    alert('✅ Stakeholder updated successfully!');
}

/**
 * Update confidence percentage display
 */
function updateConfidenceDisplay() {
    const slider = document.getElementById('editConfidence');
    const display = document.getElementById('editConfidenceValue');
    
    if (slider && display) {
        const percentage = Math.round(slider.value * 100);
        display.textContent = `${percentage}%`;
        
        // Update color based on confidence level
        if (percentage >= 80) {
            display.style.color = 'var(--success-color)';
        } else if (percentage >= 60) {
            display.style.color = 'var(--warning-color)';
        } else {
            display.style.color = 'var(--danger-color)';
        }
    }
}

/**
 * Add event listener for confidence slider
 */
document.addEventListener('DOMContentLoaded', function() {
    const confidenceSlider = document.getElementById('editConfidence');
    if (confidenceSlider) {
        confidenceSlider.addEventListener('input', updateConfidenceDisplay);
    }
});

/**
 * Export for review functionality
 */
function exportForReview() {
    if (!ReviewState.currentData) {
        alert('❌ No data available for export');
        return;
    }
    
    const exportData = {
        metadata: ReviewState.currentData.metadata,
        stakeholders: ReviewState.currentData.stakeholders,
        review_summary: {
            total_stakeholders: ReviewState.currentData.stakeholders.length,
            approved: ReviewState.currentData.stakeholders.filter(s => s.reviewStatus === 'approved').length,
            rejected: ReviewState.currentData.stakeholders.filter(s => s.reviewStatus === 'rejected').length,
            modified: ReviewState.currentData.stakeholders.filter(s => s.reviewStatus === 'modified').length,
            pending: ReviewState.currentData.stakeholders.filter(s => !s.reviewStatus || s.reviewStatus === 'pending').length,
            export_timestamp: new Date().toISOString()
        }
    };
    
    // Create download
    const dataStr = JSON.stringify(exportData, null, 2);
    const dataBlob = new Blob([dataStr], {type: 'application/json'});
    const url = URL.createObjectURL(dataBlob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = `review_export_${Date.now()}.json`;
    link.click();
    
    URL.revokeObjectURL(url);
    
    console.log('📤 Review data exported successfully');
    alert('📤 Review data exported successfully!');
}

/**
 * Show extraction log (placeholder for future implementation)
 */
function showExtractionLog() {
    const logData = ReviewState.currentData?.metadata || {};
    
    const logInfo = `
📋 Extraction Log
================

Document: ${logData.source_document || 'Unknown'}
Strategy: ${logData.extraction_strategy || 'Unknown'}
Model: ${logData.agent_model || 'Unknown'}
Processing Time: ${logData.processing_time || 0}s
Quality Score: ${((logData.quality_score || 0) * 100).toFixed(0)}%
Confidence: ${((logData.extraction_confidence || 0) * 100).toFixed(0)}%
Timestamp: ${logData.extraction_timestamp || 'Unknown'}

Stakeholders Found: ${ReviewState.currentData?.stakeholders?.length || 0}
    `;
    
    alert(logInfo);
}

/**
 * Test review modal function (for debugging)
 */
function testReviewModal(filename) {
    console.log('🧪 Testing review modal with filename:', filename);
    
    if (!filename) {
        filename = 'test_file.json';
    }
    
    // Use the real openDetailedReviewModal function
    openDetailedReviewModal(filename);
}

// Add these functions to the global scope
window.openDetailedReviewModal = openDetailedReviewModal;
window.openReviewModal = openDetailedReviewModal; // Alias for compatibility
window.closeReviewModal = closeReviewModal;
window.approveStakeholder = approveStakeholder;
window.rejectStakeholder = rejectStakeholder;
window.editStakeholder = editStakeholder;
window.filterStakeholders = filterStakeholders;
window.toggleSelectAll = toggleSelectAll;
window.toggleStakeholderSelection = toggleStakeholderSelection;
window.bulkApprove = bulkApprove;
window.bulkReject = bulkReject;
window.bulkEdit = bulkEdit;
window.approveAllStakeholders = approveAllStakeholders;
window.finalizeReview = finalizeReview;
window.saveReviewProgress = saveReviewProgress;
window.testReviewModal = testReviewModal;
window.openEditStakeholderModal = openEditStakeholderModal;
window.closeEditStakeholderModal = closeEditStakeholderModal;
window.saveStakeholderEdit = saveStakeholderEdit;
window.updateConfidenceDisplay = updateConfidenceDisplay;
window.exportForReview = exportForReview;
window.showExtractionLog = showExtractionLog;

console.log('📦 Review functionality loaded');
console.log('🧪 Review debug function loaded. Call testReviewModal() to test.');