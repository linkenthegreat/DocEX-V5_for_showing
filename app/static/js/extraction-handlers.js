/**
 * DocEX Extraction Button Handlers
 * Event handlers and utility functions
 */

/**
 * Test function that calls the real extraction modal
 */
function testExtractionButton(filename) {
    console.log('🧪 Test: Extract button clicked for:', filename);
    
    try {
        if (typeof window.openExtractionModal === 'function') {
            window.openExtractionModal(filename);
        } else {
            console.error('❌ openExtractionModal function not found');
            alert('❌ Extraction modal not available. Please refresh the page.');
        }
    } catch (error) {
        console.error('❌ Modal error:', error);
        alert(`❌ Modal Error: ${error.message}`);
    }
}

/**
 * Test function for review button
 */
function testReviewButton(filename) {
    console.log('🧪 Test: Review button clicked for:', filename);
    
    try {
        if (typeof window.openDetailedReviewModal === 'function') {
            window.openDetailedReviewModal(filename);
        } else {
            alert(`🧪 Review functionality not yet loaded.\n\nFilename: ${filename}`);
        }
    } catch (error) {
        console.error('❌ Review error:', error);
        alert(`❌ Review Error: ${error.message}`);
    }
}

/**
 * Handle bulk extraction (placeholder for now)
 */
function handleBulkExtraction() {
    console.log('🔄 Bulk extraction clicked');
    alert('📦 Bulk extraction functionality will be implemented in the next phase.\n\nThis will allow you to:\n• Extract from multiple files at once\n• Batch process documents\n• Queue management\n• Progress tracking');
}

/**
 * Handle dashboard click
 */
function handleDashboardClick() {
    console.log('📊 Dashboard clicked');
    alert('📈 Dashboard functionality will be implemented in a future step.\n\nThis will show:\n• Extraction statistics\n• Model performance\n• Cost tracking\n• Success rates');
}

/**
 * Retry extraction after error
 */
function retryExtraction() {
    console.log('🔄 Retrying extraction...');
    if (typeof window.showExtractionPhase === 'function') {
        window.showExtractionPhase('extractionSetup');
    }
    if (typeof window.resetModalState === 'function') {
        window.resetModalState();
    }
}

/**
 * Reject extraction results
 */
function rejectExtraction() {
    const confirmed = confirm('❌ Are you sure you want to reject these extraction results?\n\nThis will discard all extracted stakeholders.');
    
    if (confirmed) {
        console.log('❌ Extraction results rejected');
        if (typeof window.closeExtractionModal === 'function') {
            window.closeExtractionModal();
        }
    }
}

/**
 * Edit extraction results (opens review modal)
 */
function editExtraction(jobId) {
    console.log('✏️ Editing extraction results for job:', jobId);
    
    // Fetch real extraction results for editing
    fetch(`/api/agent/extract/${jobId}/edit`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Failed to get edit data: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('📝 Edit data received:', data);
            showEditModal(data);
        })
        .catch(error => {
            console.error('❌ Error getting edit data:', error);
            showNotification(`❌ Failed to load edit data: ${error.message}`, 'error');
        });
}

