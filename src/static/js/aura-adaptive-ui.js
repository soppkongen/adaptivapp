/**
 * AURA Adaptive UI Response System
 * 
 * Handles real-time interface adaptations based on biometric feedback
 * with smooth animations and intelligent state management.
 */

class AURAAdaptiveUI {
    constructor(options = {}) {
        this.options = {
            animationDuration: 300,
            enableTransitions: true,
            respectUserPreferences: true,
            maxAdaptationsPerMinute: 10,
            debugMode: false,
            ...options
        };
        
        this.isInitialized = false;
        this.currentState = {};
        this.adaptationHistory = [];
        this.activeAdaptations = new Map();
        
        // Adaptation cooldowns
        this.cooldowns = new Map();
        
        // CSS custom properties for dynamic theming
        this.cssVariables = new Map();
        
        // Animation queue
        this.animationQueue = [];
        this.isAnimating = false;
        
        // State management
        this.stateStack = [];
        this.maxStateHistory = 10;
        
        this.log('AURA Adaptive UI initialized');
    }
    
    /**
     * Initialize the adaptive UI system
     */
    initialize() {
        try {
            this.setupCSSVariables();
            this.setupAnimationSystem();
            this.setupStateManagement();
            this.setupEventListeners();
            
            this.isInitialized = true;
            this.log('Adaptive UI system initialized');
            
            return { success: true };
            
        } catch (error) {
            console.error('Failed to initialize Adaptive UI:', error);
            return { success: false, error: error.message };
        }
    }
    
    /**
     * Setup CSS custom properties for dynamic theming
     */
    setupCSSVariables() {
        const root = document.documentElement;
        
        // Define default AURA CSS variables
        const defaultVariables = {
            // Color scheme variables
            '--aura-primary-hue': '210',
            '--aura-primary-saturation': '50%',
            '--aura-primary-lightness': '50%',
            '--aura-background-opacity': '1',
            '--aura-text-opacity': '1',
            '--aura-contrast-ratio': '1',
            
            // Typography variables
            '--aura-font-size-multiplier': '1',
            '--aura-line-height-multiplier': '1',
            '--aura-letter-spacing': '0',
            '--aura-font-weight': '400',
            
            // Layout variables
            '--aura-content-density': '1',
            '--aura-spacing-multiplier': '1',
            '--aura-border-radius': '8px',
            '--aura-shadow-intensity': '0.1',
            
            // Animation variables
            '--aura-animation-speed': '1',
            '--aura-transition-timing': 'ease-out',
            
            // Interaction variables
            '--aura-hover-intensity': '1',
            '--aura-focus-intensity': '1',
            '--aura-feedback-intensity': '1'
        };
        
        // Set default values
        Object.entries(defaultVariables).forEach(([property, value]) => {
            root.style.setProperty(property, value);
            this.cssVariables.set(property, value);
        });
        
        this.log('CSS variables initialized');
    }
    
