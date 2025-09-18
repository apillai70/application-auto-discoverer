class DataPipeline {
    constructor() {
        this.status = null;
        this.pollInterval = null;
        this.callbacks = [];
    }
    
    async checkStatus() {
        try {
            const response = await fetch('/api/data/status');
            this.status = await response.json();
            
            // Notify all callbacks of status change
            this.callbacks.forEach(callback => callback(this.status));
            
            return this.status;
        } catch (error) {
            console.error('Failed to check pipeline status:', error);
            return null;
        }
    }
    
    async getCurrentEndpoint() {
        try {
            const response = await fetch('/api/data/current');
            if (response.ok) {
                const data = await response.json();
                return data.endpoint;
            }
        } catch (error) {
            console.error('Failed to get current endpoint:', error);
        }
        
        // Fallback to old hardcoded path
        return null;
    }
    
    startPolling(intervalMs = 30000) {
        // Check status every 30 seconds for new processed files
        this.pollInterval = setInterval(() => {
            this.checkStatus();
        }, intervalMs);
        
        // Initial check
        this.checkStatus();
    }
    
    stopPolling() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = null;
        }
    }
    
    onStatusChange(callback) {
        this.callbacks.push(callback);
    }
    
    getStatusSummary() {
        if (!this.status) return "Unknown";
        
        const { pending, processed, failed } = this.status.status;
        
        if (pending.count > 0) {
            return `Processing: ${pending.count} pending`;
        } else if (processed.count > 0) {
            return `Ready: ${processed.count} processed`;
        } else if (failed.count > 0) {
            return `Issues: ${failed.count} failed`;
        } else {
            return "No data files";
        }
    }
}

// Global instance
window.dataPipeline = new DataPipeline();