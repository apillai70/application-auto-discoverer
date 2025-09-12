// Dynamic Data Source Manager
// Replaces hardcoded CSV paths with file upload functionality

class DataSourceManager {
    constructor(appDataInstance) {
        this.appData = appDataInstance;
        this.uploadedFiles = []; // Track uploaded files
        this.masterTopology = { nodes: [], links: [] }; // Consolidated topology
        this.dataSources = []; // Track all data sources
        this.duplicateDetection = new Map(); // Track records to prevent duplicates
    }

    // Initialize file upload functionality
    setupFileUpload() {
        // Replace the hardcoded data source with upload button
        this.createUploadInterface();
        this.setupUploadHandlers();
    }

    createUploadInterface() {
        const dataSourcePath = document.getElementById('data-source-path');
        if (dataSourcePath) {
            // Replace static path with upload button
            dataSourcePath.innerHTML = `
                <button onclick="dataSourceManager.triggerFileUpload()" 
                        style="background: var(--accent-blue); color: white; padding: 4px 8px; 
                               border: none; border-radius: 4px; cursor: pointer; font-size: 11px;">
                    📁 Upload CSV
                </button>
                <span id="current-source-name" style="margin-left: 8px; font-size: 11px;">
                    No files uploaded
                </span>
                <input type="file" id="csv-upload-input" accept=".csv" multiple style="display: none;">
            `;
        }
    }

    triggerFileUpload() {
        const input = document.getElementById('csv-upload-input');
        if (input) {
            input.click();
        }
    }

    setupUploadHandlers() {
        const input = document.getElementById('csv-upload-input');
        if (input) {
            input.addEventListener('change', (event) => {
                this.handleFileUpload(event.target.files);
            });
        }
    }
	
	// Add to DataSourceManager class
	hasTrafficFile() {
		return this.uploadedFiles.some(file => 
			file.name.toLowerCase().includes('traffic') || 
			file.name.toLowerCase().includes('synthetic')
		);
	}

	getTrafficData() {
		const trafficFile = this.uploadedFiles.find(file => 
			file.name.toLowerCase().includes('traffic') || 
			file.name.toLowerCase().includes('synthetic')
		);
		return trafficFile ? trafficFile.data : [];
	}
	
    async handleFileUpload(files) {
        if (!files || files.length === 0) return;

        console.log(`Processing ${files.length} uploaded files...`);
        
        for (const file of files) {
            await this.processUploadedFile(file);
        }

        // After processing all files, consolidate and save
        this.consolidateData();
        this.saveMasterTopology();
        this.updateUI();
    }

    async processUploadedFile(file) {
        try {
            console.log(`Processing: ${file.name} (${(file.size / 1024).toFixed(2)} KB)`);
            
            // Read file content
            const csvText = await this.readFileAsText(file);
            
            // Parse CSV
            const results = Papa.parse(csvText, {
                header: true,
                dynamicTyping: true,
                skipEmptyLines: true,
                transformHeader: (header) => header.trim()
            });

            // Store file info
            const fileData = {
                name: file.name,
                size: file.size,
                uploadTime: new Date().toISOString(),
                recordCount: results.data.length,
                data: results.data,
                headers: results.meta.fields,
                hash: await this.generateFileHash(csvText) // For duplicate detection
            };

            // Check for duplicates
            if (!this.isDuplicateFile(fileData.hash)) {
                this.uploadedFiles.push(fileData);
                this.addToMasterData(fileData);
                console.log(`✓ Added ${file.name}: ${results.data.length} records`);
            } else {
                console.log(`⚠ Skipped ${file.name}: Duplicate file`);
            }

        } catch (error) {
            console.error(`Failed to process ${file.name}:`, error);
        }
    }

