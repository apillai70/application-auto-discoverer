/**
 * Application Data Manager - Dynamic File Discovery Version
 * Handles CSV loading, application management, and network topology generation
 * 
 * DATA ARCHITECTURE:
 * - applicationList.csv: STATIC file that stays in data_staging/ permanently
 * - Traffic CSV files: DYNAMIC files processed through pipeline (pending → processed/failed)
 * 
 * PIPELINE FLOW:
 * 1. Applications: Always loaded from /data_staging/applicationList.csv (never moves)
 * 2. Traffic Data: Loaded from pipeline-discovered files in processed/ or pending states
 * 3. File Discovery: Only applies to traffic data files, not applicationList.csv
 */

console.log('Loading dynamic app-data.js...');

class ApplicationDataManager {
    constructor() {
        // Core data structures
        this.applications = [];
        this.trafficData = [];
        this.networkTopology = { nodes: [], links: [] };
        
        // State management
        this.isDataLoaded = false;
        this.lastUpdate = null;
        this.loadingProgress = 0;
        this.errors = [];
        this.pipelineStatus = null;
        
        // Deduplication tracking
        this.recordRegistry = new Map(); // Track all processed records
        this.duplicateStats = {
            totalProcessed: 0,
            duplicatesIgnored: 0,
            recordsUpdated: 0
        };
        
        this.preservedApplications = new Set(); // Apps that came from loaded topology
        this.applicationSources = new Map();
        
        this.autoSaveEnabled = false; // Default off, can be toggled via UI
        
        // Configuration
        this.config = {
            maxTrafficRows: 500000, // Limit for performance
            csvPaths: {
                applications: '/data_staging/applicationList.csv', // Static - never moves
                traffic: null // Will be determined dynamically from pipeline
            },
            apiEndpoints: {
                dataStatus: '/api/v1/data/status',
                currentCsv: '/api/v1/data/current',
                filesList: '/api/v1/data/files'
            },
            archetypeClassification: {
                // Keywords for classifying applications by name
                'Microservices': ['api', 'service', 'micro', 'rest', 'endpoint', 'gateway'],
                'Web + API Headless': ['web', 'portal', 'ui', 'frontend', 'site', 'dashboard'],
                'Database-Centric': ['db', 'database', 'data', 'warehouse', 'storage', 'repo'],
                'Event-Driven': ['event', 'queue', 'stream', 'message', 'broker', 'kafka', 'rabbit'],
                'Monolithic': ['legacy', 'mainframe', 'core', 'enterprise', 'erp', 'crm'],
                'SOA': ['soa', 'soap', 'enterprise service', 'esb'],
                'Client-Server': ['client', 'desktop', 'thick client', 'fat client'],
                '3-Tier': ['system', 'application', 'platform']
            }
        };
        
        this.init();
    }
    
    async init() {
        console.log('Initializing Application Data Manager with dynamic file discovery...');
        this.updateProgress(0, 'Starting initialization...');
        
        try {
            // First, check the data pipeline status
            await this.checkPipelineStatus();
            this.updateProgress(20, 'Pipeline status checked, discovering CSV files...');
            
            // Discover current CSV files dynamically
            await this.discoverCurrentCsvFiles();
            this.updateProgress(40, 'CSV files discovered, loading applications...');
            
            // Load applications first (always required)
            await this.loadApplications();
            this.updateProgress(65, 'Applications loaded, loading traffic data...');
            
            // Load traffic data (optional)
            await this.loadTrafficData();
            this.updateProgress(85, 'Generating network topology...');
            
            // Generate initial topology
            this.generateNetworkTopology();
            this.updateProgress(100, 'Initialization complete');
            
            this.isDataLoaded = true;
            this.lastUpdate = new Date();
            
            console.log(`Initialization complete: ${this.applications.length} apps, ${this.trafficData.length} traffic records`);
            console.log('Pipeline status:', this.pipelineStatus?.pipeline_health?.status || 'unknown');
            
        } catch (error) {
            console.error('Initialization failed:', error);
            this.errors.push(`Initialization failed: ${error.message}`);
            this.createFallbackData();
        }
    }
    
    async checkPipelineStatus() {
        console.log('Checking data pipeline status...');
        
        try {
            const response = await fetch(this.config.apiEndpoints.dataStatus);
            if (response.ok) {
                this.pipelineStatus = await response.json();
                console.log('Pipeline status:', this.pipelineStatus.pipeline_health);
                
                // Log pipeline statistics
                const stats = this.pipelineStatus.status;
                console.log(`Pipeline files - Processed: ${stats.processed.count}, Failed: ${stats.failed.count}, Pending: ${stats.pending.count}`);
                
                return this.pipelineStatus;
            } else {
                console.warn('Pipeline status endpoint not available, using fallback discovery');
                return null;
            }
        } catch (error) {
            console.warn('Failed to check pipeline status:', error);
            this.errors.push(`Pipeline status check failed: ${error.message}`);
            return null;
        }
    }
    
