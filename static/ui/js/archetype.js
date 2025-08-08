// Complete Network Traffic-Based Archetype Classification Dashboard
class NetworkBasedArchetypeClassificationDashboard {
    constructor() {
        this.canvas = document.getElementById('appCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.currentView = 'cards';
        this.selectedArchetypes = new Set();
        this.selectedApps = new Set();
        this.searchTerm = '';
        this.selectedApp = null;
        
        // Caching system for large data files
        this.dataCache = {
            flowData: null,
            applications: null,
            lastLoaded: null,
            cacheExpiry: 5 * 60 * 1000 // 5 minutes cache
        };
        
        // Loading state management
        this.isLoading = false;
        this.loadingProgress = 0;
        
        // Real archetype definitions based on network evidence
        this.archetypeDefinitions = {
            'Microservices': { 
                color: '#f59e0b',
                description: 'Services communicating on ports 3000-3099 with east-west traffic',
                evidencePattern: 'High east-west traffic, multiple service ports (3000-3099), distributed architecture',
                typicalPorts: ['3000-3009'],
                trafficPattern: 'East-West Service Communication'
            },
            'SOA': { 
                color: '#10b981',
                description: 'Enterprise Service Bus mediated communication via port 8080',
                evidencePattern: 'ESB tier, centralized service communication, SOAP/HTTP protocols',
                typicalPorts: ['8080'],
                trafficPattern: 'ESB-Mediated'
            },
            'Web + API Headless': { 
                color: '#3b82f6',
                description: 'SPA frontend with API backend separation',
                evidencePattern: 'SPA tier, standard web ports, frontend-backend separation',
                typicalPorts: ['80', '443'],
                trafficPattern: 'Frontend-Backend Split'
            },
            '3-Tier': { 
                color: '#8b5cf6',
                description: 'Traditional web-app-database layered architecture',
                evidencePattern: 'Web/App/Database tiers, north-south traffic, structured layers',
                typicalPorts: ['80', '443', '3306', '1433'],
                trafficPattern: 'North-South Layered'
            },
            'Event-Driven': { 
                color: '#ec4899',
                description: 'Message queue and pub/sub communication patterns',
                evidencePattern: 'Publisher/Subscriber tiers, message broker communication',
                typicalPorts: ['5672', '9092'],
                trafficPattern: 'Pub/Sub Messaging'
            },
            'Client-Server': { 
                color: '#06b6d4',
                description: 'Direct database connections from client applications',
                evidencePattern: 'Direct database connectivity, client-server protocols',
                typicalPorts: ['1433'],
                trafficPattern: 'Direct Database'
            },
            'Monolithic': { 
                color: '#64748b',
                description: 'Single application handling multiple concerns',
                evidencePattern: 'Mono tier, combined functionality, single deployment',
                typicalPorts: ['3306', '8080'],
                trafficPattern: 'Centralized Processing'
            }
        };
        
        this.networkData = null;
        this.applications = [];
        this.filteredApps = [];
        this.archetypes = [];
        
        this.init();
    }
    
    async init() {
        this.showLoadingSpinner('Initializing dashboard...');
        
        // Wait for DOM to be fully rendered
        await new Promise(resolve => setTimeout(resolve, 100));
        
        // Check cache first
        if (this.isCacheValid()) {
            console.log('Using cached data...');
            this.applications = this.dataCache.applications;
            this.filteredApps = this.applications.slice();
            this.archetypes = this.generateArchetypeSummary();
            this.hideLoadingSpinner();
        } else {
            await this.loadNetworkFlowData();
        }
        
        // Setup UI components (skip canvas setup since we start in cards view)
        setTimeout(() => {
            this.setupEventListeners();
            this.setupSearchDropdown();
            this.renderArchetypeList();
            this.renderLegend();
            this.updateStats();
            this.setInitialButtonState();
            
            // Initial render (cards view doesn't need canvas)
            this.render();
        }, 150);
        
        // Handle window resize
        window.addEventListener('resize', () => {
            setTimeout(() => {
                this.canvasRetryCount = 0; // Reset retry count on resize
                // Only setup canvas if we're in a canvas view
                if (this.currentView !== 'cards') {
                    this.setupCanvas();
                    this.render();
                }
            }, 100);
        });
        
        console.log('Dashboard initialization complete');
    }
    
    isCacheValid() {
        if (!this.dataCache.applications || !this.dataCache.lastLoaded) {
            return false;
        }
        
        const now = Date.now();
        const cacheAge = now - this.dataCache.lastLoaded;
        return cacheAge < this.dataCache.cacheExpiry;
    }
    
    showLoadingSpinner(message = 'Loading...') {
        this.isLoading = true;
        this.loadingProgress = 0;
        
        // Create or update loading overlay
        let overlay = document.getElementById('loadingOverlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'loadingOverlay';
            overlay.className = 'loading-overlay';
            document.body.appendChild(overlay);
        }
        
        overlay.innerHTML = `
            <div class="loading-spinner">
                <div class="spinner"></div>
                <div class="loading-message">${message}</div>
                <div class="loading-progress">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${this.loadingProgress}%"></div>
                    </div>
                    <div class="progress-text">${this.loadingProgress}%</div>
                </div>
            </div>
        `;
        
        overlay.style.display = 'flex';
    }
    
    updateLoadingProgress(percentage, message) {
        this.loadingProgress = Math.min(100, Math.max(0, percentage));
        
        const overlay = document.getElementById('loadingOverlay');
        if (overlay && this.isLoading) {
            const messageEl = overlay.querySelector('.loading-message');
            const progressFill = overlay.querySelector('.progress-fill');
            const progressText = overlay.querySelector('.progress-text');
            
            if (messageEl && message) messageEl.textContent = message;
            if (progressFill) progressFill.style.width = `${this.loadingProgress}%`;
            if (progressText) progressText.textContent = `${Math.round(this.loadingProgress)}%`;
        }
    }
    
    hideLoadingSpinner() {
        this.isLoading = false;
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.style.display = 'none';
        }
    }
    
