/**
 * DocEX Extraction Core Functions
 * Core extraction functionality and state management
 */

// Global state
const ExtractionInterface = {
    agentStatus: null,
    modelAvailability: {},
    isLoading: false
};

// Modal state management
const ModalState = {
    currentFilename: null,
    currentJobId: null,
    extractionInProgress: false,
    progressTimer: null,
    startTime: null
};

/**
 * Initialize the extraction interface
 */
function initializeInterface() {
    loadAgentStatus();
    setupEventListeners();
    console.log('✅ Enhanced Extraction Interface Ready');
}

/**
 * Set up event listeners for the interface
 */
function setupEventListeners() {
    // Bulk extract button
    const bulkExtractBtn = document.getElementById('bulkExtractBtn');
    if (bulkExtractBtn) {
        bulkExtractBtn.addEventListener('click', handleBulkExtraction);
    }
    
    // Dashboard button  
    const dashboardBtn = document.getElementById('dashboardBtn');
    if (dashboardBtn) {
        dashboardBtn.addEventListener('click', handleDashboardClick);
    }
    
    console.log('✅ Event listeners configured');
}

/**
 * Load agent status and update UI
 */
async function loadAgentStatus() {
    try {
        console.log('📊 Loading agent status...');
        
        const response = await fetch('/api/agent/status');
        const data = await response.json();
        
        ExtractionInterface.agentStatus = data.status;
        ExtractionInterface.modelAvailability = data.model_availability;
        
        updateAgentStatusDisplay(data);
        console.log('✅ Agent status loaded:', data.status);
        
    } catch (error) {
        console.error('❌ Failed to load agent status:', error);
        displayAgentError();
    }
}

/**
 * Update the agent status display in the UI
 */
function updateAgentStatusDisplay(data) {
    const agentStatusElement = document.getElementById('agent-status');
    const modelStatusElement = document.getElementById('model-status');
    
    if (!agentStatusElement || !modelStatusElement) {
        console.warn('⚠️ Agent status elements not found');
        return;
    }
    
    // Update agent status
    const isReady = data.status === 'ready';
    agentStatusElement.innerHTML = `
        <span class="${isReady ? 'status-ready' : 'status-error'}">
            ${isReady ? '✅ Ready' : '❌ Error'}
        </span>
    `;
    agentStatusElement.className = isReady ? 'status-ready' : 'status-error';
    
    // Update model availability
    const availableModels = data.available_models_count || 0;
    const totalModels = 3;
    const isFullyAvailable = availableModels === totalModels;
    
    modelStatusElement.innerHTML = `
        <span class="${isFullyAvailable ? 'status-ready' : (availableModels > 0 ? 'status-partial' : 'status-error')}">
            ${availableModels}/${totalModels} Available
        </span>
    `;
    
    // Update extraction buttons based on availability
    updateExtractionButtonsState(availableModels > 0);
}

/**
 * Display agent error state
 */
function displayAgentError() {
    const agentStatusElement = document.getElementById('agent-status');
    const modelStatusElement = document.getElementById('model-status');
    
    if (agentStatusElement) {
        agentStatusElement.innerHTML = '<span class="status-error">❌ Connection Error</span>';
        agentStatusElement.className = 'status-error';
    }
    
    if (modelStatusElement) {
        modelStatusElement.innerHTML = '<span class="status-error">Unknown</span>';
        modelStatusElement.className = 'status-error';
    }
    
    updateExtractionButtonsState(false);
}

/**
 * Update extraction buttons state based on agent availability
 */
function updateExtractionButtonsState(isAvailable) {
    const extractionButtons = document.querySelectorAll('.extraction-btn');
    const bulkExtractBtn = document.getElementById('bulkExtractBtn');
    
    extractionButtons.forEach(btn => {
        btn.disabled = !isAvailable;
        btn.title = isAvailable ? 'Extract stakeholders' : 'Agent not available';
        
        if (!isAvailable) {
            btn.classList.add('btn-disabled');
        } else {
            btn.classList.remove('btn-disabled');
        }
    });
    
    if (bulkExtractBtn) {
        bulkExtractBtn.disabled = !isAvailable;
        bulkExtractBtn.title = isAvailable ? 'Extract from all documents' : 'Agent not available';
    }
}

// Export functions to global scope
window.ExtractionInterface = ExtractionInterface;
window.ModalState = ModalState;
window.initializeInterface = initializeInterface;
window.loadAgentStatus = loadAgentStatus;
window.updateAgentStatusDisplay = updateAgentStatusDisplay;

console.log('🔧 Extraction Core loaded');