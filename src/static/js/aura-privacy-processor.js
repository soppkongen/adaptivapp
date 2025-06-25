/**
 * AURA Privacy-First Local Processing System
 * 
 * Ensures all sensitive biometric data is processed locally with privacy-preserving
 * techniques, only sending anonymized insights to the backend.
 */

class AURAPrivacyProcessor {
    constructor(options = {}) {
        this.options = {
            privacyLevel: 'standard', // 'minimal', 'standard', 'comprehensive'
            dataRetentionHours: 24,
            anonymizationStrength: 'high', // 'low', 'medium', 'high'
            enableLocalStorage: true,
            enableEncryption: true,
            debugMode: false,
            ...options
        };
        
        this.isInitialized = false;
        this.encryptionKey = null;
        this.localDataStore = new Map();
        this.anonymizationSalt = null;
        
        // Privacy metrics
        this.privacyMetrics = {
            dataPointsProcessed: 0,
            dataPointsAnonymized: 0,
            dataPointsDiscarded: 0,
            encryptionOperations: 0
        };
        
        this.log('AURA Privacy Processor initialized');
    }
    
    /**
     * Initialize privacy processing system
     */
    async initialize() {
        try {
            // Generate encryption key for local data
            await this.generateEncryptionKey();
            
            // Generate anonymization salt
            this.generateAnonymizationSalt();
            
            // Setup local storage
            this.setupLocalStorage();
            
            // Setup data retention policies
            this.setupDataRetention();
            
            this.isInitialized = true;
            this.log('Privacy processing system initialized');
            
            return { success: true };
            
        } catch (error) {
            console.error('Failed to initialize privacy processor:', error);
            return { success: false, error: error.message };
        }
    }
    
    /**
     * Generate encryption key for local data protection
     */
    async generateEncryptionKey() {
        if (!this.options.enableEncryption) {
            return;
        }
        
        try {
            // Generate a random encryption key
            const keyMaterial = window.crypto.getRandomValues(new Uint8Array(32));
            
            // Import key for AES-GCM encryption
            this.encryptionKey = await window.crypto.subtle.importKey(
                'raw',
                keyMaterial,
                { name: 'AES-GCM' },
                false,
                ['encrypt', 'decrypt']
            );
            
            this.log('Encryption key generated');
            
        } catch (error) {
            console.warn('Encryption not available, falling back to plain storage');
            this.options.enableEncryption = false;
        }
    }
    
    /**
     * Generate anonymization salt
     */
    generateAnonymizationSalt() {
        this.anonymizationSalt = window.crypto.getRandomValues(new Uint8Array(16));
        this.log('Anonymization salt generated');
    }
    
    /**
     * Setup local storage system
     */
    setupLocalStorage() {
        if (!this.options.enableLocalStorage) {
            return;
        }
        
        // Check storage availability
        try {
            localStorage.setItem('aura_test', 'test');
            localStorage.removeItem('aura_test');
            this.log('Local storage available');
        } catch (error) {
            console.warn('Local storage not available, using memory only');
            this.options.enableLocalStorage = false;
        }
    }
    
    /**
     * Setup data retention policies
     */
    setupDataRetention() {
        // Clean up old data periodically
        setInterval(() => {
            this.cleanupOldData();
        }, 60000); // Check every minute
        
        // Clean up on page unload
        window.addEventListener('beforeunload', () => {
            this.cleanupSensitiveData();
        });
    }
    
    /**
     * Process biometric data with privacy preservation
     */
    async processPrivately(rawBiometricData) {
        if (!this.isInitialized) {
            throw new Error('Privacy processor not initialized');
        }
        
        this.privacyMetrics.dataPointsProcessed++;
        
        try {
            // Step 1: Local processing and analysis
            const localInsights = await this.extractLocalInsights(rawBiometricData);
            
            // Step 2: Apply privacy filters based on privacy level
            const filteredData = this.applyPrivacyFilters(localInsights);
            
            // Step 3: Anonymize the data
            const anonymizedData = await this.anonymizeData(filteredData);
            
            // Step 4: Store locally if enabled
            if (this.options.enableLocalStorage) {
                await this.storeLocally(rawBiometricData, anonymizedData);
            }
            
            // Step 5: Prepare data for backend (only anonymized insights)
            const backendData = this.prepareBackendData(anonymizedData);
            
            this.privacyMetrics.dataPointsAnonymized++;
            
            return {
                localInsights: localInsights,
                backendData: backendData,
                privacyLevel: this.options.privacyLevel
            };
            
        } catch (error) {
            this.log('Error in privacy processing:', error);
            this.privacyMetrics.dataPointsDiscarded++;
            throw error;
        }
    }
    