    async loadNetworkFlowData() {
        try {
            if (!this.isLoading) {
                this.showLoadingSpinner('Loading network flow data...');
            }
            
            this.updateLoadingProgress(10, 'Fetching 12MB Excel file...');
            
            // Try multiple possible paths for the Excel file
            const possiblePaths = [
                '../data/synthetic_flows_apps_archetype_mapped.xlsx',
                'data/synthetic_flows_apps_archetype_mapped.xlsx',
                '/static/data/synthetic_flows_apps_archetype_mapped.xlsx',
                '../../data/synthetic_flows_apps_archetype_mapped.xlsx',
                '/data/synthetic_flows_apps_archetype_mapped.xlsx',
                './data/synthetic_flows_apps_archetype_mapped.xlsx'
            ];
            
            let response = null;
            let successPath = null;
            
            for (const path of possiblePaths) {
                try {
                    const fullUrl = new URL(path, window.location.href).href;
                    console.log(`🔍 Trying path: ${path} → Full URL: ${fullUrl}`);
                    response = await fetch(path);
                    console.log(`📊 Response status: ${response.status} for ${path}`);
                    if (response.ok) {
                        successPath = path;
                        console.log(`✅ SUCCESS! Working path: ${path}`);
                        break;
                    }
                } catch (e) {
                    console.log(`❌ Exception for path ${path}:`, e.message);
                }
            }
            
            if (!response || !response.ok) {
                throw new Error(`All paths failed. Last status: ${response?.status || 'No response'}`);
            }
            
            this.updateLoadingProgress(30, 'Downloading file...');
            
            // Get total file size for progress tracking
            const contentLength = response.headers.get('content-length');
            const total = parseInt(contentLength, 10);
            
            // Read response with progress tracking
            const reader = response.body.getReader();
            let receivedLength = 0;
            let chunks = [];
            
            while (true) {
                const { done, value } = await reader.read();
                
                if (done) break;
                
                chunks.push(value);
                receivedLength += value.length;
                
                if (total) {
                    const progress = 30 + (receivedLength / total) * 40;
                    this.updateLoadingProgress(progress, `Downloaded ${(receivedLength / 1024 / 1024).toFixed(1)}MB of ${(total / 1024 / 1024).toFixed(1)}MB`);
                }
            }
            
            this.updateLoadingProgress(70, 'Processing Excel file...');
            
            // Combine chunks into single array buffer
            const arrayBuffer = new Uint8Array(receivedLength);
            let position = 0;
            for (let chunk of chunks) {
                arrayBuffer.set(chunk, position);
                position += chunk.length;
            }
            
            this.updateLoadingProgress(80, 'Parsing Excel data...');
            
            // Use SheetJS from CDN
            const workbook = XLSX.read(arrayBuffer);
            const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
            
            this.updateLoadingProgress(85, 'Converting to JSON...');
            
            // Convert to JSON in chunks to avoid blocking UI
            const flowData = await this.processLargeDataset(firstSheet);
            console.log(`Loaded ${flowData.length} flow records`);
            
            this.updateLoadingProgress(90, 'Analyzing application traffic...');
            
            // Process and aggregate flow data by application
            const appAnalysis = this.analyzeApplicationTraffic(flowData);
            
            this.updateLoadingProgress(95, 'Creating application objects...');
            
            // Create application objects with network-based evidence
            this.applications = Object.entries(appAnalysis).map(([appName, analysis]) => {
                const definition = this.archetypeDefinitions[analysis.archetype];
                
                return {
                    id: this.generateAppId(appName),
                    name: appName,
                    archetype: analysis.archetype,
                    color: definition.color,
                    status: this.determineStatusFromTraffic(analysis),
                    trafficPattern: definition.trafficPattern,
                    
                    // Network evidence
                    flowCount: analysis.flows,
                    uniquePorts: Array.from(analysis.ports),
                    tierTypes: Array.from(analysis.tiers),
                    sourceCount: analysis.sources.size,
                    destinationCount: analysis.destinations.size,
                    
                    // Traffic characteristics
                    primaryPorts: this.getTopPorts(analysis.portCounts, 3),
                    communicationPattern: this.analyzeCommunicationPattern(analysis),
                    networkEvidence: this.generateNetworkEvidence(analysis),
                    
                    // Visual properties
                    x: Math.random() * 800,
                    y: Math.random() * 600,
                    description: definition.description
                };
            });
            
            // Cache the processed data
            this.dataCache.flowData = flowData;
            this.dataCache.applications = this.applications;
            this.dataCache.lastLoaded = Date.now();
            
            this.filteredApps = this.applications.slice();
            this.archetypes = this.generateArchetypeSummary();
            
            this.updateLoadingProgress(100, 'Complete!');
            
            console.log(`✅ Processed ${this.applications.length} applications across ${this.archetypes.length} archetypes`);
            
            // Hide spinner after short delay to show completion
            setTimeout(() => {
                this.hideLoadingSpinner();
            }, 500);
            
        } catch (error) {
            console.error('Error loading network flow data:', error);
            this.updateLoadingProgress(50, 'Excel failed, trying CSV fallback...');
            await this.loadCSVData();
        }
    }
    
    async processLargeDataset(sheet) {
        return new Promise((resolve) => {
            // Process data in chunks to avoid blocking the UI
            setTimeout(() => {
                const data = XLSX.utils.sheet_to_json(sheet);
                resolve(data);
            }, 100);
        });
    }
    
    async loadCSVData() {
        try {
            this.updateLoadingProgress(60, 'Loading CSV fallback...');
            
            // Try multiple possible paths for the CSV file
            const possiblePaths = [
                '../data/applicationList.csv',
                'data/applicationList.csv',
                '/static/data/applicationList.csv',
                '../../data/applicationList.csv',
                '/data/applicationList.csv',
                './data/applicationList.csv'
            ];
            
            let response = null;
            let successPath = null;
            
            for (const path of possiblePaths) {
                try {
                    console.log(`Trying CSV path: ${path}`);
                    response = await fetch(path);
                    if (response.ok) {
                        successPath = path;
                        console.log(`✅ CSV Success with path: ${path}`);
                        break;
                    }
                } catch (e) {
                    console.log(`❌ CSV Failed path: ${path}`);
                }
            }
            
            if (!response || !response.ok) {
                throw new Error(`All CSV paths failed. Last status: ${response?.status || 'No response'}`);
            }
            
            const csvText = await response.text();
            console.log('Loading CSV application data...');
            
            this.updateLoadingProgress(70, 'Processing CSV data...');
            
            // Parse CSV using simple parsing
            const lines = csvText.split('\n');
            const headers = lines[0].split(',');
            
            const apps = [];
            for (let i = 1; i < lines.length; i++) {
                if (lines[i].trim()) {
                    const values = lines[i].split(',');
                    if (values.length >= 2) {
                        apps.push({
                            app_id: values[0].trim(),
                            app_name: values[1].trim()
                        });
                    }
                }
            }
            
            console.log(`Loaded ${apps.length} applications from CSV`);
            
            this.updateLoadingProgress(85, 'Classifying applications...');
            
            // Create applications with intelligent archetype classification
            this.applications = apps.map((app, index) => {
                const archetype = this.classifyApplicationFromName(app.app_name || app.app_id);
                const definition = this.archetypeDefinitions[archetype];
                
                return {
                    id: app.app_id || `app-${index}`,
                    name: app.app_name || app.app_id,
                    archetype: archetype,
                    color: definition.color,
                    status: this.generateRandomStatus(),
                    trafficPattern: definition.trafficPattern,
                    
                    // Simulated network evidence based on archetype
                    flowCount: this.generateFlowCount(archetype),
                    uniquePorts: this.getArchetypePorts(archetype),
                    tierTypes: this.getArchetypeTiers(archetype),
                    sourceCount: Math.floor(Math.random() * 500) + 50,
                    destinationCount: Math.floor(Math.random() * 500) + 50,
                    
                    // Traffic characteristics
                    primaryPorts: this.generatePrimaryPorts(archetype),
                    communicationPattern: this.getArchetypeCommunicationPattern(archetype),
                    networkEvidence: this.generateArchetypeEvidence(archetype),
                    
                    // Visual properties
                    x: Math.random() * 800,
                    y: Math.random() * 600,
                    description: definition.description
                };
            });
            
            // Cache the processed data
            this.dataCache.applications = this.applications;
            this.dataCache.lastLoaded = Date.now();
            
            this.filteredApps = this.applications.slice();
            this.archetypes = this.generateArchetypeSummary();
            
            this.updateLoadingProgress(100, 'CSV processing complete!');
            
            console.log(`✅ Classified ${this.applications.length} applications with intelligent archetype detection`);
            
            // Hide spinner after short delay
            setTimeout(() => {
                this.hideLoadingSpinner();
            }, 500);
            
        } catch (error) {
            console.error('Error loading CSV data:', error);
            this.updateLoadingProgress(100, 'Using demo data...');
            this.generateFallbackData();
            setTimeout(() => {
                this.hideLoadingSpinner();
            }, 500);
        }
    }
    
    classifyApplicationFromName(appName) {
        const name = appName.toLowerCase();
        
        // Enhanced classification logic based on application name patterns
        if (name.includes('api') || name.includes('service') || name.includes('endpoint')) {
            if (name.includes('gateway') || name.includes('proxy')) {
                return 'SOA';
            }
            if (name.includes('micro') || name.includes('ms ')) {
                return 'Microservices';
            }
            return 'Web + API Headless';
        }
        
        if (name.includes('web') || name.includes('portal') || name.includes('ui') || name.includes('frontend') || name.includes('dashboard')) {
            return 'Web + API Headless';
        }
        
        if (name.includes('queue') || name.includes('event') || name.includes('kafka') || name.includes('rabbit') || name.includes('message')) {
            return 'Event-Driven';
        }
        
        if (name.includes('etl') || name.includes('pipeline') || name.includes('batch') || name.includes('data') || name.includes('analytics')) {
            return 'Event-Driven';
        }
        
        if (name.includes('lambda') || name.includes('function') || name.includes('serverless')) {
            return 'Microservices';
        }
        
        if (name.includes('cloud') || name.includes('aws') || name.includes('azure') || name.includes('gcp')) {
            return 'Microservices';
        }
        
        if (name.includes('mainframe') || name.includes('cobol') || name.includes('legacy') || name.includes('old')) {
            return 'Monolithic';
        }
        
        if (name.includes('soa') || name.includes('esb') || name.includes('soap') || name.includes('enterprise')) {
            return 'SOA';
        }
        
        if (name.includes('client') || name.includes('desktop') || name.includes('thick') || name.includes('workstation')) {
            return 'Client-Server';
        }
        
        if (name.includes('engine') || name.includes('processing') || name.includes('vault') || name.includes('core')) {
            return 'Monolithic';
        }
        
        if (name.includes('auth') || name.includes('security') || name.includes('login') || name.includes('identity')) {
            return 'SOA';
        }
        
        if (name.includes('mobile') || name.includes('app') || name.includes('ios') || name.includes('android')) {
            return 'Web + API Headless';
        }
        
        // Default to 3-Tier for most enterprise applications
        return '3-Tier';
    }
    
