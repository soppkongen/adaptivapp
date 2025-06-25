/**
 * AURA Main System Integration
 * 
 * Orchestrates all AURA components to create a seamless biometric-responsive
 * interface experience for the Elite Command Data API.
 */

class AURASystem {
    constructor(options = {}) {
        this.options = {
            userId: null,
            enableBiometricTracking: true,
            enableAdaptiveUI: true,
            enablePrivacyProcessing: true,
            privacyLevel: 'standard',
            autoStart: false,
            debugMode: false,
            ...options
        };
        
        this.isInitialized = false;
        this.isActive = false;
        this.sessionId = null;
        
        // Component instances
        this.biometricTracker = null;
        this.adaptiveUI = null;
        this.privacyProcessor = null;
        
        // System state
        this.systemState = {
            biometricTracking: 'inactive',
            adaptiveUI: 'inactive',
            privacyProcessing: 'inactive',
            lastAdaptation: null,
            performanceMetrics: {}
        };
        
        // Event handlers
        this.eventHandlers = {
            onSystemReady: null,
            onAdaptation: null,
            onError: null,
            onPrivacyUpdate: null
        };
        
        // Performance monitoring
        this.performanceMonitor = {
            startTime: null,
            adaptationCount: 0,
            errorCount: 0,
            averageProcessingTime: 0
        };
        
        this.log('AURA System initialized');
    }
    
    /**
     * Initialize the complete AURA system
     */
    async initialize(userId) {
        try {
            this.options.userId = userId;
            this.performanceMonitor.startTime = performance.now();
            
            this.log('Initializing AURA system...');
            
            // Step 1: Initialize Privacy Processor first
            if (this.options.enablePrivacyProcessing) {
                await this.initializePrivacyProcessor();
            }
            
            // Step 2: Initialize Adaptive UI
            if (this.options.enableAdaptiveUI) {
                await this.initializeAdaptiveUI();
            }
            
            // Step 3: Initialize Biometric Tracker
            if (this.options.enableBiometricTracking) {
                await this.initializeBiometricTracker();
            }
            
            // Step 4: Setup system integration
            this.setupSystemIntegration();
            
            // Step 5: Setup error handling
            this.setupErrorHandling();
            
            this.isInitialized = true;
            this.systemState.status = 'ready';
            
            this.log('AURA system initialized successfully');
            
            // Auto-start if configured
            if (this.options.autoStart) {
                await this.start();
            }
            
            // Trigger ready event
            if (this.eventHandlers.onSystemReady) {
                this.eventHandlers.onSystemReady(this.getSystemStatus());
            }
            
            return {
                success: true,
                sessionId: this.sessionId,
                capabilities: this.getCapabilities(),
                status: this.getSystemStatus()
            };
            
        } catch (error) {
            this.handleSystemError('System initialization failed', error);
            return { success: false, error: error.message };
        }
    }
    
    /**
     * Initialize Privacy Processor
     */
    async initializePrivacyProcessor() {
        this.log('Initializing Privacy Processor...');
        
        this.privacyProcessor = new AURAPrivacyProcessor({
            privacyLevel: this.options.privacyLevel,
            debugMode: this.options.debugMode
        });
        
        const result = await this.privacyProcessor.initialize();
        if (!result.success) {
            throw new Error(`Privacy processor initialization failed: ${result.error}`);
        }
        
        this.systemState.privacyProcessing = 'active';
        this.log('Privacy Processor initialized');
    }
    
    /**
     * Initialize Adaptive UI
     */
    async initializeAdaptiveUI() {
        this.log('Initializing Adaptive UI...');
        
        this.adaptiveUI = new AURAAdaptiveUI({
            debugMode: this.options.debugMode
        });
        
        const result = this.adaptiveUI.initialize();
        if (!result.success) {
            throw new Error(`Adaptive UI initialization failed: ${result.error}`);
        }
        
        this.systemState.adaptiveUI = 'active';
        this.log('Adaptive UI initialized');
    }
    
