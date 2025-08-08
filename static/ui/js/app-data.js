// Enhanced Application Data Management - Web Application Integration
// Integrates with ACTIVnet File Processing System using proper directory structure
// Loads data from /templates/activnet_data.json and /static/ui/data/synthetic_flows_apps_archetype_mapped.xlsx

// Check if ApplicationDataManager already exists to avoid redeclaration
if (typeof window.ApplicationDataManager === 'undefined') {
    
    class ApplicationDataManager {
        constructor() {
            this.applications = [];
            this.flows = [];
            this.applicationList = [];
            this.isDataLoaded = false;
            this.networkTopology = { nodes: [], links: [] };
            this.lastUpdate = null;
            this.activnetData = []; // Store raw ACTIVnet data
            this.portServiceMap = new Map(); // Cache for port service definitions
            this.currentDataSource = null; // Track which file we're using
			this.lastDataTimestamp = null;
			this.lastDataETag = null;
			this.lastCheckTime = null;
            
            // localStorage keys for caching
            this.STORAGE_KEYS = {
                APPLICATIONS: 'app_discovery_applications',
                NETWORK_DATA: 'app_discovery_network_data',
                ACTIVNET_DATA: 'app_discovery_activnet_data',
                PORT_SERVICES: 'app_discovery_port_services',
                LAST_UPDATE: 'app_discovery_last_update',
                DATA_SOURCE: 'app_discovery_data_source',
                VERSION: 'app_discovery_data_version'
            };
            
            // Data version for cache invalidation
            this.DATA_VERSION = '5.0.0-webapp';
            
            // Event listeners for data updates
            this.dataLoadedCallbacks = [];
            this.filterChangeCallbacks = [];
            
            // Dynamic color mapping based on real architectures
            this.nodeColorMap = {};
            
            // Web application file paths
            this.dataPaths = {
                jsonData: '/templates/activnet_data.json',
                masterExcel: '/static/ui/data/synthetic_flows_apps_archetype_mapped.xlsx',
                fallbackPaths: [
                    '/static/ui/data/activnet_data.json',
                    '/templates/data.json',
                    'activnet_data.json'
                ]
            };
            
            // Auto-refresh configuration
            this.autoRefreshInterval = 60000; // Check for updates every minute
            this.refreshTimer = null;
            
            // Initialize with enhanced loading
            this.init();
        }
        
        async init() {
            console.log('🚀 Initializing Web-Integrated ACTIVnet Application Data Manager...');
            console.log('📁 Data paths configured:');
            console.log(`   JSON: ${this.dataPaths.jsonData}`);
            console.log(`   Excel: ${this.dataPaths.masterExcel}`);
            
            // Check if we have valid cached data
            if (this.hasCachedData() && this.isCacheValid()) {
                console.log('📦 Loading data from localStorage cache...');
                this.loadFromCache();
                
                // Still check for newer data in background
                setTimeout(() => this.checkForNewerData(), 2000);
            } else {
                console.log('📁 Loading fresh data from web application...');
                await this.loadWebApplicationData();
            }
            
            this.setupFilterSync();
            this.startAutoRefresh();
            console.log('✅ Web-Integrated ACTIVnet Data Manager initialized');
        }
        
        // ===========================
        // WEB APPLICATION DATA LOADING
        // ===========================
        
        async loadWebApplicationData() {
            console.log('🔍 Loading data from web application structure...');
            
            let dataLoaded = false;
            
            // Try primary JSON data file first
            try {
                await this.loadFromJSONData(this.dataPaths.jsonData);
                dataLoaded = true;
                console.log('✅ Successfully loaded from primary JSON data');
            } catch (error) {
                console.log('⚠️ Primary JSON data loading failed:', error.message);
            }
            
            // Try fallback paths if primary failed
            if (!dataLoaded) {
                for (const fallbackPath of this.dataPaths.fallbackPaths) {
                    try {
                        await this.loadFromJSONData(fallbackPath);
                        dataLoaded = true;
                        console.log(`✅ Successfully loaded from fallback: ${fallbackPath}`);
                        break;
                    } catch (error) {
                        console.log(`⚠️ Fallback ${fallbackPath} failed:`, error.message);
                    }
                }
            }
            
            // If still no data, try to load Excel file directly
            if (!dataLoaded) {
                try {
                    await this.loadFromMasterExcel();
                    dataLoaded = true;
                    console.log('✅ Successfully loaded from Excel file');
                } catch (error) {
                    console.log('⚠️ Excel loading failed:', error.message);
                }
            }
            
            // Final fallback to sample data
            if (!dataLoaded) {
                console.warn('❌ Could not load any data files. Using sample data.');
                console.warn('📋 Expected data files:');
                console.warn(`   • ${this.dataPaths.jsonData}`);
                console.warn(`   • ${this.dataPaths.masterExcel}`);
                await this.createSampleData();
                this.showDataSourceNotification('sample');
            } else {
                this.showDataSourceNotification('webapp', this.currentDataSource);
            }
            
            // Process the loaded data
            this.processLoadedData();
            this.generateNetworkTopology();
            this.saveToCache();
            this.isDataLoaded = true;
            this.lastUpdate = new Date();
            this.notifyDataLoaded();
        }
        
        async loadFromJSONData(jsonPath) {
            /**
             * Load data from JSON file (primary method)
             */
            console.log(`📖 Loading data from: ${jsonPath}`);
            
            const response = await fetch(jsonPath);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const jsonData = await response.json();
            
            // Process JSON data structure
            if (jsonData.applications) {
                this.applications = jsonData.applications.map(app => this.enhanceApplicationData(app));
                console.log(`📊 Loaded ${this.applications.length} applications from JSON`);
            }
            
            if (jsonData.raw_data_sample) {
                this.activnetData = jsonData.raw_data_sample;
                console.log(`📈 Loaded ${this.activnetData.length} raw data samples`);
            }
            
            if (jsonData.port_services) {
                this.portServiceMap = new Map(Object.entries(jsonData.port_services));
                console.log(`🔌 Loaded ${this.portServiceMap.size} port service mappings`);
            }
            
            // Store metadata
            this.metadata = jsonData.metadata || {};
            this.summaryStats = jsonData.summary_stats || {};
            this.currentDataSource = jsonPath;
            
            console.log(`✅ JSON data loaded successfully from ${jsonPath}`);
        }
        
        async loadFromMasterExcel() {
            /**
             * Load data from master Excel file (fallback method)
             */
            console.log(`📊 Attempting to load Excel data from: ${this.dataPaths.masterExcel}`);
            
            // Note: This requires additional JavaScript libraries for Excel parsing
            // For now, we'll create a placeholder that could be enhanced
            try {
                const response = await fetch(this.dataPaths.masterExcel);
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                // Check if we have XLSX library available
                if (typeof XLSX !== 'undefined') {
                    const arrayBuffer = await response.arrayBuffer();
                    const workbook = XLSX.read(arrayBuffer);
                    
                    // Get the main data sheet
                    const sheetName = workbook.SheetNames.find(name => 
                        name.includes('synthetic_flows') || name.includes('flows')
                    ) || workbook.SheetNames[0];
                    
                    const worksheet = workbook.Sheets[sheetName];
                    const jsonData = XLSX.utils.sheet_to_json(worksheet);
                    
                    this.activnetData = jsonData;
                    this.processExcelDataIntoApplications();
                    this.currentDataSource = this.dataPaths.masterExcel;
                    
                    console.log(`✅ Loaded ${jsonData.length} records from Excel`);
                } else {
                    throw new Error('XLSX library not available for Excel parsing');
                }
                
            } catch (error) {
                console.error('Excel loading failed:', error);
                throw error;
            }
        }
        
        processExcelDataIntoApplications() {
            /**
             * Process Excel data into application summaries
             */
            if (!this.activnetData || this.activnetData.length === 0) {
                return;
            }
            
            // Group by application
            const appMap = new Map();
            
            this.activnetData.forEach(record => {
                const appId = record.application || record.application_original || 'NETWORK_DATA';
                
                if (!appMap.has(appId)) {
                    appMap.set(appId, {
                        id: appId,
                        name: this.getFullApplicationName(appId),
                        records: [],
                        protocols: new Set(),
                        services: new Set(),
                        bytesIn: 0,
                        bytesOut: 0,
                        sources: new Set(),
                        destinations: new Set()
                    });
                }
                
                const app = appMap.get(appId);
                app.records.push(record);
                if (record.protocol) app.protocols.add(record.protocol);
                if (record.service_definition) app.services.add(record.service_definition);
                if (record.src) app.sources.add(record.src);
                if (record.dst) app.destinations.add(record.dst);
                app.bytesIn += parseFloat(record.bytes_in || 0);
                app.bytesOut += parseFloat(record.bytes_out || 0);
            });
            
            // Convert to application array
            this.applications = Array.from(appMap.values()).map(app => ({
                id: app.id,
                name: app.name,
                total_records: app.records.length,
                unique_sources: app.sources.size,
                unique_destinations: app.destinations.size,
                total_bytes: app.bytesIn + app.bytesOut,
                most_common_protocol: Array.from(app.protocols)[0] || 'TCP',
                most_common_service: Array.from(app.services)[0] || 'Network Service',
                complexity: this.determineComplexity(app.records.length, app.services.size, app.sources.size + app.destinations.size),
                protocols: Array.from(app.protocols),
                archetype: 'Network Service'
            })).map(app => this.enhanceApplicationData(app));
            
            // Sort by activity
            this.applications.sort((a, b) => b.total_records - a.total_records);
            
            console.log(`📊 Processed ${this.applications.length} applications from Excel data`);
        }
        
        enhanceApplicationData(app) {
            /**
             * Enhance application data with additional computed fields
             */
            return {
                ...app,
                app_id: app.id, // Backward compatibility
                app_name: app.name, // Backward compatibility
                displayName: `${app.name} (${app.id})`,
                searchText: `${app.name} ${app.id} ${app.most_common_protocol || ''} ${app.most_common_service || ''}`.toLowerCase(),
                isActive: true,
                priority: this.calculatePriority(app),
                color: this.getColorForArchetype(app.archetype || 'Network Service'),
                nodeCount: this.calculateNodesFromComplexity(app.complexity || 'medium', app.id),
                
                // Enhanced metrics from web application data
                webAppMetrics: {
                    dataSource: this.currentDataSource,
                    loadTime: new Date().toISOString(),
                    isRealData: true,
                    fromMasterFile: this.currentDataSource === this.dataPaths.masterExcel
                }
            };
        }
        
		async checkForNewerData() {
			console.log('🔍 Checking for newer web application data...');
			
			// Get the primary data source path
			const primaryDataPath = this.dataPaths?.jsonData || '/templates/activnet_data.json';
			
			try {
				
				// Skip HEAD request entirely, go straight to GET
				console.log('⚠️ Skipping HEAD request (server does not support HEAD method)');
				let response = await this.tryGetRequest(primaryDataPath);
				
				// If HEAD fails with 501, fall back to GET request
				if (!response || response.status === 501) {
					console.warn('❌ Failed to check for newer data:', response?.status, response?.statusText);
					return this.checkForNewerDataSimple(); // Fall back to time-based
				}
				
				// Check headers for updates
				const lastModified = response.headers.get('last-modified');
				const etag = response.headers.get('etag');
				
				console.log('📊 Server response headers:');
				console.log('  Last-Modified:', lastModified);
				console.log('  ETag:', etag);
				console.log('  Current data timestamp:', this.lastDataTimestamp);

				// Check if data has been modified
				if (lastModified) {
					const serverTime = new Date(lastModified).getTime();
					if (this.lastDataTimestamp && serverTime <= this.lastDataTimestamp) {
						console.log('✅ Data is up to date (Last-Modified check)');
						return false;
					}
					console.log('🔄 Newer data available (Last-Modified check)');
					
					// If newer data found, reload it
					await this.loadWebApplicationData();
					return true;
				}
				
				if (etag && this.lastDataETag) {
					if (etag === this.lastDataETag) {
						console.log('✅ Data is up to date (ETag check)');
						return false;
					}
					console.log('🔄 Newer data available (ETag check)');
					
					// If newer data found, reload it
					await this.loadWebApplicationData();
					return true;
				}

				// If no caching headers available, use simple time-based check
				return this.checkForNewerDataSimple();

			} catch (error) {
				console.error('❌ Error checking for newer data:', error);
				
				// Fall back to simple time-based check
				return this.checkForNewerDataSimple();
			}
		}

		// Helper method to try HEAD request
		async tryHeadRequest(dataPath) {
			try {
				console.log('🔍 Trying HEAD request to:', dataPath);
				
				const response = await fetch(dataPath, {
					method: 'HEAD',
					headers: {
						'Cache-Control': 'no-cache',
						'Accept': 'application/json'
					},
					// Add timeout to prevent hanging
					signal: AbortSignal.timeout(10000) // 10 seconds timeout
				});
				
				console.log(`📊 HEAD response: ${response.status} ${response.statusText}`);
				return response;
				
			} catch (error) {
				console.log('⚠️ HEAD request failed:', error.message);
				return null;
			}
		}

		// Helper method to try GET request (as fallback)
		async tryGetRequest(dataPath) {
			try {
				console.log('🔍 Trying GET request to:', dataPath);
				
				const response = await fetch(dataPath, {
					method: 'GET',
					headers: {
						'Cache-Control': 'no-cache',
						'Accept': 'application/json',
						// Only get headers, not full content (Range request)
						'Range': 'bytes=0-0'
					},
					// Add timeout to prevent hanging
					signal: AbortSignal.timeout(10000) // 10 seconds timeout
				});
				
				console.log(`📊 GET response: ${response.status} ${response.statusText}`);
				
				// If Range request is not supported, we'll get 200 instead of 206
				// This is fine for checking headers
				if (response.status === 200 || response.status === 206) {
					return response;
				}
				
				return response;
				
			} catch (error) {
				console.log('⚠️ GET request failed:', error.message);
				return null;
			}
		}

		// Simple time-based check (no HEAD requests needed)
		checkForNewerDataSimple() {
			console.log('🔄 Using simple data check (no HEAD requests)...');
			
			// Simple time-based check - reload data every X minutes
			const CHECK_INTERVAL = 5 * 60 * 1000; // 5 minutes
			const now = Date.now();
			
			if (!this.lastCheckTime || (now - this.lastCheckTime) > CHECK_INTERVAL) {
				console.log('⏰ Time-based data refresh needed');
				this.lastCheckTime = now;
				
				// Reload data in background
				setTimeout(() => {
					this.loadWebApplicationData().then(() => {
						console.log('✅ Background data refresh completed');
					});
				}, 1000);
				
				return true;
			}
			
			console.log('✅ Data is still fresh (time-based check)');
			return false;
		}

		// ALSO UPDATE your loadFromJSONData method to store caching info:
		async loadFromJSONData(jsonPath) {
			console.log(`📖 Loading data from: ${jsonPath}`);
			
			const response = await fetch(jsonPath);
			if (!response.ok) {
				throw new Error(`HTTP ${response.status}: ${response.statusText}`);
			}
			
			// STORE CACHING INFORMATION
			const lastModified = response.headers.get('last-modified');
			const etag = response.headers.get('etag');
			
			if (lastModified) {
				this.lastDataTimestamp = new Date(lastModified).getTime();
				console.log('📅 Stored Last-Modified timestamp:', this.lastDataTimestamp);
			}
			
			if (etag) {
				this.lastDataETag = etag;
				console.log('🏷️ Stored ETag:', this.lastDataETag);
			}
			
			// Update timestamp for fallback
			this.lastDataTimestamp = this.lastDataTimestamp || Date.now();
			
			const jsonData = await response.json();
			
			// ... rest of your existing loadFromJSONData code
			
			console.log(`✅ JSON data loaded successfully from ${jsonPath}`);
		}

		// Debug function to test server capabilities
		async debugServerCapabilities() {
			console.log('🔍 === Web App Server Capability Test ===');
			
			const testPaths = [
				this.dataPaths?.jsonData || '/templates/activnet_data.json',
				this.dataPaths?.masterExcel || '/static/ui/data/synthetic_flows_apps_archetype_mapped.xlsx'
			];
			
			for (const path of testPaths) {
				console.log(`\n🧪 Testing path: ${path}`);
				
				const methods = ['HEAD', 'GET', 'OPTIONS'];
				
				for (const method of methods) {
					try {
						const response = await fetch(path, {
							method: method,
							signal: AbortSignal.timeout(5000)
						});
						
						console.log(`✅ ${method}: ${response.status} ${response.statusText}`);
						
						// Log relevant headers
						const headers = ['last-modified', 'etag', 'cache-control', 'content-type'];
						headers.forEach(header => {
							const value = response.headers.get(header);
							if (value) {
								console.log(`  ${header}: ${value}`);
							}
						});
						
					} catch (error) {
						console.log(`❌ ${method}: ${error.message}`);
					}
				}
			}
			
			console.log('\n=== End Server Test ===');
		}

		// Console debugging commands:
		// window.AppData.debugServerCapabilities() - Test your web app server
		// window.AppData.checkForNewerData() - Test the data checking

		// Usage instructions:
		// 1. Replace your existing checkForNewerData method with the fixed version above
		// 2. Add the helper methods (tryHeadRequest, tryGetRequest) to your class
		// 3. Optionally, use debugServerCapabilities() to test your server
		// 4. If you want to avoid HEAD requests entirely, use checkForNewerDataSimple() instead

		// Console commands for debugging:
		// window.AppData.debugServerCapabilities() - Test server methods
		// window.AppData.checkForNewerData() - Test the fixed data checking
        startAutoRefresh() {
            /**
             * Start automatic refresh timer to check for new data
             */
            if (this.refreshTimer) {
                clearInterval(this.refreshTimer);
            }
            
            this.refreshTimer = setInterval(() => {
                this.checkForNewerData();
            }, this.autoRefreshInterval);
            
            console.log(`🔄 Auto-refresh enabled (${this.autoRefreshInterval / 1000}s interval)`);
        }
        
        stopAutoRefresh() {
            /**
             * Stop automatic refresh timer
             */
            if (this.refreshTimer) {
                clearInterval(this.refreshTimer);
                this.refreshTimer = null;
                console.log('⏹️ Auto-refresh stopped');
            }
        }
        
        // ===========================
        // FALLBACK AND UTILITY METHODS
        // ===========================
        
        async createSampleData() {
            /**
             * Create minimal sample data when no real data is available
             */
            this.applications = [
                {
                    id: 'WEBAPP_DEMO',
                    name: 'Web Application Demo Service',
                    total_records: 0,
                    complexity: 'low',
                    archetype: 'Demo Service',
                    most_common_protocol: 'TCP',
                    most_common_service: 'Demo Service - Drop files in data_staging/ to load real data'
                }
            ].map(app => this.enhanceApplicationData(app));
            
            this.applicationList = this.applications;
            this.activnetData = [];
            this.isDataLoaded = true;
            this.lastUpdate = new Date();
            this.notifyDataLoaded();
        }
        
        processLoadedData() {
            /**
             * Process and enhance loaded data
             */
            // Set backward compatibility
            this.applicationList = this.applications;
            
            // Sort by priority and name
            this.applications.sort((a, b) => {
                if (a.priority !== b.priority) {
                    return b.priority - a.priority;
                }
                return a.name.localeCompare(b.name);
            });
        }
        
        showDataSourceNotification(source, path = null) {
            /**
             * Show notification about data source
             */
            const notifications = {
                'webapp': {
                    title: '✅ Web Application Data Loaded',
                    message: `Loaded real data from web application: ${path}`,
                    type: 'success'
                },
                'sample': {
                    title: '⚠️ Demo Mode Active',
                    message: 'No data files found. Process files through data_staging/ to load real data.',
                    type: 'warning'
                }
            };
            
            const notif = notifications[source];
            console.log(`${notif.title}: ${notif.message}`);
            
            // Create visual notification if possible
            if (typeof this.createUserNotification === 'function') {
                this.createUserNotification(notif.title, notif.message, notif.type);
            }
        }
        
        notifyDataUpdated() {
            /**
             * Notify components that data has been updated
             */
            // Dispatch custom event
            const event = new CustomEvent('activnetDataUpdated', {
                detail: {
                    source: this.currentDataSource,
                    applicationCount: this.applications.length,
                    updateTime: this.lastUpdate,
                    dataSource: 'web-application'
                }
            });
            window.dispatchEvent(event);
            
            // Update topology dashboard if available
            if (window.topologyDashboard) {
                window.topologyDashboard.populateApplicationFilter();
                window.topologyDashboard.updateNetworkData();
                window.topologyDashboard.render();
                window.topologyDashboard.updateStats();
            }
            
            console.log('🔄 Data updated notification sent');
        }
        
        // ===========================
        // EXISTING METHODS (maintained for compatibility)
        // ===========================
        
        getFullApplicationName(appId) {
            const nameMap = {
                'ACDM': 'Application Component Discovery and Mapping',
                'HTTP': 'Web Service Application',
                'HTTPS': 'Secure Web Service Application',
                'DNS': 'Domain Name Service',
                'NTP': 'Network Time Protocol Service',
                'CIFS': 'Common Internet File System',
                'NETWORK_DATA': 'Network Data Application'
            };
            return nameMap[appId] || appId;
        }
        
        determineComplexity(recordCount, serviceCount, ipCount) {
            if (recordCount > 100 || serviceCount > 10 || ipCount > 50) return 'very-high';
            if (recordCount > 50 || serviceCount > 5 || ipCount > 20) return 'high';
            if (recordCount > 10 || serviceCount > 2 || ipCount > 5) return 'medium';
            return 'low';
        }
        
        calculatePriority(app) {
            let priority = 0;
            if (app.complexity === 'very-high') priority += 100;
            else if (app.complexity === 'high') priority += 50;
            else if (app.complexity === 'medium') priority += 25;
            
            priority += (app.total_records || 0) / 10; // Boost by activity
            return Math.floor(priority);
        }
        
        getColorForArchetype(archetype) {
            if (!this.nodeColorMap[archetype]) {
                const colors = [
                    '#3b82f6', '#10b981', '#f59e0b', '#ef4444', 
                    '#8b5cf6', '#06b6d4', '#f97316', '#84cc16'
                ];
                const colorIndex = Object.keys(this.nodeColorMap).length % colors.length;
                this.nodeColorMap[archetype] = colors[colorIndex];
            }
            return this.nodeColorMap[archetype];
        }
        
        calculateNodesFromComplexity(complexity, appId = null) {
            switch (complexity) {
                case 'very-high': return Math.floor(Math.random() * 3) + 5;
                case 'high': return 4;
                case 'medium': return Math.floor(Math.random() * 2) + 3;
                case 'low': return 2;
                default: return 4;
            }
        }
        
        // ===========================
        // NETWORK TOPOLOGY GENERATION
        // ===========================
        
        generateNetworkTopology(selectedAppNames = ['all'], includeUpstream = true, includeDownstream = true) {
            /**
             * Generate network topology from web application data
             */
            if (!this.isDataLoaded || this.applications.length === 0) {
                return { nodes: [], links: [] };
            }
            
            let selectedApps = this.applications;
            if (!selectedAppNames.includes('all')) {
                selectedApps = this.applications.filter(app => 
                    selectedAppNames.includes(app.id) || selectedAppNames.includes(app.name)
                );
            }
            
            const nodes = [];
            const links = [];
            
            // Generate topology based on real web application data
            selectedApps.forEach((app, appIndex) => {
                const nodeCount = app.nodeCount || 4;
                const appNodes = [];
                
                for (let i = 0; i < nodeCount; i++) {
                    const subnet = 10 + (appIndex % 245);
                    const host = 10 + i;
                    const nodeId = `${subnet}.0.3.${host}`;
                    
                    const nodeTypes = ['gateway', 'processor', 'data-service', 'storage'];
                    const nodeType = nodeTypes[i % nodeTypes.length];
                    
                    const node = {
                        id: nodeId,
                        name: `${app.id}-${nodeType}`,
                        ip: nodeId,
                        application: app.name,
                        applicationId: app.id,
                        archetype: app.archetype,
                        tier: nodeType,
                        color: this.getColorForArchetype(app.archetype),
                        type: nodeType,
                        status: 'active',
                        size: 10 + (app.complexity === 'very-high' ? 6 : 2),
                        isInternal: true,
                        
                        // Web application specific data
                        webAppData: {
                            source: this.currentDataSource,
                            totalRecords: app.total_records || 0,
                            complexity: app.complexity,
                            realData: true
                        }
                    };
                    
                    nodes.push(node);
                    appNodes.push(node);
                }
                
                // Create internal links
                for (let i = 0; i < appNodes.length - 1; i++) {
                    links.push({
                        source: appNodes[i].id,
                        target: appNodes[i + 1].id,
                        type: app.most_common_protocol || 'HTTP',
                        isInternal: true,
                        application: app.name,
                        realData: true
                    });
                }
            });
            
            console.log(`Generated web app topology: ${nodes.length} nodes, ${links.length} links`);
            return { nodes, links };
        }
        
        // ===========================
        // CACHE MANAGEMENT
        // ===========================
        
        hasCachedData() {
            return localStorage.getItem(this.STORAGE_KEYS.APPLICATIONS) !== null &&
                   localStorage.getItem(this.STORAGE_KEYS.LAST_UPDATE) !== null;
        }
        
        isCacheValid() {
            const cachedVersion = localStorage.getItem(this.STORAGE_KEYS.VERSION);
            const lastUpdate = localStorage.getItem(this.STORAGE_KEYS.LAST_UPDATE);
            
            if (cachedVersion !== this.DATA_VERSION) {
                console.log('📊 Cache version mismatch, invalidating cache');
                return false;
            }
            
            if (lastUpdate) {
                const cacheAge = Date.now() - parseInt(lastUpdate);
                const maxAge = 2 * 60 * 60 * 1000; // 2 hours for web app integration
                
                if (cacheAge > maxAge) {
                    console.log('⏰ Cache expired, will reload from source');
                    return false;
                }
            }
            
            return true;
        }
        
        saveToCache() {
            try {
                localStorage.setItem(this.STORAGE_KEYS.APPLICATIONS, JSON.stringify(this.applications));
                localStorage.setItem(this.STORAGE_KEYS.NETWORK_DATA, JSON.stringify(this.networkTopology));
                localStorage.setItem(this.STORAGE_KEYS.DATA_SOURCE, this.currentDataSource || '');
                localStorage.setItem(this.STORAGE_KEYS.LAST_UPDATE, Date.now().toString());
                localStorage.setItem(this.STORAGE_KEYS.VERSION, this.DATA_VERSION);
                
                console.log(`💾 Cached ${this.applications.length} applications`);
            } catch (error) {
                console.error('❌ Failed to save to localStorage:', error);
            }
        }
        
        loadFromCache() {
            try {
                const cachedApps = localStorage.getItem(this.STORAGE_KEYS.APPLICATIONS);
                const cachedSource = localStorage.getItem(this.STORAGE_KEYS.DATA_SOURCE);
                const lastUpdate = localStorage.getItem(this.STORAGE_KEYS.LAST_UPDATE);
                
                if (cachedApps) {
                    this.applications = JSON.parse(cachedApps);
                    this.applicationList = this.applications;
                }
                
                if (cachedSource) {
                    this.currentDataSource = cachedSource;
                }
                
                if (lastUpdate) {
                    this.lastUpdate = new Date(parseInt(lastUpdate));
                }
                
                this.isDataLoaded = true;
                this.notifyDataLoaded();
                
                console.log(`📦 Loaded ${this.applications.length} applications from cache`);
            } catch (error) {
                console.error('❌ Failed to load from cache:', error);
                this.clearCache();
            }
        }
        
        clearCache() {
            Object.values(this.STORAGE_KEYS).forEach(key => {
                localStorage.removeItem(key);
            });
        }
        
        // ===========================
        // EVENT SYSTEM & API METHODS
        // ===========================
        
        onDataLoaded(callback) {
            this.dataLoadedCallbacks.push(callback);
            if (this.isDataLoaded) {
                callback();
            }
        }
        
        notifyDataLoaded() {
            this.dataLoadedCallbacks.forEach(callback => {
                try {
                    callback();
                } catch (error) {
                    console.error('Error in data loaded callback:', error);
                }
            });
        }
        
        // Filter support
        getApplicationNamesForFilter() {
            const apps = [
                { id: 'all', name: 'ALL Applications', archetype: 'All', status: 'active' }
            ];
            
            this.applicationList.forEach(app => {
                apps.push({
                    id: app.id,
                    name: app.id,
                    fullName: app.name,
                    displayName: `${app.name} (${app.id})`,
                    archetype: app.archetype || 'Unknown',
                    dataSource: 'web-application'
                });
            });
            
            return apps;
        }
        
        // API methods
        getApplicationById(id) {
            if (id === 'all') {
                return { id: 'all', name: 'ALL Applications' };
            }
            return this.applications.find(app => app.id === id || app.app_id === id);
        }
        
        getApplicationsByIds(ids) {
            if (ids.includes('all')) {
                return this.applications;
            }
            return this.applications.filter(app => ids.includes(app.id) || ids.includes(app.app_id));
        }
        
        getCacheInfo() {
            return {
                hasCache: this.hasCachedData(),
                isValid: this.isCacheValid(),
                lastUpdate: this.lastUpdate,
                version: this.DATA_VERSION,
                applicationCount: this.applications.length,
                currentDataSource: this.currentDataSource,
                autoRefreshEnabled: !!this.refreshTimer,
                dataSource: 'web-application',
                expectedPaths: this.dataPaths
            };
        }
        
        async refreshData() {
            console.log('🔄 Manually refreshing data from web application...');
            this.clearCache();
            await this.loadWebApplicationData();
            return {
                status: 'success',
                message: 'Data refreshed from web application',
                count: this.applications.length,
                source: this.currentDataSource,
                timestamp: new Date().toISOString()
            };
        }
        
        // Utility methods
        setupFilterSync() {
            // Placeholder for filter synchronization
        }
        
        async loadData() {
            console.log('Web-integrated application data ready');
            return Promise.resolve();
        }
    }

    // Store the class globally to prevent redeclaration
    window.ApplicationDataManager = ApplicationDataManager;
}