function showEditModal(extractionData) {
    console.log('📝 Showing edit modal with real data:', extractionData);
    
    const modal = document.getElementById('editModal') || createEditModal();
    
    // Build stakeholder editing interface with real data
    const stakeholdersHtml = extractionData.stakeholders.map((stakeholder, index) => `
        <div class="stakeholder-edit-card" data-index="${index}">
            <div class="stakeholder-edit-header">
                <h4>Stakeholder ${index + 1}</h4>
                <button type="button" class="btn btn-sm btn-danger" onclick="removeStakeholder(${index})">
                    🗑️ Remove
                </button>
            </div>
            <div class="stakeholder-edit-fields">
                <div class="form-group">
                    <label>Name:</label>
                    <input type="text" class="form-control" name="name_${index}" value="${stakeholder.name || ''}" />
                </div>
                <div class="form-group">
                    <label>Type:</label>
                    <select class="form-control" name="stakeholderType_${index}">
                        <option value="INDIVIDUAL" ${stakeholder.stakeholderType === 'INDIVIDUAL' ? 'selected' : ''}>Individual</option>
                        <option value="ORGANIZATION" ${stakeholder.stakeholderType === 'ORGANIZATION' ? 'selected' : ''}>Organization</option>
                        <option value="COMMITTEE" ${stakeholder.stakeholderType === 'COMMITTEE' ? 'selected' : ''}>Committee</option>
                        <option value="GOVERNMENT" ${stakeholder.stakeholderType === 'GOVERNMENT' ? 'selected' : ''}>Government</option>
                        <option value="UNKNOWN" ${stakeholder.stakeholderType === 'UNKNOWN' ? 'selected' : ''}>Unknown</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Role:</label>
                    <input type="text" class="form-control" name="role_${index}" value="${stakeholder.role || ''}" />
                </div>
                <div class="form-group">
                    <label>Organization:</label>
                    <input type="text" class="form-control" name="organization_${index}" value="${stakeholder.organization || ''}" />
                </div>
                <div class="form-group">
                    <label>Contact:</label>
                    <input type="text" class="form-control" name="contact_${index}" value="${stakeholder.contact || ''}" />
                </div>
            </div>
        </div>
    `).join('');
    
    const modalContent = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>✏️ Edit Extraction Results</h3>
                <span class="close" onclick="closeEditModal()">&times;</span>
            </div>
            <div class="modal-body">
                <div class="edit-info">
                    <p><strong>File:</strong> ${extractionData.filename}</p>
                    <p><strong>Stakeholders:</strong> ${extractionData.stakeholders.length}</p>
                </div>
                
                <div id="stakeholdersList">
                    ${stakeholdersHtml}
                </div>
                
                <div class="edit-actions">
                    <button type="button" class="btn btn-success" onclick="addNewStakeholder()">
                        ➕ Add Stakeholder
                    </button>
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-primary" onclick="saveEditedResults('${extractionData.job_id}')">
                    💾 Save Changes
                </button>
                <button type="button" class="btn btn-secondary" onclick="closeEditModal()">
                    ❌ Cancel
                </button>
            </div>
        </div>
    `;
    
    modal.innerHTML = modalContent;
    modal.style.display = 'block';
}

function saveEditedResults(jobId) {
    console.log('💾 Saving edited results for job:', jobId);
    
    // Collect edited stakeholder data
    const stakeholders = [];
    const stakeholderCards = document.querySelectorAll('.stakeholder-edit-card');
    
    stakeholderCards.forEach((card, index) => {
        const name = card.querySelector(`input[name="name_${index}"]`).value;
        const stakeholderType = card.querySelector(`select[name="stakeholderType_${index}"]`).value;
        const role = card.querySelector(`input[name="role_${index}"]`).value;
        const organization = card.querySelector(`input[name="organization_${index}"]`).value;
        const contact = card.querySelector(`input[name="contact_${index}"]`).value;
        
        if (name.trim()) {  // Only include stakeholders with names
            stakeholders.push({
                name: name.trim(),
                stakeholderType: stakeholderType,
                role: role.trim(),
                organization: organization.trim(),
                contact: contact.trim(),
                confidenceScore: 1.0  // User-edited = high confidence
            });
        }
    });
    
    // Send updated data to backend
    fetch(`/api/agent/extract/${jobId}/edit`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            stakeholders: stakeholders
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Failed to save edits: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('✅ Edit results saved:', data);
        showNotification(`✅ Changes saved successfully! ${data.stakeholder_count} stakeholders updated.`, 'success');
        closeEditModal();
        
        // Refresh the results display
        if (window.currentJobId === jobId) {
            pollExtractionProgress(jobId);
        }
    })
    .catch(error => {
        console.error('❌ Error saving edits:', error);
        showNotification(`❌ Failed to save changes: ${error.message}`, 'error');
    });
}

function removeStakeholder(index) {
    const card = document.querySelector(`.stakeholder-edit-card[data-index="${index}"]`);
    if (card) {
        card.remove();
        showNotification('🗑️ Stakeholder removed (save to confirm)', 'info');
    }
}

function addNewStakeholder() {
    const stakeholdersList = document.getElementById('stakeholdersList');
    const currentCount = stakeholdersList.children.length;
    
    const newStakeholderHtml = `
        <div class="stakeholder-edit-card" data-index="${currentCount}">
            <div class="stakeholder-edit-header">
                <h4>New Stakeholder ${currentCount + 1}</h4>
                <button type="button" class="btn btn-sm btn-danger" onclick="removeStakeholder(${currentCount})">
                    🗑️ Remove
                </button>
            </div>
            <div class="stakeholder-edit-fields">
                <div class="form-group">
                    <label>Name:</label>
                    <input type="text" class="form-control" name="name_${currentCount}" value="" />
                </div>
                <div class="form-group">
                    <label>Type:</label>
                    <select class="form-control" name="stakeholderType_${currentCount}">
                        <option value="INDIVIDUAL">Individual</option>
                        <option value="ORGANIZATION">Organization</option>
                        <option value="COMMITTEE">Committee</option>
                        <option value="GOVERNMENT">Government</option>
                        <option value="UNKNOWN">Unknown</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Role:</label>
                    <input type="text" class="form-control" name="role_${currentCount}" value="" />
                </div>
                <div class="form-group">
                    <label>Organization:</label>
                    <input type="text" class="form-control" name="organization_${currentCount}" value="" />
                </div>
                <div class="form-group">
                    <label>Contact:</label>
                    <input type="text" class="form-control" name="contact_${currentCount}" value="" />
                </div>
            </div>
        </div>
    `;
    
    stakeholdersList.insertAdjacentHTML('beforeend', newStakeholderHtml);
    showNotification('➕ New stakeholder added', 'success');
}

function closeEditModal() {
    const modal = document.getElementById('editModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function createEditModal() {
    const modal = document.createElement('div');
    modal.id = 'editModal';
    modal.className = 'modal';
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
            closeEditModal();
        }
    });
    
    return modal;
}

/**
 * Get CSS class for confidence score styling
 * @param {number} score - Confidence score (0.0 to 1.0)
 * @returns {string} CSS class name
 */
function getConfidenceClass(score) {
    if (score >= 0.8) return 'confidence-high';
    if (score >= 0.6) return 'confidence-medium';
    if (score >= 0.4) return 'confidence-low';
    return 'confidence-very-low';
}

/**
 * Open review modal (placeholder for now)
 * @param {string} filename - File to review
 */
function openReviewModal(filename) {
    console.log('📝 Opening review modal for:', filename);
    alert(`📝 Review Modal\n\nFilename: ${filename}\n\nDetailed review functionality will be implemented in the next phase.`);
}

/**
 * Show notification to user
 * @param {string} message - Notification message
 * @param {string} type - Notification type (success, error, info, warning)
 */
function showNotification(message, type = 'info') {
    // Create or get notification container
    let container = document.getElementById('notificationContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notificationContainer';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 2000;
            pointer-events: none;
        `;
        document.body.appendChild(container);
    }
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.style.cssText = `
        background: ${getNotificationColor(type)};
        color: white;
        padding: 12px 20px;
        border-radius: 6px;
        margin-bottom: 10px;
        max-width: 350px;
        word-wrap: break-word;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        pointer-events: auto;
        animation: slideIn 0.3s ease-out;
        font-size: 14px;
        line-height: 1.4;
    `;
    
    notification.textContent = message;
    
    // Add close button
    const closeBtn = document.createElement('span');
    closeBtn.innerHTML = '&times;';
    closeBtn.style.cssText = `
        float: right;
        font-size: 18px;
        font-weight: bold;
        cursor: pointer;
        margin-left: 10px;
        opacity: 0.7;
    `;
    closeBtn.onclick = () => notification.remove();
    notification.appendChild(closeBtn);
    
    container.appendChild(notification);
    
    // Auto-remove after delay
    const delay = type === 'error' ? 8000 : 4000;
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, delay);
}