    /**
     * Initialize Biometric Tracker
     */
    async initializeBiometricTracker() {
        this.log('Initializing Biometric Tracker...');
        
        this.biometricTracker = new AURABiometricTracker({
            privacyMode: this.options.privacyLevel,
            debugMode: this.options.debugMode
        });
        
        const result = await this.biometricTracker.initialize(this.options.userId);
        if (!result.success) {
            throw new Error(`Biometric tracker initialization failed: ${result.error}`);
        }
        
        this.sessionId = result.sessionId;
        this.systemState.biometricTracking = 'active';
        this.log('Biometric Tracker initialized');
    }
    
    /**
     * Setup system integration between components
     */
    setupSystemIntegration() {
        // Connect biometric tracker to privacy processor and adaptive UI
        if (this.biometricTracker) {
            this.biometricTracker.onData((biometricData, backendResponse) => {
                this.handleBiometricData(biometricData, backendResponse);
            });
            
            this.biometricTracker.onAdaptation((adaptation) => {
                this.handleAdaptationRequest(adaptation);
            });
            
            this.biometricTracker.onError((error) => {
                this.handleComponentError('BiometricTracker', error);
            });
        }
        
        this.log('System integration setup complete');
    }
    
    /**
     * Setup error handling
     */
    setupErrorHandling() {
        // Global error handler
        window.addEventListener('error', (event) => {
            this.handleSystemError('Global error', event.error);
        });
        
        // Unhandled promise rejection handler
        window.addEventListener('unhandledrejection', (event) => {
            this.handleSystemError('Unhandled promise rejection', event.reason);
        });
    }
    
    /**
     * Start the AURA system
     */
    async start() {
        if (!this.isInitialized) {
            throw new Error('System not initialized');
        }
        
        if (this.isActive) {
            this.log('System already active');
            return;
        }
        
        try {
            this.log('Starting AURA system...');
            
            // Start biometric tracking
            if (this.biometricTracker) {
                await this.biometricTracker.startTracking();
            }
            
            this.isActive = true;
            this.systemState.status = 'active';
            
            this.log('AURA system started successfully');
            
            return { success: true, status: 'active' };
            
        } catch (error) {
            this.handleSystemError('Failed to start system', error);
            return { success: false, error: error.message };
        }
    }
    
    /**
     * Stop the AURA system
     */
    async stop() {
        if (!this.isActive) {
            return;
        }
        
        try {
            this.log('Stopping AURA system...');
            
            // Stop biometric tracking
            if (this.biometricTracker) {
                await this.biometricTracker.stopTracking();
            }
            
            // Reset adaptive UI to default state
            if (this.adaptiveUI) {
                this.adaptiveUI.resetToDefault();
            }
            
            this.isActive = false;
            this.systemState.status = 'stopped';
            
            this.log('AURA system stopped');
            
            return { success: true, status: 'stopped' };
            
        } catch (error) {
            this.handleSystemError('Failed to stop system', error);
            return { success: false, error: error.message };
        }
    }
    
    /**
     * Handle biometric data from tracker
     */
    async handleBiometricData(biometricData, backendResponse) {
        try {
            const processingStart = performance.now();
            
            // Process data through privacy processor
            let processedData = biometricData;
            if (this.privacyProcessor) {
                const privacyResult = await this.privacyProcessor.processPrivately(biometricData);
                processedData = privacyResult.localInsights;
            }
            
            // Handle any adaptations from backend response
            if (backendResponse && backendResponse.adaptations) {
                for (const adaptation of backendResponse.adaptations) {
                    await this.handleAdaptationRequest(adaptation);
                }
            }
            
            // Update performance metrics
            const processingTime = performance.now() - processingStart;
            this.updatePerformanceMetrics(processingTime);
            
            this.log('Biometric data processed', { 
                dataQuality: biometricData.confidence,
                processingTime: processingTime
            });
            
        } catch (error) {
            this.handleComponentError('BiometricDataProcessing', error);
        }
    }
    
