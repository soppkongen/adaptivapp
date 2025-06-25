/**
 * AURA Biometric Tracker
 * 
 * Client-side biometric tracking library for face and eye tracking
 * using WebRTC and TensorFlow.js for privacy-preserving analysis.
 */

class AURABiometricTracker {
    constructor(options = {}) {
        this.options = {
            enableFaceTracking: true,
            enableEyeTracking: true,
            enableEmotionDetection: true,
            samplingRate: 10, // Hz
            confidenceThreshold: 0.7,
            privacyMode: 'standard', // 'minimal', 'standard', 'comprehensive'
            debugMode: false,
            ...options
        };
        
        this.isInitialized = false;
        this.isTracking = false;
        this.sessionId = null;
        this.userId = null;
        
        // Video and canvas elements
        this.videoElement = null;
        this.canvasElement = null;
        this.canvasContext = null;
        
        // ML models
        this.faceModel = null;
        this.emotionModel = null;
        this.gazeModel = null;
        
        // Tracking data
        this.lastReading = null;
        this.calibrationData = null;
        
        // Event handlers
        this.onDataCallback = null;
        this.onAdaptationCallback = null;
        this.onErrorCallback = null;
        
        // Performance monitoring
        this.performanceMetrics = {
            frameRate: 0,
            processingTime: 0,
            modelLoadTime: 0
        };
        
        this.log('AURA Biometric Tracker initialized');
    }
    
    /**
     * Initialize the biometric tracking system
     */
    async initialize(userId, sessionId = null) {
        try {
            this.userId = userId;
            this.sessionId = sessionId || this.generateSessionId();
            
            this.log('Initializing biometric tracking...');
            
            // Load required ML models
            await this.loadModels();
            
            // Setup video capture
            await this.setupVideoCapture();
            
            // Setup canvas for processing
            this.setupCanvas();
            
            // Initialize calibration if needed
            if (this.options.enableEyeTracking) {
                await this.initializeCalibration();
            }
            
            this.isInitialized = true;
            this.log('Biometric tracking initialized successfully');
            
            return {
                success: true,
                sessionId: this.sessionId,
                capabilities: this.getCapabilities()
            };
            
        } catch (error) {
            this.handleError('Initialization failed', error);
            return { success: false, error: error.message };
        }
    }
    
    /**
     * Load required machine learning models
     */
    async loadModels() {
        const startTime = performance.now();
        
        try {
            // Load face detection model (MediaPipe or TensorFlow.js)
            if (this.options.enableFaceTracking) {
                this.log('Loading face detection model...');
                // Using a lightweight face detection model
                this.faceModel = await this.loadFaceDetectionModel();
            }
            
            // Load emotion recognition model
            if (this.options.enableEmotionDetection) {
                this.log('Loading emotion detection model...');
                this.emotionModel = await this.loadEmotionModel();
            }
            
            // Load gaze estimation model
            if (this.options.enableEyeTracking) {
                this.log('Loading gaze estimation model...');
                this.gazeModel = await this.loadGazeModel();
            }
            
            this.performanceMetrics.modelLoadTime = performance.now() - startTime;
            this.log(`Models loaded in ${this.performanceMetrics.modelLoadTime.toFixed(2)}ms`);
            
        } catch (error) {
            throw new Error(`Failed to load ML models: ${error.message}`);
        }
    }
    
    /**
     * Load face detection model
     */
    async loadFaceDetectionModel() {
        // Using TensorFlow.js BlazeFace model for lightweight face detection
        const model = await tf.loadLayersModel('/models/blazeface/model.json');
        return model;
    }
    
    /**
     * Load emotion recognition model
     */
    async loadEmotionModel() {
        // Load a pre-trained emotion recognition model
        const model = await tf.loadLayersModel('/models/emotion/model.json');
        return model;
    }
    
    /**
     * Load gaze estimation model
     */
    async loadGazeModel() {
        // Load gaze estimation model
        const model = await tf.loadLayersModel('/models/gaze/model.json');
        return model;
    }
    
