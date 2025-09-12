// static/js/security-logging.js
// Frontend security logging integration with file-based storage backend

class SecurityLogger {
    constructor() {
        this.apiBase = 'http://localhost:8001/api/v1/audit';
        this.sessionId = this.generateSessionId();
        this.userId = null;
        this.sourceIp = null;
        
        // Batch logging configuration
        this.batchSize = 10;
        this.batchTimeout = 5000; // 5 seconds
        this.eventQueue = [];
        this.batchTimer = null;
        
        // Initialize
        this.init();
    }
    
    async init() {
        try {
            // Get user info from authentication
            await this.getCurrentUser();
            
            // Get client IP
            await this.getClientIP();
            
            // Set up automatic logging
            this.setupAutomaticLogging();
            
            // Log initialization
            await this.logEvent({
                event_type: 'user_action',
                level: 'info',
                action: 'security_logger_initialized',
                page_url: window.location.href,
                details: {
                    user_agent: navigator.userAgent,
                    screen_resolution: `${screen.width}x${screen.height}`,
                    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
                }
            });
            
            console.log('🛡️ Security logging initialized');
            
        } catch (error) {
            console.warn('Security logging initialization failed:', error);
        }
    }
    
    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    async getCurrentUser() {
        try {
            const response = await fetch(`${this.apiBase.replace('/audit', '/auth')}/profile`);
            if (response.ok) {
                const userData = await response.json();
                this.userId = userData.user_id || userData.username;
            }
        } catch (error) {
            console.warn('Could not get current user:', error);
            this.userId = 'anonymous_' + Math.random().toString(36).substr(2, 9);
        }
    }
    
    async getClientIP() {
        try {
            // Use a public IP service or internal endpoint
            const response = await fetch('https://api.ipify.org?format=json');
            if (response.ok) {
                const data = await response.json();
                this.sourceIp = data.ip;
            }
        } catch (error) {
            console.warn('Could not get client IP:', error);
            this.sourceIp = 'unknown';
        }
    }
    