    /**
     * Extract insights locally without sending raw data
     */
    async extractLocalInsights(rawData) {
        const insights = {
            timestamp: rawData.timestamp,
            
            // Emotional state (aggregated)
            emotionalState: this.aggregateEmotionalState(rawData.facial_expressions),
            
            // Attention metrics (normalized)
            attentionMetrics: {
                level: this.normalizeValue(rawData.attention_score),
                stability: this.calculateAttentionStability(rawData),
                focus_quality: this.calculateFocusQuality(rawData)
            },
            
            // Stress indicators (categorized)
            stressIndicators: {
                level: this.categorizeStressLevel(rawData.stress_level),
                trend: this.calculateStressTrend(rawData),
                physiological: this.extractPhysiologicalStress(rawData)
            },
            
            // Cognitive load (simplified)
            cognitiveLoad: {
                level: this.categorizeCognitiveLoad(rawData.cognitive_load),
                processing_efficiency: this.calculateProcessingEfficiency(rawData)
            },
            
            // Interaction patterns (anonymized)
            interactionPatterns: {
                gaze_pattern: this.anonymizeGazePattern(rawData.gaze_position),
                engagement_level: this.calculateEngagementLevel(rawData),
                decision_confidence: this.calculateDecisionConfidence(rawData)
            },
            
            // Quality metrics
            dataQuality: rawData.confidence,
            processingLatency: performance.now()
        };
        
        return insights;
    }
    
    /**
     * Aggregate emotional state without exposing specific expressions
     */
    aggregateEmotionalState(expressions) {
        const positive = (expressions.happy || 0) + (expressions.surprise || 0);
        const negative = (expressions.angry || 0) + (expressions.sad || 0) + (expressions.fear || 0);
        const neutral = expressions.neutral || 0;
        
        // Return aggregated emotional valence
        if (positive > negative && positive > neutral) {
            return 'positive';
        } else if (negative > positive && negative > neutral) {
            return 'negative';
        } else {
            return 'neutral';
        }
    }
    
    /**
     * Calculate attention stability without exposing exact gaze coordinates
     */
    calculateAttentionStability(data) {
        // Use relative stability measures instead of absolute coordinates
        const gazeVariance = Math.abs(data.gaze_position[0] - 0.5) + Math.abs(data.gaze_position[1] - 0.5);
        return Math.max(0, 1 - gazeVariance);
    }
    
    /**
     * Calculate focus quality from multiple indicators
     */
    calculateFocusQuality(data) {
        const blinkNormality = 1 - Math.abs(data.blink_rate - 0.15) / 0.15;
        const pupilStability = 1 - Math.abs(data.pupil_diameter - 0.5);
        const attentionScore = data.attention_score;
        
        return (blinkNormality + pupilStability + attentionScore) / 3;
    }
    
    /**
     * Categorize stress level instead of exact values
     */
    categorizeStressLevel(stressLevel) {
        if (stressLevel < 0.3) return 'low';
        if (stressLevel < 0.6) return 'moderate';
        if (stressLevel < 0.8) return 'high';
        return 'very_high';
    }
    
    /**
     * Calculate stress trend without storing historical data
     */
    calculateStressTrend(data) {
        // Use current indicators to infer trend
        const physiologicalStress = data.pupil_diameter > 0.6 ? 'increasing' : 'stable';
        const emotionalStress = this.aggregateEmotionalState(data.facial_expressions) === 'negative' ? 'increasing' : 'stable';
        
        return physiologicalStress === 'increasing' || emotionalStress === 'increasing' ? 'increasing' : 'stable';
    }
    