    /**
     * Setup animation system
     */
    setupAnimationSystem() {
        // Create animation stylesheet
        const style = document.createElement('style');
        style.id = 'aura-animations';
        style.textContent = `
            .aura-adaptive {
                transition: all calc(var(--aura-animation-speed) * ${this.options.animationDuration}ms) var(--aura-transition-timing);
            }
            
            .aura-color-adaptive {
                transition: 
                    background-color calc(var(--aura-animation-speed) * ${this.options.animationDuration}ms) var(--aura-transition-timing),
                    color calc(var(--aura-animation-speed) * ${this.options.animationDuration}ms) var(--aura-transition-timing),
                    border-color calc(var(--aura-animation-speed) * ${this.options.animationDuration}ms) var(--aura-transition-timing);
            }
            
            .aura-layout-adaptive {
                transition: 
                    transform calc(var(--aura-animation-speed) * ${this.options.animationDuration}ms) var(--aura-transition-timing),
                    opacity calc(var(--aura-animation-speed) * ${this.options.animationDuration}ms) var(--aura-transition-timing),
                    width calc(var(--aura-animation-speed) * ${this.options.animationDuration}ms) var(--aura-transition-timing),
                    height calc(var(--aura-animation-speed) * ${this.options.animationDuration}ms) var(--aura-transition-timing);
            }
            
            .aura-typography-adaptive {
                transition: 
                    font-size calc(var(--aura-animation-speed) * ${this.options.animationDuration}ms) var(--aura-transition-timing),
                    line-height calc(var(--aura-animation-speed) * ${this.options.animationDuration}ms) var(--aura-transition-timing),
                    letter-spacing calc(var(--aura-animation-speed) * ${this.options.animationDuration}ms) var(--aura-transition-timing);
            }
            
            .aura-breathing {
                animation: aura-breathe calc(var(--aura-animation-speed) * 4000ms) ease-in-out infinite;
            }
            
            @keyframes aura-breathe {
                0%, 100% { transform: scale(1); opacity: 1; }
                50% { transform: scale(1.02); opacity: 0.95; }
            }
            
            .aura-pulse {
                animation: aura-pulse calc(var(--aura-animation-speed) * 2000ms) ease-in-out infinite;
            }
            
            @keyframes aura-pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.7; }
            }
            
            .aura-glow {
                box-shadow: 0 0 calc(var(--aura-shadow-intensity) * 20px) hsla(var(--aura-primary-hue), var(--aura-primary-saturation), var(--aura-primary-lightness), 0.3);
            }
        `;
        
        document.head.appendChild(style);
        
        // Add adaptive classes to relevant elements
        this.addAdaptiveClasses();
    }
    
