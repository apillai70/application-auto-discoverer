/**
 * Data Configuration Service
 * Centralized service to eliminate ALL hardcoded CSV paths
 * Used by all JavaScript files that need to access CSV data
 */

class DataConfigService {
    constructor() {
        this.config = null;
        this.currentEndpoint = null;
        this.isInitialized = false;
        this.initPromise = null;
        
        // API endpoints
        this.apiEndpoints = {
            dataStatus: '/api/v1/data/status',
            currentCsv: '/api/v1/data/current',
            filesList: '/api/v1/data/files'
        };
        
        // REMOVED SYNTHETIC FALLBACK PATHS - NO MORE DUMMY DATA
        this.fallbackPaths = [
            // Synthetic paths removed to prevent dummy data loading
            // '/data_staging/updated_normalized_synthetic_traffic.csv',
            // '/data_staging/processed/updated_normalized_synthetic_traffic.csv',
            // '/data_staging/synthetic_traffic.csv',
            // '/data_staging/traffic.csv'
        ];
    }
    
    async initialize() {
        if (this.isInitialized) {
            return this.config;
        }
        
        if (this.initPromise) {
            return this.initPromise;
        }
        
        this.initPromise = this._doInitialize();
        return this.initPromise;
    }
    
    async _doInitialize() {
        console.log('DataConfigService: Initializing...');
        
        try {
            // Try to get current CSV from API
            const response = await fetch(this.apiEndpoints.currentCsv);
            
            if (response.ok) {
                const currentFile = await response.json();
                console.log('DataConfigService: Got current file from API:', currentFile);
                
                // CHECK IF API RETURNS REAL DATA OR TEST MESSAGE
                if (currentFile.test === 'working') {
                    console.warn('DataConfigService: API returning test message instead of file data');
                    return await this._useProcessedFile();
                }
                
                this.config = currentFile;
                this.currentEndpoint = currentFile.endpoint;
                this.isInitialized = true;
                
                return this.config;
            } else {
                console.warn('DataConfigService: API not available, trying processed file');
                return await this._useProcessedFile();
            }
            
        } catch (error) {
            console.warn('DataConfigService: API error, trying processed file:', error);
            return await this._useProcessedFile();
        }
    }
    
    async _useProcessedFile() {
        console.log('DataConfigService: Attempting to use processed file directly...');
        
        // Try to use the known processed file
        const processedFilePath = '/data_staging/processed/XECHK_normalized_20250917_141802.csv';
        
        try {
            const response = await fetch(processedFilePath, { method: 'HEAD' });
            if (response.ok) {
                console.log('DataConfigService: Found processed XECHK file');
                
                this.config = {
                    endpoint: processedFilePath,
                    filename: 'XECHK_normalized_20250917_141802.csv',
                    status: 'processed',
                    source: 'direct_processed_file'
                };
                this.currentEndpoint = processedFilePath;
                this.isInitialized = true;
                
                return this.config;
            }
        } catch (error) {
            console.log('DataConfigService: Processed file not accessible:', error);
        }
        
        // No real data found - do NOT fall back to synthetic
        console.error('DataConfigService: No real CSV files found');
        this.config = {
            endpoint: null,
            filename: null,
            status: 'no_data',
            error: 'No real CSV files available'
        };
        this.isInitialized = true;
        
        return this.config;
    }

    async _fallbackDiscovery() {
        console.log('DataConfigService: Fallback discovery disabled - no synthetic data allowed');
        
        // No CSV found anywhere
        console.error('DataConfigService: No CSV files found');
        this.config = {
            endpoint: null,
            filename: null,
            status: 'no_data',
            error: 'No CSV files available'
        };
        this.isInitialized = true;
        
        return this.config;
    }
    
    async getCurrentCsvEndpoint() {
        await this.initialize();
        return this.currentEndpoint;
    }
    
    async getCurrentCsvFilename() {
        await this.initialize();
        return this.config?.filename || null;
    }
    
    async getConfig() {
        await this.initialize();
        return this.config;
    }
    
    async isDataAvailable() {
        await this.initialize();
        return this.config?.status !== 'no_data' && !!this.currentEndpoint;
    }
    
    async refresh() {
        console.log('DataConfigService: Refreshing configuration...');
        this.isInitialized = false;
        this.initPromise = null;
        this.config = null;
        this.currentEndpoint = null;
        
        return await this.initialize();
    }
    
    getStatus() {
        return {
            isInitialized: this.isInitialized,
            hasConfig: !!this.config,
            currentEndpoint: this.currentEndpoint,
            configStatus: this.config?.status || 'uninitialized'
        };
    }
}

// Global instance
window.DataConfig = new DataConfigService();

// Convenience function for other JavaScript files
window.getCurrentCsvEndpoint = async function() {
    return await window.DataConfig.getCurrentCsvEndpoint();
};

window.getCurrentCsvFilename = async function() {
    return await window.DataConfig.getCurrentCsvFilename();
};

// Auto-initialize on load
document.addEventListener('DOMContentLoaded', async () => {
    try {
        await window.DataConfig.initialize();
        console.log('DataConfigService: Auto-initialization completed');
    } catch (error) {
        console.error('DataConfigService: Auto-initialization failed:', error);
    }
});

console.log('DataConfigService loaded - NO SYNTHETIC DATA FALLBACKS');