    /**
     * Handle adaptation request
     */
    async handleAdaptationRequest(adaptation) {
        try {
            if (!this.adaptiveUI) {
                this.log('Adaptive UI not available, skipping adaptation');
                return;
            }
            
            this.log('Applying adaptation', adaptation);
            
            // Apply the adaptation
            await this.adaptiveUI.applyAdaptation(adaptation);
            
            // Record the adaptation
            this.systemState.lastAdaptation = {
                ...adaptation,
                timestamp: Date.now()
            };
            
            this.performanceMonitor.adaptationCount++;
            
            // Trigger adaptation event
            if (this.eventHandlers.onAdaptation) {
                this.eventHandlers.onAdaptation(adaptation);
            }
            
        } catch (error) {
            this.handleComponentError('AdaptationApplication', error);
        }
    }
    
    /**
     * Handle component errors
     */
    handleComponentError(component, error) {
        this.performanceMonitor.errorCount++;
        
        const errorInfo = {
            component: component,
            error: error.message || error,
            timestamp: Date.now(),
            systemState: this.systemState
        };
        
        this.log(`Component error in ${component}:`, errorInfo);
        
        // Trigger error event
        if (this.eventHandlers.onError) {
            this.eventHandlers.onError(errorInfo);
        }
        
        // Attempt recovery based on error type
        this.attemptErrorRecovery(component, error);
    }
    
    /**
     * Handle system-level errors
     */
    handleSystemError(message, error) {
        this.performanceMonitor.errorCount++;
        
        const errorInfo = {
            type: 'system',
            message: message,
            error: error.message || error,
            timestamp: Date.now(),
            systemState: this.systemState
        };
        
        console.error('AURA System Error:', errorInfo);
        
        // Trigger error event
        if (this.eventHandlers.onError) {
            this.eventHandlers.onError(errorInfo);
        }
    }
    
    /**
     * Attempt error recovery
     */
    attemptErrorRecovery(component, error) {
        switch (component) {
            case 'BiometricTracker':
                // Try to restart biometric tracking
                setTimeout(async () => {
                    try {
                        if (this.biometricTracker && this.isActive) {
                            await this.biometricTracker.startTracking();
                            this.log('Biometric tracking recovered');
                        }
                    } catch (recoveryError) {
                        this.log('Failed to recover biometric tracking:', recoveryError);
                    }
                }, 5000);
                break;
                
            case 'AdaptiveUI':
                // Reset UI to safe state
                if (this.adaptiveUI) {
                    this.adaptiveUI.resetToDefault();
                    this.log('Adaptive UI reset to default state');
                }
                break;
                
            default:
                this.log(`No recovery strategy for component: ${component}`);
        }
    }
    
    /**
     * Update performance metrics
     */
    updatePerformanceMetrics(processingTime) {
        const metrics = this.performanceMonitor;
        
        // Update average processing time
        const totalProcessingTime = metrics.averageProcessingTime * metrics.adaptationCount + processingTime;
        metrics.averageProcessingTime = totalProcessingTime / (metrics.adaptationCount + 1);
        
        // Update system state
        this.systemState.performanceMetrics = {
            uptime: performance.now() - metrics.startTime,
            adaptationCount: metrics.adaptationCount,
            errorCount: metrics.errorCount,
            averageProcessingTime: metrics.averageProcessingTime,
            errorRate: metrics.errorCount / Math.max(metrics.adaptationCount, 1)
        };
    }
    
    /**
     * Get system capabilities
     */
    getCapabilities() {
        const capabilities = {
            biometricTracking: false,
            adaptiveUI: false,
            privacyProcessing: false
        };
        
        if (this.biometricTracker) {
            capabilities.biometricTracking = this.biometricTracker.getCapabilities();
        }
        
        if (this.adaptiveUI) {
            capabilities.adaptiveUI = true;
        }
        
        if (this.privacyProcessor) {
            capabilities.privacyProcessing = this.privacyProcessor.getPrivacyMetrics();
        }
        
        return capabilities;
    }
    
    /**
     * Get system status
     */
    getSystemStatus() {
        return {
            isInitialized: this.isInitialized,
            isActive: this.isActive,
            sessionId: this.sessionId,
            systemState: this.systemState,
            performanceMetrics: this.systemState.performanceMetrics,
            timestamp: Date.now()
        };
    }
    