    generateRandomStatus() {
        const statuses = ['active', 'inactive', 'migrating', 'deprecated'];
        const weights = [0.6, 0.2, 0.15, 0.05];
        
        const random = Math.random();
        let cumulative = 0;
        
        for (let i = 0; i < statuses.length; i++) {
            cumulative += weights[i];
            if (random <= cumulative) {
                return statuses[i];
            }
        }
        
        return 'active';
    }
    
    generateFlowCount(archetype) {
        const ranges = {
            'Microservices': [3000, 5000],
            'SOA': [4000, 6000],
            'Web + API Headless': [2000, 4000],
            '3-Tier': [3000, 5000],
            'Event-Driven': [4000, 7000],
            'Client-Server': [1000, 3000],
            'Monolithic': [2000, 4000]
        };
        
        const range = ranges[archetype] || [1000, 3000];
        return Math.floor(Math.random() * (range[1] - range[0])) + range[0];
    }
    
    getArchetypePorts(archetype) {
        const portMappings = {
            'Microservices': ['3000', '3001', '3002', '3003', '3004'],
            'SOA': ['8080', '8443'],
            'Web + API Headless': ['80', '443', '8080'],
            '3-Tier': ['80', '443', '3306', '1433'],
            'Event-Driven': ['5672', '9092'],
            'Client-Server': ['1433', '3389'],
            'Monolithic': ['3306', '8080']
        };
        
        return portMappings[archetype] || ['80', '443'];
    }
    
    getArchetypeTiers(archetype) {
        const tierMappings = {
            'Microservices': ['Service', 'Client'],
            'SOA': ['ESB', 'Service'],
            'Web + API Headless': ['SPA', 'API'],
            '3-Tier': ['Web', 'App', 'Database'],
            'Event-Driven': ['Publisher', 'Subscriber'],
            'Client-Server': ['Client', 'Database'],
            'Monolithic': ['Mono']
        };
        
        return tierMappings[archetype] || ['App'];
    }
    
    generatePrimaryPorts(archetype) {
        const ports = this.getArchetypePorts(archetype);
        return ports.slice(0, 3).map(port => ({
            port: parseInt(port),
            count: Math.floor(Math.random() * 2000) + 500
        }));
    }
    
    getArchetypeCommunicationPattern(archetype) {
        const patterns = {
            'Microservices': 'Highly Distributed',
            'SOA': 'ESB-Mediated',
            'Web + API Headless': 'Frontend-Backend',
            '3-Tier': 'Layered Communication',
            'Event-Driven': 'Event-Based',
            'Client-Server': 'Direct Connection',
            'Monolithic': 'Centralized'
        };
        
        return patterns[archetype] || 'Standard Communication';
    }
    
    generateArchetypeEvidence(archetype) {
        const evidenceMap = {
            'Microservices': ['Service mesh communication', 'Container orchestration', 'API Gateway integration'],
            'SOA': ['Enterprise Service Bus', 'SOAP/XML protocols', 'Service registry'],
            'Web + API Headless': ['SPA framework', 'REST API endpoints', 'CORS configuration'],
            '3-Tier': ['Web server tier', 'Application server', 'Database connectivity'],
            'Event-Driven': ['Message broker', 'Pub/Sub patterns', 'Event streaming'],
            'Client-Server': ['Direct database access', 'Client applications', 'Persistent connections'],
            'Monolithic': ['Single deployment unit', 'Integrated components', 'Shared database']
        };
        
        return evidenceMap[archetype] || ['Standard application patterns'];
    }
    
    analyzeApplicationTraffic(flowData) {
        const appAnalysis = {};
        
        flowData.forEach(flow => {
            const appName = flow.application;
            
            if (!appAnalysis[appName]) {
                appAnalysis[appName] = {
                    archetype: flow.archetype,
                    flows: 0,
                    ports: new Set(),
                    tiers: new Set(),
                    sources: new Set(),
                    destinations: new Set(),
                    portCounts: {},
                    protocols: new Set(),
                    timestamps: []
                };
            }
            
            const analysis = appAnalysis[appName];
            analysis.flows++;
            analysis.ports.add(flow.port);
            analysis.tiers.add(flow.tier);
            analysis.sources.add(flow.src);
            analysis.destinations.add(flow.dst);
            analysis.protocols.add(flow.protocol);
            analysis.timestamps.push(flow.timestamp);
            
            // Count port usage
            if (!analysis.portCounts[flow.port]) {
                analysis.portCounts[flow.port] = 0;
            }
            analysis.portCounts[flow.port]++;
        });
        
        return appAnalysis;
    }
    
    determineStatusFromTraffic(analysis) {
        if (analysis.flows > 4000) return 'active';
        if (analysis.flows > 2000) return 'active';
        if (analysis.flows > 1000) return 'migrating';
        return 'inactive';
    }
    
    getTopPorts(portCounts, limit = 3) {
        return Object.entries(portCounts)
            .sort((a, b) => b[1] - a[1])
            .slice(0, limit)
            .map(([port, count]) => ({ port: parseInt(port), count }));
    }
    
    analyzeCommunicationPattern(analysis) {
        const sourceDestRatio = analysis.sources.size / analysis.destinations.size;
        const portSpread = analysis.ports.size;
        
        if (portSpread > 10) return 'Highly Distributed';
        if (sourceDestRatio > 2) return 'Fan-out Pattern';
        if (sourceDestRatio < 0.5) return 'Fan-in Pattern';
        return 'Balanced Communication';
    }
    
    generateNetworkEvidence(analysis) {
        const evidence = [];
        
        if (analysis.ports.size > 5) {
            evidence.push(`Multiple ports (${analysis.ports.size})`);
        }
        
        if (analysis.tiers.has('Service')) {
            evidence.push('Service-to-service communication');
        }
        
        if (analysis.tiers.has('ESB')) {
            evidence.push('Enterprise Service Bus integration');
        }
        
        if (analysis.flows > 3000) {
            evidence.push('High traffic volume');
        }
        
        return evidence.slice(0, 3);
    }
    
    generateAppId(appName) {
        return appName.split(' ').map(word => word.charAt(0).toUpperCase()).join('') + 
               Math.random().toString(36).substr(2, 3).toUpperCase();
    }
    
    generateArchetypeSummary() {
        const summary = {};
        
        Object.keys(this.archetypeDefinitions).forEach(archetype => {
            summary[archetype] = {
                name: archetype,
                color: this.archetypeDefinitions[archetype].color,
                count: 0,
                apps: []
            };
        });
        
        this.applications.forEach(app => {
            if (summary[app.archetype]) {
                summary[app.archetype].count++;
                summary[app.archetype].apps.push(app);
            }
        });
        
        return Object.values(summary).filter(archetype => archetype.count > 0);
    }
    
    generateFallbackData() {
        console.log('Using fallback demo data');
        // Create demo applications if file loading fails
        this.applications = [
            {
                id: 'DEMO1',
                name: 'Demo Web Application',
                archetype: '3-Tier',
                color: '#8b5cf6',
                status: 'active',
                trafficPattern: 'North-South Layered',
                flowCount: 2500,
                uniquePorts: ['80', '443', '3306'],
                tierTypes: ['Web', 'App', 'Database'],
                sourceCount: 150,
                destinationCount: 45,
                primaryPorts: [{ port: 80, count: 1200 }, { port: 443, count: 800 }],
                communicationPattern: 'Balanced Communication',
                networkEvidence: ['Standard web ports', 'Database connectivity'],
                x: Math.random() * 800,
                y: Math.random() * 600,
                description: 'Traditional web-app-database layered architecture'
            }
        ];
        this.filteredApps = this.applications.slice();
        this.archetypes = this.generateArchetypeSummary();
    }
    