// Initialize global AppData only if it doesn't exist
if (!window.AppData) {
    window.AppData = new window.ApplicationDataManager();
}

// Auto-load data when script loads
document.addEventListener('DOMContentLoaded', async () => {
    if (window.AppData && !window.AppData.isDataLoaded) {
        await window.AppData.loadData();
    }
    
    // Notify other components that web application data is ready
    if (window.topologyDashboard) {
        window.topologyDashboard.populateApplicationFilter();
        window.topologyDashboard.updateNetworkData();
        window.topologyDashboard.render();
        window.topologyDashboard.updateStats();
    }
    
    // Show current data source info
    console.log('📊 Web Application Data Manager Status:', window.AppData.getCacheInfo());
});

// Listen for data updates
window.addEventListener('activnetDataUpdated', (event) => {
    console.log('🔄 ACTIVnet data updated from web application:', event.detail);
    
    // Refresh any dependent visualizations
    if (window.topologyDashboard) {
        window.topologyDashboard.populateApplicationFilter();
        window.topologyDashboard.updateNetworkData();
        window.topologyDashboard.render();
        window.topologyDashboard.updateStats();
    }
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.AppData) {
        window.AppData.stopAutoRefresh();
    }
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ApplicationDataManager };
}

console.log('🎯 Web-Integrated ACTIVnet Data Manager loaded - Connected to /templates/activnet_data.json and /static/ui/data/');