    /**
     * Update privacy settings
     */
    updatePrivacySettings(newSettings) {
        if (this.privacyProcessor) {
            this.privacyProcessor.updatePrivacySettings(newSettings);
            
            // Update system options
            Object.assign(this.options, newSettings);
            
            // Trigger privacy update event
            if (this.eventHandlers.onPrivacyUpdate) {
                this.eventHandlers.onPrivacyUpdate(newSettings);
            }
            
            this.log('Privacy settings updated', newSettings);
        }
    }
    
    /**
     * Get adaptation history
     */
    getAdaptationHistory() {
        if (this.adaptiveUI) {
            return this.adaptiveUI.getCurrentState().adaptationHistory;
        }
        return [];
    }
    
    /**
     * Manual adaptation trigger
     */
    async triggerAdaptation(adaptationType, parameters) {
        const adaptation = {
            type: adaptationType,
            parameters: parameters,
            confidence: 1.0,
            urgency: 0.5,
            source: 'manual'
        };
        
        await this.handleAdaptationRequest(adaptation);
    }
    
    /**
     * Set event handlers
     */
    onSystemReady(callback) {
        this.eventHandlers.onSystemReady = callback;
    }
    
    onAdaptation(callback) {
        this.eventHandlers.onAdaptation = callback;
    }
    
    onError(callback) {
        this.eventHandlers.onError = callback;
    }
    
    onPrivacyUpdate(callback) {
        this.eventHandlers.onPrivacyUpdate = callback;
    }
    
    /**
     * Get performance report
     */
    getPerformanceReport() {
        const biometricMetrics = this.biometricTracker ? 
            this.biometricTracker.getPerformanceMetrics() : {};
        
        const privacyMetrics = this.privacyProcessor ? 
            this.privacyProcessor.getPrivacyMetrics() : {};
        
        return {
            system: this.systemState.performanceMetrics,
            biometric: biometricMetrics,
            privacy: privacyMetrics,
            timestamp: Date.now()
        };
    }
    
    /**
     * Export system configuration
     */
    exportConfiguration() {
        return {
            options: { ...this.options },
            capabilities: this.getCapabilities(),
            systemState: this.systemState,
            timestamp: Date.now()
        };
    }
    
    /**
     * Import system configuration
     */
    importConfiguration(config) {
        if (config.options) {
            Object.assign(this.options, config.options);
            this.log('Configuration imported', config.options);
        }
    }
    
    /**
     * Log messages
     */
    log(message, data = null) {
        if (this.options.debugMode) {
            console.log(`[AURA System] ${message}`, data || '');
        }
    }
    
    /**
     * Cleanup system resources
     */
    async cleanup() {
        try {
            // Stop the system
            await this.stop();
            
            // Cleanup components
            if (this.biometricTracker) {
                this.biometricTracker.cleanup();
            }
            
            if (this.adaptiveUI) {
                this.adaptiveUI.cleanup();
            }
            
            if (this.privacyProcessor) {
                this.privacyProcessor.cleanup();
            }
            
            // Reset state
            this.isInitialized = false;
            this.isActive = false;
            this.sessionId = null;
            
            this.log('AURA System cleaned up');
            
        } catch (error) {
            this.handleSystemError('Cleanup failed', error);
        }
    }
}

// Global AURA system instance
let globalAURASystem = null;

/**
 * Initialize global AURA system
 */
async function initializeAURA(userId, options = {}) {
    if (globalAURASystem) {
        console.warn('AURA system already initialized');
        return globalAURASystem;
    }
    
    globalAURASystem = new AURASystem(options);
    const result = await globalAURASystem.initialize(userId);
    
    if (!result.success) {
        globalAURASystem = null;
        throw new Error(`AURA initialization failed: ${result.error}`);
    }
    
    return globalAURASystem;
}

/**
 * Get global AURA system instance
 */
function getAURASystem() {
    return globalAURASystem;
}

/**
 * Cleanup global AURA system
 */
async function cleanupAURA() {
    if (globalAURASystem) {
        await globalAURASystem.cleanup();
        globalAURASystem = null;
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { 
        AURASystem, 
        initializeAURA, 
        getAURASystem, 
        cleanupAURA 
    };
} else if (typeof window !== 'undefined') {
    window.AURASystem = AURASystem;
    window.initializeAURA = initializeAURA;
    window.getAURASystem = getAURASystem;
    window.cleanupAURA = cleanupAURA;
}