    setupSearchDropdown() {
        const searchInput = document.getElementById('archetypeSearch');
        const searchContainer = document.querySelector('.search-container');
        
        if (!searchInput || !searchContainer) return;
        
        const dropdown = document.createElement('div');
        dropdown.className = 'search-dropdown';
        dropdown.id = 'searchDropdown';
        
        const selectedContainer = document.createElement('div');
        selectedContainer.className = 'selected-apps-container';
        selectedContainer.innerHTML = `
            <div class="selected-apps-title">Selected Applications</div>
            <div class="selected-apps-list" id="selectedAppsList"></div>
            <button class="clear-all-btn" onclick="clearAllSelectedApps()">Clear All</button>
        `;
        
        searchContainer.appendChild(dropdown);
        searchContainer.appendChild(selectedContainer);
        
        searchInput.addEventListener('input', (e) => {
            this.handleSearchInput(e.target.value);
        });
        
        searchInput.addEventListener('focus', () => {
            this.showSearchDropdown();
        });
        
        document.addEventListener('click', (e) => {
            if (!searchContainer.contains(e.target)) {
                this.hideSearchDropdown();
            }
        });
        
        this.updateSelectedAppsDisplay();
    }
    
    handleSearchInput(query) {
        this.searchTerm = query.toLowerCase();
        this.updateSearchDropdown();
        this.applyFilters();
    }
    
    updateSearchDropdown() {
        const dropdown = document.getElementById('searchDropdown');
        if (!dropdown) return;
        
        const filteredApps = this.searchTerm ? 
            this.applications.filter(app => 
                app.name.toLowerCase().includes(this.searchTerm) ||
                app.id.toLowerCase().includes(this.searchTerm) ||
                app.archetype.toLowerCase().includes(this.searchTerm) ||
                app.primaryPorts.some(p => p.port.toString().includes(this.searchTerm)) ||
                app.tierTypes.some(t => t.toLowerCase().includes(this.searchTerm))
            ) : this.applications;
        
        const groupedApps = {};
        filteredApps.forEach(app => {
            if (!groupedApps[app.archetype]) {
                groupedApps[app.archetype] = [];
            }
            groupedApps[app.archetype].push(app);
        });
        
        let dropdownHTML = '';
        
        if (this.searchTerm) {
            dropdownHTML += `
                <div class="dropdown-section">
                    <div class="dropdown-item" onclick="selectAllFilteredApps()">
                        <span>📋</span>
                        <span>Select All (${filteredApps.length} apps)</span>
                    </div>
                </div>
            `;
        }
        
        Object.entries(groupedApps).forEach(([archetype, apps]) => {
            const archetypeInfo = this.archetypeDefinitions[archetype];
            dropdownHTML += `
                <div class="dropdown-section">
                    <div class="dropdown-header">
                        ${archetype} (${apps.length})
                        <div style="font-size: 9px; font-weight: normal; margin-top: 2px; color: #94a3b8;">
                            ${archetypeInfo.evidencePattern}
                        </div>
                    </div>
            `;
            
            apps.forEach(app => {
                const isSelected = this.selectedApps.has(app.id);
                const topPort = app.primaryPorts[0]?.port || 'N/A';
                const flows = app.flowCount || 0;
                
                dropdownHTML += `
                    <div class="dropdown-item ${isSelected ? 'selected' : ''}" onclick="toggleAppSelection('${app.id}')">
                        <div class="app-indicator" style="background-color: ${archetypeInfo.color}"></div>
                        <div style="flex-grow: 1;">
                            <div style="font-weight: 600;">${app.name}</div>
                            <div style="font-size: 10px; color: #94a3b8;">
                                ${app.id} • Port ${topPort} • ${flows} flows • ${app.status}
                            </div>
                        </div>
                    </div>
                `;
            });
            
            dropdownHTML += '</div>';
        });
        
        if (dropdownHTML === '') {
            dropdownHTML = '<div class="dropdown-item">No applications found</div>';
        }
        
        dropdown.innerHTML = dropdownHTML;
    }
    
    showSearchDropdown() {
        this.updateSearchDropdown();
        const dropdown = document.getElementById('searchDropdown');
        if (dropdown) {
            dropdown.classList.add('show');
        }
    }
    
    hideSearchDropdown() {
        const dropdown = document.getElementById('searchDropdown');
        if (dropdown) {
            dropdown.classList.remove('show');
        }
    }
    
    updateSelectedAppsDisplay() {
        const container = document.querySelector('.selected-apps-container');
        const list = document.getElementById('selectedAppsList');
        
        if (!container || !list) return;
        
        if (this.selectedApps.size === 0) {
            container.classList.remove('show');
            return;
        }
        
        container.classList.add('show');
        
        const selectedAppsArray = Array.from(this.selectedApps).map(id => 
            this.applications.find(app => app.id === id)
        ).filter(Boolean);
        
        let tagsHTML = '';
        selectedAppsArray.forEach(app => {
            tagsHTML += `<div class="selected-app-tag"><span>${app.name}</span><button class="remove-btn" onclick="removeAppSelection('${app.id}')">×</button></div>`;
        });
        
        list.innerHTML = tagsHTML;
    }
    
    toggleAppSelection(appId) {
        if (this.selectedApps.has(appId)) {
            this.selectedApps.delete(appId);
        } else {
            this.selectedApps.add(appId);
        }
        
        this.updateSearchDropdown();
        this.updateSelectedAppsDisplay();
        this.applyFilters();
    }
    
    selectAllFilteredApps() {
        const filteredApps = this.searchTerm ? 
            this.applications.filter(app => 
                app.name.toLowerCase().includes(this.searchTerm) ||
                app.archetype.toLowerCase().includes(this.searchTerm)
            ) : this.applications;
        
        filteredApps.forEach(app => {
            this.selectedApps.add(app.id);
        });
        
        this.updateSearchDropdown();
        this.updateSelectedAppsDisplay();
        this.applyFilters();
        this.hideSearchDropdown();
    }
    
    clearAllSelectedApps() {
        this.selectedApps.clear();
        this.updateSearchDropdown();
        this.updateSelectedAppsDisplay();
        this.applyFilters();
    }
    
    removeAppSelection(appId) {
        this.selectedApps.delete(appId);
        this.updateSearchDropdown();
        this.updateSelectedAppsDisplay();
        this.applyFilters();
    }
    
    setInitialButtonState() {
        document.querySelectorAll('.view-controls .btn').forEach(btn => {
            btn.classList.remove('active');
        });
        
        const cardsBtn = document.getElementById('cardsBtn');
        if (cardsBtn) {
            cardsBtn.classList.add('active');
        }
    }
    
    setupCanvas() {
        if (!this.canvas) return;
        
        // Don't setup canvas if we're in cards view (canvas is hidden)
        if (this.currentView === 'cards') {
            console.log('Skipping canvas setup - currently in cards view');
            return;
        }
        
        // Add retry limit to prevent infinite loops
        if (!this.canvasRetryCount) this.canvasRetryCount = 0;
        
        const rect = this.canvas.getBoundingClientRect();
        
        // Ensure we have valid dimensions
        if (rect.width === 0 || rect.height === 0) {
            this.canvasRetryCount++;
            
            if (this.canvasRetryCount > 10) {
                console.error('Canvas setup failed after 10 retries. Setting fallback dimensions.');
                // Set fallback dimensions
                this.canvasWidth = 800;
                this.canvasHeight = 600;
                this.canvas.width = this.canvasWidth * window.devicePixelRatio;
                this.canvas.height = this.canvasHeight * window.devicePixelRatio;
                this.ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
                this.canvas.style.width = this.canvasWidth + 'px';
                this.canvas.style.height = this.canvasHeight + 'px';
                return;
            }
            
            console.warn(`Canvas has zero dimensions, retrying... (attempt ${this.canvasRetryCount}/10)`);
            setTimeout(() => this.setupCanvas(), 100);
            return;
        }
        
        // Reset retry count on successful setup
        this.canvasRetryCount = 0;
        
        this.canvas.width = rect.width * window.devicePixelRatio;
        this.canvas.height = rect.height * window.devicePixelRatio;
        this.ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
        this.canvas.style.width = rect.width + 'px';
        this.canvas.style.height = rect.height + 'px';
        this.canvasWidth = rect.width;
        this.canvasHeight = rect.height;
        
        console.log(`Canvas setup successful: ${this.canvasWidth}x${this.canvasHeight}`);
    }
    
