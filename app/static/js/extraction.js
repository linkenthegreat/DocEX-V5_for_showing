/**
 * DocEX Enhanced Extraction Interface - Main Module
 * Coordinates all extraction functionality - modular version
 */

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Enhanced Extraction Interface Loading...');
    
    // Wait for all modules to load, then initialize
    setTimeout(() => {
        if (typeof window.initializeInterface === 'function') {
            window.initializeInterface();
        } else {
            console.error('❌ Core functions not loaded');
        }
    }, 100);
});

console.log('📦 Extraction main module loaded');