    /**
     * Extract physiological stress indicators
     */
    extractPhysiologicalStress(data) {
        return {
            pupil_response: data.pupil_diameter > 0.6 ? 'elevated' : 'normal',
            blink_pattern: data.blink_rate > 0.2 ? 'rapid' : 'normal'
        };
    }
    
    /**
     * Categorize cognitive load
     */
    categorizeCognitiveLoad(cognitiveLoad) {
        if (cognitiveLoad < 0.4) return 'low';
        if (cognitiveLoad < 0.7) return 'moderate';
        return 'high';
    }
    
    /**
     * Calculate processing efficiency
     */
    calculateProcessingEfficiency(data) {
        // Combine attention and cognitive load for efficiency measure
        const efficiency = data.attention_score / Math.max(data.cognitive_load, 0.1);
        return Math.min(efficiency, 2.0); // Cap at 2.0
    }
    
    /**
     * Anonymize gaze pattern by using relative zones
     */
    anonymizeGazePattern(gazePosition) {
        const [x, y] = gazePosition;
        
        // Convert to zone-based representation
        const zoneX = x < 0.33 ? 'left' : x < 0.66 ? 'center' : 'right';
        const zoneY = y < 0.33 ? 'top' : y < 0.66 ? 'middle' : 'bottom';
        
        return `${zoneY}_${zoneX}`;
    }
    
    /**
     * Calculate engagement level
     */
    calculateEngagementLevel(data) {
        const attentionWeight = 0.4;
        const emotionalWeight = 0.3;
        const physiologicalWeight = 0.3;
        
        const emotionalEngagement = data.facial_expressions.happy + data.facial_expressions.surprise;
        const physiologicalEngagement = 1 - Math.abs(data.pupil_diameter - 0.5);
        
        const engagement = (
            data.attention_score * attentionWeight +
            emotionalEngagement * emotionalWeight +
            physiologicalEngagement * physiologicalWeight
        );
        
        return Math.max(0, Math.min(1, engagement));
    }
    
    /**
     * Calculate decision confidence
     */
    calculateDecisionConfidence(data) {
        const uncertainty = data.facial_expressions.surprise + data.facial_expressions.fear;
        const stability = this.calculateAttentionStability(data);
        
        return Math.max(0, stability - uncertainty);
    }
    
    /**
     * Apply privacy filters based on privacy level
     */
    applyPrivacyFilters(insights) {
        const filtered = { ...insights };
        
        switch (this.options.privacyLevel) {
            case 'minimal':
                // Only basic engagement metrics
                return {
                    timestamp: filtered.timestamp,
                    attentionMetrics: {
                        level: filtered.attentionMetrics.level
                    },
                    dataQuality: filtered.dataQuality
                };
                
            case 'standard':
                // Remove detailed physiological data
                delete filtered.stressIndicators.physiological;
                delete filtered.interactionPatterns.gaze_pattern;
                return filtered;
                
            case 'comprehensive':
                // Keep all insights but anonymized
                return filtered;
                
            default:
                return filtered;
        }
    }
    
    /**
     * Anonymize data using differential privacy techniques
     */
    async anonymizeData(data) {
        const anonymized = { ...data };
        
        // Add noise to numerical values based on anonymization strength
        const noiseLevel = this.getNoiseLevel();
        
        // Apply noise to attention metrics
        if (anonymized.attentionMetrics) {
            anonymized.attentionMetrics.level = this.addNoise(anonymized.attentionMetrics.level, noiseLevel);
            if (anonymized.attentionMetrics.stability) {
                anonymized.attentionMetrics.stability = this.addNoise(anonymized.attentionMetrics.stability, noiseLevel);
            }
        }
        
        // Apply noise to cognitive load
        if (anonymized.cognitiveLoad && anonymized.cognitiveLoad.processing_efficiency) {
            anonymized.cognitiveLoad.processing_efficiency = this.addNoise(
                anonymized.cognitiveLoad.processing_efficiency, 
                noiseLevel
            );
        }
        
        // Apply noise to engagement level
        if (anonymized.interactionPatterns && anonymized.interactionPatterns.engagement_level) {
            anonymized.interactionPatterns.engagement_level = this.addNoise(
                anonymized.interactionPatterns.engagement_level, 
                noiseLevel
            );
        }
        
        // Hash timestamp for temporal privacy
        anonymized.timestamp = await this.hashTimestamp(data.timestamp);
        
        return anonymized;
    }
    