    setupEventListeners() {
        this.canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        this.canvas.addEventListener('click', (e) => this.handleClick(e));
        this.canvas.addEventListener('mouseleave', () => this.hideAppDetails());
    }
    
    render() {
        this.filteredApps = this.applications.filter(app => {
            const matchesSearch = this.searchTerm === '' || 
                app.name.toLowerCase().includes(this.searchTerm) ||
                app.id.toLowerCase().includes(this.searchTerm) ||
                app.archetype.toLowerCase().includes(this.searchTerm);
            
            const matchesArchetype = this.selectedArchetypes.size === 0 || 
                this.selectedArchetypes.has(app.archetype);
            
            const matchesAppSelection = this.selectedApps.size === 0 || 
                this.selectedApps.has(app.id);
            
            return matchesSearch && matchesArchetype && matchesAppSelection;
        });
        
        if (this.currentView === 'cards') {
            this.renderArchetypeCards();
        } else {
            this.renderCanvasView();
        }
        
        this.updateStats();
    }
    
    renderArchetypeCards() {
        const canvas = document.getElementById('appCanvas');
        const container = canvas.parentElement;
        
        canvas.style.display = 'none';
        
        let cardsContainer = container.querySelector('.archetype-cards-container');
        if (!cardsContainer) {
            cardsContainer = document.createElement('div');
            cardsContainer.className = 'archetype-cards-container';
            container.appendChild(cardsContainer);
        }
        
        // Always show and reset the container - FORCE 3 COLUMNS
        cardsContainer.style.display = 'grid';
        cardsContainer.style.gridTemplateColumns = 'repeat(3, 1fr)'; // FIXED 3 COLUMNS
        cardsContainer.style.gap = '16px';
        cardsContainer.style.padding = '16px';
        cardsContainer.style.height = 'calc(100% - 80px)';
        cardsContainer.style.overflowY = 'auto';
        
        const archetypeGroups = {};
        this.filteredApps.forEach(app => {
            if (!archetypeGroups[app.archetype]) {
                archetypeGroups[app.archetype] = [];
            }
            archetypeGroups[app.archetype].push(app);
        });
        
        cardsContainer.innerHTML = '';
        this.archetypes.forEach(archetype => {
            const apps = archetypeGroups[archetype.name] || [];
            if (apps.length === 0) return;
            
            const card = this.createNetworkBasedArchetypeCard(archetype, apps);
            cardsContainer.appendChild(card);
        });
        
        console.log(`Rendered ${this.archetypes.length} archetype cards`);
    }
    
    createNetworkBasedArchetypeCard(archetype, apps) {
        const card = document.createElement('div');
        card.className = 'archetype-card';
        card.style.borderLeftColor = archetype.color;
        
        const activeApps = apps.filter(app => app.status === 'active').length;
        const definition = this.archetypeDefinitions[archetype.name];
        const totalFlows = apps.reduce((sum, app) => sum + (app.flowCount || 0), 0);
        const avgFlowsPerApp = Math.round(totalFlows / apps.length);
        
        const applicationsGridHTML = apps.map(app => this.createNetworkAppNode(app)).join('');
        const evidenceHTML = apps[0]?.networkEvidence?.slice(0, 3).map(evidence => 
            `<span class="pattern-tag">${evidence}</span>`
        ).join('') || '';
        
        // Add traffic pattern tags - RESTORED
        const trafficPatterns = [...new Set(apps.map(app => app.trafficPattern))];
        const trafficPatternsHTML = trafficPatterns.map(pattern => 
            `<span class="traffic-pattern-tag">${pattern}</span>`
        ).join('');
        
        card.innerHTML = `
            <div class="archetype-card-header">
                <div class="archetype-card-title">
                    <div class="archetype-icon" style="background-color: ${archetype.color}"></div>
                    <h3>${archetype.name}</h3>
                </div>
                <div class="archetype-count">${apps.length}</div>
            </div>
            <div class="archetype-stats">
                <div class="stat-row">
                    <span>Active:</span>
                    <span class="stat-value active">${activeApps}/${apps.length}</span>
                </div>
                <div class="stat-row">
                    <span>Avg Flows:</span>
                    <span class="stat-value">${avgFlowsPerApp.toLocaleString()}</span>
                </div>
                <div class="stat-row">
                    <span>Pattern:</span>
                    <span class="stat-value">${definition.trafficPattern}</span>
                </div>
            </div>
            <div class="applications-grid">${applicationsGridHTML}</div>
            <div class="traffic-pattern-tags">
                <div class="traffic-pattern-title">Traffic Patterns:</div>
                <div class="traffic-pattern-list">${trafficPatternsHTML}</div>
            </div>
            <div class="archetype-patterns">
                <div class="pattern-title">Network Evidence:</div>
                <div class="pattern-list">${evidenceHTML}</div>
            </div>
        `;
        
        card.addEventListener('click', (e) => {
            if (e.target.classList.contains('app-node')) {
                const appId = e.target.dataset.appId;
                const app = apps.find(a => a.id === appId);
                if (app) {
                    this.showNetworkAppDetails(app, e.target);
                }
            }
        });
        
        return card;
    }
    
    createNetworkAppNode(app) {
        const statusClass = app.status === 'active' ? 'active' : 
                           app.status === 'migrating' ? 'migrating' : 'inactive';
        
        const flowVolume = app.flowCount > 4000 ? 'high' : app.flowCount > 2000 ? 'medium' : 'low';
        
        return `<div class="app-node ${statusClass} flow-${flowVolume}" data-app-id="${app.id}" 
                     style="background-color: ${app.color}" 
                     title="${app.name} • ${app.flowCount} flows • Ports: ${app.primaryPorts.map(p => p.port).join(', ')}">
                    <div class="app-node-inner"></div>
                </div>`;
    }
    
    showNetworkAppDetails(app, element) {
        const details = document.getElementById('appDetails');
        if (!details) return;
        
        const detailAppName = document.getElementById('detailAppName');
        const detailArchetype = document.getElementById('detailArchetype');
        const detailTraffic = document.getElementById('detailTraffic');
        const detailStatus = document.getElementById('detailStatus');
        
        if (detailAppName) detailAppName.textContent = app.name;
        if (detailArchetype) detailArchetype.textContent = app.archetype;
        if (detailTraffic) detailTraffic.textContent = app.trafficPattern;
        if (detailStatus) detailStatus.textContent = app.status;
        
        const indicatorsContainer = document.getElementById('detailIndicators');
        if (indicatorsContainer) {
            const networkInfo = [
                `${app.flowCount} network flows`,
                `${app.sourceCount} sources → ${app.destinationCount} destinations`,
                `${app.tierTypes.join(', ')} tiers`
            ];
            indicatorsContainer.innerHTML = networkInfo.map(info => 
                `<span class="indicator-tag">${info}</span>`
            ).join('');
        }
        
        const portsContainer = document.getElementById('detailPorts');
        if (portsContainer) {
            portsContainer.innerHTML = app.primaryPorts.map(portInfo => 
                `<span class="port-tag">${portInfo.port} (${portInfo.count} flows)</span>`
            ).join('');
        }
        
        details.classList.add('visible');
        
        const rect = element.getBoundingClientRect();
        const containerRect = element.closest('.graph-container').getBoundingClientRect();
        details.style.top = Math.min(rect.top - containerRect.top, containerRect.height - 300) + 'px';
    }
    
    hideAppDetails() {
        const details = document.getElementById('appDetails');
        if (details) {
            details.classList.remove('visible');
        }
    }
    
