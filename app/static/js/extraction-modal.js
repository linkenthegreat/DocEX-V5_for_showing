/**
 * DocEX Extraction Modal Functions
 * Modal UI and interaction handling
 */

// Priority configuration details
const PriorityConfigs = {
    cost: {
        model: "Local Llama 3.1 8B",
        cost: "$0.00",
        speed: "3-4 minutes",
        quality: "Good",
        description: "Free local processing with excellent quality for most documents"
    },
    quality: {
        model: "GPT-4o",
        cost: "$0.005-0.015",
        speed: "1-2 minutes", 
        quality: "Excellent",
        description: "Premium AI model for highest accuracy and detail extraction"
    },
    speed: {
        model: "DeepSeek-V3",
        cost: "$0.001-0.003",
        speed: "30-60 seconds",
        quality: "Very Good",
        description: "Fast cloud processing with excellent cost-performance balance"
    },
    privacy: {
        model: "Local Llama 3.1 8B",
        cost: "$0.00",
        speed: "3-4 minutes",
        quality: "Good",
        description: "Complete privacy with local-only processing (no data leaves your system)"
    }
};

/**
 * Show specific extraction phase in the modal
 * @param {string} phaseId - The ID of the phase to show
 */
function showExtractionPhase(phaseId) {
    console.log(`🔄 Switching to phase: ${phaseId}`);
    
    const phases = ['extractionSetup', 'extractionProgress', 'extractionResults', 'extractionError'];
    
    phases.forEach(phase => {
        const element = document.getElementById(phase);
        if (element) {
            element.style.display = phase === phaseId ? 'block' : 'none';
        }
    });
    
    // Reset progress when showing setup
    if (phaseId === 'extractionSetup') {
        resetProgressDisplay();
    }
}

/**
 * Reset progress display elements
 */
function resetProgressDisplay() {
    const progressFill = document.getElementById('progressBarFill');
    const progressPercentage = document.getElementById('progressPercentage');
    const progressTime = document.getElementById('progressTime');
    const progressText = document.getElementById('progressText');
    const progressSubtext = document.getElementById('progressSubtext');
    
    if (progressFill) progressFill.style.width = '0%';
    if (progressPercentage) progressPercentage.textContent = '0%';
    if (progressTime) progressTime.textContent = '00:00';
    if (progressText) progressText.textContent = 'Initializing...';
    if (progressSubtext) progressSubtext.textContent = '';
}

/**
 * Open extraction modal for a specific file
 * @param {string} filename - The filename to extract from
 */
function openExtractionModal(filename) {
    console.log(`📊 Opening extraction modal for: ${filename}`);
    
    // Check if extraction interface is available
    if (!window.ExtractionInterface) {
        console.warn('⚠️ ExtractionInterface not available, proceeding anyway...');
    }
    
    // More lenient agent status check - allow if status is unknown/loading
    const agentStatus = window.ExtractionInterface?.agentStatus;
    if (agentStatus === 'error' || agentStatus === 'offline') {
        showErrorAlert('⚠️ Agent is not available. Please check the system status and try again.');
        return;
    }
    
    // If status is null/undefined (still loading) or 'ready', proceed
    console.log(`🔍 Agent status: ${agentStatus || 'loading'} - proceeding with modal`);
    
    window.ModalState.currentFilename = filename;
    
    // Update modal content
    const filenameElement = document.getElementById('extractionFilename');
    if (filenameElement) {
        filenameElement.textContent = filename;
    } else {
        console.warn('⚠️ extractionFilename element not found');
    }
    
    // Reset modal state
    showExtractionPhase('extractionSetup');
    
    // Set up priority selector
    setupPrioritySelector();
    
    // Show modal
    const modal = document.getElementById('extractionModal');
    if (modal) {
        modal.classList.add('show');
        modal.style.display = 'flex';
        
        // Focus on priority selector for keyboard users
        setTimeout(() => {
            const prioritySelector = document.getElementById('extractionPriority');
            if (prioritySelector) prioritySelector.focus();
        }, 300);
    } else {
        console.error('❌ Extraction modal element not found');
        showErrorAlert('❌ Extraction modal not available. Please refresh the page.');
    }
}