    /**
     * Setup video capture from webcam
     */
    async setupVideoCapture() {
        try {
            // Create video element
            this.videoElement = document.createElement('video');
            this.videoElement.width = 640;
            this.videoElement.height = 480;
            this.videoElement.autoplay = true;
            this.videoElement.muted = true;
            
            // Get user media
            const stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 640 },
                    height: { ideal: 480 },
                    frameRate: { ideal: 30 }
                }
            });
            
            this.videoElement.srcObject = stream;
            
            // Wait for video to be ready
            await new Promise((resolve) => {
                this.videoElement.onloadedmetadata = resolve;
            });
            
            this.log('Video capture setup complete');
            
        } catch (error) {
            throw new Error(`Failed to setup video capture: ${error.message}`);
        }
    }
    
    /**
     * Setup canvas for image processing
     */
    setupCanvas() {
        this.canvasElement = document.createElement('canvas');
        this.canvasElement.width = this.videoElement.width;
        this.canvasElement.height = this.videoElement.height;
        this.canvasContext = this.canvasElement.getContext('2d');
        
        // Hide canvas (processing only)
        this.canvasElement.style.display = 'none';
        document.body.appendChild(this.canvasElement);
    }
    
    /**
     * Initialize eye tracking calibration
     */
    async initializeCalibration() {
        this.log('Starting eye tracking calibration...');
        
        // Simple 9-point calibration
        const calibrationPoints = [
            [0.1, 0.1], [0.5, 0.1], [0.9, 0.1],
            [0.1, 0.5], [0.5, 0.5], [0.9, 0.5],
            [0.1, 0.9], [0.5, 0.9], [0.9, 0.9]
        ];
        
        this.calibrationData = {
            points: calibrationPoints,
            measurements: [],
            quality: 0
        };
        
        // In a real implementation, this would show calibration UI
        // and collect gaze data for each point
        this.log('Calibration initialized (simplified for demo)');
    }
    
    /**
     * Start biometric tracking
     */
    async startTracking() {
        if (!this.isInitialized) {
            throw new Error('Tracker not initialized');
        }
        
        if (this.isTracking) {
            this.log('Tracking already active');
            return;
        }
        
        this.isTracking = true;
        this.log('Starting biometric tracking...');
        
        // Start the tracking loop
        this.trackingLoop();
        
        // Start session with backend
        await this.startBiometricSession();
    }
    
    /**
     * Stop biometric tracking
     */
    async stopTracking() {
        if (!this.isTracking) {
            return;
        }
        
        this.isTracking = false;
        this.log('Stopping biometric tracking...');
        
        // End session with backend
        await this.endBiometricSession();
    }
    
    /**
     * Main tracking loop
     */
    async trackingLoop() {
        if (!this.isTracking) {
            return;
        }
        
        const startTime = performance.now();
        
        try {
            // Capture current frame
            const imageData = this.captureFrame();
            
            // Process biometric data
            const biometricData = await this.processBiometricData(imageData);
            
            // Send data to backend and get adaptations
            if (biometricData && biometricData.confidence > this.options.confidenceThreshold) {
                await this.sendBiometricData(biometricData);
            }
            
            // Update performance metrics
            this.performanceMetrics.processingTime = performance.now() - startTime;
            this.performanceMetrics.frameRate = 1000 / this.performanceMetrics.processingTime;
            
        } catch (error) {
            this.handleError('Tracking loop error', error);
        }
        
        // Schedule next frame
        const targetInterval = 1000 / this.options.samplingRate;
        const actualInterval = Math.max(0, targetInterval - this.performanceMetrics.processingTime);
        
        setTimeout(() => this.trackingLoop(), actualInterval);
    }
    
    /**
     * Capture current video frame
     */
    captureFrame() {
        this.canvasContext.drawImage(
            this.videoElement, 
            0, 0, 
            this.canvasElement.width, 
            this.canvasElement.height
        );
        
        return this.canvasContext.getImageData(
            0, 0, 
            this.canvasElement.width, 
            this.canvasElement.height
        );
    }
    
    /**
     * Process biometric data from image
     */
    async processBiometricData(imageData) {
        const results = {
            timestamp: new Date().toISOString(),
            facial_expressions: {},
            gaze_position: [0.5, 0.5],
            pupil_diameter: 0.5,
            blink_rate: 0.15,
            attention_score: 0.5,
            stress_level: 0.3,
            cognitive_load: 0.4,
            confidence: 0.8
        };
        
        try {
            // Convert ImageData to tensor
            const tensor = this.imageDataToTensor(imageData);
            
            // Face detection and analysis
            if (this.faceModel && this.options.enableFaceTracking) {
                const faceData = await this.detectFace(tensor);
                if (faceData) {
                    results.confidence = faceData.confidence;
                    
                    // Emotion detection
                    if (this.emotionModel && this.options.enableEmotionDetection) {
                        results.facial_expressions = await this.detectEmotions(faceData.faceRegion);
                    }
                    
                    // Eye tracking and gaze estimation
                    if (this.gazeModel && this.options.enableEyeTracking) {
                        const gazeData = await this.estimateGaze(faceData.eyeRegions);
                        results.gaze_position = gazeData.position;
                        results.pupil_diameter = gazeData.pupilDiameter;
                        results.blink_rate = gazeData.blinkRate;
                    }
                    
                    // Calculate derived metrics
                    results.attention_score = this.calculateAttentionScore(results);
                    results.stress_level = this.calculateStressLevel(results);
                    results.cognitive_load = this.calculateCognitiveLoad(results);
                }
            }
            
            // Clean up tensor
            tensor.dispose();
            
            this.lastReading = results;
            return results;
            
        } catch (error) {
            this.handleError('Biometric processing error', error);
            return null;
        }
    }
    
    /**
     * Convert ImageData to TensorFlow tensor
     */
    imageDataToTensor(imageData) {
        const tensor = tf.browser.fromPixels(imageData)
            .resizeNearestNeighbor([224, 224]) // Resize to model input size
            .toFloat()
            .div(255.0) // Normalize to 0-1
            .expandDims(0); // Add batch dimension
        
        return tensor;
    }
    
    /**
     * Detect face in image
     */
    async detectFace(tensor) {
        try {
            const predictions = await this.faceModel.predict(tensor).data();
            
            // Process face detection results
            // This is simplified - real implementation would parse bounding boxes
            const confidence = Math.max(...predictions);
            
            if (confidence > this.options.confidenceThreshold) {
                return {
                    confidence: confidence,
                    faceRegion: tensor, // In real implementation, would crop face region
                    eyeRegions: tensor  // In real implementation, would extract eye regions
                };
            }
            
            return null;
            
        } catch (error) {
            this.handleError('Face detection error', error);
            return null;
        }
    }
    
    /**
     * Detect emotions from face region
     */
    async detectEmotions(faceRegion) {
        try {
            const predictions = await this.emotionModel.predict(faceRegion).data();
            
            // Map predictions to emotion labels
            const emotions = ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral'];
            const emotionScores = {};
            
            emotions.forEach((emotion, index) => {
                emotionScores[emotion] = predictions[index] || 0;
            });
            
            return emotionScores;
            
        } catch (error) {
            this.handleError('Emotion detection error', error);
            return { neutral: 1.0 };
        }
    }
    
    /**
     * Estimate gaze direction and eye metrics
     */
    async estimateGaze(eyeRegions) {
        try {
            const predictions = await this.gazeModel.predict(eyeRegions).data();
            
            // Process gaze estimation results
            return {
                position: [predictions[0] || 0.5, predictions[1] || 0.5],
                pupilDiameter: predictions[2] || 0.5,
                blinkRate: predictions[3] || 0.15
            };
            
        } catch (error) {
            this.handleError('Gaze estimation error', error);
            return {
                position: [0.5, 0.5],
                pupilDiameter: 0.5,
                blinkRate: 0.15
            };
        }
    }
    
    /**
     * Calculate attention score from biometric data
     */
    calculateAttentionScore(data) {
        // Simplified attention calculation
        const gazeStability = 1.0 - Math.abs(data.gaze_position[0] - 0.5) - Math.abs(data.gaze_position[1] - 0.5);
        const emotionalEngagement = data.facial_expressions.happy + data.facial_expressions.surprise;
        const blinkNormality = 1.0 - Math.abs(data.blink_rate - 0.15) / 0.15;
        
        return Math.max(0, Math.min(1, (gazeStability + emotionalEngagement + blinkNormality) / 3));
    }
    
    /**
     * Calculate stress level from biometric data
     */
    calculateStressLevel(data) {
        // Simplified stress calculation
        const negativeEmotions = data.facial_expressions.angry + data.facial_expressions.fear + data.facial_expressions.sad;
        const pupilDilation = Math.max(0, data.pupil_diameter - 0.5) * 2;
        const blinkRate = Math.max(0, data.blink_rate - 0.15) / 0.15;
        
        return Math.max(0, Math.min(1, (negativeEmotions + pupilDilation + blinkRate) / 3));
    }
    
    /**
     * Calculate cognitive load from biometric data
     */
    calculateCognitiveLoad(data) {
        // Simplified cognitive load calculation
        const concentration = data.facial_expressions.neutral;
        const pupilDilation = data.pupil_diameter;
        const gazeIntensity = 1.0 - (Math.abs(data.gaze_position[0] - 0.5) + Math.abs(data.gaze_position[1] - 0.5));
        
        return Math.max(0, Math.min(1, (concentration + pupilDilation + gazeIntensity) / 3));
    }
    
    /**
     * Start biometric session with backend
     */
    async startBiometricSession() {
        try {
            const response = await fetch('/api/biometric/session/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_id: this.userId,
                    device_info: this.getDeviceInfo(),
                    privacy_settings: this.getPrivacySettings()
                })
            });
            
            const data = await response.json();
            if (data.session_id) {
                this.sessionId = data.session_id;
                this.log(`Biometric session started: ${this.sessionId}`);
            }
            
        } catch (error) {
            this.handleError('Failed to start session', error);
        }
    }
    
    /**
     * End biometric session with backend
     */
    async endBiometricSession() {
        if (!this.sessionId) return;
        
        try {
            await fetch(`/api/biometric/session/${this.sessionId}/end`, {
                method: 'POST'
            });
            
            this.log(`Biometric session ended: ${this.sessionId}`);
            
        } catch (error) {
            this.handleError('Failed to end session', error);
        }
    }
    
    /**
     * Send biometric data to backend
     */
    async sendBiometricData(data) {
        if (!this.sessionId) return;
        
        try {
            const response = await fetch('/api/biometric/data/ingest', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    ...data
                })
            });
            
            const result = await response.json();
            
            // Handle adaptations
            if (result.adaptations && result.adaptations.length > 0) {
                this.handleAdaptations(result.adaptations);
            }
            
            // Trigger data callback
            if (this.onDataCallback) {
                this.onDataCallback(data, result);
            }
            
        } catch (error) {
            this.handleError('Failed to send biometric data', error);
        }
    }
    
    /**
     * Handle interface adaptations
     */
    handleAdaptations(adaptations) {
        adaptations.forEach(adaptation => {
            this.log(`Applying adaptation: ${adaptation.type}`, adaptation.parameters);
            
            if (this.onAdaptationCallback) {
                this.onAdaptationCallback(adaptation);
            }
        });
    }
    
    /**
     * Get device information
     */
    getDeviceInfo() {
        return {
            userAgent: navigator.userAgent,
            screen: {
                width: screen.width,
                height: screen.height
            },
            video: {
                width: this.videoElement.width,
                height: this.videoElement.height
            },
            timestamp: new Date().toISOString()
        };
    }
    
    /**
     * Get privacy settings
     */
    getPrivacySettings() {
        return {
            privacy_mode: this.options.privacyMode,
            data_retention: '24h',
            sharing_enabled: false
        };
    }
    
    /**
     * Get system capabilities
     */
    getCapabilities() {
        return {
            face_tracking: this.options.enableFaceTracking && !!this.faceModel,
            emotion_detection: this.options.enableEmotionDetection && !!this.emotionModel,
            eye_tracking: this.options.enableEyeTracking && !!this.gazeModel,
            sampling_rate: this.options.samplingRate,
            privacy_mode: this.options.privacyMode
        };
    }
    
    /**
     * Generate session ID
     */
    generateSessionId() {
        return 'aura_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    /**
     * Set event callbacks
     */
    onData(callback) {
        this.onDataCallback = callback;
    }
    
    onAdaptation(callback) {
        this.onAdaptationCallback = callback;
    }
    
    onError(callback) {
        this.onErrorCallback = callback;
    }
    
    /**
     * Handle errors
     */
    handleError(message, error) {
        const errorInfo = {
            message: message,
            error: error.message || error,
            timestamp: new Date().toISOString()
        };
        
        console.error('AURA Biometric Tracker Error:', errorInfo);
        
        if (this.onErrorCallback) {
            this.onErrorCallback(errorInfo);
        }
    }
    
    /**
     * Log messages
     */
    log(message, data = null) {
        if (this.options.debugMode) {
            console.log(`[AURA] ${message}`, data || '');
        }
    }
    
    /**
     * Get performance metrics
     */
    getPerformanceMetrics() {
        return { ...this.performanceMetrics };
    }
    
    /**
     * Cleanup resources
     */
    cleanup() {
        this.stopTracking();
        
        if (this.videoElement && this.videoElement.srcObject) {
            this.videoElement.srcObject.getTracks().forEach(track => track.stop());
        }
        
        if (this.canvasElement && this.canvasElement.parentNode) {
            this.canvasElement.parentNode.removeChild(this.canvasElement);
        }
        
        // Dispose ML models
        if (this.faceModel) this.faceModel.dispose();
        if (this.emotionModel) this.emotionModel.dispose();
        if (this.gazeModel) this.gazeModel.dispose();
        
        this.log('AURA Biometric Tracker cleaned up');
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AURABiometricTracker;
} else if (typeof window !== 'undefined') {
    window.AURABiometricTracker = AURABiometricTracker;
}