    readFileAsText(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result);
            reader.onerror = () => reject(reader.error);
            reader.readAsText(file);
        });
    }

    async generateFileHash(content) {
        // Simple hash for duplicate detection
        const encoder = new TextEncoder();
        const data = encoder.encode(content);
        const hashBuffer = await crypto.subtle.digest('SHA-256', data);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    }

    isDuplicateFile(hash) {
        return this.uploadedFiles.some(file => file.hash === hash);
    }

    addToMasterData(fileData) {
        // Add unique records to master data set
        fileData.data.forEach(record => {
            const recordKey = this.generateRecordKey(record);
            
            if (!this.duplicateDetection.has(recordKey)) {
                this.duplicateDetection.set(recordKey, {
                    record: record,
                    source: fileData.name,
                    uploadTime: fileData.uploadTime
                });
            }
        });

        // Track data source
        this.dataSources.push({
            filename: fileData.name,
            recordCount: fileData.recordCount,
            uploadTime: fileData.uploadTime,
            headers: fileData.headers
        });
    }

    generateRecordKey(record) {
        // Create unique key for record deduplication
        // Adjust based on your CSV columns
        const source = record.source || record.src || record.source_ip || '';
        const dest = record.destination || record.dst || record.destination_ip || '';
        const protocol = record.protocol || '';
        const timestamp = record.timestamp || '';
        const application = record.application || record.app_id || '';
        
        return `${source}->${dest}:${protocol}:${application}:${timestamp}`;
    }

    consolidateData() {
        // Convert deduplicated records back to arrays
        const consolidatedRecords = Array.from(this.duplicateDetection.values())
            .map(item => item.record);

        // Update appData with consolidated data
        this.appData.csvData = consolidatedRecords;
        this.appData.csvTrafficData = consolidatedRecords;

        // Regenerate applications and topology
        this.appData.processCSVData();
        this.appData.generateBasicTopology();

        console.log(`Consolidated ${consolidatedRecords.length} unique records from ${this.uploadedFiles.length} files`);
    }

    saveMasterTopology() {
        // Save consolidated topology to master file
        const masterData = {
            metadata: {
                created: new Date().toISOString(),
                version: '2.0.0',
                totalFiles: this.uploadedFiles.length,
                totalRecords: this.duplicateDetection.size,
                dataSources: this.dataSources,
                deduplicationEnabled: true
            },
            topology: this.appData.networkTopology,
            rawData: Array.from(this.duplicateDetection.values()),
            applications: this.appData.applications,
            uploadHistory: this.uploadedFiles.map(f => ({
                name: f.name,
                size: f.size,
                uploadTime: f.uploadTime,
                recordCount: f.recordCount
            }))
        };

        // Save to browser storage
        try {
            localStorage.setItem('network_topology_master', JSON.stringify(masterData));
            console.log('✓ Master topology saved to browser storage');
        } catch (error) {
            console.warn('⚠ Could not save to storage, downloading instead');
            this.downloadMasterFile(masterData);
        }

        // Also download as backup
        this.downloadMasterFile(masterData);
    }

    downloadMasterFile(data) {
        const filename = `network_topology_master.json`;
        
        const blob = new Blob([JSON.stringify(data, null, 2)], 
                             { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        
        URL.revokeObjectURL(url);
        console.log(`✓ Master topology downloaded: ${filename}`);
    }

    updateUI() {
        // Update data source display
        const sourceName = document.getElementById('current-source-name');
        if (sourceName) {
            const fileCount = this.uploadedFiles.length;
            const recordCount = this.duplicateDetection.size;
            sourceName.textContent = fileCount > 0 ? 
                `${fileCount} files (${recordCount.toLocaleString()} unique records)` :
                'No files uploaded';
        }

        // Update metadata display
        const metadataEl = document.getElementById('data-metadata');
        if (metadataEl) {
            const stats = this.getConsolidatedStats();
            metadataEl.innerHTML = `
                Records: ${stats.totalRecords.toLocaleString()} | 
                Apps: ${stats.applications} | 
                Files: ${stats.uploadedFiles} |
                Nodes: ${stats.nodes.toLocaleString()} | 
                Links: ${stats.links.toLocaleString()}
            `;
        }

        // Refresh topology visualization
        if (window.topologyDashboard) {
            window.topologyDashboard.updateNetworkData();
            window.topologyDashboard.render();
            window.topologyDashboard.updateStats();
        }
    }

    getConsolidatedStats() {
        return {
            totalRecords: this.duplicateDetection.size,
            applications: this.appData.applications.length,
            uploadedFiles: this.uploadedFiles.length,
            nodes: this.appData.networkTopology.nodes.length,
            links: this.appData.networkTopology.links.length,
            uniqueSources: new Set(Array.from(this.duplicateDetection.values())
                .map(item => item.record.src || item.record.source)).size,
            uniqueDestinations: new Set(Array.from(this.duplicateDetection.values())
                .map(item => item.record.dst || item.record.destination)).size
        };
    }

    // Load existing master topology
    async loadMasterTopology() {
        try {
            const stored = localStorage.getItem('network_topology_master');
            if (stored) {
                const masterData = JSON.parse(stored);
                
                // Restore uploaded files info
                this.uploadedFiles = masterData.uploadHistory || [];
                this.dataSources = masterData.metadata.dataSources || [];
                
                // Restore deduplicated data
                if (masterData.rawData) {
                    this.duplicateDetection.clear();
                    masterData.rawData.forEach(item => {
                        const key = this.generateRecordKey(item.record);
                        this.duplicateDetection.set(key, item);
                    });
                }

                // Restore topology and applications
                this.appData.networkTopology = masterData.topology;
                this.appData.applications = masterData.applications || [];
                this.appData.csvData = Array.from(this.duplicateDetection.values()).map(item => item.record);
                this.appData.isDataLoaded = true;

                console.log(`✓ Loaded master topology: ${this.duplicateDetection.size} records from ${this.uploadedFiles.length} files`);
                this.updateUI();
                return true;
            }
        } catch (error) {
            console.error('Failed to load master topology:', error);
        }
        return false;
    }

    // Clear all uploaded data
    clearAllData() {
        this.uploadedFiles = [];
        this.dataSources = [];
        this.duplicateDetection.clear();
        this.appData.csvData = [];
        this.appData.csvTrafficData = [];
        this.appData.applications = [];
        
        localStorage.removeItem('masterTopology');
        
        this.updateUI();
        console.log('✓ All uploaded data cleared');
    }

    // Export current state for sharing
    exportMasterFile() {
        const exportData = {
            metadata: {
                exported: new Date().toISOString(),
                version: '2.0.0',
                totalFiles: this.uploadedFiles.length,
                totalRecords: this.duplicateDetection.size
            },
            dataSources: this.dataSources,
            topology: this.appData.networkTopology,
            applications: this.appData.applications,
            settings: {
                selectedApps: window.topologyDashboard?.selectedApps || [],
                displayOptions: window.topologyDashboard?.displayOptions || {},
                layout: window.topologyDashboard?.currentLayout || 'force'
            }
        };

        this.downloadMasterFile(exportData);
    }

    // Get upload history for debugging
    getUploadHistory() {
        return {
            files: this.uploadedFiles,
            totalRecords: this.duplicateDetection.size,
            dataSources: this.dataSources,
            deduplicationMap: this.duplicateDetection.size
        };
    }
}

// Integration functions for your existing HTML

function setupDynamicDataSource() {
    // Initialize data source manager
    if (window.AppData) {
        window.dataSourceManager = new DataSourceManager(window.AppData);
        window.dataSourceManager.setupFileUpload();
        
        // Try to load existing master topology
        window.dataSourceManager.loadMasterTopology();
    }
}

function uploadCSVFiles() {
    // Trigger file upload
    if (window.dataSourceManager) {
        window.dataSourceManager.triggerFileUpload();
    }
}

function clearUploadedData() {
    if (window.dataSourceManager) {
        if (confirm('Clear all uploaded data and reset to empty state?')) {
            window.dataSourceManager.clearAllData();
        }
    }
}

function exportMasterTopology() {
    if (window.dataSourceManager) {
        window.dataSourceManager.exportMasterFile();
    }
}

function getUploadStats() {
    if (window.dataSourceManager) {
        const stats = window.dataSourceManager.getUploadHistory();
        console.log('Upload Statistics:', stats);
        return stats;
    }
}

// Updated save functions for your existing HTML

function saveTopology() {
    if (!window.AppData) {
        createToast('Data not loaded yet', 'error');
        return;
    }
    
    // Enhanced save that includes uploaded data sources
    const topologyData = {
        metadata: {
            generated: new Date().toISOString(),
            nodeCount: window.AppData.networkTopology.nodes?.length || 0,
            linkCount: window.AppData.networkTopology.links?.length || 0,
            applications: window.AppData.applications.length,
            uploadedFiles: window.dataSourceManager?.uploadedFiles.length || 0,
            version: '2.0.0'
        },
        topology: window.AppData.networkTopology,
        applications: window.AppData.applications,
        uploadedSources: window.dataSourceManager?.dataSources || [],
        settings: {
            selectedApps: window.topologyDashboard?.selectedApps || [],
            displayOptions: window.topologyDashboard?.displayOptions || {},
            showUpstream: window.topologyDashboard?.showUpstream || false,
            showDownstream: window.topologyDashboard?.showDownstream || false,
            layout: window.topologyDashboard?.currentLayout || 'force'
        }
    };
    
    // Save to master file
    if (window.dataSourceManager) {
        window.dataSourceManager.saveMasterTopology();
        updateTopologySaveStatus('Saved to master file');
    } else {
        // Fallback to regular save
        const blob = new Blob([JSON.stringify(topologyData, null, 2)], 
                             { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `topology_${new Date().toISOString().slice(0,19).replace(/:/g,'-')}.json`;
        a.click();
        
        URL.revokeObjectURL(url);
        updateTopologySaveStatus('Downloaded');
    }
}

function loadTopologyFile(input) {
    const file = input.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = async (e) => {
        try {
            const topologyData = JSON.parse(e.target.result);
            
            // Restore topology
            if (topologyData.topology) {
                window.AppData.networkTopology = topologyData.topology;
            }
            
            // Restore applications
            if (topologyData.applications) {
                window.AppData.applications = topologyData.applications;
            }
            
            // Restore uploaded sources if available
            if (topologyData.uploadedSources && window.dataSourceManager) {
                window.dataSourceManager.dataSources = topologyData.uploadedSources;
            }
            
            // Restore settings
            if (topologyData.settings && window.topologyDashboard) {
                const settings = topologyData.settings;
                
                // Restore application selection
                if (settings.selectedApps) {
                    window.topologyDashboard.selectedApps = settings.selectedApps;
                }
                
                // Restore display options
                if (settings.displayOptions) {
                    window.topologyDashboard.displayOptions = settings.displayOptions;
                    
                    // Update UI checkboxes
                    Object.entries(settings.displayOptions).forEach(([key, value]) => {
                        const checkboxId = key.replace(/([A-Z])/g, '-$1').toLowerCase().replace(/^-/, 'show-');
                        const checkbox = document.getElementById(checkboxId);
                        if (checkbox) checkbox.checked = value;
                    });
                }
                
                // Restore layout
                if (settings.layout) {
                    window.topologyDashboard.setLayout(settings.layout);
                }
            }
            
            // Update visualization
            if (window.topologyDashboard) {
                window.topologyDashboard.updateNetworkData();
                window.topologyDashboard.render();
                window.topologyDashboard.updateStats();
            }
            
            createToast('Topology loaded successfully', 'success');
            
        } catch (error) {
            console.error('Failed to load topology:', error);
            createToast('Failed to load topology file', 'error');
        }
    };
    
    reader.readAsText(file);
    input.value = ''; // Reset input
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Setup dynamic data source after a delay to ensure AppData is ready
    setTimeout(() => {
        setupDynamicDataSource();
    }, 1000);
});

// Enhanced getMetadata function for your app-data.js
function getEnhancedMetadata() {
    const baseMetadata = window.AppData.getMetadata();
    
    if (window.dataSourceManager) {
        const stats = window.dataSourceManager.getConsolidatedStats();
        return {
            ...baseMetadata,
            recordCount: stats.totalRecords,
            uploadedFiles: stats.uploadedFiles,
            summaryStats: {
                unique_sources: stats.uniqueSources,
                unique_destinations: stats.uniqueDestinations,
                unique_protocols: window.AppData.getUniqueProtocols()
            }
        };
    }
    
    return baseMetadata;
}