/**
 * Close extraction modal
 */
function closeExtractionModal() {
    const modal = document.getElementById('extractionModal');
    modal.classList.remove('show');
    
    setTimeout(() => {
        modal.style.display = 'none';
        resetModalState();
    }, 300);
}

/**
 * Set up priority selector with dynamic details
 */
function setupPrioritySelector() {
    const selector = document.getElementById('extractionPriority');
    const detailsDiv = document.getElementById('priorityDetails');
    
    if (!selector || !detailsDiv) return;
    
    // Update details when selection changes
    selector.addEventListener('change', function() {
        const priority = this.value;
        const config = PriorityConfigs[priority];
        
        if (config) {
            detailsDiv.innerHTML = `
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 10px; margin-top: 8px;">
                    <div><strong>Model:</strong><br><span style="color: var(--accent-color);">${config.model}</span></div>
                    <div><strong>Cost:</strong><br><span style="color: var(--success-color);">${config.cost}</span></div>
                    <div><strong>Speed:</strong><br><span style="color: var(--info-color);">${config.speed}</span></div>
                    <div><strong>Quality:</strong><br><span style="color: var(--warning-color);">${config.quality}</span></div>
                </div>
                <div style="margin-top: 10px; font-style: italic; color: var(--text-muted);">
                    ${config.description}
                </div>
            `;
            detailsDiv.style.display = 'block';
        }
    });
    
    // Trigger initial update
    selector.dispatchEvent(new Event('change'));
}

/**
 * Display extraction error in the modal
 * @param {string} errorMessage - The error message to display
 */
function displayExtractionError(errorMessage) {
    console.error(`❌ Displaying extraction error: ${errorMessage}`);
    
    showExtractionPhase('extractionError');
    
    const errorMessageElement = document.getElementById('errorMessage');
    if (errorMessageElement) {
        errorMessageElement.textContent = errorMessage;
    }
    
    // Stop any ongoing progress tracking
    window.ModalState.extractionInProgress = false;
    stopProgressAnimation();
}

/**
 * Show error alert
 * @param {string} message - The error message to show
 */
function showErrorAlert(message) {
    console.error(`⚠️ Error Alert: ${message}`);
    alert(message);
}

/**
 * Stop progress animation and timers
 */
function stopProgressAnimation() {
    if (window.ModalState.progressTimer) {
        clearInterval(window.ModalState.progressTimer);
        window.ModalState.progressTimer = null;
    }
    
    console.log('⏹️ Progress animation stopped');
}

/**
 * Reset modal state
 */
function resetModalState() {
    window.ModalState.currentFilename = null;
    window.ModalState.currentJobId = null;
    window.ModalState.extractionInProgress = false;
    window.ModalState.startTime = null;
    
    if (window.ModalState.progressTimer) {
        clearInterval(window.ModalState.progressTimer);
        window.ModalState.progressTimer = null;
    }
    
    // Reset progress bar
    const progressFill = document.getElementById('progressBarFill');
    const progressPercentage = document.getElementById('progressPercentage');
    
    if (progressFill) progressFill.style.width = '0%';
    if (progressPercentage) progressPercentage.textContent = '0%';
}

// Export functions to global scope
window.showExtractionPhase = showExtractionPhase;
window.openExtractionModal = openExtractionModal;
window.closeExtractionModal = closeExtractionModal;
window.displayExtractionError = displayExtractionError;
window.showErrorAlert = showErrorAlert;
window.resetModalState = resetModalState;
window.setupPrioritySelector = setupPrioritySelector;

console.log('🎨 Extraction Modal loaded');