    async discoverCurrentCsvFiles() {
        console.log('Discovering current CSV files...');
        
        try {
            const response = await fetch(this.config.apiEndpoints.currentCsv);
            if (response.ok) {
                const currentFile = await response.json();
                console.log('Current CSV discovered:', currentFile);
                
                this.config.csvPaths.traffic = currentFile.endpoint;
                console.log('Dynamic traffic CSV path:', this.config.csvPaths.traffic);
                
                return currentFile;
            } else if (response.status === 404) {
                console.warn('No current CSV file available from pipeline');
                return await this.tryRecentFilesFallback();
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            console.warn('CSV discovery failed, using fallback:', error);
            this.errors.push(`CSV discovery failed: ${error.message}`);
            
            return await this.tryRecentFilesFallback();
        }
    }

    // Generic method to find the most recent CSV file
    async tryRecentFilesFallback() {
        console.log('Trying to find most recent CSV files...');
        
        // Priority order for file patterns (most specific to least specific)
        const filePatterns = [
            '_normalized_',     // Files from generate_file.py pipeline  
            '_processed_',      // Processed files
            'traffic',          // General traffic files
            'network',          // Network data files
            'edges',           // Edge data files
            '.csv'             // Any CSV file as last resort
        ];
        
        // Directories to search in priority order
        const searchPaths = [
            '/data_staging/processed',
            '/data_staging'
        ];
        
        for (const basePath of searchPaths) {
            for (const pattern of filePatterns) {
                try {
                    // Try to discover files by attempting common naming conventions
                    const potentialFiles = await this.discoverFilesWithPattern(basePath, pattern);
                    
                    if (potentialFiles.length > 0) {
                        const latestFile = potentialFiles[0]; // Assume first is most recent
                        console.log(`Found recent file: ${latestFile}`);
                        this.config.csvPaths.traffic = latestFile;
                        return { 
                            endpoint: latestFile, 
                            filename: latestFile.split('/').pop(), 
                            status: 'recent_fallback',
                            pattern: pattern
                        };
                    }
                } catch (e) {
                    console.log(`No files found with pattern '${pattern}' in ${basePath}`);
                }
            }
        }
        
        console.warn('No suitable CSV files found in fallback search');
        return null;
    }

    async discoverFilesWithPattern(basePath, pattern) {
        // Since we can't list directory contents via HTTP, try common file naming patterns
        const commonTimestamps = this.generateRecentTimestamps();
        const potentialFiles = [];
        const prefixes = ['', 'processed_', 'updated_', 'normalized_', 'App_Code_'];
        
        for (const timestamp of commonTimestamps) {
            for (const prefix of prefixes) {
                const testPaths = [
                    `${basePath}/${prefix}${pattern}${timestamp}.csv`,
                    `${basePath}/${prefix}${pattern}.csv`
                ];
                
                for (const testPath of testPaths) {
                    try {
                        const response = await fetch(testPath, { method: 'HEAD' });
                        if (response.ok) {
                            potentialFiles.push(testPath);
                        }
                    } catch (e) {
                        // File doesn't exist, continue
                    }
                }
            }
            
            if (potentialFiles.length > 0) break; // Found files, stop searching
        }
        
        return potentialFiles;
    }

    generateRecentTimestamps() {
        const timestamps = [];
        const now = new Date();
        
        // Generate timestamps for the last few days
        for (let hours = 0; hours < 72; hours++) {
            const date = new Date(now.getTime() - (hours * 60 * 60 * 1000));
            
            // Multiple timestamp formats to match your generate_file.py output
            const formats = [
                date.toISOString().slice(0, 19).replace(/[:-]/g, '').replace('T', '_'), // 20250917_115121
                date.toISOString().slice(0, 10).replace(/-/g, ''),                     // 20250917
                date.toISOString().slice(0, 16).replace(/[:-]/g, '').replace('T', '_') // 20250917_1151
            ];
            
            timestamps.push(...formats);
        }
        
        return [...new Set(timestamps)]; // Remove duplicates
    }
    
    async getAllPipelineFiles() {
        console.log('Getting all pipeline files...');
        
        try {
            const response = await fetch(this.config.apiEndpoints.filesList);
            if (response.ok) {
                const filesList = await response.json();
                console.log('Pipeline files:', filesList);
                return filesList;
            } else {
                console.warn('Files list endpoint not available');
                return null;
            }
        } catch (error) {
            console.warn('Failed to get pipeline files:', error);
            return null;
        }
    }
    
    updateProgress(percentage, message) {
        this.loadingProgress = percentage;
        console.log(`Progress: ${percentage}% - ${message}`);
    }
    
    async loadApplications() {
        console.log('Loading applications from static CSV...');
        
        try {
            const response = await fetch(this.config.csvPaths.applications);
            if (response.ok) {
                const csvText = await response.text();
                this.applications = this.parseApplicationsCSV(csvText);
                console.log(`Loaded ${this.applications.length} applications from static CSV`);
            } else {
                console.warn('Applications CSV not available, creating fallback applications');
                this.createFallbackApplications();
            }
        } catch (error) {
            console.warn('Applications loading failed, using fallback:', error);
            this.errors.push(`Applications loading failed: ${error.message}`);
            this.createFallbackApplications();
        }
    }
    
    // Fallback methods
    async createFallbackData() {
		console.log('No CSV found, attempting to load saved topology...');
		
		try {
			// Try to load your specific saved topology file
			const success = await this.loadSpecificTopology('netseg_topology_20250917T231658.json');
			if (success) {
				console.log('✅ Loaded saved topology instead of creating fake data');
				this.isDataLoaded = true;
				this.lastUpdate = new Date();
				return;
			}
		} catch (error) {
			console.warn('Failed to load saved topology:', error);
		}
		
		// Only create minimal fallback if topology loading fails
		console.log('Creating minimal fallback data...');
		this.createFallbackApplications();
		this.generateNetworkTopology();
		this.isDataLoaded = true;
		this.lastUpdate = new Date();
	}
    
    createFallbackApplications() {
        this.applications = [
            {
                id: 'CORE_BANKING',
                name: 'Core Banking System',
                displayName: 'Core Banking System [CORE_BANKING]',
                archetype: 'Database-Centric',
                businessFunction: 'Core Banking',
                criticality: 'critical',
                technology: 'Database Platform',
                status: 'active',
                ports: ['3306', '1433'],
                protocols: ['SQL', 'HTTP'],
                searchText: 'core banking system core_banking',
                connectionCount: 150,
                trafficVolume: 2500,
                responseTime: 45
            },
            {
                id: 'CUSTOMER_PORTAL',
                name: 'Customer Portal',
                displayName: 'Customer Portal [CUSTOMER_PORTAL]',
                archetype: 'Web + API Headless',
                businessFunction: 'Customer Services',
                criticality: 'high',
                technology: 'Web Platform',
                status: 'active',
                ports: ['80', '443', '8080'],
                protocols: ['HTTP', 'HTTPS'],
                searchText: 'customer portal customer_portal',
                connectionCount: 85,
                trafficVolume: 1800,
                responseTime: 25
            },
            {
                id: 'PAYMENT_API',
                name: 'Payment API Gateway',
                displayName: 'Payment API Gateway [PAYMENT_API]',
                archetype: 'Microservices',
                businessFunction: 'Payment Processing',
                criticality: 'critical',
                technology: 'Container Platform',
                status: 'active',
                ports: ['8080', '8443', '3000'],
                protocols: ['HTTP', 'HTTPS', 'gRPC'],
                searchText: 'payment api gateway payment_api',
                connectionCount: 95,
                trafficVolume: 3200,
                responseTime: 15
            },
            {
                id: 'ANALYTICS_ENGINE',
                name: 'Analytics Engine',
                displayName: 'Analytics Engine [ANALYTICS_ENGINE]',
                archetype: 'Event-Driven',
                businessFunction: 'Reporting & Analytics',
                criticality: 'medium',
                technology: 'Messaging Platform',
                status: 'active',
                ports: ['5672', '9092', '8080'],
                protocols: ['AMQP', 'HTTP'],
                searchText: 'analytics engine analytics_engine',
                connectionCount: 45,
                trafficVolume: 950,
                responseTime: 35
            }
        ];
        
        console.log('Created fallback applications:', this.applications.length);
    }
    
    parseApplicationsCSV(csvText) {
        const lines = csvText.trim().split('\n');
        if (lines.length < 2) {
            throw new Error('CSV file is empty or invalid');
        }
        
        // Parse header
        const headers = this.parseCSVLine(lines[0])
            .map(h => h.trim().toLowerCase().replace(/"/g, ''));
        
        const appIdIndex = headers.findIndex(h => h.includes('app_id') || h.includes('id'));
        const appNameIndex = headers.findIndex(h => h.includes('app_name') || h.includes('name'));
        
        if (appIdIndex === -1 || appNameIndex === -1) {
            throw new Error('Required columns (app_id, app_name) not found in CSV');
        }
        
        console.log(`Found columns - app_id: ${headers[appIdIndex]}, app_name: ${headers[appNameIndex]}`);
        
        const applications = [];
        
        // Parse data rows
        for (let i = 1; i < lines.length; i++) {
            const line = lines[i].trim();
            if (!line) continue;
            
            try {
                const columns = this.parseCSVLine(line);
                
                if (columns.length > Math.max(appIdIndex, appNameIndex)) {
                    const appId = this.cleanCSVValue(columns[appIdIndex]);
                    const appName = this.cleanCSVValue(columns[appNameIndex]);
                    
                    if (appId && appName) {
                        const archetype = this.classifyArchetype(appName);
                        
                        applications.push({
                            id: appId,
                            name: appName,
                            displayName: `${appName} [${appId}]`,
                            archetype: archetype,
                            businessFunction: this.inferBusinessFunction(appName),
                            criticality: this.inferCriticality(appName),
                            technology: this.inferTechnology(archetype),
                            status: 'active',
                            ports: this.generatePortsForArchetype(archetype),
                            protocols: this.generateProtocolsForArchetype(archetype),
                            searchText: `${appName} ${appId}`.toLowerCase(),
                            // Metrics (synthetic for now)
                            connectionCount: 0,
                            trafficVolume: 0,
                            responseTime: 0
                        });
                    }
                }
            } catch (rowError) {
                console.warn(`Skipping row ${i}: ${rowError.message}`);
            }
        }
        
        return applications.sort((a, b) => a.name.localeCompare(b.name));
    }
    
    async loadTrafficData() {
		console.log('Loading traffic data from dynamically discovered CSV...');
		
		// TRY DATACONFIG FIRST - this is the fix!
		let trafficPath = null;
		
		try {
			if (window.DataConfig) {
				trafficPath = await window.DataConfig.getCurrentCsvEndpoint();
				console.log('DataConfig provided traffic path:', trafficPath);
			}
		} catch (error) {
			console.warn('DataConfig not available:', error);
		}
		
		// Fallback to old config if DataConfig didn't work
		if (!trafficPath && this.config.csvPaths.traffic) {
			trafficPath = this.config.csvPaths.traffic;
			console.log('Using fallback traffic path:', trafficPath);
		}
		
		if (!trafficPath) {
			console.warn('No traffic CSV path available from DataConfig or config');
			return;
		}
		
		// Track deduplication stats before processing
		const statsBeforeProcessing = { ...this.duplicateStats };
		
		try {
			console.log('Attempting to load traffic from:', trafficPath);
			const response = await fetch(trafficPath);
			if (!response.ok) {
				console.warn(`Traffic data not available: HTTP ${response.status} for ${trafficPath}`);
				
				// Try alternative paths if the dynamic path fails
				await this.tryAlternativeTrafficPaths();
				return;
			}
			
			const csvText = await response.text();
			console.log(`Traffic CSV loaded: ${csvText.length} characters from ${trafficPath}`);
			
			this.trafficData = this.parseTrafficCSV(csvText);
			console.log(`Parsed ${this.trafficData.length} traffic records`);
			
			// Enrich applications with traffic data
			this.enrichApplicationsWithTraffic();
			
			// Check if significant changes occurred and auto-save is enabled
			const newRecordsAdded = this.duplicateStats.totalProcessed - statsBeforeProcessing.totalProcessed;
			const recordsUpdated = this.duplicateStats.recordsUpdated - statsBeforeProcessing.recordsUpdated;
			
			if (this.autoSaveEnabled && (newRecordsAdded > 0 || recordsUpdated > 0)) {
				console.log(`Auto-saving topology: ${newRecordsAdded} new records, ${recordsUpdated} updated records`);
				try {
					const saveResult = this.saveTopologyToFile();
					console.log('Auto-save completed:', saveResult.filename);
				} catch (saveError) {
					console.warn('Auto-save failed:', saveError.message);
					this.errors.push(`Auto-save failed: ${saveError.message}`);
				}
			}
			
		} catch (error) {
			console.warn('Traffic data loading failed (non-critical):', error);
			this.errors.push(`Traffic loading failed: ${error.message}`);
			
			// Try alternative paths
			await this.tryAlternativeTrafficPaths();
		}
	}
    
    async tryAlternativeTrafficPaths() {
        console.log('Trying alternative traffic file paths using generic discovery...');
        return await this.tryRecentFilesFallback();
    }
    
    parseTrafficCSV(csvText) {
        const lines = csvText.trim().split('\n');
        if (lines.length < 2) {
            console.warn('Traffic CSV is empty');
            return [];
        }
        
        // Parse header
        const headers = this.parseCSVLine(lines[0])
            .map(h => h.trim().toLowerCase().replace(/"/g, ''));
        
        console.log('Traffic CSV headers:', headers.slice(0, 10), '...');
        
        const trafficData = [];
        const maxRows = Math.min(lines.length - 1, this.config.maxTrafficRows);
        
        // DON'T reset deduplication stats for this file - we want accumulation
        // Keep existing registry and stats, just track new additions
        const fileStats = {
            totalRows: 0,
            duplicatesIgnored: 0,
            recordsUpdated: 0,
            newRecords: 0
        };
        
        // Parse data rows with deduplication (but keep existing registry)
        for (let i = 1; i <= maxRows; i++) {
            if (i % 5000 === 0) {
                console.log(`Parsing traffic data: ${i}/${maxRows} rows (${fileStats.newRecords} new, ${fileStats.recordsUpdated} updated, ${fileStats.duplicatesIgnored} duplicates ignored)`);
            }
            
            const line = lines[i].trim();
            if (!line) continue;
            
            try {
                const columns = this.parseCSVLine(line);
                const row = {};
                
                headers.forEach((header, index) => {
                    if (index < columns.length) {
                        const value = this.cleanCSVValue(columns[index]);
                        row[header] = this.convertValue(value);
                    }
                });
                
                // Only process rows with meaningful data
                if (row.source_ip || row.destination_ip || row.protocol) {
                    fileStats.totalRows++;
                    
                    // Create unique key for deduplication
                    const recordKey = this.createRecordKey(row);
                    
                    if (recordKey) {
                        const processResult = this.processRecordForDeduplication(recordKey, row);
                        
                        if (processResult.action === 'add') {
                            trafficData.push(row);
                            fileStats.newRecords++;
                        } else if (processResult.action === 'update') {
                            trafficData.push(row);
                            fileStats.recordsUpdated++;
                        } else if (processResult.action === 'ignore') {
                            fileStats.duplicatesIgnored++;
                        }
                    } else {
                        // No valid key could be created, add as new record
                        trafficData.push(row);
                        fileStats.newRecords++;
                    }
                }
                
            } catch (rowError) {
                // Skip problematic rows silently
                if (i % 10000 === 0) {
                    console.warn(`Traffic parsing issues around row ${i}`);
                }
            }
        }
        
        // Update global stats (accumulative)
        this.duplicateStats.totalProcessed += fileStats.totalRows;
        this.duplicateStats.duplicatesIgnored += fileStats.duplicatesIgnored;
        this.duplicateStats.recordsUpdated += fileStats.recordsUpdated;
        
        console.log(`Traffic CSV processed - File stats: Total: ${fileStats.totalRows}, New: ${fileStats.newRecords}, Updated: ${fileStats.recordsUpdated}, Ignored duplicates: ${fileStats.duplicatesIgnored}`);
        console.log(`Global stats - Total processed: ${this.duplicateStats.totalProcessed}, Total ignored: ${this.duplicateStats.duplicatesIgnored}, Registry size: ${this.recordRegistry.size}`);
        
        return trafficData;
    }
    
    createRecordKey(record) {
        // Create unique key based on core identifying fields
        // Adjust these fields based on what makes a record unique in your data
        const keyFields = [
            record.source_ip,
            record.destination_ip,
            record.protocol,
            record.port || record.dst_port || record.destination_port,
            record.timestamp || record.time || record.datetime
        ].filter(field => field !== null && field !== undefined && field !== '');
        
        if (keyFields.length < 3) {
            // Not enough identifying information
            return null;
        }
        
        return keyFields.join('|').toLowerCase();
    }
    
    processRecordForDeduplication(recordKey, newRecord) {
        if (!this.recordRegistry.has(recordKey)) {
            // New record - add to registry
            this.recordRegistry.set(recordKey, {
                record: { ...newRecord },
                firstSeen: new Date().toISOString(),
                lastUpdated: new Date().toISOString(),
                updateCount: 0
            });
            return { action: 'add', reason: 'new_record' };
        }
        
        // Record exists - check if it's different
        const existingEntry = this.recordRegistry.get(recordKey);
        const existingRecord = existingEntry.record;
        
        if (this.recordsAreDifferent(existingRecord, newRecord)) {
            // Record has changed - update it
            this.recordRegistry.set(recordKey, {
                record: { ...newRecord },
                firstSeen: existingEntry.firstSeen,
                lastUpdated: new Date().toISOString(),
                updateCount: existingEntry.updateCount + 1
            });
            return { action: 'update', reason: 'record_changed' };
        }
        
        // Record is identical - ignore
        return { action: 'ignore', reason: 'duplicate' };
    }
    
    recordsAreDifferent(record1, record2) {
        // Compare significant fields (exclude metadata like timestamps that might differ)
        const significantFields = [
            'source_ip', 'destination_ip', 'protocol', 'port', 'dst_port', 'destination_port',
            'bytes', 'packets', 'duration', 'flags', 'service', 'application',
            'source_port', 'traffic_type', 'connection_state'
        ];
        
        for (const field of significantFields) {
            const val1 = record1[field];
            const val2 = record2[field];
            
            // Convert to strings for comparison to handle type differences
            const str1 = val1 !== null && val1 !== undefined ? String(val1).trim() : '';
            const str2 = val2 !== null && val2 !== undefined ? String(val2).trim() : '';
            
            if (str1 !== str2) {
                return true;
            }
        }
        
        return false;
    }
    
    enrichApplicationsWithTraffic() {
		if (!this.trafficData.length) {
			console.log('No traffic data available for enrichment');
			return;
		}
		
		console.log('Enriching existing applications with traffic data...');
		console.log(`Starting with ${this.applications.length} existing applications:`, 
			this.applications.map(app => app.name));
		
		// Create a map of existing applications by name for faster lookup
		const existingApps = new Map();
		this.applications.forEach(app => {
			// Add multiple lookup keys for each app
			existingApps.set(app.name, app);                    // Full name
			existingApps.set(app.id, app);                      // App ID  
			existingApps.set(app.name.toLowerCase(), app);      // Case insensitive name
			existingApps.set(app.id.toLowerCase(), app);        // Case insensitive ID
			
			// Extract acronyms/abbreviations from parentheses
			const acronymMatch = app.name.match(/\(([^)]+)\)/);
			if (acronymMatch) {
				existingApps.set(acronymMatch[1], app);          // (FTM4C) -> FTM4C
				existingApps.set(acronymMatch[1].toLowerCase(), app);
			}
			
			// Extract words that might be used as short names
			const words = app.name.split(/\s+/);
			if (words.length > 1) {
				// Try combinations like "Financial Transaction" -> "Financial"
				existingApps.set(words[0], app);
				existingApps.set(words[0].toLowerCase(), app);
			}
		});
		
		// Extract unique applications from traffic data
		const appTrafficMap = new Map();
		
		this.trafficData.forEach(record => {
			const appName = record.application || 'Unknown';
			
			if (!appTrafficMap.has(appName)) {
				appTrafficMap.set(appName, {
					trafficRecords: 0,
					uniqueIPs: new Set(),
					protocols: new Set(),
					ports: new Set()
				});
			}
			
			const appTraffic = appTrafficMap.get(appName);
			appTraffic.trafficRecords++;
			
			if (record.source_ip) appTraffic.uniqueIPs.add(record.source_ip);
			if (record.destination_ip) appTraffic.uniqueIPs.add(record.destination_ip);
			if (record.protocol) appTraffic.protocols.add(record.protocol);
			if (record.port) appTraffic.ports.add(record.port);
		});
		
		console.log(`Found ${appTrafficMap.size} applications in traffic data:`, 
			Array.from(appTrafficMap.keys()));
		
		// Add new applications or update existing ones
		// IMPORTANT: Only process apps found in traffic data, don't remove existing ones
		appTrafficMap.forEach((trafficData, appName) => {
			// TRY MULTIPLE LOOKUP STRATEGIES - THIS IS THE FIX
			let existingApp = existingApps.get(appName) ||           // Exact match
							 existingApps.get(appName.toUpperCase()) ||  // Uppercase
							 existingApps.get(appName.toLowerCase()) ||  // Lowercase
							 existingApps.get(appName.trim());           // Trim whitespace
			
			if (existingApp) {
				// Update existing application with traffic data
				console.log(`Updating existing app: ${appName} -> ${existingApp.name}`);
				
				existingApp.trafficRecords = trafficData.trafficRecords;
				existingApp.uniqueIPs = trafficData.uniqueIPs.size;
				existingApp.observedProtocols = Array.from(trafficData.protocols);
				existingApp.observedPorts = Array.from(trafficData.ports);
				
				// Update metrics based on traffic
				existingApp.connectionCount = Math.floor(trafficData.trafficRecords / 10) + 5;
				existingApp.trafficVolume = trafficData.trafficRecords * 100;
			} else {
				// Create new application from traffic data ONLY if no match found anywhere
				console.log(`Creating new app from traffic: ${appName} (no match found in existing apps)`);
				
				const newApp = {
					id: appName.toUpperCase(),
					name: appName,
					displayName: `${appName} [${appName.toUpperCase()}]`,
					archetype: this.classifyArchetype(appName),
					businessFunction: this.inferBusinessFunction(appName),
					criticality: this.inferCriticality(appName),
					technology: this.inferTechnology(this.classifyArchetype(appName)),
					status: 'active',
					searchText: `${appName}`.toLowerCase(),
					trafficRecords: trafficData.trafficRecords,
					uniqueIPs: trafficData.uniqueIPs.size,
					observedProtocols: Array.from(trafficData.protocols),
					observedPorts: Array.from(trafficData.ports),
					ports: this.generatePortsForArchetype(this.classifyArchetype(appName)),
					protocols: this.generateProtocolsForArchetype(this.classifyArchetype(appName)),
					connectionCount: Math.floor(trafficData.trafficRecords / 10) + 5,
					trafficVolume: trafficData.trafficRecords * 100,
					responseTime: Math.floor(Math.random() * 50) + 10,
					source: 'traffic_data' // Mark source for debugging
				};
				
				this.applications.push(newApp);
			}
		});
		
		// CRITICAL: Don't remove existing applications that aren't in traffic data
		// They might be from previous uploads or initial discovery
		console.log(`After enrichment: ${this.applications.length} total applications`);
		
		// Log all applications with their sources
		this.applications.forEach(app => {
			const hasTraffic = appTrafficMap.has(app.name) || appTrafficMap.has(app.id);
			console.log(`  - ${app.name}: ${app.trafficRecords || 0} traffic records ${hasTraffic ? '(updated)' : '(preserved)'}`);
		});
	}
    
    // Public API methods
    async loadData() {
        if (!this.isDataLoaded) {
            await this.init();
        }
        return Promise.resolve();
    }
    
    isReady() {
        return this.isDataLoaded;
    }
    
    getStatus() {
        return {
            isReady: this.isDataLoaded,
            dataLoaded: this.isDataLoaded,
            applicationCount: this.applications.length,
            trafficRecordCount: this.trafficData.length,
            hasTrafficData: this.trafficData.length > 0,
            lastUpdate: this.lastUpdate,
            loadingProgress: this.loadingProgress,
            errors: this.errors,
            dataSource: this.trafficData.length > 0 ? 'Dynamic CSV discovery with traffic' : 'Dynamic CSV discovery - applications only',
            pipelineStatus: this.pipelineStatus?.pipeline_health || null,
            currentTrafficCsv: this.config.csvPaths.traffic,
            fileDiscovery: {
                enabled: true,
                statusEndpoint: this.config.apiEndpoints.dataStatus,
                currentEndpoint: this.config.apiEndpoints.currentCsv,
                filesEndpoint: this.config.apiEndpoints.filesList
            },
            deduplication: {
                enabled: true,
                totalProcessed: this.duplicateStats.totalProcessed,
                duplicatesIgnored: this.duplicateStats.duplicatesIgnored,
                recordsUpdated: this.duplicateStats.recordsUpdated,
                uniqueRecords: this.recordRegistry.size,
                deduplicationRate: this.duplicateStats.totalProcessed > 0 
                    ? ((this.duplicateStats.duplicatesIgnored / this.duplicateStats.totalProcessed) * 100).toFixed(2) + '%'
                    : '0%'
            }
        };
    }
    
    getApplicationNamesForFilter() {
        const apps = [
            {
                id: 'all',
                name: 'ALL Applications',
                displayName: `ALL Applications (${this.applications.length} total)`,
                archetype: 'All',
                status: 'active',
                businessFunction: 'All',
                criticality: 'all'
            }
        ];
        
        this.applications.forEach(app => {
            apps.push({
                id: app.id,
                name: app.name,
                displayName: app.displayName,
                fullName: app.name,
                archetype: app.archetype,
                businessFunction: app.businessFunction,
                criticality: app.criticality,
                technology: app.technology,
                status: app.status,
                searchText: app.searchText
            });
        });
        
        return apps;
    }
    
    getApplicationById(id) {
        if (id === 'all') {
            return { id: 'all', name: 'ALL Applications' };
        }
        return this.applications.find(app => app.id === id);
    }
    
    getApplicationsByIds(ids) {
        if (ids.includes('all')) {
            return this.applications;
        }
        return this.applications.filter(app => ids.includes(app.id));
    }
    
    searchApplications(query) {
        if (!query || query.trim() === '') return this.applications;
        
        const searchTerm = query.toLowerCase().trim();
        return this.applications.filter(app => 
            app.searchText.includes(searchTerm) ||
            app.archetype.toLowerCase().includes(searchTerm) ||
            app.businessFunction.toLowerCase().includes(searchTerm)
        );
    }
    
    getMetadata() {
        return {
            dataSource: 'Static applicationList.csv + Dynamic traffic file discovery',
            lastUpdate: this.lastUpdate ? this.lastUpdate.toISOString() : null,
            applicationCount: this.applications.length,
            trafficRecordCount: this.trafficData.length,
            hasTrafficData: this.trafficData.length > 0,
            version: '2.1.0',
            loadTime: this.lastUpdate ? this.lastUpdate.toISOString() : null,
            archetypeDistribution: this.getArchetypeDistribution(),
            criticalityDistribution: this.getCriticalityDistribution(),
            businessFunctionDistribution: this.getBusinessFunctionDistribution(),
            pipelineHealth: this.pipelineStatus?.pipeline_health || null,
            currentTrafficSource: this.config.csvPaths.traffic,
            fileDiscovery: {
                enabled: true,
                statusChecked: !!this.pipelineStatus,
                filesDiscovered: !!this.config.csvPaths.traffic,
                applicationsCsvStatic: true // applicationList.csv never moves
            }
        };
    }
    
    getArchetypeDistribution() {
        const distribution = {};
        this.applications.forEach(app => {
            distribution[app.archetype] = (distribution[app.archetype] || 0) + 1;
        });
        return distribution;
    }
    
    getCriticalityDistribution() {
        const distribution = {};
        this.applications.forEach(app => {
            distribution[app.criticality] = (distribution[app.criticality] || 0) + 1;
        });
        return distribution;
    }
    
    getBusinessFunctionDistribution() {
        const distribution = {};
        this.applications.forEach(app => {
            distribution[app.businessFunction] = (distribution[app.businessFunction] || 0) + 1;
        });
        return distribution;
    }
    
    async refreshData() {
        console.log('Refreshing application data with dynamic discovery...');
        
        // Reset state
        this.isDataLoaded = false;
        this.trafficData = []; // Only clear traffic data
        this.errors = [];
        this.pipelineStatus = null;
        
        // Clear deduplication registry for fresh start
        this.recordRegistry.clear();
        this.duplicateStats = {
            totalProcessed: 0,
            duplicatesIgnored: 0,
            recordsUpdated: 0
        };
        
        await this.init();
        return this.getStatus();
    }
    
    async refreshPipelineStatus() {
        console.log('Refreshing pipeline status...');
        await this.checkPipelineStatus();
        await this.discoverCurrentCsvFiles();
        return this.pipelineStatus;
    }

	async switchToSpecificFile(filename) {
		console.log(`Processing file: ${filename}`);
		
		// Don't allow switching applicationList.csv as it's static
		if (filename === 'applicationList.csv') {
			console.warn('Cannot process applicationList.csv - it is a static reference file');
			this.errors.push('applicationList.csv is a static file and cannot be processed');
			return this.getStatus();
		}
		
		// Only search in /data_staging directory
		const sourceFilePath = `/data_staging/${filename}`;
		const processedPath = `/data_staging/processed/${filename}`;
		const failedPath = `/data_staging/failed/${filename}`;
		
		// Store previous state for rollback if needed
		const previousPath = this.config.csvPaths.traffic;
		const previousTrafficData = [...this.trafficData];
		const previousApplications = [...this.applications];
		
		try {
			// 1. Check if file exists in /data_staging
			console.log(`Checking for file at: ${sourceFilePath}`);
			const sourceResponse = await fetch(sourceFilePath, { method: 'HEAD' });
			
			if (!sourceResponse.ok) {
				throw new Error(`File ${filename} not found in /data_staging (HTTP ${sourceResponse.status})`);
			}
			
			const fileInfo = {
				size: sourceResponse.headers.get('content-length'),
				lastModified: sourceResponse.headers.get('last-modified'),
				contentType: sourceResponse.headers.get('content-type')
			};
			
			console.log(`Found file: ${fileInfo.size} bytes, modified: ${fileInfo.lastModified}`);
			
			// 2. Process the file
			console.log(`Processing ${filename}...`);
			
			// Set the traffic CSV path to the source file
			this.config.csvPaths.traffic = sourceFilePath;
			
			// Clear existing traffic data
			this.trafficData = [];
			
			// Load traffic data from the file
			await this.loadTrafficData();
			
			// Validate that data was loaded successfully
			if (this.trafficData.length === 0) {
				throw new Error(`No traffic data loaded from ${filename} - file may be empty or invalid`);
			}
			
			// Re-enrich applications with new traffic data
			this.enrichApplicationsWithTraffic();
			
			// Regenerate network topology
			this.generateNetworkTopology();
			
			// Update last update timestamp
			this.lastUpdate = new Date();
			
			console.log(`Successfully processed ${filename}: ${this.trafficData.length} records loaded`);
			
			// 3. Move file to processed directory (simulate via API call)
			try {
				console.log(`Moving ${filename} to processed directory...`);
				
				const moveResponse = await fetch('/api/v1/data/move', {
					method: 'POST',
					headers: {
						'Content-Type': 'application/json',
					},
					body: JSON.stringify({
						filename: filename,
						action: 'processed',
						sourceData: {
							recordCount: this.trafficData.length,
							applicationCount: this.applications.length,
							processedAt: new Date().toISOString()
						}
					})
				});
				
				if (moveResponse.ok) {
					console.log(`File ${filename} moved to processed directory`);
					// Update path to reflect new location
					this.config.csvPaths.traffic = processedPath;
				} else {
					console.warn(`Failed to move file to processed directory: HTTP ${moveResponse.status}`);
					// Continue anyway - processing was successful
				}
				
			} catch (moveError) {
				console.warn(`Failed to move file to processed directory: ${moveError.message}`);
				// Continue anyway - processing was successful
			}
			
			// 4. Trigger UI refresh if dashboard exists
			if (window.topologyDashboard) {
				window.topologyDashboard.updateNetworkData();
				window.topologyDashboard.render();
				window.topologyDashboard.updateStats();
			}
			
			return {
				success: true,
				filename: filename,
				sourcePath: sourceFilePath,
				currentPath: this.config.csvPaths.traffic,
				recordCount: this.trafficData.length,
				applicationCount: this.applications.length,
				fileInfo: fileInfo,
				processedAt: new Date().toISOString(),
				moved: this.config.csvPaths.traffic === processedPath,
				message: `Successfully processed ${filename}: ${this.trafficData.length} records loaded, ${this.applications.length} applications`,
				...this.getStatus()
			};
			
		} catch (error) {
			console.error(`Failed to process ${filename}:`, error);
			
			// Rollback state
			this.config.csvPaths.traffic = previousPath;
			this.trafficData = previousTrafficData;
			this.applications = previousApplications;
			
			// Move file to failed directory (simulate via API call)
			try {
				console.log(`Moving ${filename} to failed directory due to processing error...`);
				
				const failResponse = await fetch('/api/v1/data/move', {
					method: 'POST',
					headers: {
						'Content-Type': 'application/json',
					},
					body: JSON.stringify({
						filename: filename,
						action: 'failed',
						error: error.message,
						failedAt: new Date().toISOString()
					})
				});
				
				if (failResponse.ok) {
					console.log(`File ${filename} moved to failed directory`);
				} else {
					console.warn(`Failed to move file to failed directory: HTTP ${failResponse.status}`);
				}
				
			} catch (failMoveError) {
				console.warn(`Failed to move file to failed directory: ${failMoveError.message}`);
			}
			
			const errorMsg = `Failed to process ${filename}: ${error.message}`;
			this.errors.push(errorMsg);
			
			return {
				success: false,
				error: errorMsg,
				filename: filename,
				sourcePath: sourceFilePath,
				failedPath: failedPath,
				rolledBack: true,
				failedAt: new Date().toISOString(),
				message: `Processing failed for ${filename}: ${error.message}`,
				...this.getStatus()
			};
		}
	}

	// Helper method to check pipeline directories
	async checkPipelineDirectories() {
		const directories = [
			'/data_staging',
			'/data_staging/processed', 
			'/data_staging/failed'
		];
		
		const status = {};
		
		for (const dir of directories) {
			try {
				const response = await fetch(dir, { method: 'HEAD' });
				status[dir] = {
					accessible: response.ok,
					status: response.status
				};
			} catch (error) {
				status[dir] = {
					accessible: false,
					error: error.message
				};
			}
		}
		
		console.log('Pipeline directories status:', status);
		return status;
	}

	// Method to list files in data_staging waiting to be processed
	async listPendingFiles() {
		try {
			const response = await fetch('/api/v1/data/pending');
			if (response.ok) {
				const pendingFiles = await response.json();
				console.log('Files pending processing:', pendingFiles);
				return pendingFiles;
			} else {
				console.warn('Could not retrieve pending files list');
				return [];
			}
		} catch (error) {
			console.warn('Error retrieving pending files:', error.message);
			return [];
		}
	}
    
    // Pipeline-specific methods
    async getPipelineFiles() {
        return await this.getAllPipelineFiles();
    }
    
    getPipelineHealth() {
        return this.pipelineStatus?.pipeline_health || { status: 'unknown' };
    }
    
    getCurrentTrafficSource() {
        return {
            path: this.config.csvPaths.traffic,
            recordCount: this.trafficData.length,
            lastLoaded: this.lastUpdate,
            pipelineFile: this.pipelineStatus?.current_active_file || null
        };
    }
    
    // Topology management methods
    async saveTopologyToFile() {
        const timestamp = new Date().toISOString();
        const currentTrafficSource = this.getCurrentTrafficSource();
        
        const topologyData = {
            metadata: {
                generated: timestamp,
                version: '2.1.0',
                source: 'ApplicationDataManager with Dynamic Discovery & Deduplication',
                nodeCount: this.networkTopology.nodes?.length || 0,
                linkCount: this.networkTopology.links?.length || 0,
                applicationCount: this.applications.length,
                trafficRecordCount: this.trafficData.length,
                
                // Pipeline information
                pipelineHealth: this.getPipelineHealth(),
                currentTrafficSource: currentTrafficSource,
                
                // Preservation Tracking
                preservation: {
                    preservedApplicationCount: this.preservedApplications.size,
                    preservedApplications: Array.from(this.preservedApplications),
                    applicationSources: Object.fromEntries(this.applicationSources)
                },
                
                // Deduplication statistics
                deduplication: {
                    enabled: true,
                    totalProcessed: this.duplicateStats.totalProcessed,
                    duplicatesIgnored: this.duplicateStats.duplicatesIgnored,
                    recordsUpdated: this.duplicateStats.recordsUpdated,
                    uniqueRecordsTracked: this.recordRegistry.size,
                    deduplicationRate: this.duplicateStats.totalProcessed > 0 
                        ? ((this.duplicateStats.duplicatesIgnored / this.duplicateStats.totalProcessed) * 100).toFixed(2) + '%'
                        : '0%'
                }
            },
            
            // Core topology data
            topology: this.networkTopology,
            
            // Application data with traffic enrichment
            applications: this.applications.map(app => ({
                id: app.id,
                name: app.name,
                archetype: app.archetype,
                businessFunction: app.businessFunction,
                criticality: app.criticality,
                technology: app.technology,
                status: app.status,
                trafficRecords: app.trafficRecords || 0,
                uniqueIPs: app.uniqueIPs || 0,
                observedProtocols: app.observedProtocols || [],
                observedPorts: app.observedPorts || []
            })),
            
            // UI state preservation
            visualization: {
                selectedApps: window.topologyDashboard?.selectedApps || [],
                displayOptions: window.topologyDashboard?.displayOptions || {},
                showUpstream: window.topologyDashboard?.showUpstream || true,
                showDownstream: window.topologyDashboard?.showDownstream || true,
                layout: window.topologyDashboard?.currentLayout || 'force'
            },
            
            // Pipeline and system state
            systemState: {
                pipelineStatus: this.pipelineStatus,
                lastUpdate: this.lastUpdate,
                errors: this.errors.length > 0 ? this.errors.slice(-5) : [], // Last 5 errors only
                dataLoadingProgress: this.loadingProgress
            }
        };
        
        const filename = `netseg_topology_${timestamp.slice(0,19).replace(/[:-]/g, '')}.json`;
        const jsonString = JSON.stringify(topologyData, null, 2);
        
        // Try to save to server /results/ directory first
        try {
            const saveResponse = await fetch('/api/v1/topology/save', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    filename: filename,
                    data: topologyData
                })
            });
            
            if (saveResponse.ok) {
                const result = await saveResponse.json();
                console.log(`✅ Topology saved to server: /results/${filename}`);
                console.log(`File includes: ${this.applications.length} apps, ${this.networkTopology.nodes?.length || 0} nodes`);
                console.log(`Reload with: AppDataUtils.topologyOps.load('${filename}')`);
                
                return {
                    success: true,
                    filename: filename,
                    location: `/results/${filename}`,
                    size: jsonString.length,
                    deduplicationStats: this.duplicateStats,
                    serverSaved: true
                };
            } else {
                throw new Error(`Server responded with ${saveResponse.status}`);
            }
            
        } catch (serverError) {
            console.warn(`❌ Server save failed: ${serverError.message}`);
            console.log(`💾 Falling back to download - you'll need to manually move the file to /results/`);
            
            // Fallback to download
            try {
                const blob = new Blob([jsonString], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                
                const downloadLink = document.createElement('a');
                downloadLink.href = url;
                downloadLink.download = filename;
                downloadLink.style.display = 'none';
                
                document.body.appendChild(downloadLink);
                downloadLink.click();
                document.body.removeChild(downloadLink);
                
                URL.revokeObjectURL(url);
                
                console.log(`📁 File downloaded: ${filename}`);
                console.log(`⚠️  IMPORTANT: Move this file to /results/ directory to enable reloading`);
                console.log(`Once moved, reload with: AppDataUtils.topologyOps.load('${filename}')`);
                
                return {
                    success: true,
                    filename: filename,
                    location: 'Downloads folder',
                    size: jsonString.length,
                    deduplicationStats: this.duplicateStats,
                    serverSaved: false,
                    requiresManualMove: true,
                    instructions: `Move ${filename} from Downloads to /results/ directory`
                };
                
            } catch (downloadError) {
                console.error('Both server save and download failed:', downloadError);
                this.errors.push(`Save failed completely: ${downloadError.message}`);
                throw downloadError;
            }
        }
    }
    
	async loadSpecificTopology(filename) {
		try {
			// Try loading from results directory
			const response = await fetch(`/results/${filename}`);
			if (!response.ok) {
				throw new Error(`HTTP ${response.status}: ${response.statusText}`);
			}
			
			const topologyData = await response.json();
			
			// Load the network topology
			this.networkTopology = topologyData.topology || { nodes: [], links: [] };
			
			// Restore applications if available
			if (topologyData.applications) {
				this.applications = topologyData.applications;
				
				// Mark all loaded applications as preserved
				this.preservedApplications.clear();
				this.applicationSources.clear();
				
				this.applications.forEach(app => {
					this.preservedApplications.add(app.name);
					this.applicationSources.set(app.name, 'loaded_topology');
				});
				
				console.log(`Restored ${this.applications.length} applications from saved topology`);
			}
			
			// Clear traffic data since we're loading from saved state
			this.trafficData = [];
			this.recordRegistry.clear();
			this.duplicateStats = {
				totalProcessed: 0,
				duplicatesIgnored: 0,
				recordsUpdated: 0
			};
			
			console.log(`✅ Loaded topology from ${filename}`);
			return true;
			
		} catch (error) {
			console.error(`Failed to load topology from ${filename}:`, error);
			return false;
		}
	}
    
    // Method to track application sources and changes
    trackApplicationChanges(operation, details = {}) {
        if (!this.applicationHistory) {
            this.applicationHistory = [];
        }
        
        const snapshot = {
            timestamp: new Date().toISOString(),
            operation: operation,
            details: details,
            applicationCount: this.applications.length,
            applicationNames: this.applications.map(app => ({
                name: app.name,
                id: app.id,
                source: app.source || 'unknown',
                trafficRecords: app.trafficRecords || 0
            }))
        };
        
        this.applicationHistory.push(snapshot);
        console.log(`[APP TRACKING] ${operation}:`, snapshot);
        
        // Keep only last 20 entries
        if (this.applicationHistory.length > 20) {
            this.applicationHistory = this.applicationHistory.slice(-20);
        }
    }

    // Method to preserve specific applications during operations
    preserveApplications(appNamesToPreserve) {
        if (!Array.isArray(appNamesToPreserve)) {
            appNamesToPreserve = [appNamesToPreserve];
        }
        
        const preserved = this.applications.filter(app => 
            appNamesToPreserve.includes(app.name)
        );
        
        console.log(`Preserving ${preserved.length} applications:`, preserved.map(app => app.name));
        return preserved;
    }

    // Enhanced processTrafficCSV with preservation
    async processTrafficCSVWithPreservation(csvText, filename, preserveApps = []) {
        console.log(`Processing traffic CSV: ${filename}`);
        this.trackApplicationChanges('process_traffic_csv_start', { 
            filename, 
            preserveApps,
            currentApps: this.applications.length 
        });
        
        // Preserve specific applications if requested
        const preservedApps = preserveApps.length > 0 ? 
            this.preserveApplications(preserveApps) : [];
        
        // Parse new traffic data
        const newTrafficData = this.parseTrafficCSV(csvText);
        
        // Append new traffic data to existing data
        this.trafficData = [...this.trafficData, ...newTrafficData];
        
        // If we have preserved apps, ensure they stay in the applications array
        if (preservedApps.length > 0) {
            // Remove preserved apps from current list to avoid duplicates
            this.applications = this.applications.filter(app => 
                !preservedApps.some(preserved => preserved.name === app.name)
            );
            
            // Add preserved apps back
            this.applications = [...preservedApps, ...this.applications];
            console.log(`Restored ${preservedApps.length} preserved applications`);
        }
        
        // Add/update applications with ALL traffic data (old + new)
        this.enrichApplicationsWithTraffic();
        
        this.trackApplicationChanges('process_traffic_csv_end', { 
            filename,
            newRecords: newTrafficData.length,
            totalRecords: this.trafficData.length,
            finalApps: this.applications.length
        });
        
        // Regenerate network topology with all applications
        this.generateNetworkTopology();
        
        this.lastUpdate = new Date();
        this.isDataLoaded = true;
        
        console.log(`Successfully processed ${newTrafficData.length} new traffic records from ${filename}`);
        console.log(`Total traffic records now: ${this.trafficData.length}`);
        console.log(`Total applications now: ${this.applications.length}`);
        
        // Trigger UI refresh
        if (window.topologyDashboard) {
            window.topologyDashboard.updateNetworkData();
            window.topologyDashboard.render();
            window.topologyDashboard.updateStats();
        }
        
        return {
            success: true,
            recordCount: newTrafficData.length,
            totalRecords: this.trafficData.length,
            totalApplications: this.applications.length,
            preservedApps: preservedApps.length,
            filename: filename,
            type: 'traffic',
            message: `Added ${newTrafficData.length} records from ${filename}. Total: ${this.trafficData.length} records, ${this.applications.length} applications`
        };
    }

    // CSV processing methods
    async processCSVData(csvText, filename) {
		// Add null/undefined check before trying to access .length
		if (!csvText) {
			console.error(`No CSV text provided for ${filename}`);
			throw new Error(`CSV text is undefined or null for file: ${filename}`);
		}
    
        console.log(`Processing uploaded CSV: ${filename}, ${csvText.length} characters`);
        
        try {
            // Determine file type based on content and filename
            const fileType = this.determineCSVType(csvText, filename);
            
            switch (fileType) {
                case 'traffic':
                    return await this.processTrafficCSV(csvText, filename);
                case 'applications':
                    return await this.processApplicationsCSV(csvText, filename);
                default:
                    // Default to traffic processing for unknown types
                    return await this.processTrafficCSV(csvText, filename);
            }
            
        } catch (error) {
            console.error('Error processing CSV data:', error);
            this.errors.push(`CSV processing failed: ${error.message}`);
            throw error;
        }
    }
    
    determineCSVType(csvText, filename) {
        const firstLine = csvText.split('\n')[0].toLowerCase();
        const name = filename.toLowerCase();
        
        // Check headers to determine file type
        if (firstLine.includes('source_ip') && firstLine.includes('destination_ip')) {
            return 'traffic';
        }
        if (firstLine.includes('app_id') && firstLine.includes('app_name')) {
            return 'applications';
        }
        
        // Fallback to filename patterns
        if (name.includes('traffic') || name.includes('network') || name.includes('normalized')) {
            return 'traffic';
        }
        if (name.includes('app') && name.includes('list')) {
            return 'applications';
        }
        
        return 'traffic'; // Default to traffic
    }

    async processTrafficCSV(csvText, filename) {
        console.log(`Processing traffic CSV: ${filename}`);
        console.log(`Preserved applications: ${Array.from(this.preservedApplications)}`);
        
        // Store preserved apps before processing
        const preservedApps = this.applications.filter(app => 
            this.preservedApplications.has(app.name)
        );
        
        console.log(`Protecting ${preservedApps.length} preserved applications during upload`);
        
        // Parse new traffic data (this will add to existing this.trafficData)
        const newTrafficData = this.parseTrafficCSV(csvText);
        
        // Append new traffic data to existing data
        this.trafficData = [...this.trafficData, ...newTrafficData];
        
        // Ensure preserved apps remain in the applications array
        const nonPreservedApps = this.applications.filter(app => 
            !this.preservedApplications.has(app.name)
        );
        
        // Start with preserved apps, then add/update with traffic enrichment
        this.applications = [...preservedApps];
        
        // Add/update applications with ALL traffic data (old + new)
        this.enrichApplicationsWithTraffic();
        
        // Mark new applications from traffic data
        this.applications.forEach(app => {
            if (!this.applicationSources.has(app.name)) {
                this.applicationSources.set(app.name, 'traffic_data');
            }
        });
        
        // Regenerate network topology with all applications
        this.generateNetworkTopology();
        
        this.lastUpdate = new Date();
        this.isDataLoaded = true;
        
        console.log(`Successfully processed ${newTrafficData.length} new traffic records from ${filename}`);
        console.log(`Total traffic records now: ${this.trafficData.length}`);
        console.log(`Total applications now: ${this.applications.length}`);
        console.log(`Preserved: ${preservedApps.length}, From traffic: ${this.applications.length - preservedApps.length}`);
        
        // Trigger UI refresh
        if (window.topologyDashboard) {
            window.topologyDashboard.updateNetworkData();
            window.topologyDashboard.render();
            window.topologyDashboard.updateStats();
        }
        
        return {
            success: true,
            recordCount: newTrafficData.length,
            totalRecords: this.trafficData.length,
            totalApplications: this.applications.length,
            preservedApps: preservedApps.length,
            filename: filename,
            type: 'traffic',
            message: `Added ${newTrafficData.length} records from ${filename}. Total: ${this.trafficData.length} records, ${this.applications.length} applications (${preservedApps.length} preserved)`
        };
    }
    
    async processApplicationsCSV(csvText, filename) {
        console.log(`Processing applications CSV: ${filename}`);
        
        // Parse and replace applications
        this.applications = this.parseApplicationsCSV(csvText);
        this.lastUpdate = new Date();
        
        console.log(`Successfully processed ${this.applications.length} applications from ${filename}`);
        
        // Regenerate topology and refresh UI
        this.generateNetworkTopology();
        if (window.topologyDashboard) {
            window.topologyDashboard.populateApplicationFilter();
            window.topologyDashboard.updateNetworkData();
            window.topologyDashboard.render();
            window.topologyDashboard.updateStats();
        }
        
        return {
            success: true,
            recordCount: this.applications.length,
            filename: filename,
            type: 'applications',
            message: `Loaded ${this.applications.length} applications from ${filename}`
        };
    }

    // Debug utilities
    getApplicationHistory() {
        return this.applicationHistory || [];
    }

    findMissingApplications(expectedApps) {
        const currentAppNames = this.applications.map(app => app.name.toLowerCase());
        const missing = expectedApps.filter(appName => 
            !currentAppNames.includes(appName.toLowerCase())
        );
        
        console.log('Expected apps:', expectedApps);
        console.log('Current apps:', currentAppNames);
        console.log('Missing apps:', missing);
        
        return missing;
    }
    
    getPreservationStatus() {
        return {
            preservedApps: Array.from(this.preservedApplications),
            applicationSources: Object.fromEntries(this.applicationSources),
            totalApps: this.applications.length,
            preservedCount: this.preservedApplications.size
        };
    }

    debugPreservation() {
        console.log('=== PRESERVATION DEBUG ===');
        console.log('Preserved applications:', Array.from(this.preservedApplications));
        console.log('Application sources:');
        this.applicationSources.forEach((source, appName) => {
            console.log(`  ${appName}: ${source}`);
        });
        console.log('Current applications:');
        this.applications.forEach(app => {
            const isPreserved = this.preservedApplications.has(app.name);
            const source = this.applicationSources.get(app.name) || 'unknown';
            console.log(`  ${app.name}: ${source} ${isPreserved ? '(PRESERVED)' : ''}`);
        });
    }

    debugApplicationFlow() {
        console.log('=== APPLICATION DEBUG INFO ===');
        console.log('Current applications:', this.applications.length);
        this.applications.forEach((app, index) => {
            console.log(`  ${index + 1}. ${app.name} (${app.id}) - Traffic: ${app.trafficRecords || 0} - Source: ${app.source || 'unknown'}`);
        });
        
        console.log('Traffic data records:', this.trafficData.length);
        console.log('Deduplication registry size:', this.recordRegistry.size);
        
        if (this.applicationHistory) {
            console.log('Recent application history:');
            this.applicationHistory.slice(-5).forEach(entry => {
                console.log(`  ${entry.timestamp}: ${entry.operation} - ${entry.applicationCount} apps`);
            });
        }
        
        return {
            applications: this.applications.length,
            trafficRecords: this.trafficData.length,
            registrySize: this.recordRegistry.size,
            history: this.applicationHistory?.length || 0
        };
    }

    // EMERGENCY RECOVERY METHODS
    diagnoseDataloss(targetAppName = 'XECHG') {
        console.log(`=== DIAGNOSING ${targetAppName} LOSS ===`);
        
        const results = {
            targetApp: targetAppName,
            currentlyExists: false,
            inApplicationsArray: false,
            inTrafficData: false,
            inPreservedList: false,
            preservationEnabled: true,
            recommendations: []
        };
        
        // Check current applications array
        const foundInApps = this.applications.find(app => 
            app.name === targetAppName || app.id === targetAppName
        );
        
        if (foundInApps) {
            results.currentlyExists = true;
            results.inApplicationsArray = true;
            console.log(`✓ ${targetAppName} found in applications array:`, foundInApps);
        } else {
            console.log(`✗ ${targetAppName} NOT found in applications array`);
            console.log('Current applications:', this.applications.map(app => app.name));
        }
        
        // Check traffic data
        const trafficMatches = this.trafficData.filter(record => 
            record.application === targetAppName
        );
        
        if (trafficMatches.length > 0) {
            results.inTrafficData = true;
            console.log(`✓ ${targetAppName} found in ${trafficMatches.length} traffic records`);
        } else {
            console.log(`✗ ${targetAppName} NOT found in traffic data`);
            console.log('Applications in traffic data:', 
                [...new Set(this.trafficData.map(r => r.application))].slice(0, 10));
        }
        
        // Check preservation system
        results.inPreservedList = this.preservedApplications.has(targetAppName);
        
        if (results.inPreservedList) {
            console.log(`✓ ${targetAppName} is in preserved applications list`);
        } else {
            console.log(`✗ ${targetAppName} NOT in preserved applications list`);
            console.log('Preserved apps:', Array.from(this.preservedApplications));
        }
        
        // Generate recommendations
        if (!results.currentlyExists && results.inTrafficData) {
            results.recommendations.push('App exists in traffic but missing from applications - run enrichApplicationsWithTraffic()');
        }
        
        if (!results.inPreservedList && results.currentlyExists) {
            results.recommendations.push('Add app to preservation list to protect in future uploads');
        }
        
        console.log('\n=== RECOMMENDATIONS ===');
        results.recommendations.forEach((rec, i) => {
            console.log(`${i + 1}. ${rec}`);
        });
        
        return results;
    }

    emergencyRecoverApp(appName, fallbackData = null) {
        console.log(`=== EMERGENCY RECOVERY FOR ${appName} ===`);
        
        // Try to find app in various sources
        let recoveredApp = null;
        
        // 1. Check if it exists but just not showing
        recoveredApp = this.applications.find(app => 
            app.name.toLowerCase() === appName.toLowerCase() || 
            app.id.toLowerCase() === appName.toLowerCase()
        );
        
        if (recoveredApp) {
            console.log('✓ App found in applications array with different case:', recoveredApp);
            return recoveredApp;
        }
        
        // 2. Try to reconstruct from traffic data
        const trafficRecords = this.trafficData.filter(record => 
            record.application && record.application.toLowerCase() === appName.toLowerCase()
        );
        
        if (trafficRecords.length > 0) {
            console.log(`✓ Found ${trafficRecords.length} traffic records for ${appName}`);
            
            recoveredApp = {
                id: appName.toUpperCase(),
                name: appName,
                displayName: `${appName} [${appName.toUpperCase()}]`,
                archetype: this.classifyArchetype(appName),
                businessFunction: this.inferBusinessFunction(appName),
                criticality: this.inferCriticality(appName),
                technology: this.inferTechnology(this.classifyArchetype(appName)),
                status: 'active',
                searchText: appName.toLowerCase(),
                trafficRecords: trafficRecords.length,
                source: 'emergency_recovery',
                recoveredAt: new Date().toISOString()
            };
            
            this.applications.push(recoveredApp);
            
            // Add to preservation list
            if (this.preservedApplications) {
                this.preservedApplications.add(appName);
                console.log(`✓ Added ${appName} to preservation list`);
            }
            
            console.log('✓ App recovered from traffic data:', recoveredApp);
            return recoveredApp;
        }
        
        // 3. Use fallback data if provided
        if (fallbackData) {
            recoveredApp = {
                ...fallbackData,
                source: 'emergency_recovery_fallback',
                recoveredAt: new Date().toISOString()
            };
            
            this.applications.push(recoveredApp);
            
            if (this.preservedApplications) {
                this.preservedApplications.add(recoveredApp.name);
            }
            
            console.log('✓ App recovered from fallback data:', recoveredApp);
            return recoveredApp;
        }
        
        // 4. Create minimal app entry
        recoveredApp = {
            id: appName.toUpperCase(),
            name: appName,
            displayName: `${appName} [${appName.toUpperCase()}] (Recovered)`,
            archetype: '3-Tier',
            businessFunction: 'Operations',
            criticality: 'medium',
            technology: 'Enterprise Platform',
            status: 'active',
            searchText: appName.toLowerCase(),
            source: 'emergency_recovery_minimal',
            recoveredAt: new Date().toISOString()
        };
        
        this.applications.push(recoveredApp);
        
        if (this.preservedApplications) {
            this.preservedApplications.add(appName);
        }
        
        console.log('✓ Created minimal app entry:', recoveredApp);
        return recoveredApp;
    }
    
	getRepresentativeIPForApp(app) {
		// Get traffic records for this specific application
		const appTraffic = this.trafficData.filter(record => 
			record.application === app.name || record.application === app.id
		);
		
		if (appTraffic.length === 0) {
			// No traffic data for this app, return null
			return null;
		}
		
		// Collect all unique source IPs for this application
		const sourceIPs = appTraffic
			.map(record => record.source_ip)
			.filter(ip => ip && ip.trim() !== '');
		
		if (sourceIPs.length === 0) {
			// Try destination IPs as fallback
			const destIPs = appTraffic
				.map(record => record.destination_ip)
				.filter(ip => ip && ip.trim() !== '');
			
			return destIPs.length > 0 ? destIPs[0] : null;
		}
		
		// Return the most frequently used source IP for this app
		const ipCounts = {};
		sourceIPs.forEach(ip => {
			ipCounts[ip] = (ipCounts[ip] || 0) + 1;
		});
		
		// Find IP with highest count
		const mostCommonIP = Object.entries(ipCounts)
			.sort(([,a], [,b]) => b - a)[0]?.[0];
		
		return mostCommonIP || null;
	}
	
    generateNetworkTopology(selectedAppIds = ['all'], options = {}) {
        const {
            includeUpstream = true,
            includeDownstream = true,
            maxNodesPerApp = 3
        } = options;
        
        console.log('Generating network topology for:', selectedAppIds);
        
        // Determine which applications to include
        const selectedApps = selectedAppIds.includes('all') 
			? this.applications.filter(app => app.trafficRecords > 0) // Only apps with real traffic
			: this.applications.filter(app => selectedAppIds.includes(app.id));
        
        const nodes = [];
        const links = [];
        const nodeMap = new Map();
        
        // Generate nodes for each application
        selectedApps.forEach((app, appIndex) => {
            const tiers = this.getTiersForArchetype(app.archetype, maxNodesPerApp);
            
            tiers.forEach((tier, tierIndex) => {
                const nodeId = `${app.id}_${tier.type}`;
                
                const node = {
                    id: nodeId,
                    name: `${app.name} ${tier.displayName}`,
                  //ip: `10.${Math.floor(appIndex / 254) + 1}.${(appIndex % 254) + 1}.${tierIndex + 10}`,
				    ip: this.getRepresentativeIPForApp(app),
                    application: app.name,
                    applicationId: app.id,
                    archetype: app.archetype,
                    tier: tier.type,
                    type: tier.type,
                    status: app.status,
                    criticality: app.criticality,
                    businessFunction: app.businessFunction,
                    technology: app.technology,
                    
                    // Network properties
                    ports: tier.ports || app.ports || [],
                    protocols: tier.protocols || app.protocols || [],
                    
                    // Performance metrics (synthetic)
                    cpu: Math.floor(Math.random() * 80) + 10,
                    memory: Math.floor(Math.random() * 90) + 10,
                    connections: app.connectionCount || Math.floor(Math.random() * 50) + 5,
                    responseTime: app.responseTime || Math.floor(Math.random() * 100) + 10,
                    trafficVolume: app.trafficVolume || Math.floor(Math.random() * 1000) + 50,
                    
                    // Enrichment from traffic data
                    trafficRecords: app.trafficRecords || 0,
                    uniqueIPs: app.uniqueIPs || 0,
                    observedProtocols: app.observedProtocols || [],
                    observedPorts: app.observedPorts || []
                };
                
                nodes.push(node);
                nodeMap.set(nodeId, node);
            });
            
            // Create internal links between tiers of the same application
            for (let i = 0; i < tiers.length - 1; i++) {
                const sourceId = `${app.id}_${tiers[i].type}`;
                const targetId = `${app.id}_${tiers[i + 1].type}`;
                
                links.push(this.createLink(sourceId, targetId, {
                    protocol: tiers[i].connectionProtocol || 'HTTP',
                    port: tiers[i].connectionPort || '8080',
                    type: 'internal',
                    application: app.name,
                    bandwidth: Math.floor(Math.random() * 1000) + 100,
                    latency: Math.floor(Math.random() * 20) + 1
                }));
            }
        });
        
        // Create inter-application links
        if (selectedApps.length > 1 && (includeUpstream || includeDownstream)) {
            this.generateInterApplicationLinks(selectedApps, links, { includeUpstream, includeDownstream });
        }
        
        this.networkTopology = { nodes, links };
        
        console.log(`Generated topology: ${nodes.length} nodes, ${links.length} links`);
        return this.networkTopology;
    }
    
    generateInterApplicationLinks(applications, links, options) {
        const { includeUpstream, includeDownstream } = options;
        
        for (let i = 0; i < applications.length - 1; i++) {
            const sourceApp = applications[i];
            const targetApp = applications[i + 1];
            
            if (includeDownstream) {
                // App tier to web tier connection
                const sourceNodeId = `${sourceApp.id}_app`;
                const targetNodeId = `${targetApp.id}_web`;
                
                if (this.nodeExists(sourceNodeId) && this.nodeExists(targetNodeId)) {
                    links.push(this.createLink(sourceNodeId, targetNodeId, {
                        protocol: 'HTTP',
                        port: '80',
                        type: 'downstream',
                        bandwidth: Math.floor(Math.random() * 500) + 50,
                        latency: Math.floor(Math.random() * 30) + 5,
                        color: '#10b981'
                    }));
                }
            }
            
            if (includeUpstream) {
                // Database to database connection
                const sourceNodeId = `${targetApp.id}_data`;
                const targetNodeId = `${sourceApp.id}_data`;
                
                if (this.nodeExists(sourceNodeId) && this.nodeExists(targetNodeId)) {
                    links.push(this.createLink(sourceNodeId, targetNodeId, {
                        protocol: 'SQL',
                        port: '3306',
                        type: 'upstream',
                        bandwidth: Math.floor(Math.random() * 300) + 25,
                        latency: Math.floor(Math.random() * 40) + 10,
                        color: '#f59e0b'
                    }));
                }
            }
        }
    }
    
    nodeExists(nodeId) {
        return this.networkTopology.nodes.some(node => node.id === nodeId);
    }
    
    createLink(sourceId, targetId, properties = {}) {
        return {
            id: `${sourceId}|${targetId}`,
            source: sourceId,
            target: targetId,
            protocol: properties.protocol || 'TCP',
            port: properties.port || '8080',
            type: properties.type || 'connection',
            status: properties.status || 'active',
            bandwidth: properties.bandwidth || 100,
            latency: properties.latency || 10,
            color: properties.color || this.getProtocolColor(properties.protocol),
            width: properties.width || 2,
            ...properties
        };
    }
    
    // Helper methods for classification and inference
    classifyArchetype(appName) {
        const name = appName.toLowerCase();
        
        for (const [archetype, keywords] of Object.entries(this.config.archetypeClassification)) {
            if (keywords.some(keyword => name.includes(keyword))) {
                return archetype;
            }
        }
        
        return '3-Tier'; // Default
    }
    
    inferBusinessFunction(appName) {
        const name = appName.toLowerCase();
        const functions = {
            'Core Banking': ['banking', 'core', 'account', 'deposit'],
            'Customer Services': ['customer', 'portal', 'service', 'support'],
            'Payment Processing': ['payment', 'gateway', 'transaction', 'settle'],
            'Risk & Compliance': ['risk', 'compliance', 'audit', 'regulatory'],
            'Reporting & Analytics': ['report', 'analytics', 'dashboard', 'insight'],
            'Security & Identity': ['security', 'auth', 'identity', 'access'],
            'Trading & Markets': ['trade', 'trading', 'market', 'exchange'],
            'Lending': ['loan', 'credit', 'lending', 'mortgage'],
            'Operations': ['ops', 'operations', 'admin', 'management']
        };
        
        for (const [func, keywords] of Object.entries(functions)) {
            if (keywords.some(keyword => name.includes(keyword))) {
                return func;
            }
        }
        
        return 'Operations';
    }
    
    inferCriticality(appName) {
        const name = appName.toLowerCase();
        if (name.includes('core') || name.includes('critical') || name.includes('primary')) {
            return 'critical';
        }
        if (name.includes('customer') || name.includes('payment') || name.includes('security')) {
            return 'high';
        }
        if (name.includes('report') || name.includes('analytics') || name.includes('support')) {
            return 'medium';
        }
        return 'low';
    }
    
    inferTechnology(archetype) {
        const techMap = {
            'Microservices': 'Container Platform',
            'Web + API Headless': 'Web Platform',
            'Database-Centric': 'Database Platform',
            'Event-Driven': 'Messaging Platform',
            'Monolithic': 'Enterprise Platform',
            'SOA': 'Service Platform',
            'Client-Server': 'Desktop Platform',
            '3-Tier': 'Web Application Platform'
        };
        return techMap[archetype] || 'Enterprise Platform';
    }
    
    generatePortsForArchetype(archetype) {
        const portMap = {
            'Microservices': ['8080', '8443', '3000', '9000'],
            'Web + API Headless': ['80', '443', '8080', '3000'],
            'Database-Centric': ['3306', '5432', '1433', '1521'],
            'Event-Driven': ['5672', '9092', '61616', '1883'],
            'Monolithic': ['8080', '1433', '80'],
            'SOA': ['8080', '8443', '7001', '9080'],
            'Client-Server': ['1433', '3389', '1521'],
            '3-Tier': ['80', '443', '8080', '3306']
        };
        return portMap[archetype] || ['8080'];
    }
    
    generateProtocolsForArchetype(archetype) {
        const protocolMap = {
            'Microservices': ['HTTP', 'HTTPS', 'gRPC'],
            'Web + API Headless': ['HTTP', 'HTTPS', 'WebSocket'],
            'Database-Centric': ['SQL', 'TCP', 'HTTP'],
            'Event-Driven': ['AMQP', 'MQTT', 'HTTP'],
            'Monolithic': ['HTTP', 'SQL', 'TCP'],
            'SOA': ['SOAP', 'HTTP', 'JMS'],
            'Client-Server': ['TCP', 'SQL', 'RDP'],
            '3-Tier': ['HTTP', 'HTTPS', 'SQL']
        };
        return protocolMap[archetype] || ['HTTP', 'TCP'];
    }
    
    getTiersForArchetype(archetype, maxTiers = 3) {
        const tierConfigs = {
            'Microservices': [
                { type: 'api', displayName: 'API Gateway', ports: ['8080', '8443'], connectionProtocol: 'HTTP', connectionPort: '8080' },
                { type: 'service', displayName: 'Service', ports: ['9000', '9001'], connectionProtocol: 'gRPC', connectionPort: '9000' },
                { type: 'data', displayName: 'Data Store', ports: ['3306', '6379'], connectionProtocol: 'SQL', connectionPort: '3306' }
            ],
            'Web + API Headless': [
                { type: 'web', displayName: 'Frontend', ports: ['80', '443'], connectionProtocol: 'HTTP', connectionPort: '80' },
                { type: 'api', displayName: 'API', ports: ['8080', '3000'], connectionProtocol: 'REST', connectionPort: '8080' },
                { type: 'data', displayName: 'Database', ports: ['3306'], connectionProtocol: 'SQL', connectionPort: '3306' }
            ],
            'Database-Centric': [
                { type: 'app', displayName: 'Application', ports: ['8080'], connectionProtocol: 'HTTP', connectionPort: '8080' },
                { type: 'data', displayName: 'Database', ports: ['3306', '5432'], connectionProtocol: 'SQL', connectionPort: '3306' }
            ],
            'Event-Driven': [
                { type: 'producer', displayName: 'Producer', ports: ['8080'], connectionProtocol: 'HTTP', connectionPort: '8080' },
                { type: 'broker', displayName: 'Message Broker', ports: ['5672', '9092'], connectionProtocol: 'AMQP', connectionPort: '5672' },
                { type: 'consumer', displayName: 'Consumer', ports: ['8081'], connectionProtocol: 'AMQP', connectionPort: '5672' }
            ],
            'Monolithic': [
                { type: 'app', displayName: 'Application', ports: ['8080'], connectionProtocol: 'HTTP', connectionPort: '8080' },
                { type: 'data', displayName: 'Database', ports: ['1433'], connectionProtocol: 'SQL', connectionPort: '1433' }
            ],
            'SOA': [
                { type: 'service', displayName: 'Service', ports: ['8080'], connectionProtocol: 'SOAP', connectionPort: '8080' },
                { type: 'esb', displayName: 'ESB', ports: ['7001'], connectionProtocol: 'JMS', connectionPort: '7001' },
                { type: 'data', displayName: 'Database', ports: ['1521'], connectionProtocol: 'SQL', connectionPort: '1521' }
            ]
        };
        
        const defaultTiers = [
            { type: 'web', displayName: 'Web Tier', ports: ['80', '443'], connectionProtocol: 'HTTP', connectionPort: '80' },
            { type: 'app', displayName: 'App Tier', ports: ['8080'], connectionProtocol: 'HTTP', connectionPort: '8080' },
            { type: 'data', displayName: 'Data Tier', ports: ['3306'], connectionProtocol: 'SQL', connectionPort: '3306' }
        ];
        
        const tiers = tierConfigs[archetype] || defaultTiers;
        return tiers.slice(0, maxTiers);
    }
    
    getProtocolColor(protocol) {
        const colorMap = {
            'HTTP': '#3b82f6',
            'HTTPS': '#10b981',
            'SQL': '#f59e0b',
            'TCP': '#8b5cf6',
            'gRPC': '#06b6d4',
            'AMQP': '#ef4444',
            'SOAP': '#84cc16'
        };
        return colorMap[protocol] || '#6b7280';
    }
    
    // CSV parsing utilities
    parseCSVLine(line) {
        const result = [];
        let current = '';
        let inQuotes = false;
        
        for (let i = 0; i < line.length; i++) {
            const char = line[i];
            
            if (char === '"') {
                if (inQuotes && line[i + 1] === '"') {
                    current += '"';
                    i++;
                } else {
                    inQuotes = !inQuotes;
                }
            } else if (char === ',' && !inQuotes) {
                result.push(current);
                current = '';
            } else {
                current += char;
            }
        }
        
        result.push(current);
        return result;
    }
    
    cleanCSVValue(value) {
        if (!value) return '';
        return value.trim().replace(/^"(.*)"$/, '$1');
    }
    
    convertValue(value) {
        if (!value || value === '') return null;
        
        // Try to convert to number
        const num = parseFloat(value);
        if (!isNaN(num) && isFinite(num) && value.toString() === num.toString()) {
            return num;
        }
        
        return value;
    }
}

// Initialize global AppData instance
console.log('Initializing global AppData with dynamic file discovery...');

try {
    window.AppData = new ApplicationDataManager();
    console.log('AppData initialized successfully with dynamic file discovery');
} catch (error) {
    console.error('Failed to initialize AppData:', error);
    
    // Create minimal fallback
    window.AppData = {
        isDataLoaded: false,
        applications: [],
        networkTopology: { nodes: [], links: [] },
        errors: [error.message],
        pipelineStatus: null,
        
        isReady: () => false,
        getStatus: () => ({ 
            isReady: false, 
            error: error.message,
            applicationCount: 0,
            trafficRecordCount: 0,
            fileDiscovery: { enabled: false, error: error.message }
        }),
        loadData: () => Promise.reject(error),
        getApplicationNamesForFilter: () => [
            { id: 'all', name: 'ALL Applications', displayName: 'ALL Applications (0 total)' }
        ],
        generateNetworkTopology: () => ({ nodes: [], links: [] }),
        getMetadata: () => ({ error: error.message, version: '2.1.0' }),
        refreshPipelineStatus: () => Promise.reject(error),
        getPipelineFiles: () => Promise.reject(error),
        getCurrentTrafficSource: () => ({ path: null, error: error.message })
    };
}

// Auto-load on DOM ready
document.addEventListener('DOMContentLoaded', async () => {
    if (window.AppData && !window.AppData.isDataLoaded && window.AppData.loadData) {
        console.log('Auto-loading data on DOM ready with dynamic discovery...');
        try {
            await window.AppData.loadData();
            console.log('Auto-load completed successfully');
            
            // Log pipeline status
            const status = window.AppData.getStatus();
            if (status.pipelineStatus) {
                console.log('Pipeline health:', status.pipelineStatus.status);
                console.log('Current traffic source:', status.currentTrafficCsv);
            }
        } catch (error) {
            console.error('Auto-load failed:', error);
        }
    }
});

// Enhanced debug utilities
window.AppDataUtils = {
    refresh: () => window.AppData.refreshData(),
    status: () => window.AppData.getStatus(),
    apps: () => window.AppData.applications,
    search: (query) => window.AppData.searchApplications(query),
    metadata: () => window.AppData.getMetadata(),
    topology: () => window.AppData.networkTopology,
    generateTopology: (apps, options) => window.AppData.generateNetworkTopology(apps, options),
    saveTopology: () => window.AppData.saveTopologyToFile(),
    errors: () => window.AppData.errors,
    
    // Pipeline utilities
    pipeline: {
        status: () => window.AppData.refreshPipelineStatus(),
        health: () => window.AppData.getPipelineHealth(),
        files: () => window.AppData.getPipelineFiles(),
        currentSource: () => window.AppData.getCurrentTrafficSource(),
        switchFile: (filename) => window.AppData.switchToSpecificFile(filename)
    },
    
    history: () => window.AppData.getApplicationHistory(),
    findMissing: (expectedApps) => window.AppData.findMissingApplications(expectedApps),
    debug: () => window.AppData.debugApplicationFlow(),
    
    // Deduplication utilities
    deduplication: {
        stats: () => window.AppData.duplicateStats,
        registrySize: () => window.AppData.recordRegistry.size,
        clearRegistry: () => {
            window.AppData.recordRegistry.clear();
            window.AppData.duplicateStats = { totalProcessed: 0, duplicatesIgnored: 0, recordsUpdated: 0 };
            console.log('Deduplication registry cleared');
        },
        inspectRecord: (sourceIp, destIp) => {
            const key = `${sourceIp}|${destIp}`;
            for (const [recordKey, entry] of window.AppData.recordRegistry.entries()) {
                if (recordKey.includes(key)) {
                    console.log('Found record:', recordKey, entry);
                    return entry;
                }
            }
            console.log('No record found for:', key);
            return null;
        }
    },
    
    // Preservation utilities
    preservation: {
        status: () => window.AppData.getPreservationStatus(),
        debug: () => window.AppData.debugPreservation(),
        preserved: () => Array.from(window.AppData.preservedApplications || []),
        sources: () => Object.fromEntries(window.AppData.applicationSources || new Map()),
        
        // Check if specific app is preserved
        isPreserved: (appName) => window.AppData.preservedApplications?.has(appName) || false,
        
        // Manually add app to preservation (if needed)
        preserve: (appName) => {
            if (window.AppData.preservedApplications) {
                window.AppData.preservedApplications.add(appName);
                console.log(`Added ${appName} to preservation list`);
            }
        },
        
        // Remove app from preservation
        unpreserve: (appName) => {
            if (window.AppData.preservedApplications) {
                window.AppData.preservedApplications.delete(appName);
                console.log(`Removed ${appName} from preservation list`);
            }
        }
    },
    
    // Topology utilities
    topologyOps: {
        save: () => window.AppData.saveTopologyToFile(),
        load: (filename) => window.AppData.loadSpecificTopology(filename),
        
        // Check what will be preserved before upload
        checkPreservation: () => {
            const preserved = Array.from(window.AppData.preservedApplications || []);
            const current = window.AppData.applications.map(app => app.name);
            console.log('Will be preserved on next upload:', preserved);
            console.log('Current applications:', current);
            console.log('Would be lost:', current.filter(name => !preserved.includes(name)));
            return { preserved, current, wouldBeLost: current.filter(name => !preserved.includes(name)) };
        }
    },

    // Emergency utilities
    emergency: {
        // Check current state before doing anything
        checkState: () => {
            console.log('=== CURRENT STATE ===');
            console.log('Applications:', window.AppData.applications.map(app => app.name));
            console.log('Traffic records:', window.AppData.trafficData.length);
            console.log('Preserved apps:', Array.from(window.AppData.preservedApplications || []));
            console.log('Has XECHG:', window.AppData.applications.some(app => app.name === 'XECHG'));
            
            return {
                apps: window.AppData.applications.map(app => app.name),
                trafficRecords: window.AppData.trafficData.length,
                preserved: Array.from(window.AppData.preservedApplications || []),
                hasXECHG: window.AppData.applications.some(app => app.name === 'XECHG')
            };
        },
        
        // Diagnose where XECHG went
        diagnose: (appName = 'XECHG') => window.AppData.diagnoseDataloss(appName),
        
        // Recover lost app
        recover: (appName = 'XECHG', fallbackData = null) => 
            window.AppData.emergencyRecoverApp(appName, fallbackData),
        
        // Quick recovery for XECHG specifically
        recoverXECHG: () => {
            const xechgFallback = {
                id: 'XECHG',
                name: 'XECHG',
                displayName: 'XECHG [XECHG]',
                archetype: 'Database-Centric',
                businessFunction: 'Core Banking',
                criticality: 'critical',
                technology: 'Database Platform',
                status: 'active',
                ports: ['3306', '1433'],
                protocols: ['SQL', 'HTTP'],
                searchText: 'xechg'
            };
            return window.AppData.emergencyRecoverApp('XECHG', xechgFallback);
        },
        
        // Force preservation of current apps
        preserveAll: () => {
            if (!window.AppData.preservedApplications) {
                window.AppData.preservedApplications = new Set();
            }
            
            window.AppData.applications.forEach(app => {
                window.AppData.preservedApplications.add(app.name);
            });
            
            console.log(`Preserved ${window.AppData.applications.length} applications:`, 
                Array.from(window.AppData.preservedApplications));
            
            return Array.from(window.AppData.preservedApplications);
        }
    }
};

console.log('Dynamic file discovery app-data.js loaded successfully');
console.log('Features: Dynamic CSV discovery, pipeline health monitoring, fallback handling, emergency recovery');
console.log('Debug: Use AppDataUtils.emergency.checkState() to check current state or AppDataUtils.status() for overall status');
console.log('Emergency: Use AppDataUtils.emergency.recoverXECHG() to recover XECHG if missing');
console.log('Pipeline: Use AppDataUtils.pipeline.files() to see available files or AppDataUtils.pipeline.health() for health');