    renderCanvasView() {
        const canvas = document.getElementById('appCanvas');
        const container = canvas.parentElement;
        
        canvas.style.display = 'block';
        const cardsContainer = container.querySelector('.archetype-cards-container');
        if (cardsContainer) {
            cardsContainer.style.display = 'none';
        }
        
        // Force canvas to have proper dimensions
        canvas.style.minHeight = '400px';
        
        // Reset retry count and setup canvas
        this.canvasRetryCount = 0;
        this.setupCanvas();
        
        // Only proceed with drawing if canvas has valid dimensions
        if (this.canvasWidth > 0 && this.canvasHeight > 0) {
            // Wait a frame for canvas to be ready, then draw
            requestAnimationFrame(() => {
                this.positionApplications();
                this.drawVisualization();
            });
        } else {
            console.warn('Canvas still has invalid dimensions, skipping drawing');
        }
    }
    
    positionApplications() {
        if (!this.filteredApps || this.filteredApps.length === 0) {
            console.warn('No applications to position');
            return;
        }
        
        const margin = 50;
        const width = Math.max(400, this.canvasWidth - 2 * margin);
        const height = Math.max(300, this.canvasHeight - 2 * margin);
        
        console.log(`Positioning ${this.filteredApps.length} apps in ${this.currentView} view (${width}x${height})`);
        
        switch (this.currentView) {
            case 'cluster':
                this.positionClusterView(margin, width, height);
                break;
            case 'network':
                this.positionNetworkView(margin, width, height);
                break;
            case 'hierarchy':
                this.positionHierarchyView(margin, width, height);
                break;
            default:
                this.positionClusterView(margin, width, height);
        }
    }
    
    positionClusterView(margin, width, height) {
        const archetypeGroups = {};
        this.filteredApps.forEach(app => {
            if (!archetypeGroups[app.archetype]) {
                archetypeGroups[app.archetype] = [];
            }
            archetypeGroups[app.archetype].push(app);
        });
        
        const groupNames = Object.keys(archetypeGroups);
        const cols = Math.ceil(Math.sqrt(groupNames.length));
        const rows = Math.ceil(groupNames.length / cols);
        
        groupNames.forEach((groupName, index) => {
            const row = Math.floor(index / cols);
            const col = index % cols;
            
            const centerX = margin + (col + 0.5) * (width / cols);
            const centerY = margin + (row + 0.5) * (height / rows);
            const radius = Math.min(width / cols, height / rows) * 0.3;
            
            const apps = archetypeGroups[groupName];
            apps.forEach((app, appIndex) => {
                const angle = (appIndex / apps.length) * 2 * Math.PI;
                const distance = Math.random() * radius;
                app.x = centerX + Math.cos(angle) * distance;
                app.y = centerY + Math.sin(angle) * distance;
            });
        });
    }
    
    positionNetworkView(margin, width, height) {
        const centerX = margin + width / 2;
        const centerY = margin + height / 2;
        
        const archetypeGroups = {};
        this.filteredApps.forEach(app => {
            if (!archetypeGroups[app.archetype]) {
                archetypeGroups[app.archetype] = [];
            }
            archetypeGroups[app.archetype].push(app);
        });
        
        const groupNames = Object.keys(archetypeGroups);
        const angleStep = (2 * Math.PI) / groupNames.length;
        const maxRadius = Math.min(width, height) * 0.4; // Larger spread - was 0.45
        
        groupNames.forEach((groupName, groupIndex) => {
            const groupAngle = groupIndex * angleStep;
            const groupRadius = maxRadius;
            const groupCenterX = centerX + Math.cos(groupAngle) * groupRadius;
            const groupCenterY = centerY + Math.sin(groupAngle) * groupRadius;
            
            const apps = archetypeGroups[groupName];
            const localRadius = Math.min(150, Math.sqrt(apps.length) * 20); // Larger local radius
            
            apps.forEach((app, appIndex) => {
                if (apps.length === 1) {
                    app.x = groupCenterX;
                    app.y = groupCenterY;
                } else {
                    const localAngle = (appIndex / apps.length) * 2 * Math.PI;
                    const distance = localRadius * (0.5 + Math.random() * 0.5); // Better spread
                    app.x = groupCenterX + Math.cos(localAngle) * distance;
                    app.y = groupCenterY + Math.sin(localAngle) * distance;
                }
                
                app.x = Math.max(margin + 20, Math.min(margin + width - 20, app.x));
                app.y = Math.max(margin + 20, Math.min(margin + height - 20, app.y));
            });
        });
        
        this.networkConnections = [];
        this.filteredApps.forEach((app, i) => {
            this.filteredApps.slice(i + 1).forEach(other => {
                if (app.archetype !== other.archetype) {
                    const distance = Math.sqrt((app.x - other.x) ** 2 + (app.y - other.y) ** 2);
                    if (distance < 250 && Math.random() > 0.3) { // More connections, larger distance
                        this.networkConnections.push({ source: app, target: other });
                    }
                }
            });
        });
    }
    
    positionHierarchyView(margin, width, height) {
        const layers = {
            'Client-Server': 0,
            'Web + API Headless': 1,
            '3-Tier': 2,
            'Microservices': 3,
            'SOA': 4,
            'Event-Driven': 5,
            'Monolithic': 6
        };
        
        const layerGroups = {};
        this.filteredApps.forEach(app => {
            const layer = layers[app.archetype] || 3;
            if (!layerGroups[layer]) layerGroups[layer] = [];
            layerGroups[layer].push(app);
        });
        
        Object.keys(layerGroups).forEach(layer => {
            const apps = layerGroups[layer];
            const y = margin + (parseInt(layer) + 0.5) * (height / 7);
            
            apps.forEach((app, index) => {
                app.x = margin + (index + 1) * (width / (apps.length + 1));
                app.y = y + (Math.random() - 0.5) * 40;
            });
        });
    }
    
    drawVisualization() {
        if (!this.ctx || !this.canvasWidth || !this.canvasHeight) {
            console.warn('Canvas not ready for drawing');
            return;
        }
        
        this.ctx.clearRect(0, 0, this.canvasWidth, this.canvasHeight);
        
        // Draw background
        this.ctx.fillStyle = '#0f172a';
        this.ctx.fillRect(0, 0, this.canvasWidth, this.canvasHeight);
        
        if (this.currentView === 'network') {
            this.drawConnections();
        }
        
        if (this.filteredApps && this.filteredApps.length > 0) {
            this.filteredApps.forEach(app => {
                this.drawApplication(app);
            });
            
            console.log(`Drew ${this.filteredApps.length} applications in ${this.currentView} view`);
        } else {
            // Draw "no data" message
            this.ctx.fillStyle = '#64748b';
            this.ctx.font = '16px system-ui';
            this.ctx.textAlign = 'center';
            this.ctx.textBaseline = 'middle';
            this.ctx.fillText('No applications to display', this.canvasWidth / 2, this.canvasHeight / 2);
        }
        
        if (this.currentView === 'cluster') {
            this.drawClusterLabels();
        }
    }
    
    drawConnections() {
        if (!this.networkConnections) return;
        
        this.ctx.strokeStyle = '#475569';
        this.ctx.lineWidth = 1;
        this.ctx.globalAlpha = 0.6;
        
        this.networkConnections.forEach(connection => {
            this.ctx.beginPath();
            this.ctx.moveTo(connection.source.x, connection.source.y);
            this.ctx.lineTo(connection.target.x, connection.target.y);
            this.ctx.stroke();
        });
        
        this.ctx.globalAlpha = 1;
    }
    
    drawApplication(app) {
        const isSelected = this.selectedApp === app;
        const baseRadius = 6; // Larger dots - was 4
        const radius = baseRadius + (isSelected ? 3 : 0); // Bigger selection highlight
        
        this.ctx.beginPath();
        this.ctx.arc(app.x, app.y, radius, 0, 2 * Math.PI);
        this.ctx.fillStyle = app.color;
        this.ctx.fill();
        
        this.ctx.strokeStyle = isSelected ? '#ffffff' : '#ffffff';
        this.ctx.lineWidth = isSelected ? 3 : 2; // Thicker borders
        this.ctx.stroke();
        
        if (app.status !== 'active') {
            const indicatorSize = 3; // Larger indicators
            let indicatorColor = '#64748b';
            if (app.status === 'migrating') indicatorColor = '#f59e0b';
            if (app.status === 'deprecated') indicatorColor = '#ef4444';
            
            this.ctx.beginPath();
            this.ctx.arc(app.x + radius - 2, app.y - radius + 2, indicatorSize, 0, 2 * Math.PI);
            this.ctx.fillStyle = indicatorColor;
            this.ctx.fill();
        }
    }
    