/**
 * Get notification background color based on type
 * @param {string} type - Notification type
 * @returns {string} CSS color value
 */
function getNotificationColor(type) {
    const colors = {
        'success': '#28a745',
        'error': '#dc3545',
        'warning': '#ffc107',
        'info': '#17a2b8'
    };
    return colors[type] || colors['info'];
}

/**
 * Format confidence score for display
 * @param {number} score - Confidence score (0.0 to 1.0)
 * @returns {string} Formatted percentage
 */
function formatConfidence(score) {
    if (typeof score !== 'number' || isNaN(score)) {
        return 'N/A';
    }
    return `${Math.round(score * 100)}%`;
}

/**
 * Format extraction status for display
 * @param {string} status - Status string
 * @returns {string} Formatted status with emoji
 */
function formatStatus(status) {
    const statusMap = {
        'pending': '⏳ Pending',
        'running': '🔄 Processing',
        'complete': '✅ Complete',
        'error': '❌ Error',
        'approved': '👍 Approved',
        'rejected': '👎 Rejected'
    };
    return statusMap[status] || status;
}

/**
 * Create CSS for animations if not already present
 */
function addNotificationStyles() {
    if (document.getElementById('notificationStyles')) {
        return; // Already added
    }
    
    const style = document.createElement('style');
    style.id = 'notificationStyles';
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        .notification {
            transition: all 0.3s ease;
        }
        
        .notification:hover {
            transform: scale(1.02);
        }
        
        .confidence-high {
            color: #28a745;
            font-weight: bold;
        }
        
        .confidence-medium {
            color: #ffc107;
            font-weight: 600;
        }
        
        .confidence-low {
            color: #fd7e14;
            font-weight: 500;
        }
        
        .confidence-very-low {
            color: #dc3545;
            font-weight: 400;
        }
    `;
    
    document.head.appendChild(style);
}

// Initialize notification styles when the script loads
addNotificationStyles();

// Export functions to global scope (make sure ALL functions are exported)
window.testExtractionButton = testExtractionButton;
window.testReviewButton = testReviewButton;
window.handleBulkExtraction = handleBulkExtraction;
window.handleDashboardClick = handleDashboardClick;
window.retryExtraction = retryExtraction;
window.rejectExtraction = rejectExtraction;
window.editExtraction = editExtraction;
window.getConfidenceClass = getConfidenceClass;
window.openReviewModal = openReviewModal;
window.showNotification = showNotification;
window.formatConfidence = formatConfidence;
window.formatStatus = formatStatus;
window.removeStakeholder = removeStakeholder;
window.addNewStakeholder = addNewStakeholder;
window.saveEditedResults = saveEditedResults;
window.closeEditModal = closeEditModal;

console.log('🔧 Extraction Handlers loaded with all utility functions');