    /**
     * Add adaptive classes to DOM elements
     */
    addAdaptiveClasses() {
        // Add classes to common elements
        const selectors = [
            'body',
            '.dashboard',
            '.card',
            '.button',
            '.input',
            '.text',
            'h1, h2, h3, h4, h5, h6',
            'p',
            '.metric',
            '.chart',
            '.alert'
        ];
        
        selectors.forEach(selector => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(element => {
                element.classList.add('aura-adaptive');
                
                // Add specific adaptive classes based on element type
                if (element.tagName.match(/^H[1-6]$/) || element.tagName === 'P') {
                    element.classList.add('aura-typography-adaptive');
                }
                
                if (element.classList.contains('card') || element.classList.contains('dashboard')) {
                    element.classList.add('aura-layout-adaptive', 'aura-color-adaptive');
                }
                
                if (element.classList.contains('button') || element.classList.contains('input')) {
                    element.classList.add('aura-color-adaptive');
                }
            });
        });
    }
    
    /**
     * Setup state management
     */
    setupStateManagement() {
        this.currentState = {
            colorScheme: 'default',
            typography: 'default',
            layoutDensity: 'default',
            informationFiltering: 'default',
            interactionSpeed: 'default',
            contentPrioritization: 'default',
            automationLevel: 'default',
            feedbackIntensity: 'default'
        };
        
        this.saveState();
    }
    
    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Listen for user preference changes
        if (window.matchMedia) {
            // Dark mode preference
            const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');
            darkModeQuery.addListener(() => this.handleSystemPreferenceChange());
            
            // Reduced motion preference
            const reducedMotionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
            reducedMotionQuery.addListener(() => this.handleSystemPreferenceChange());
        }
        
        // Listen for window resize
        window.addEventListener('resize', () => this.handleWindowResize());
        
        // Listen for visibility changes
        document.addEventListener('visibilitychange', () => this.handleVisibilityChange());
    }
    
    /**
     * Apply interface adaptation
     */
    async applyAdaptation(adaptation) {
        if (!this.isInitialized) {
            this.log('UI not initialized, queuing adaptation');
            this.animationQueue.push(adaptation);
            return;
        }
        
        const { type, parameters, confidence, urgency } = adaptation;
        
        // Check cooldown
        if (this.isOnCooldown(type)) {
            this.log(`Adaptation ${type} is on cooldown`);
            return;
        }
        
        // Check rate limiting
        if (!this.checkRateLimit()) {
            this.log('Rate limit exceeded, skipping adaptation');
            return;
        }
        
        this.log(`Applying adaptation: ${type}`, parameters);
        
        try {
            // Save current state
            this.saveState();
            
            // Apply the adaptation
            await this.executeAdaptation(type, parameters);
            
            // Record the adaptation
            this.recordAdaptation(adaptation);
            
            // Set cooldown
            this.setCooldown(type);
            
            this.log(`Adaptation ${type} applied successfully`);
            
        } catch (error) {
            console.error(`Failed to apply adaptation ${type}:`, error);
            this.revertLastState();
        }
    }
    
    /**
     * Execute specific adaptation type
     */
    async executeAdaptation(type, parameters) {
        switch (type) {
            case 'color_scheme':
                await this.adaptColorScheme(parameters);
                break;
                
            case 'typography':
                await this.adaptTypography(parameters);
                break;
                
            case 'layout_density':
                await this.adaptLayoutDensity(parameters);
                break;
                
            case 'information_filtering':
                await this.adaptInformationFiltering(parameters);
                break;
                
            case 'interaction_speed':
                await this.adaptInteractionSpeed(parameters);
                break;
                
            case 'content_prioritization':
                await this.adaptContentPrioritization(parameters);
                break;
                
            case 'automation_level':
                await this.adaptAutomationLevel(parameters);
                break;
                
            case 'feedback_intensity':
                await this.adaptFeedbackIntensity(parameters);
                break;
                
            default:
                throw new Error(`Unknown adaptation type: ${type}`);
        }
        
        this.currentState[type] = parameters;
    }
    
    /**
     * Adapt color scheme
     */
    async adaptColorScheme(parameters) {
        const { scheme, intensity = 0.8, brightness = 1.0, contrast = 1.0 } = parameters;
        
        let hue, saturation, lightness;
        
        switch (scheme) {
            case 'calming':
                hue = 200; // Blue
                saturation = 30;
                lightness = 60;
                break;
                
            case 'energizing':
                hue = 25; // Orange
                saturation = 70;
                lightness = 55;
                break;
                
            case 'warm':
                hue = 45; // Yellow-orange
                saturation = 40;
                lightness = 65;
                break;
                
            case 'cool':
                hue = 180; // Cyan
                saturation = 35;
                lightness = 55;
                break;
                
            case 'high_contrast':
                hue = this.cssVariables.get('--aura-primary-hue');
                saturation = 80;
                lightness = contrast > 1 ? 30 : 70;
                break;
                
            default:
                hue = 210;
                saturation = 50;
                lightness = 50;
        }
        
        // Apply color changes
        this.setCSSVariable('--aura-primary-hue', hue);
        this.setCSSVariable('--aura-primary-saturation', `${saturation * intensity}%`);
        this.setCSSVariable('--aura-primary-lightness', `${lightness * brightness}%`);
        this.setCSSVariable('--aura-contrast-ratio', contrast);
        
        // Update background and text opacity for comfort
        if (scheme === 'calming') {
            this.setCSSVariable('--aura-background-opacity', '0.95');
            this.setCSSVariable('--aura-text-opacity', '0.9');
        } else {
            this.setCSSVariable('--aura-background-opacity', '1');
            this.setCSSVariable('--aura-text-opacity', '1');
        }
    }
    
    /**
     * Adapt typography
     */
    async adaptTypography(parameters) {
        const { 
            size_increase = 1.0, 
            spacing_increase = 1.0, 
            weight_increase = 0,
            readability_mode = false 
        } = parameters;
        
        this.setCSSVariable('--aura-font-size-multiplier', size_increase);
        this.setCSSVariable('--aura-line-height-multiplier', 1 + (spacing_increase - 1) * 0.5);
        this.setCSSVariable('--aura-letter-spacing', `${(spacing_increase - 1) * 0.5}px`);
        
        if (weight_increase > 0) {
            const baseWeight = 400;
            const newWeight = Math.min(700, baseWeight + weight_increase * 100);
            this.setCSSVariable('--aura-font-weight', newWeight);
        }
        
        if (readability_mode) {
            // Apply readability enhancements
            this.setCSSVariable('--aura-line-height-multiplier', '1.6');
            this.setCSSVariable('--aura-letter-spacing', '0.5px');
        }
    }
    
    /**
     * Adapt layout density
     */
    async adaptLayoutDensity(parameters) {
        const { density = 'default' } = parameters;
        
        let densityMultiplier, spacingMultiplier;
        
        switch (density) {
            case 'minimal':
                densityMultiplier = 0.6;
                spacingMultiplier = 1.5;
                break;
                
            case 'simplified':
                densityMultiplier = 0.8;
                spacingMultiplier = 1.2;
                break;
                
            case 'detailed':
                densityMultiplier = 1.2;
                spacingMultiplier = 0.9;
                break;
                
            case 'comprehensive':
                densityMultiplier = 1.4;
                spacingMultiplier = 0.8;
                break;
                
            default:
                densityMultiplier = 1.0;
                spacingMultiplier = 1.0;
        }
        
        this.setCSSVariable('--aura-content-density', densityMultiplier);
        this.setCSSVariable('--aura-spacing-multiplier', spacingMultiplier);
        
        // Hide/show elements based on density
        await this.adjustElementVisibility(density);
    }
    
    /**
     * Adjust element visibility based on density
     */
    async adjustElementVisibility(density) {
        const elements = document.querySelectorAll('[data-aura-priority]');
        
        elements.forEach(element => {
            const priority = parseInt(element.dataset.auraPriority) || 5;
            let shouldShow = true;
            
            switch (density) {
                case 'minimal':
                    shouldShow = priority <= 3;
                    break;
                case 'simplified':
                    shouldShow = priority <= 6;
                    break;
                case 'detailed':
                    shouldShow = priority <= 8;
                    break;
                case 'comprehensive':
                    shouldShow = true;
                    break;
                default:
                    shouldShow = priority <= 7;
            }
            
            if (shouldShow) {
                element.style.display = '';
                element.style.opacity = '1';
            } else {
                element.style.opacity = '0.3';
                setTimeout(() => {
                    if (element.style.opacity === '0.3') {
                        element.style.display = 'none';
                    }
                }, this.options.animationDuration);
            }
        });
    }
    
    /**
     * Adapt information filtering
     */
    async adaptInformationFiltering(parameters) {
        const { filter_level = 'default', confidence_threshold = 0.7 } = parameters;
        
        // Apply filtering to data elements
        const dataElements = document.querySelectorAll('[data-aura-confidence]');
        
        dataElements.forEach(element => {
            const confidence = parseFloat(element.dataset.auraConfidence) || 1.0;
            let shouldShow = true;
            
            switch (filter_level) {
                case 'essential_only':
                    shouldShow = confidence >= 0.9;
                    break;
                case 'high_priority':
                    shouldShow = confidence >= 0.8;
                    break;
                case 'comprehensive':
                    shouldShow = confidence >= 0.3;
                    break;
                default:
                    shouldShow = confidence >= confidence_threshold;
            }
            
            element.style.opacity = shouldShow ? '1' : '0.5';
            element.style.pointerEvents = shouldShow ? 'auto' : 'none';
        });
    }
    
    /**
     * Adapt interaction speed
     */
    async adaptInteractionSpeed(parameters) {
        const { speed = 'normal' } = parameters;
        
        let speedMultiplier;
        
        switch (speed) {
            case 'fast':
                speedMultiplier = 0.5;
                break;
            case 'relaxed':
                speedMultiplier = 1.5;
                break;
            case 'slow':
                speedMultiplier = 2.0;
                break;
            default:
                speedMultiplier = 1.0;
        }
        
        this.setCSSVariable('--aura-animation-speed', speedMultiplier);
        
        // Adjust hover and focus timing
        this.setCSSVariable('--aura-hover-intensity', speedMultiplier);
        this.setCSSVariable('--aura-focus-intensity', speedMultiplier);
    }
    
    /**
     * Adapt content prioritization
     */
    async adaptContentPrioritization(parameters) {
        const { 
            highlight_important = false, 
            focus_mode = false,
            comparison_mode = false 
        } = parameters;
        
        if (highlight_important) {
            this.highlightImportantContent();
        }
        
        if (focus_mode) {
            this.enableFocusMode();
        }
        
        if (comparison_mode) {
            this.enableComparisonMode();
        }
    }
    
    /**
     * Highlight important content
     */
    highlightImportantContent() {
        const importantElements = document.querySelectorAll('[data-aura-importance="high"]');
        
        importantElements.forEach(element => {
            element.classList.add('aura-glow');
            element.style.transform = 'scale(1.02)';
            element.style.zIndex = '10';
        });
    }
    
    /**
     * Enable focus mode
     */
    enableFocusMode() {
        const nonEssentialElements = document.querySelectorAll('[data-aura-priority]:not([data-aura-priority="1"]):not([data-aura-priority="2"])');
        
        nonEssentialElements.forEach(element => {
            element.style.opacity = '0.3';
            element.style.filter = 'blur(1px)';
        });
        
        // Add breathing animation to focused content
        const focusedElements = document.querySelectorAll('[data-aura-priority="1"], [data-aura-priority="2"]');
        focusedElements.forEach(element => {
            element.classList.add('aura-breathing');
        });
    }
    
    /**
     * Enable comparison mode
     */
    enableComparisonMode() {
        const comparableElements = document.querySelectorAll('[data-aura-comparable]');
        
        comparableElements.forEach(element => {
            element.style.border = '2px solid hsla(var(--aura-primary-hue), var(--aura-primary-saturation), var(--aura-primary-lightness), 0.5)';
            element.style.margin = '4px';
        });
    }
    
    /**
     * Adapt automation level
     */
    async adaptAutomationLevel(parameters) {
        const { level = 'standard', suggestions = 'normal' } = parameters;
        
        // This would integrate with the AI command system
        // For now, we'll adjust UI feedback about automation
        
        const automationIndicators = document.querySelectorAll('.automation-indicator');
        
        automationIndicators.forEach(indicator => {
            switch (level) {
                case 'increased':
                    indicator.textContent = 'High Automation';
                    indicator.style.color = 'green';
                    break;
                case 'reduced':
                    indicator.textContent = 'Manual Control';
                    indicator.style.color = 'orange';
                    break;
                default:
                    indicator.textContent = 'Standard';
                    indicator.style.color = 'blue';
            }
        });
    }
    
    /**
     * Adapt feedback intensity
     */
    async adaptFeedbackIntensity(parameters) {
        const { 
            intensity = 'normal', 
            explanations = false, 
            guidance = false,
            decision_support = false 
        } = parameters;
        
        let intensityMultiplier;
        
        switch (intensity) {
            case 'minimal':
                intensityMultiplier = 0.5;
                break;
            case 'enhanced':
                intensityMultiplier = 1.5;
                break;
            case 'maximum':
                intensityMultiplier = 2.0;
                break;
            default:
                intensityMultiplier = 1.0;
        }
        
        this.setCSSVariable('--aura-feedback-intensity', intensityMultiplier);
        
        // Show/hide explanatory elements
        const explanationElements = document.querySelectorAll('.explanation, .help-text');
        explanationElements.forEach(element => {
            element.style.display = explanations ? 'block' : 'none';
        });
        
        // Show/hide guidance elements
        const guidanceElements = document.querySelectorAll('.guidance, .hint');
        guidanceElements.forEach(element => {
            element.style.display = guidance ? 'block' : 'none';
        });
        
        // Show/hide decision support
        const decisionElements = document.querySelectorAll('.decision-support, .recommendation');
        decisionElements.forEach(element => {
            element.style.display = decision_support ? 'block' : 'none';
        });
    }
    
    /**
     * Set CSS custom property
     */
    setCSSVariable(property, value) {
        document.documentElement.style.setProperty(property, value);
        this.cssVariables.set(property, value);
    }
    
    /**
     * Save current state
     */
    saveState() {
        const state = {
            timestamp: Date.now(),
            state: { ...this.currentState },
            cssVariables: new Map(this.cssVariables)
        };
        
        this.stateStack.push(state);
        
        // Limit state history
        if (this.stateStack.length > this.maxStateHistory) {
            this.stateStack.shift();
        }
    }
    
    /**
     * Revert to last state
     */
    revertLastState() {
        if (this.stateStack.length < 2) {
            return;
        }
        
        // Remove current state
        this.stateStack.pop();
        
        // Get previous state
        const previousState = this.stateStack[this.stateStack.length - 1];
        
        // Restore state
        this.currentState = { ...previousState.state };
        
        // Restore CSS variables
        previousState.cssVariables.forEach((value, property) => {
            this.setCSSVariable(property, value);
        });
        
        this.log('Reverted to previous state');
    }
    
    /**
     * Check if adaptation type is on cooldown
     */
    isOnCooldown(type) {
        const cooldownEnd = this.cooldowns.get(type);
        return cooldownEnd && Date.now() < cooldownEnd;
    }
    
    /**
     * Set cooldown for adaptation type
     */
    setCooldown(type) {
        const cooldownDuration = 30000; // 30 seconds
        this.cooldowns.set(type, Date.now() + cooldownDuration);
    }
    
    /**
     * Check rate limiting
     */
    checkRateLimit() {
        const now = Date.now();
        const oneMinuteAgo = now - 60000;
        
        // Count adaptations in the last minute
        const recentAdaptations = this.adaptationHistory.filter(
            adaptation => adaptation.timestamp > oneMinuteAgo
        );
        
        return recentAdaptations.length < this.options.maxAdaptationsPerMinute;
    }
    
    /**
     * Record adaptation
     */
    recordAdaptation(adaptation) {
        this.adaptationHistory.push({
            ...adaptation,
            timestamp: Date.now()
        });
        
        // Limit history size
        if (this.adaptationHistory.length > 100) {
            this.adaptationHistory.shift();
        }
    }
    
    /**
     * Handle system preference changes
     */
    handleSystemPreferenceChange() {
        if (!this.options.respectUserPreferences) {
            return;
        }
        
        // Check for reduced motion preference
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            this.setCSSVariable('--aura-animation-speed', '0.1');
        }
        
        // Check for dark mode preference
        if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
            this.setCSSVariable('--aura-primary-lightness', '30%');
        }
    }
    
    /**
     * Handle window resize
     */
    handleWindowResize() {
        // Adjust layout density based on screen size
        const width = window.innerWidth;
        
        if (width < 768) {
            // Mobile - increase density
            this.setCSSVariable('--aura-content-density', '0.8');
            this.setCSSVariable('--aura-spacing-multiplier', '0.9');
        } else if (width > 1920) {
            // Large screen - decrease density
            this.setCSSVariable('--aura-content-density', '1.2');
            this.setCSSVariable('--aura-spacing-multiplier', '1.1');
        }
    }
    
    /**
     * Handle visibility changes
     */
    handleVisibilityChange() {
        if (document.hidden) {
            // Page is hidden - reduce animations
            this.setCSSVariable('--aura-animation-speed', '0.1');
        } else {
            // Page is visible - restore animations
            this.setCSSVariable('--aura-animation-speed', '1');
        }
    }
    
    /**
     * Get current adaptation state
     */
    getCurrentState() {
        return {
            state: { ...this.currentState },
            cssVariables: Object.fromEntries(this.cssVariables),
            adaptationHistory: [...this.adaptationHistory],
            isAnimating: this.isAnimating
        };
    }
    
    /**
     * Reset to default state
     */
    resetToDefault() {
        this.currentState = {
            colorScheme: 'default',
            typography: 'default',
            layoutDensity: 'default',
            informationFiltering: 'default',
            interactionSpeed: 'default',
            contentPrioritization: 'default',
            automationLevel: 'default',
            feedbackIntensity: 'default'
        };
        
        // Reset CSS variables
        this.setupCSSVariables();
        
        // Remove adaptive classes
        document.querySelectorAll('.aura-glow, .aura-breathing, .aura-pulse').forEach(element => {
            element.classList.remove('aura-glow', 'aura-breathing', 'aura-pulse');
            element.style.transform = '';
            element.style.opacity = '';
            element.style.filter = '';
            element.style.border = '';
            element.style.margin = '';
        });
        
        this.log('Reset to default state');
    }
    
    /**
     * Log messages
     */
    log(message, data = null) {
        if (this.options.debugMode) {
            console.log(`[AURA UI] ${message}`, data || '');
        }
    }
    
    /**
     * Cleanup resources
     */
    cleanup() {
        // Remove event listeners
        window.removeEventListener('resize', this.handleWindowResize);
        document.removeEventListener('visibilitychange', this.handleVisibilityChange);
        
        // Reset to default state
        this.resetToDefault();
        
        // Remove animation stylesheet
        const style = document.getElementById('aura-animations');
        if (style) {
            style.remove();
        }
        
        this.log('AURA Adaptive UI cleaned up');
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AURAAdaptiveUI;
} else if (typeof window !== 'undefined') {
    window.AURAAdaptiveUI = AURAAdaptiveUI;
}