    drawClusterLabels() {
        const archetypePositions = {};
        
        this.filteredApps.forEach(app => {
            if (!archetypePositions[app.archetype]) {
                archetypePositions[app.archetype] = { x: 0, y: 0, count: 0, minY: Infinity };
            }
            archetypePositions[app.archetype].x += app.x;
            archetypePositions[app.archetype].y += app.y;
            archetypePositions[app.archetype].count++;
            
            if (app.y < archetypePositions[app.archetype].minY) {
                archetypePositions[app.archetype].minY = app.y;
            }
        });
        
        Object.keys(archetypePositions).forEach(archetype => {
            const pos = archetypePositions[archetype];
            const centerX = pos.x / pos.count;
            const labelY = pos.minY - 25;
            
            this.ctx.save();
            this.ctx.fillStyle = 'rgba(15, 23, 42, 0.9)';
            this.ctx.strokeStyle = 'rgba(59, 130, 246, 0.5)';
            this.ctx.lineWidth = 1;
            
            this.ctx.font = '12px system-ui';
            const textWidth = this.ctx.measureText(archetype).width;
            const boxWidth = textWidth + 16;
            const boxHeight = 20;
            
            const boxX = centerX - boxWidth / 2;
            const boxY = labelY - 15;
            
            this.ctx.beginPath();
            this.ctx.roundRect(boxX, boxY, boxWidth, boxHeight, 4);
            this.ctx.fill();
            this.ctx.stroke();
            
            this.ctx.fillStyle = '#e2e8f0';
            this.ctx.font = '12px system-ui';
            this.ctx.textAlign = 'center';
            this.ctx.textBaseline = 'middle';
            this.ctx.fillText(archetype, centerX, labelY - 5);
            
            this.ctx.restore();
        });
    }
    
    renderArchetypeList() {
        const container = document.getElementById('archetypeList');
        if (!container) return;
        
        container.innerHTML = '';
        
        this.archetypes.forEach(archetype => {
            const item = document.createElement('div');
            item.className = 'archetype-item';
            item.onclick = () => this.toggleArchetype(archetype.name);
            
            const visibleCount = this.filteredApps.filter(app => app.archetype === archetype.name).length;
            
            item.innerHTML = `<div class="archetype-name"><div class="archetype-color" style="background-color: ${archetype.color}"></div><span>${archetype.name}</span></div><div class="archetype-count">${visibleCount}</div>`;
            
            container.appendChild(item);
        });
    }
    
    renderLegend() {
        const container = document.getElementById('archetypeLegend');
        if (!container) return;
        
        container.innerHTML = '';
        
        this.archetypes.forEach(archetype => {
            const item = document.createElement('div');
            item.className = 'legend-item';
            item.innerHTML = `<div class="legend-color" style="background-color: ${archetype.color}"></div><span>${archetype.name}</span>`;
            container.appendChild(item);
        });
    }
    
    toggleArchetype(archetypeName) {
        if (this.selectedArchetypes.has(archetypeName)) {
            this.selectedArchetypes.delete(archetypeName);
        } else {
            this.selectedArchetypes.add(archetypeName);
        }
        this.applyFilters();
        this.updateArchetypeSelection();
    }
    
    updateArchetypeSelection() {
        const items = document.querySelectorAll('.archetype-item');
        items.forEach((item, index) => {
            const archetypeName = this.archetypes[index].name;
            if (this.selectedArchetypes.has(archetypeName)) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });
    }
    
    applyFilters() {
        this.filteredApps = this.applications.filter(app => {
            const matchesSearch = this.searchTerm === '' || 
                app.name.toLowerCase().includes(this.searchTerm) ||
                app.archetype.toLowerCase().includes(this.searchTerm);
            
            const matchesArchetype = this.selectedArchetypes.size === 0 || 
                this.selectedArchetypes.has(app.archetype);
            
            const matchesAppSelection = this.selectedApps.size === 0 || 
                this.selectedApps.has(app.id);
            
            return matchesSearch && matchesArchetype && matchesAppSelection;
        });
        
        this.renderArchetypeList();
        this.updateStats();
        this.render();
    }
    
    updateStats() {
        const totalApps = document.getElementById('totalApps');
        const classifiedApps = document.getElementById('classifiedApps');
        const archetypeCount = document.getElementById('archetypeCount');
        const visibleApps = document.getElementById('visibleApps');
        
        if (totalApps) totalApps.textContent = this.applications.length;
        if (classifiedApps) classifiedApps.textContent = this.applications.filter(app => app.archetype).length;
        if (archetypeCount) archetypeCount.textContent = this.archetypes.length;
        if (visibleApps) visibleApps.textContent = this.filteredApps.length;
    }
    
    handleMouseMove(e) {
        // Mouse move handling for canvas views
    }
    
    handleClick(e) {
        // Click handling for canvas views
    }
}

// Global functions for UI interaction - Attach to window for HTML access
window.toggleAppSelection = function(appId) {
    if (window.dashboard) {
        window.dashboard.toggleAppSelection(appId);
    }
};

window.selectAllFilteredApps = function() {
    if (window.dashboard) {
        window.dashboard.selectAllFilteredApps();
    }
};

window.clearAllSelectedApps = function() {
    if (window.dashboard) {
        window.dashboard.clearAllSelectedApps();
    }
};

window.removeAppSelection = function(appId) {
    if (window.dashboard) {
        window.dashboard.removeAppSelection(appId);
    }
};

window.setView = function(viewType) {
    if (window.dashboard) {
        console.log(`Switching to ${viewType} view`);
        window.dashboard.currentView = viewType;
        
        document.querySelectorAll('.view-controls .btn').forEach(btn => {
            btn.classList.remove('active');
        });
        
        const targetBtn = document.getElementById(viewType + 'Btn');
        if (targetBtn) targetBtn.classList.add('active');
        
        // Reset canvas retry count when switching views
        window.dashboard.canvasRetryCount = 0;
        
        // Force a re-render with proper timing
        setTimeout(() => {
            window.dashboard.render();
        }, 50);
    }
};

window.resetFilters = function() {
    if (window.dashboard) {
        window.dashboard.selectedArchetypes.clear();
        window.dashboard.selectedApps.clear();
        window.dashboard.searchTerm = '';
        const searchInput = document.getElementById('archetypeSearch');
        if (searchInput) {
            searchInput.value = '';
        }
        window.dashboard.applyFilters();
        window.dashboard.updateArchetypeSelection();
        window.dashboard.updateSelectedAppsDisplay();
    }
};

// Legacy function definitions for backward compatibility
function toggleAppSelection(appId) {
    window.toggleAppSelection(appId);
}

function selectAllFilteredApps() {
    window.selectAllFilteredApps();
}

function clearAllSelectedApps() {
    window.clearAllSelectedApps();
}

function removeAppSelection(appId) {
    window.removeAppSelection(appId);
}

function setView(viewType) {
    window.setView(viewType);
}

function resetFilters() {
    window.resetFilters();
}

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    window.dashboard = new NetworkBasedArchetypeClassificationDashboard();
});

// Canvas roundRect polyfill for older browsers
if (!CanvasRenderingContext2D.prototype.roundRect) {
    CanvasRenderingContext2D.prototype.roundRect = function (x, y, w, h, r) {
        if (w < 2 * r) r = w / 2;
        if (h < 2 * r) r = h / 2;
        this.beginPath();
        this.moveTo(x + r, y);
        this.arcTo(x + w, y, x + w, y + h, r);
        this.arcTo(x + w, y + h, x, y + h, r);
        this.arcTo(x, y + h, x, y, r);
        this.arcTo(x, y, x + w, y, r);
        this.closePath();
        return this;
    };
}