    setupAutomaticLogging() {
        // Log page navigation
        window.addEventListener('beforeunload', () => {
            this.logEvent({
                event_type: 'navigation',
                level: 'info',
                action: 'page_unload',
                page_url: window.location.href,
                details: {
                    time_on_page: Date.now() - this.pageLoadTime
                }
            }, true); // Immediate send
        });
        
        // Log performance metrics
        window.addEventListener('load', () => {
            setTimeout(() => {
                this.logPerformanceMetrics();
            }, 2000);
        });
        
        // Log errors
        window.addEventListener('error', (event) => {
            this.logError(event.error, event.filename, event.lineno);
        });
        
        // Log unhandled promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            this.logError(event.reason, 'promise', 0);
        });
        
        // Log visibility changes
        document.addEventListener('visibilitychange', () => {
            this.logEvent({
                event_type: 'user_action',
                level: 'info',
                action: document.hidden ? 'page_hidden' : 'page_visible',
                page_url: window.location.href
            });
        });
        
        // Store page load time
        this.pageLoadTime = Date.now();
    }
    
    async logEvent(eventData, immediate = false) {
        try {
            // Enhance event data
            const enhancedEvent = {
                ...eventData,
                session_id: this.sessionId,
                source_ip: this.sourceIp,
                user_agent: navigator.userAgent,
                timestamp: new Date().toISOString(),
                page_url: eventData.page_url || window.location.href
            };
            
            if (immediate) {
                // Send immediately
                await this.sendEvent(enhancedEvent);
            } else {
                // Add to batch queue
                this.eventQueue.push(enhancedEvent);
                
                // Process batch if full or start timer
                if (this.eventQueue.length >= this.batchSize) {
                    await this.processBatch();
                } else if (!this.batchTimer) {
                    this.batchTimer = setTimeout(() => {
                        this.processBatch();
                    }, this.batchTimeout);
                }
            }
            
        } catch (error) {
            console.error('Error logging event:', error);
        }
    }
    
    async processBatch() {
        if (this.eventQueue.length === 0) return;
        
        const batch = [...this.eventQueue];
        this.eventQueue = [];
        
        if (this.batchTimer) {
            clearTimeout(this.batchTimer);
            this.batchTimer = null;
        }
        
        try {
            // Send batch to backend
            for (const event of batch) {
                await this.sendEvent(event);
            }
        } catch (error) {
            console.error('Error processing event batch:', error);
        }
    }
    
    async sendEvent(eventData) {
        try {
            const response = await fetch(`${this.apiBase}/frontend/events`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    // Add authentication header if available
                    'Authorization': this.getAuthHeader()
                },
                body: JSON.stringify(eventData)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
            
        } catch (error) {
            console.error('Error sending event to backend:', error);
            throw error;
        }
    }
    
    getAuthHeader() {
        // Get auth token from localStorage, sessionStorage, or cookies
        const token = localStorage.getItem('auth_token') || 
                     sessionStorage.getItem('auth_token') ||
                     this.getCookie('auth_token');
        
        return token ? `Bearer ${token}` : '';
    }
    
    getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }
    
    // Public API methods
    
    async logUserInteraction(element, action, additionalData = {}) {
        const interactionData = {
            element: element.tagName + (element.id ? `#${element.id}` : '') + 
                    (element.className ? `.${element.className.split(' ').join('.')}` : ''),
            action: action,
            coordinates: this.getMouseCoordinates(),
            viewport: {
                width: window.innerWidth,
                height: window.innerHeight
            },
            form_data: this.extractFormData(element),
            ...additionalData
        };
        
        try {
            const response = await fetch(`${this.apiBase}/frontend/interactions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': this.getAuthHeader()
                },
                body: JSON.stringify(interactionData)
            });
            
            if (response.ok) {
                console.log('✅ User interaction logged');
            }
            
        } catch (error) {
            console.error('Error logging user interaction:', error);
        }
    }
    
    async logApiCall(endpoint, method, statusCode, responseTime, errorMessage = null) {
        const apiData = {
            endpoint: endpoint,
            method: method.toUpperCase(),
            status_code: statusCode,
            response_time: responseTime,
            error_message: errorMessage,
            referrer: document.referrer,
            request_id: this.generateRequestId()
        };
        
        try {
            const response = await fetch(`${this.apiBase}/frontend/api-calls`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': this.getAuthHeader()
                },
                body: JSON.stringify(apiData)
            });
            
            if (response.ok) {
                console.log('✅ API call logged');
            }
            
        } catch (error) {
            console.error('Error logging API call:', error);
        }
    }
    
    async logSecurityViolation(violationType, threatLevel, blockedAction, context = {}) {
        const violationData = {
            violation_type: violationType,
            threat_level: threatLevel,
            blocked_action: blockedAction,
            detection_method: 'frontend',
            context: context,
            page_url: window.location.href,
            source_ip: this.sourceIp,
            user_agent: navigator.userAgent
        };
        
        try {
            const response = await fetch(`${this.apiBase}/frontend/security-violations`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': this.getAuthHeader()
                },
                body: JSON.stringify(violationData)
            });
            
            if (response.ok) {
                console.log('🚨 Security violation logged');
            }
            
        } catch (error) {
            console.error('Error logging security violation:', error);
        }
    }
    
    async logError(error, filename = '', lineno = 0) {
        await this.logEvent({
            event_type: 'error',
            level: 'error',
            action: 'javascript_error',
            details: {
                error_message: error.message || String(error),
                error_stack: error.stack || '',
                filename: filename,
                line_number: lineno,
                error_type: error.constructor.name || 'Error'
            }
        });
    }
    
    async logPerformanceMetrics() {
        try {
            const perfData = performance.getEntriesByType('navigation')[0];
            const paintEntries = performance.getEntriesByType('paint');
            
            const performanceData = {
                load_time_ms: perfData.loadEventEnd - perfData.loadEventStart,
                dom_ready_time_ms: perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart,
                first_paint: paintEntries.find(entry => entry.name === 'first-paint')?.startTime || 0,
                largest_contentful_paint: 0, // Would need PerformanceObserver for real LCP
                memory_usage: performance.memory ? {
                    used: performance.memory.usedJSHeapSize,
                    total: performance.memory.totalJSHeapSize,
                    limit: performance.memory.jsHeapSizeLimit
                } : null,
                network_info: navigator.connection ? {
                    type: navigator.connection.effectiveType,
                    downlink: navigator.connection.downlink,
                    rtt: navigator.connection.rtt
                } : null
            };
            
            const response = await fetch(`${this.apiBase}/frontend/performance`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': this.getAuthHeader()
                },
                body: JSON.stringify(performanceData)
            });
            
            if (response.ok) {
                console.log('📊 Performance metrics logged');
            }
            
        } catch (error) {
            console.error('Error logging performance metrics:', error);
        }
    }
    
    // Helper methods
    
    getMouseCoordinates() {
        // Store last known mouse coordinates
        if (!this.lastMouseCoords) {
            this.lastMouseCoords = { x: 0, y: 0 };
            document.addEventListener('mousemove', (e) => {
                this.lastMouseCoords = { x: e.clientX, y: e.clientY };
            });
        }
        return this.lastMouseCoords;
    }
    
    extractFormData(element) {
        if (element.tagName === 'FORM') {
            const formData = new FormData(element);
            const data = {};
            for (let [key, value] of formData.entries()) {
                // Don't log sensitive data
                if (!this.isSensitiveField(key)) {
                    data[key] = value;
                }
            }
            return data;
        }
        return {};
    }
    
    isSensitiveField(fieldName) {
        const sensitiveFields = ['password', 'token', 'secret', 'key', 'auth'];
        return sensitiveFields.some(sensitive => 
            fieldName.toLowerCase().includes(sensitive)
        );
    }
    
    generateRequestId() {
        return 'req_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    // Public utility methods
    
    async getUserActivitySummary(hours = 24) {
        try {
            const response = await fetch(
                `${this.apiBase}/frontend/user-activity/${this.userId}?hours=${hours}`,
                {
                    headers: { 'Authorization': this.getAuthHeader() }
                }
            );
            
            if (response.ok) {
                return await response.json();
            }
            
        } catch (error) {
            console.error('Error getting user activity summary:', error);
        }
        return null;
    }
    
    async exportUserLogs(startDate, endDate, format = 'json') {
        try {
            const response = await fetch(
                `${this.apiBase}/logs/export?category=application&start_date=${startDate}&end_date=${endDate}&format=${format}`,
                {
                    method: 'POST',
                    headers: { 'Authorization': this.getAuthHeader() }
                }
            );
            
            if (response.ok) {
                const result = await response.json();
                console.log(`📄 Logs exported: ${result.export_path}`);
                return result;
            }
            
        } catch (error) {
            console.error('Error exporting logs:', error);
        }
        return null;
    }
}

// Auto-instrumentation for common interactions
class AutoInstrumentation {
    constructor(securityLogger) {
        this.logger = securityLogger;
        this.setupAutoLogging();
    }
    
    setupAutoLogging() {
        // Auto-log button clicks
        document.addEventListener('click', (event) => {
            if (event.target.tagName === 'BUTTON' || event.target.type === 'submit') {
                this.logger.logUserInteraction(event.target, 'click');
            }
        });
        
        // Auto-log form submissions
        document.addEventListener('submit', (event) => {
            this.logger.logUserInteraction(event.target, 'submit');
        });
        
        // Auto-log input focus (for form analytics)
        document.addEventListener('focus', (event) => {
            if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
                this.logger.logUserInteraction(event.target, 'focus');
            }
        }, true);
        
        // Auto-log navigation
        const originalPushState = history.pushState;
        history.pushState = function(...args) {
            originalPushState.apply(history, args);
            securityLogger.logEvent({
                event_type: 'navigation',
                level: 'info',
                action: 'spa_navigation',
                page_url: window.location.href,
                details: { method: 'pushState' }
            });
        };
        
        window.addEventListener('popstate', () => {
            securityLogger.logEvent({
                event_type: 'navigation',
                level: 'info',
                action: 'browser_navigation',
                page_url: window.location.href,
                details: { method: 'popstate' }
            });
        });
    }
}

// Enhanced fetch wrapper for API call logging
class APILogger {
    constructor(securityLogger) {
        this.logger = securityLogger;
        this.setupFetchInterception();
    }
    
    setupFetchInterception() {
        const originalFetch = window.fetch;
        
        window.fetch = async (...args) => {
            const startTime = Date.now();
            const url = args[0];
            const options = args[1] || {};
            const method = options.method || 'GET';
            
            try {
                const response = await originalFetch(...args);
                const endTime = Date.now();
                
                // Log successful API call
                await this.logger.logApiCall(
                    url,
                    method,
                    response.status,
                    endTime - startTime
                );
                
                return response;
                
            } catch (error) {
                const endTime = Date.now();
                
                // Log failed API call
                await this.logger.logApiCall(
                    url,
                    method,
                    0,
                    endTime - startTime,
                    error.message
                );
                
                throw error;
            }
        };
    }
}

// Initialize security logging when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Initialize security logger
    window.securityLogger = new SecurityLogger();
    
    // Set up auto-instrumentation
    window.autoInstrumentation = new AutoInstrumentation(window.securityLogger);
    
    // Set up API call logging
    window.apiLogger = new APILogger(window.securityLogger);
    
    console.log('🛡️ Frontend security logging fully initialized');
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { SecurityLogger, AutoInstrumentation, APILogger };
}