    /**
     * Get noise level based on anonymization strength
     */
    getNoiseLevel() {
        switch (this.options.anonymizationStrength) {
            case 'low': return 0.01;
            case 'medium': return 0.05;
            case 'high': return 0.1;
            default: return 0.05;
        }
    }
    
    /**
     * Add calibrated noise to numerical values
     */
    addNoise(value, noiseLevel) {
        const noise = (Math.random() - 0.5) * 2 * noiseLevel;
        return Math.max(0, Math.min(1, value + noise));
    }
    
    /**
     * Hash timestamp for temporal privacy
     */
    async hashTimestamp(timestamp) {
        const data = new TextEncoder().encode(timestamp + this.anonymizationSalt);
        const hashBuffer = await crypto.subtle.digest('SHA-256', data);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        return hashArray.map(b => b.toString(16).padStart(2, '0')).join('').substring(0, 16);
    }
    
    /**
     * Store data locally with encryption
     */
    async storeLocally(rawData, anonymizedData) {
        const storageKey = `aura_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        
        const dataToStore = {
            raw: rawData,
            anonymized: anonymizedData,
            timestamp: Date.now(),
            privacyLevel: this.options.privacyLevel
        };
        
        try {
            if (this.options.enableEncryption && this.encryptionKey) {
                const encryptedData = await this.encryptData(JSON.stringify(dataToStore));
                this.localDataStore.set(storageKey, encryptedData);
                this.privacyMetrics.encryptionOperations++;
            } else {
                this.localDataStore.set(storageKey, dataToStore);
            }
            
            // Also store in localStorage if available
            if (this.options.enableLocalStorage) {
                const storageData = this.options.enableEncryption ? 
                    await this.encryptData(JSON.stringify(anonymizedData)) : 
                    JSON.stringify(anonymizedData);
                
                localStorage.setItem(storageKey, storageData);
            }
            
        } catch (error) {
            this.log('Error storing data locally:', error);
        }
    }
    
    /**
     * Encrypt data using AES-GCM
     */
    async encryptData(data) {
        if (!this.encryptionKey) {
            return data;
        }
        
        try {
            const iv = window.crypto.getRandomValues(new Uint8Array(12));
            const encodedData = new TextEncoder().encode(data);
            
            const encryptedData = await window.crypto.subtle.encrypt(
                { name: 'AES-GCM', iv: iv },
                this.encryptionKey,
                encodedData
            );
            
            // Combine IV and encrypted data
            const combined = new Uint8Array(iv.length + encryptedData.byteLength);
            combined.set(iv);
            combined.set(new Uint8Array(encryptedData), iv.length);
            
            return Array.from(combined);
            
        } catch (error) {
            this.log('Encryption failed:', error);
            return data;
        }
    }
    
    /**
     * Decrypt data using AES-GCM
     */
    async decryptData(encryptedArray) {
        if (!this.encryptionKey || !Array.isArray(encryptedArray)) {
            return encryptedArray;
        }
        
        try {
            const combined = new Uint8Array(encryptedArray);
            const iv = combined.slice(0, 12);
            const encryptedData = combined.slice(12);
            
            const decryptedData = await window.crypto.subtle.decrypt(
                { name: 'AES-GCM', iv: iv },
                this.encryptionKey,
                encryptedData
            );
            
            return new TextDecoder().decode(decryptedData);
            
        } catch (error) {
            this.log('Decryption failed:', error);
            return null;
        }
    }
    
    /**
     * Prepare data for backend transmission
     */
    prepareBackendData(anonymizedData) {
        // Only send aggregated, anonymized insights
        return {
            session_id: 'anonymous', // Don't send real session ID
            timestamp: anonymizedData.timestamp, // Already hashed
            
            // Aggregated metrics only
            attention_score: anonymizedData.attentionMetrics.level,
            stress_level: this.categoryToNumeric(anonymizedData.stressIndicators.level),
            cognitive_load: this.categoryToNumeric(anonymizedData.cognitiveLoad.level),
            
            // Anonymized patterns
            gaze_pattern: anonymizedData.interactionPatterns.gaze_pattern,
            engagement_level: anonymizedData.interactionPatterns.engagement_level,
            
            // Quality and confidence
            confidence: anonymizedData.dataQuality,
            privacy_level: this.options.privacyLevel
        };
    }
    
    /**
     * Convert category to numeric for backend processing
     */
    categoryToNumeric(category) {
        const mapping = {
            'low': 0.2,
            'moderate': 0.5,
            'high': 0.8,
            'very_high': 0.95
        };
        
        return mapping[category] || 0.5;
    }
    
    /**
     * Normalize value to 0-1 range
     */
    normalizeValue(value) {
        return Math.max(0, Math.min(1, value));
    }
    
    /**
     * Clean up old data based on retention policy
     */
    cleanupOldData() {
        const cutoffTime = Date.now() - (this.options.dataRetentionHours * 60 * 60 * 1000);
        
        // Clean up memory store
        for (const [key, data] of this.localDataStore.entries()) {
            const timestamp = data.timestamp || 0;
            if (timestamp < cutoffTime) {
                this.localDataStore.delete(key);
            }
        }
        
        // Clean up localStorage
        if (this.options.enableLocalStorage) {
            for (let i = localStorage.length - 1; i >= 0; i--) {
                const key = localStorage.key(i);
                if (key && key.startsWith('aura_')) {
                    try {
                        const data = JSON.parse(localStorage.getItem(key));
                        if (data.timestamp && data.timestamp < cutoffTime) {
                            localStorage.removeItem(key);
                        }
                    } catch (error) {
                        // Remove corrupted data
                        localStorage.removeItem(key);
                    }
                }
            }
        }
    }
    
    /**
     * Clean up sensitive data immediately
     */
    cleanupSensitiveData() {
        // Clear memory store
        this.localDataStore.clear();
        
        // Clear localStorage if configured for immediate cleanup
        if (this.options.enableLocalStorage && this.options.privacyLevel === 'comprehensive') {
            for (let i = localStorage.length - 1; i >= 0; i--) {
                const key = localStorage.key(i);
                if (key && key.startsWith('aura_')) {
                    localStorage.removeItem(key);
                }
            }
        }
        
        this.log('Sensitive data cleaned up');
    }
    
    /**
     * Get privacy metrics
     */
    getPrivacyMetrics() {
        return {
            ...this.privacyMetrics,
            localDataPoints: this.localDataStore.size,
            privacyLevel: this.options.privacyLevel,
            encryptionEnabled: this.options.enableEncryption,
            dataRetentionHours: this.options.dataRetentionHours
        };
    }
    
    /**
     * Update privacy settings
     */
    updatePrivacySettings(newSettings) {
        const oldLevel = this.options.privacyLevel;
        
        Object.assign(this.options, newSettings);
        
        // If privacy level increased, clean up more data
        if (this.getPrivacyLevelNumeric(this.options.privacyLevel) > this.getPrivacyLevelNumeric(oldLevel)) {
            this.cleanupSensitiveData();
        }
        
        this.log(`Privacy settings updated to ${this.options.privacyLevel}`);
    }
    
    /**
     * Get numeric privacy level for comparison
     */
    getPrivacyLevelNumeric(level) {
        const levels = { 'minimal': 1, 'standard': 2, 'comprehensive': 3 };
        return levels[level] || 2;
    }
    
    /**
     * Log messages
     */
    log(message, data = null) {
        if (this.options.debugMode) {
            console.log(`[AURA Privacy] ${message}`, data || '');
        }
    }
    
    /**
     * Cleanup resources
     */
    cleanup() {
        this.cleanupSensitiveData();
        
        // Clear encryption key
        this.encryptionKey = null;
        this.anonymizationSalt = null;
        
        this.log('AURA Privacy Processor cleaned up');
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AURAPrivacyProcessor;
} else if (typeof window !== 'undefined') {
    window.AURAPrivacyProcessor = AURAPrivacyProcessor;
}