// Additional utility functions for enhanced functionality
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Enhanced search with debouncing
if (window.dashboard) {
    const debouncedSearch = debounce((query) => {
        window.dashboard.handleSearchInput(query);
    }, 300);
    
    // Replace existing search handler with debounced version
    const searchInput = document.getElementById('archetypeSearch');
    if (searchInput) {
        searchInput.removeEventListener('input', window.dashboard.handleSearchInput);
        searchInput.addEventListener('input', (e) => debouncedSearch(e.target.value));
    }
}

// Keyboard shortcuts for power users
document.addEventListener('keydown', (e) => {
    if (!window.dashboard) return;
    
    // Only activate shortcuts when not typing in input fields
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
    
    switch (e.key) {
        case '1':
            setView('cards');
            e.preventDefault();
            break;
        case '2':
            setView('cluster');
            e.preventDefault();
            break;
        case '3':
            setView('network');
            e.preventDefault();
            break;
        case '4':
            setView('hierarchy');
            e.preventDefault();
            break;
        case 'r':
        case 'R':
            resetFilters();
            e.preventDefault();
            break;
        case 'Escape':
            window.dashboard.hideAppDetails();
            window.dashboard.hideSearchDropdown();
            e.preventDefault();
            break;
    }
});

// Performance monitoring for large datasets
class PerformanceMonitor {
    constructor() {
        this.metrics = {
            renderTime: [],
            loadTime: 0,
            memoryUsage: []
        };
    }
    
    startRender() {
        this.renderStart = performance.now();
    }
    
    endRender() {
        if (this.renderStart) {
            const duration = performance.now() - this.renderStart;
            this.metrics.renderTime.push(duration);
            
            // Keep only last 100 measurements
            if (this.metrics.renderTime.length > 100) {
                this.metrics.renderTime.shift();
            }
            
            // Log slow renders
            if (duration > 100) {
                console.warn(`Slow render detected: ${duration.toFixed(2)}ms`);
            }
        }
    }
    
    getAverageRenderTime() {
        if (this.metrics.renderTime.length === 0) return 0;
        const sum = this.metrics.renderTime.reduce((a, b) => a + b, 0);
        return sum / this.metrics.renderTime.length;
    }
    
    logPerformance() {
        console.log('Performance Metrics:', {
            averageRenderTime: `${this.getAverageRenderTime().toFixed(2)}ms`,
            totalRenders: this.metrics.renderTime.length,
            loadTime: `${this.metrics.loadTime}ms`
        });
    }
}

// Initialize performance monitor
const performanceMonitor = new PerformanceMonitor();

// Enhanced error handling
window.addEventListener('error', (e) => {
    console.error('Application Error:', {
        message: e.message,
        filename: e.filename,
        lineno: e.lineno,
        colno: e.colno,
        error: e.error
    });
    
    // Show user-friendly error message
    const errorOverlay = document.createElement('div');
    errorOverlay.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #dc2626;
        color: white;
        padding: 12px 16px;
        border-radius: 8px;
        z-index: 10001;
        font-size: 14px;
        max-width: 400px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    `;
    errorOverlay.innerHTML = `
        <div style="font-weight: 600; margin-bottom: 4px;">Application Error</div>
        <div style="opacity: 0.9;">Something went wrong. Please refresh the page.</div>
        <button onclick="this.parentElement.remove()" style="
            position: absolute;
            top: 8px;
            right: 8px;
            background: none;
            border: none;
            color: white;
            cursor: pointer;
            font-size: 16px;
        ">×</button>
    `;
    document.body.appendChild(errorOverlay);
    
    // Auto-remove after 10 seconds
    setTimeout(() => {
        if (errorOverlay.parentElement) {
            errorOverlay.remove();
        }
    }, 10000);
});

// Browser compatibility checks
function checkBrowserCompatibility() {
    const issues = [];
    
    // Check for Canvas support
    if (!document.createElement('canvas').getContext) {
        issues.push('Canvas not supported');
    }
    
    // Check for Fetch API
    if (!window.fetch) {
        issues.push('Fetch API not supported');
    }
    
    // Check for ES6 features
    try {
        eval('const x = () => {}; class Y {}');
    } catch (e) {
        issues.push('ES6 features not supported');
    }
    
    if (issues.length > 0) {
        console.warn('Browser compatibility issues:', issues);
        
        const warningBanner = document.createElement('div');
        warningBanner.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: #f59e0b;
            color: #92400e;
            padding: 8px 16px;
            text-align: center;
            font-size: 14px;
            z-index: 10002;
        `;
        warningBanner.innerHTML = `
            ⚠️ Your browser may not fully support this application. Consider updating to a modern browser.
            <button onclick="this.parentElement.remove()" style="
                margin-left: 12px;
                background: none;
                border: 1px solid currentColor;
                color: inherit;
                padding: 2px 8px;
                border-radius: 4px;
                cursor: pointer;
            ">Dismiss</button>
        `;
        document.body.insertBefore(warningBanner, document.body.firstChild);
    }
}

// Run compatibility check on load
document.addEventListener('DOMContentLoaded', checkBrowserCompatibility);

// Data export functionality
function exportApplicationData(format = 'json') {
    if (!window.dashboard || !window.dashboard.applications) {
        console.error('No application data available for export');
        return;
    }
    
    const data = window.dashboard.applications;
    let exportData, filename, mimeType;
    
    switch (format.toLowerCase()) {
        case 'json':
            exportData = JSON.stringify(data, null, 2);
            filename = 'applications.json';
            mimeType = 'application/json';
            break;
            
        case 'csv':
            const headers = ['id', 'name', 'archetype', 'status', 'flowCount', 'primaryPorts'];
            const csvRows = [headers.join(',')];
            
            data.forEach(app => {
                const row = [
                    app.id,
                    `"${app.name}"`,
                    app.archetype,
                    app.status,
                    app.flowCount,
                    `"${app.primaryPorts.map(p => p.port).join(';')}"`
                ];
                csvRows.push(row.join(','));
            });
            
            exportData = csvRows.join('\n');
            filename = 'applications.csv';
            mimeType = 'text/csv';
            break;
            
        default:
            console.error('Unsupported export format:', format);
            return;
    }
    
    // Create and trigger download
    const blob = new Blob([exportData], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    
    console.log(`Exported ${data.length} applications to ${filename}`);
}

// Add export buttons to UI (if export container exists)
document.addEventListener('DOMContentLoaded', () => {
    const exportContainer = document.getElementById('exportContainer');
    if (exportContainer) {
        exportContainer.innerHTML = `
            <button onclick="exportApplicationData('json')" class="btn btn-secondary">
                Export JSON
            </button>
            <button onclick="exportApplicationData('csv')" class="btn btn-secondary">
                Export CSV
            </button>
        `;
    }
});

// Memory leak prevention
window.addEventListener('beforeunload', () => {
    if (window.dashboard) {
        // Clear any intervals or timeouts
        if (window.dashboard.updateInterval) {
            clearInterval(window.dashboard.updateInterval);
        }
        
        // Clear event listeners
        window.removeEventListener('resize', window.dashboard.handleResize);
        
        // Clear cache
        window.dashboard.dataCache = null;
        
        console.log('Dashboard cleanup completed');
    }
});

// Development helpers (only in development)
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    // Global access to dashboard for debugging
    window.debugDashboard = () => {
        console.log('Dashboard instance:', window.dashboard);
        console.log('Applications:', window.dashboard?.applications);
        console.log('Filtered apps:', window.dashboard?.filteredApps);
        console.log('Archetypes:', window.dashboard?.archetypes);
        performanceMonitor.logPerformance();
    };
    
    // Performance monitoring shortcut
    window.perf = performanceMonitor;
    
    console.log('Development mode detected. Available debug commands:');
    console.log('- debugDashboard() - Inspect dashboard state');
    console.log('- perf.logPerformance() - Show performance metrics');
    console.log('- exportApplicationData("json"|"csv") - Export data');
}

// Export for external use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { 
        NetworkBasedArchetypeClassificationDashboard,
        exportApplicationData,
        PerformanceMonitor
    };
}