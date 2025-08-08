// Enhanced Application Data Management with Smart Component Naming & localStorage Caching
// Merged version combining existing banking app logic with improved caching and data management

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
            
            // localStorage keys for caching
            this.STORAGE_KEYS = {
                APPLICATIONS: 'app_discovery_applications',
                NETWORK_DATA: 'app_discovery_network_data',
                LAST_UPDATE: 'app_discovery_last_update',
                VERSION: 'app_discovery_data_version'
            };
            
            // Data version for cache invalidation
            this.DATA_VERSION = '2.2.0';
            
            // Event listeners for data updates
            this.dataLoadedCallbacks = [];
            this.filterChangeCallbacks = [];
            
            this.nodeColorMap = {
                'Microservices': '#3b82f6',
                'SOA': '#10b981', 
                'Web + API Headless': '#f59e0b',
                'Monolithic': '#ef4444',
                '3-Tier': '#8b5cf6',
                'Event-Driven': '#06b6d4',
                'Client-Server': '#f97316'
            };
            
            // Initialize with enhanced loading
            this.init();
        }
        
        async init() {
            console.log('🔄 Initializing Enhanced Application Data Manager...');
            
            // Check if we have valid cached data
            if (this.hasCachedData() && this.isCacheValid()) {
                console.log('📦 Loading data from localStorage cache...');
                this.loadFromCache();
            } else {
                console.log('📁 No valid cache found, initializing with sample data...');
                await this.initializeWithSampleData();
            }
            
            this.setupFilterSync();
            console.log('✅ Enhanced Application Data Manager initialized');
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
            
            // Check version compatibility
            if (cachedVersion !== this.DATA_VERSION) {
                console.log('📊 Cache version mismatch, invalidating cache');
                return false;
            }
            
            // Check if cache is not too old (24 hours)
            if (lastUpdate) {
                const cacheAge = Date.now() - parseInt(lastUpdate);
                const maxAge = 24 * 60 * 60 * 1000; // 24 hours
                
                if (cacheAge > maxAge) {
                    console.log('⏰ Cache expired, will reload from source');
                    return false;
                }
            }
            
            return true;
        }
        
        saveToCache() {
            try {
                console.log('💾 Saving application data to localStorage...');
                
                localStorage.setItem(this.STORAGE_KEYS.APPLICATIONS, JSON.stringify(this.applications));
                localStorage.setItem(this.STORAGE_KEYS.NETWORK_DATA, JSON.stringify(this.networkTopology));
                localStorage.setItem(this.STORAGE_KEYS.LAST_UPDATE, Date.now().toString());
                localStorage.setItem(this.STORAGE_KEYS.VERSION, this.DATA_VERSION);
                
                console.log(`✅ Cached ${this.applications.length} applications and ${this.networkTopology.nodes.length} network nodes`);
            } catch (error) {
                console.error('❌ Failed to save to localStorage:', error);
                // If localStorage is full, clear old data and try again
                if (error.name === 'QuotaExceededError') {
                    this.clearCache();
                    console.log('🧹 Cleared cache due to quota exceeded, retrying...');
                    try {
                        this.saveToCache();
                    } catch (retryError) {
                        console.error('❌ Failed to save even after clearing cache:', retryError);
                    }
                }
            }
        }
        
        loadFromCache() {
            try {
                const cachedApps = localStorage.getItem(this.STORAGE_KEYS.APPLICATIONS);
                const cachedNetwork = localStorage.getItem(this.STORAGE_KEYS.NETWORK_DATA);
                const lastUpdate = localStorage.getItem(this.STORAGE_KEYS.LAST_UPDATE);
                
                if (cachedApps) {
                    this.applications = JSON.parse(cachedApps);
                    this.applicationList = this.applications; // Backward compatibility
                }
                
                if (cachedNetwork) {
                    this.networkTopology = JSON.parse(cachedNetwork);
                }
                
                if (lastUpdate) {
                    this.lastUpdate = new Date(parseInt(lastUpdate));
                }
                
                this.isDataLoaded = true;
                this.notifyDataLoaded();
                
                console.log(`📦 Loaded ${this.applications.length} applications from cache`);
                console.log(`📊 Cache last updated: ${this.lastUpdate?.toLocaleString()}`);
            } catch (error) {
                console.error('❌ Failed to load from cache:', error);
                // If cache is corrupted, clear it and load from source
                this.clearCache();
                this.initializeWithSampleData();
            }
        }
        
        clearCache() {
            console.log('🧹 Clearing localStorage cache...');
            Object.values(this.STORAGE_KEYS).forEach(key => {
                localStorage.removeItem(key);
            });
        }
        
        // ===========================
        // SAMPLE DATA INITIALIZATION (Enhanced)
        // ===========================
        
        async initializeWithSampleData() {
            // Enhanced banking applications with more realistic data
            this.applicationList = [
                { id: 'ACDA', name: 'ATM Check Card Disputes API' },
                { id: 'ALE', name: 'Advisor Locator Engine' },
                { id: 'AODSVY', name: 'AOD Survey' },
                { id: 'APSE', name: 'Appointment Setting (Timetrade)' },
                { id: 'ARA', name: 'Account Analysis Request Application' },
                { id: 'AV', name: 'Automated Vault' },
                { id: 'BCA', name: 'Branch Customer Authentication' },
                { id: 'BKO', name: 'Banko POC' },
                { id: 'BLND', name: 'BLEND SSI' },
                { id: 'BLZD', name: 'FICO/Blaze Decisioning -Rules Development' },
                { id: 'BLZE', name: 'FIXO Blace Decision Engine' },
                { id: 'BM', name: 'BLAZE BKFS MSP AGREGATED VARIABLES INPUT' },
                { id: 'BO', name: 'ACBS Loan Syndications - Datamart/Business Objects' },
                { id: 'BOD', name: 'Branch Operations Dashboard' },
                { id: 'BP', name: 'BankPro' },
                { id: 'BTIF', name: 'Branch Transaction Interface' },
                { id: 'CACS', name: 'Computer Assisted Collections System' },
                { id: 'CCPA', name: 'Contact Center Print Admin' },
                { id: 'CDD', name: 'Customer Due Diligence' },
                { id: 'CIPIV', name: 'CIP iView Reporting Application' },
                { id: 'CLSR', name: 'CRE Closer' },
                { id: 'DDPP', name: 'DataCard Data Preparation and Processing' },
                { id: 'EAPM', name: 'Enterprise Asset Portfolio Management' },
                { id: 'ELS', name: 'Electronic Lien Services' },
                { id: 'FAPI', name: 'Fraud API' },
                { id: 'FCMS', name: 'Fraud Case Management System' },
                { id: 'GWAY', name: 'Gateway Services' },
                { id: 'HCMS', name: 'Health Check Monitoring System' },
                { id: 'IDRP', name: 'Identity and Risk Profiling' },
                { id: 'KYCP', name: 'Know Your Customer Platform' }
            ].filter(app => app.id && app.id.trim() !== ''); // Remove any undefined or empty IDs
            
            // Generate enhanced sample topology based on realistic banking architecture
            this.generateSampleTopology();
            this.processApplicationData();
            this.generateNetworkTopology();
            this.saveToCache();
            this.isDataLoaded = true;
            this.lastUpdate = new Date();
            this.notifyDataLoaded();
            console.log(`Initialized with ${this.applicationList.length} banking applications`);
        }
        
        generateSampleTopology() {
            // Create sample applications with enhanced network metadata
            const realAppData = {
                'DDPP': { uniqueIPs: 2254, architecture: '3-Tier + Messaging', complexity: 'very-high' },
                'CACS': { uniqueIPs: 2000, architecture: 'Event-Driven', complexity: 'high' },
                'BLZE': { uniqueIPs: 1999, architecture: '3-Tier + Messaging', complexity: 'high' },
                'BP': { uniqueIPs: 1761, architecture: 'Event-Driven', complexity: 'high' },
                'APSE': { uniqueIPs: 1759, architecture: 'Event-Driven', complexity: 'high' },
                'CCPA': { uniqueIPs: 1750, architecture: '3-Tier Web App', complexity: 'high' },
                'ACDA': { uniqueIPs: 800, architecture: 'Dispute Processing', complexity: 'high' }
            };
            
            this.applications = this.applicationList.map((app, index) => {
                const archetypes = ['Microservices', 'SOA', 'Web + API Headless', 'Monolithic', '3-Tier', 'Event-Driven', 'Client-Server'];
                const tiers = ['Service', 'Web', 'Data', 'Gateway', 'Cache'];
                
                const archetype = archetypes[index % archetypes.length];
                const tier = tiers[index % tiers.length];
                
                // Use real data if available, otherwise generate
                const realData = realAppData[app.id];
                const complexity = realData?.complexity || 'medium';
                const realArchitecture = realData?.architecture || archetype;
                
                return {
                    id: app.id,
                    name: app.name,
                    app_id: app.id, // Backward compatibility
                    app_name: app.name, // Backward compatibility
                    archetype: archetype,
                    realArchitecture: realArchitecture,
                    tier: tier,
                    color: this.nodeColorMap[archetype],
                    behavior: this.getBehaviorFromArchetype(archetype),
                    protocol: 'TCP',
                    status: 'active',
                    criticality: this.determineCriticality(app.name),
                    owner: 'IT Team',
                    technology: this.determineTechnology(archetype),
                    businessFunction: this.inferBusinessFunction(app.name),
                    nodeCount: this.calculateNodesFromComplexity(complexity, app.id),
                    realComplexity: complexity,
                    realUniqueIPs: realData?.uniqueIPs || Math.floor(Math.random() * 500) + 100,
                    connections: Math.floor(Math.random() * 50) + 10,
                    uptime: Math.floor(Math.random() * 15) + 85,
                    responseTime: Math.floor(Math.random() * 200) + 50,
                    requestsPerSecond: Math.floor(Math.random() * 1000) + 100,
                    environment: 'production',
                    lastUpdated: new Date().toISOString(),
                    searchText: `${app.name} ${app.id} ${archetype}`.toLowerCase(),
                    isActive: true,
                    priority: this.calculatePriority({ name: app.name, criticality: this.determineCriticality(app.name) })
                };
            });
        }
        
        // ===========================
        // DATA PROCESSING & UTILITIES
        // ===========================
        
        processApplicationData() {
            // Add additional computed fields for enhanced functionality
            this.applications = this.applications.map(app => ({
                ...app,
                displayName: `${app.name} (${app.id})`,
                searchText: `${app.name} ${app.id} ${app.archetype} ${app.technology} ${app.businessFunction}`.toLowerCase(),
                isActive: app.status === 'active',
                priority: this.calculatePriority(app),
                dependencies: this.calculateDependencies(app.id)
            }));
            
            // Sort by priority and name
            this.applications.sort((a, b) => {
                if (a.priority !== b.priority) {
                    return b.priority - a.priority; // Higher priority first
                }
                return a.name.localeCompare(b.name);
            });
            
            // Set backward compatibility
            this.applicationList = this.applications;
        }
        
        calculatePriority(app) {
            let priority = 0;
            
            switch (app.criticality) {
                case 'critical': priority += 100; break;
                case 'high': priority += 50; break;
                case 'medium': priority += 25; break;
            }
            
            // Boost priority for certain business functions
            if (app.businessFunction === 'Risk & Compliance') priority += 20;
            if (app.businessFunction === 'Security & Identity') priority += 15;
            if (app.businessFunction === 'Payment Processing') priority += 10;
            
            return priority;
        }
        
        calculateDependencies(appId) {
            // Enhanced dependency calculation based on banking domain knowledge
            const deps = [];
            
            // Critical apps depend on fewer things
            const criticalApps = ['ACDA', 'FAPI', 'BCA', 'KYCP'];
            if (criticalApps.includes(appId)) {
                deps.push('GWAY'); // API Gateway
                if (appId !== 'BCA') deps.push('BCA'); // Authentication
            } else {
                // Other apps depend on critical services
                deps.push('GWAY', 'BCA');
                if (Math.random() > 0.5) deps.push('ACDA'); // Some depend on dispute handling
            }
            
            return deps.filter(dep => dep !== appId); // Don't depend on self
        }
        
        inferBusinessFunction(appName) {
            const functionMap = {
                'fraud': 'Risk & Compliance',
                'customer': 'Customer Management',
                'account': 'Account Services',
                'payment': 'Payment Processing',
                'transaction': 'Transaction Processing',
                'dispute': 'Dispute Resolution',
                'authentication': 'Security & Identity',
                'management': 'Operations',
                'dashboard': 'Reporting & Analytics'
            };
            
            const name = appName.toLowerCase();
            for (const [keyword, func] of Object.entries(functionMap)) {
                if (name.includes(keyword)) {
                    return func;
                }
            }
            return 'Core Banking'; // Default
        }
        
        // FIXED: Modified to ensure minimum nodes for specific applications
        calculateNodesFromComplexity(complexity, appId = null) {
            // Special handling for applications that must have databases
            const requiresDatabase = ['ACDA', 'FCMS', 'KYCP', 'CDD', 'IDRP', 'CACS', 'DDPP'];
            
            let nodeCount;
            switch (complexity) {
                case 'very-high': 
                    nodeCount = Math.floor(Math.random() * 3) + 5; // 5-7 nodes
                    break;
                case 'high': 
                    nodeCount = 4; // Always 4 nodes for high complexity 
                    break;
                case 'medium': 
                    nodeCount = Math.floor(Math.random() * 2) + 3; // 3-4 nodes
                    break;
                case 'low': 
                    nodeCount = 2; // 2 nodes
                    break;
                default: 
                    nodeCount = 4; // Default to 4 nodes for proper architecture
            }
            
            // FIXED: Ensure applications that require databases have at least 4 nodes
            if (appId && requiresDatabase.includes(appId) && nodeCount < 4) {
                console.log(`🔧 Fixed ${appId}: increased from ${nodeCount} to 4 nodes to include database`);
                nodeCount = 4;
            }
            
            return nodeCount;
        }
        
        getBehaviorFromArchetype(archetype) {
            const behaviorMap = {
                'Microservices': 'API',
                'SOA': 'Service',
                'Web + API Headless': 'Web',
                'Monolithic': 'Application',
                '3-Tier': 'Web',
                'Event-Driven': 'Event',
                'Client-Server': 'Client'
            };
            return behaviorMap[archetype] || 'Service';
        }
        
        async loadData() {
            console.log('Enhanced banking application data ready');
            return Promise.resolve();
        }
        
        determineCriticality(appName) {
            const criticalKeywords = ['bank', 'card', 'fraud', 'security', 'core', 'primary', 'authentication', 'dispute'];
            const appLower = appName.toLowerCase();
            
            if (criticalKeywords.some(keyword => appLower.includes(keyword))) {
                return 'critical';
            }
            return Math.random() > 0.5 ? 'high' : 'medium';
        }
        
        determineTechnology(archetype) {
            const techMap = {
                'Microservices': 'Docker/Kubernetes',
                'SOA': 'Enterprise Service Bus',
                'Web + API Headless': 'React/Node.js',
                'Monolithic': 'Java/.NET',
                '3-Tier': 'Traditional Web',
                'Event-Driven': 'Message Queues',
                'Client-Server': 'Desktop Application'
            };
            return techMap[archetype] || 'Unknown';
        }
        
        // ===========================
        // ENHANCED FILTER SUPPORT
        // ===========================
        
        getApplicationNamesForFilter() {
            // Enhanced filter with additional metadata
            const apps = [
                { id: 'all', name: 'ALL Applications', archetype: 'All', status: 'active' }
            ];
            
            // Add all applications with enhanced display information
            this.applicationList.forEach(app => {
                apps.push({
                    id: app.id,
                    name: app.id, // Show ID as primary identifier
                    fullName: app.name, // Keep full name for reference
                    displayName: `${app.name} (${app.id})`,
                    archetype: app.archetype || 'Unknown',
                    status: app.status || 'active',
                    criticality: app.criticality,
                    businessFunction: app.businessFunction,
                    technology: app.technology
                });
            });
            
            return apps;
        }
        
        // Enhanced filtering with multiple criteria
        filterApplications(criteria = {}) {
            let filtered = [...this.applications];
            
            if (criteria.archetypes && criteria.archetypes.length > 0) {
                filtered = filtered.filter(app => criteria.archetypes.includes(app.archetype));
            }
            
            if (criteria.criticality && criteria.criticality.length > 0) {
                filtered = filtered.filter(app => criteria.criticality.includes(app.criticality));
            }
            
            if (criteria.status && criteria.status.length > 0) {
                filtered = filtered.filter(app => criteria.status.includes(app.status));
            }
            
            if (criteria.businessFunction && criteria.businessFunction.length > 0) {
                filtered = filtered.filter(app => criteria.businessFunction.includes(app.businessFunction));
            }
            
            if (criteria.searchText) {
                const searchLower = criteria.searchText.toLowerCase();
                filtered = filtered.filter(app => 
                    app.searchText && app.searchText.includes(searchLower)
                );
            }
            
            return filtered;
        }
        
        // ===========================
        // NETWORK TOPOLOGY GENERATION (Enhanced)
        // ===========================
        
        generateNetworkTopology(selectedAppNames = ['all'], includeUpstream = true, includeDownstream = true) {
            if (!this.isDataLoaded) {
                console.warn('Data not loaded yet, returning empty topology');
                return { nodes: [], links: [] };
            }
            
            let baseSelectedApps = this.applications;
            
            // Filter applications by selected names
            if (!selectedAppNames.includes('all')) {
                baseSelectedApps = this.applications.filter(app => 
                    selectedAppNames.includes(app.id) || selectedAppNames.includes(app.name)
                );
            }
            
            if (baseSelectedApps.length === 0) {
                return { nodes: [], links: [] };
            }
            
            // Start with base selected apps
            let finalSelectedApps = [...baseSelectedApps];
            
            // Add upstream dependencies if enabled
            if (includeUpstream) {
                const upstreamApps = this.getUpstreamApps(baseSelectedApps);
                finalSelectedApps = [...finalSelectedApps, ...upstreamApps];
            }
            
            // Add downstream dependencies if enabled  
            if (includeDownstream) {
                const downstreamApps = this.getDownstreamApps(baseSelectedApps);
                finalSelectedApps = [...finalSelectedApps, ...downstreamApps];
            }
            
            // Remove duplicates
            finalSelectedApps = finalSelectedApps.filter((app, index, self) => 
                index === self.findIndex(a => a.id === app.id)
            );
            
            // Generate nodes and links for final app set
            const nodes = [];
            const links = [];
            const nodeMap = new Map();
            
            finalSelectedApps.forEach((app, appIndex) => {
                const nodeCount = app.nodeCount || 4;
                const appNodes = [];
                
                // Debug logging for ACDA
                if (app.id === 'ACDA') {
                    console.log(`🔍 ACDA Debug: nodeCount=${nodeCount}, complexity=${app.realComplexity}, architecture=${app.realArchitecture}`);
                }
                
                for (let i = 0; i < nodeCount; i++) {
                    const subnet = 10 + (appIndex % 245);
                    const host = 10 + i;
                    const nodeId = `${subnet}.0.3.${host}`;
                    
                    const nodeType = this.getNodeTypeFromIndex(i, nodeCount, app.realArchitecture);
                    const componentName = this.getComponentNameForApp(app.id, nodeType, i);
                    
                    // Debug logging for ACDA components
                    if (app.id === 'ACDA') {
                        console.log(`🔍 ACDA Component ${i}: ${nodeType} -> ${componentName}`);
                    }
                    
                    const node = {
                        id: nodeId,
                        name: componentName,
                        ip: nodeId,
                        application: app.name,
                        applicationId: app.id,
                        archetype: app.archetype,
                        realArchitecture: app.realArchitecture,
                        tier: nodeType,
                        componentType: nodeType,
                        color: this.getColorForNodeType(nodeType),
                        type: nodeType,
                        status: 'active',
                        criticality: app.criticality,
                        owner: app.owner,
                        technology: this.getTechnologyForNodeType(nodeType),
                        ports: this.getPortsForNodeType(nodeType, [3000, 8080, 443]),
                        uptime: app.uptime,
                        responseTime: app.responseTime + (i * 10),
                        connections: 0,
                        requestsPerSecond: Math.floor(app.requestsPerSecond / nodeCount),
                        size: 10 + (app.realComplexity === 'very-high' ? 6 : app.realComplexity === 'high' ? 4 : 2),
                        isInternal: true,
                        realUniqueIPs: app.realUniqueIPs,
                        description: this.getComponentDescription(app.id, nodeType),
                        role: this.getComponentRole(nodeType),
                        isBaseSelected: baseSelectedApps.some(base => base.id === app.id),
                        businessFunction: app.businessFunction,
                        environment: app.environment || 'production',
                        cpu: Math.floor(Math.random() * 80),
                        memory: Math.floor(Math.random() * 90)
                    };
                    
                    nodes.push(node);
                    appNodes.push(node);
                    nodeMap.set(nodeId, node);
                }
                
                // Create internal links - ALWAYS included regardless of upstream/downstream
                this.createInternalLinks(appNodes, app, links);
            });
            
            // Create inter-application links only between included apps
            this.createInterAppLinks(finalSelectedApps, nodes, links, includeUpstream, includeDownstream);
            
            // Update connection counts
            links.forEach(link => {
                const sourceNode = nodeMap.get(link.source);
                const targetNode = nodeMap.get(link.target);
                if (sourceNode) sourceNode.connections++;
                if (targetNode) targetNode.connections++;
            });
            
            const interAppLinks = links.filter(l => !l.isInternal).length;
            const internalLinks = links.filter(l => l.isInternal).length;
            
            console.log(`Generated topology: ${nodes.length} nodes, ${links.length} links for ${finalSelectedApps.length} applications`);
            console.log(`Base selected: ${baseSelectedApps.length}, Internal: ${internalLinks}, Inter-app: ${interAppLinks}`);
            
            // Debug logging for ACDA nodes
            const acdaNodes = nodes.filter(n => n.applicationId === 'ACDA');
            if (acdaNodes.length > 0) {
                console.log(`✅ ACDA has ${acdaNodes.length} nodes:`, acdaNodes.map(n => `${n.name} (${n.tier})`));
                const hasDatabase = acdaNodes.some(n => n.tier === 'storage');
                console.log(`✅ ACDA has database: ${hasDatabase}`);
            }
            
            return { nodes, links };
        }
        
        getUpstreamApps(selectedApps) {
            const bankingDependencies = this.getBankingDependencies();
            const upstreamApps = [];
            
            selectedApps.forEach(app => {
                const deps = bankingDependencies[app.id];
                if (deps && deps.upstream) {
                    deps.upstream.forEach(upstreamAppId => {
                        const upstreamApp = this.applications.find(a => a.id === upstreamAppId);
                        if (upstreamApp && !selectedApps.some(s => s.id === upstreamAppId)) {
                            upstreamApps.push(upstreamApp);
                        }
                    });
                }
            });
            
            return upstreamApps;
        }
        
        getDownstreamApps(selectedApps) {
            const bankingDependencies = this.getBankingDependencies();
            const downstreamApps = [];
            
            selectedApps.forEach(app => {
                const deps = bankingDependencies[app.id];
                if (deps && deps.downstream) {
                    deps.downstream.forEach(downstreamAppId => {
                        const downstreamApp = this.applications.find(a => a.id === downstreamAppId);
                        if (downstreamApp && !selectedApps.some(s => s.id === downstreamAppId)) {
                            downstreamApps.push(downstreamApp);
                        }
                    });
                }
            });
            
            return downstreamApps;
        }
        
        getBankingDependencies() {
            return {
                'BCA': { // Branch Customer Authentication - foundational
                    upstream: [],
                    downstream: ['ACDA', 'FAPI', 'ALE', 'KYCP', 'BP', 'APSE', 'AV']
                },
                'FAPI': { // Fraud API
                    upstream: ['BCA'],
                    downstream: ['ACDA', 'FCMS']
                },
                'ACDA': { // ATM Check Card Disputes API
                    upstream: ['BCA', 'FAPI'],
                    downstream: ['FCMS']
                },
                'FCMS': { // Fraud Case Management System
                    upstream: ['ACDA', 'FAPI'],
                    downstream: []
                },
                'KYCP': { // Know Your Customer Platform
                    upstream: ['BCA'],
                    downstream: ['ALE', 'IDRP']
                },
                'ALE': { // Advisor Locator Engine
                    upstream: ['BCA', 'KYCP'],
                    downstream: []
                },
                'IDRP': { // Identity and Risk Profiling
                    upstream: ['KYCP', 'BCA'],
                    downstream: []
                },
                'BP': { // BankPro
                    upstream: ['BCA'],
                    downstream: ['BOD']
                },
                'BOD': { // Branch Operations Dashboard
                    upstream: ['BP', 'BCA'],
                    downstream: []
                },
                'BLZE': { // Decision Engine
                    upstream: ['BCA'],
                    downstream: ['BLZD']
                },
                'BLZD': { // Rules Development
                    upstream: ['BLZE'],
                    downstream: []
                },
                'APSE': { // Appointments
                    upstream: ['BCA', 'ALE'],
                    downstream: []
                },
                'AV': { // Automated Vault
                    upstream: ['BCA'],
                    downstream: []
                }
            };
        }
        
        createInterAppLinks(selectedApps, nodes, links, includeUpstream, includeDownstream) {
            const bankingDependencies = this.getBankingDependencies();
            
            selectedApps.forEach(sourceApp => {
                const deps = bankingDependencies[sourceApp.id];
                if (!deps) return;
                
                const sourceNodes = nodes.filter(n => n.applicationId === sourceApp.id);
                if (sourceNodes.length === 0) return;
                
                const sourceNode = sourceNodes.find(n => n.tier === 'gateway') || 
                                  sourceNodes.find(n => n.tier === 'api-gateway') || 
                                  sourceNodes[0];
                
                // Create downstream connections only if downstream apps are included
                if (deps.downstream && includeDownstream) {
                    deps.downstream.forEach(targetAppId => {
                        const targetApp = selectedApps.find(a => a.id === targetAppId);
                        if (!targetApp) return;
                        
                        const targetNodes = nodes.filter(n => n.applicationId === targetAppId);
                        if (targetNodes.length === 0) return;
                        
                        const targetNode = targetNodes.find(n => n.tier === 'gateway') || 
                                          targetNodes.find(n => n.tier === 'api-gateway') || 
                                          targetNodes[0];
                        
                        links.push({
                            source: sourceNode.id,
                            target: targetNode.id,
                            type: 'HTTPS',
                            direction: 'downstream',
                            bandwidth: Math.floor(Math.random() * 600) + 400,
                            latency: Math.floor(Math.random() * 20) + 10,
                            status: 'active',
                            protocol: 'HTTPS',
                            port: 443,
                            application: `${sourceApp.name} → ${targetApp.name}`,
                            info: `${sourceApp.id} provides services to ${targetApp.id}`,
                            isInternal: false
                        });
                    });
                }
                
                // Create upstream connections only if upstream apps are included
                if (deps.upstream && includeUpstream) {
                    deps.upstream.forEach(upstreamAppId => {
                        const upstreamApp = selectedApps.find(a => a.id === upstreamAppId);
                        if (!upstreamApp) return;
                        
                        const upstreamNodes = nodes.filter(n => n.applicationId === upstreamAppId);
                        if (upstreamNodes.length === 0) return;
                        
                        const upstreamNode = upstreamNodes.find(n => n.tier === 'gateway') || 
                                            upstreamNodes.find(n => n.tier === 'api-gateway') || 
                                            upstreamNodes[0];
                        
                        links.push({
                            source: upstreamNode.id,
                            target: sourceNode.id,
                            type: 'HTTPS',
                            direction: 'downstream',
                            bandwidth: Math.floor(Math.random() * 600) + 400,
                            latency: Math.floor(Math.random() * 20) + 10,
                            status: 'active',
                            protocol: 'HTTPS',
                            port: 443,
                            application: `${upstreamApp.name} → ${sourceApp.name}`,
                            info: `${upstreamApp.id} provides services to ${sourceApp.id}`,
                            isInternal: false
                        });
                    });
                }
            });
        }
        
        getNodeTypeFromIndex(index, totalNodes, architecture) {
            if (totalNodes === 1) return 'monolith';
            
            switch (architecture) {
                case '3-Tier Web App':
                case '3-Tier + Messaging':
                    if (index === 0) return 'web-tier';
                    if (index === 1) return 'app-tier';
                    if (index === 2) return 'data-tier';
                    if (index === 3) return 'messaging';
                    return 'service';
                    
                case 'Event-Driven':
                    if (index === 0) return 'api-gateway';
                    if (index === 1) return 'event-bus';
                    if (index === 2) return 'processor';
                    if (index === 3) return 'storage';
                    return 'worker';
                    
                case 'Microservices':
                    if (index === 0) return 'gateway';
                    if (index === 1) return 'core-service';
                    if (index === 2) return 'data-service';
                    if (index === 3) return 'storage';
                    return 'service';
                    
                case 'Dispute Processing': // Special case for ACDA
                    if (index === 0) return 'gateway';
                    if (index === 1) return 'processor';
                    if (index === 2) return 'data-service';
                    if (index === 3) return 'storage';
                    return 'component';
                    
                default:
                    // Default pattern for any app - ensure 4 components
                    if (index === 0) return 'gateway';
                    if (index === 1) return 'processor';
                    if (index === 2) return 'data-service';
                    if (index === 3) return 'storage';
                    return 'component';
            }
        }
        
        getComponentNameForApp(appId, componentType, index) {
            const componentNames = this.generateGenericComponentNames(appId, componentType);
            return componentNames[componentType] || `${appId}-${componentType}`;
        }
        
        generateGenericComponentNames(appId, componentType) {
            const businessDomain = this.inferBusinessDomain(appId);
            
            const domainTemplates = {
                'dispute': {
                    'gateway': `${appId}-Gateway`,
                    'processor': `${appId}-Processor`,
                    'data-service': `${appId}-Records`,
                    'storage': `${appId}-Database`
                },
                'auth': {
                    'frontend': `${appId}-Portal`,
                    'backend': `${appId}-Engine`, 
                    'database': `${appId}-Store`,
                    'gateway': `${appId}-Gateway`,
                    'core-service': `${appId}-Validator`,
                    'data-service': `${appId}-Directory`,
                    'auth-service': `${appId}-Authenticator`
                },
                'fraud': {
                    'api-gateway': `${appId}-Gateway`,
                    'event-bus': `${appId}-AlertBus`,
                    'processor': `${appId}-Detector`,
                    'storage': `${appId}-PatternDB`,
                    'core-service': `${appId}-Engine`,
                    'data-service': `${appId}-Analytics`
                },
                'generic': {
                    'gateway': `${appId}-Gateway`,
                    'processor': `${appId}-Engine`,
                    'data-service': `${appId}-Data`,
                    'storage': `${appId}-Storage`,
                    'web-tier': `${appId}-Web`,
                    'app-tier': `${appId}-App`,
                    'data-tier': `${appId}-DB`,
                    'messaging': `${appId}-Queue`,
                    'api-gateway': `${appId}-Gateway`,
                    'event-bus': `${appId}-Events`,
                    'core-service': `${appId}-Core`,
                    'auth-service': `${appId}-Auth`,
                    'frontend': `${appId}-UI`,
                    'backend': `${appId}-Service`,
                    'database': `${appId}-DB`,
                    'component': `${appId}-Component`,
                    'service': `${appId}-Service`,
                    'worker': `${appId}-Worker`,
                    'monolith': appId
                }
            };
            
            return domainTemplates[businessDomain] || domainTemplates['generic'];
        }
        
        inferBusinessDomain(appId) {
            const appIdLower = appId.toLowerCase();
            
            // Authentication patterns
            if (appIdLower.includes('auth') || appIdLower.includes('login') || 
                appIdLower.includes('bca') || appIdLower.includes('customer') && appIdLower.includes('auth')) {
                return 'auth';
            }
            
            // Fraud patterns
            if (appIdLower.includes('fraud') || appIdLower.includes('fapi') || 
                appIdLower.includes('security') || appIdLower.includes('alert')) {
                return 'fraud';
            }
            
            // Dispute patterns
            if (appIdLower.includes('dispute') || appIdLower.includes('acda') || 
                appIdLower.includes('card') && appIdLower.includes('dispute')) {
                return 'dispute';
            }
            
            return 'generic';
        }
        
        // Continue with remaining methods from original implementation...
        getComponentDescription(appId, componentType) {
            const businessDomain = this.inferBusinessDomain(appId);
            
            const domainDescriptions = {
                'dispute': {
                    'gateway': 'Dispute processing API gateway',
                    'processor': 'Dispute resolution engine',
                    'data-service': 'Transaction and dispute records',
                    'storage': 'Dispute database and document storage'
                },
                'generic': {
                    'gateway': 'Service gateway and load balancer',
                    'processor': 'Core processing and computation engine',
                    'data-service': 'Data access and management service',
                    'storage': 'Data storage and retrieval system',
                    'web-tier': 'Web interface and presentation layer',
                    'app-tier': 'Business logic and application processing',
                    'data-tier': 'Data storage and persistence layer',
                    'messaging': 'Message queuing and event processing',
                    'api-gateway': 'API routing and request management',
                    'event-bus': 'Event streaming and message distribution',
                    'core-service': 'Core business logic service',
                    'auth-service': 'Authentication and authorization service',
                    'frontend': 'User interface and presentation',
                    'backend': 'Application server and business logic',
                    'database': 'Database and data persistence',
                    'monolith': 'Monolithic application system'
                }
            };
            
            const descriptions = domainDescriptions[businessDomain] || domainDescriptions['generic'];
            return descriptions[componentType] || `${componentType} component for ${businessDomain} domain`;
        }
        
        getComponentRole(componentType) {
            const roles = {
                'web-tier': 'Frontend',
                'app-tier': 'Backend', 
                'data-tier': 'Database',
                'messaging': 'Message Queue',
                'api-gateway': 'Gateway',
                'event-bus': 'Event Stream',
                'processor': 'Processing Engine',
                'storage': 'Data Store',
                'gateway': 'Load Balancer',
                'core-service': 'Core Service',
                'data-service': 'Data Service',
                'auth-service': 'Auth Service',
                'frontend': 'User Interface',
                'backend': 'Application Server',
                'database': 'Database Server',
                'monolith': 'Monolithic Application'
            };
            
            return roles[componentType] || componentType;
        }
        
        getTechnologyForNodeType(nodeType) {
            const tech = {
                'web-tier': 'React/Angular + Nginx',
                'app-tier': 'Java Spring/Node.js',
                'data-tier': 'PostgreSQL/MongoDB',
                'messaging': 'RabbitMQ/Apache Kafka',
                'api-gateway': 'Kong/Zuul Gateway',
                'event-bus': 'Apache Kafka/EventBridge',
                'processor': 'Java/Python Analytics',
                'storage': 'PostgreSQL/Elasticsearch',
                'gateway': 'NGINX/HAProxy',
                'core-service': 'Java Microservice',
                'data-service': 'Spring Data/Hibernate',
                'auth-service': 'OAuth2/JWT Service',
                'frontend': 'React/Vue.js',
                'backend': 'Spring Boot/Express',
                'database': 'PostgreSQL/MySQL',
                'monolith': 'Legacy Java/C#'
            };
            return tech[nodeType] || 'Unknown Technology';
        }
        
        getColorForNodeType(nodeType) {
            const colors = {
                'web-tier': '#3b82f6',      // Blue for web
                'app-tier': '#10b981',      // Green for application
                'data-tier': '#f59e0b',     // Orange for database
                'messaging': '#06b6d4',     // Cyan for messaging
                'api-gateway': '#8b5cf6',   // Purple for gateways
                'event-bus': '#06b6d4',     // Cyan for events
                'processor': '#10b981',     // Green for processing
                'storage': '#f59e0b',       // Orange for storage
                'gateway': '#8b5cf6',       // Purple for gateways
                'core-service': '#ef4444',  // Red for core services
                'data-service': '#f59e0b',  // Orange for data services
                'auth-service': '#7c3aed',  // Deep purple for auth
                'frontend': '#3b82f6',      // Blue for frontend
                'backend': '#10b981',       // Green for backend
                'database': '#f59e0b',      // Orange for database
                'monolith': '#64748b'       // Gray for monolith
            };
            return colors[nodeType] || '#64748b';
        }
        
        getPortsForNodeType(nodeType, appPorts) {
            const defaultPorts = {
                'web-tier': [80, 443],
                'app-tier': [8080, 8443],
                'data-tier': [3306, 5432, 1433],
                'messaging': [5672, 9092],
                'api-gateway': [9080, 9443],
                'event-bus': [5672, 9092],
                'processor': [8080, 8443],
                'storage': [3306, 5432],
                'gateway': [80, 443, 9080],
                'core-service': [3000, 3001, 3002],
                'data-service': [8080, 8443],
                'auth-service': [9000, 9443],
                'frontend': [80, 443],
                'backend': [8080, 8443],
                'database': [3306, 5432],
                'monolith': [80, 8080]
            };
            
            return appPorts && appPorts.length > 0 ? appPorts.slice(0, 3) : defaultPorts[nodeType] || [8080];
        }
        
        createInternalLinks(appNodes, app, links) {
            if (appNodes.length < 2) return;
            
            // Create realistic internal architecture flows
            switch (app.realArchitecture) {
                case '3-Tier Web App':
                case '3-Tier + Messaging':
                case 'Dispute Processing': // Handle ACDA architecture
                    this.create3TierLinks(appNodes, links, app);
                    break;
                case 'Event-Driven':
                    this.createEventDrivenLinks(appNodes, links, app);
                    break;
                case 'Microservices':
                    this.createMicroserviceLinks(appNodes, links, app);
                    break;
                default:
                    this.createDefaultLinks(appNodes, links, app);
            }
        }
        
        create3TierLinks(nodes, links, app) {
            // Web -> App -> Database flow
            for (let i = 0; i < nodes.length - 1; i++) {
                links.push({
                    source: nodes[i].id,
                    target: nodes[i + 1].id,
                    type: 'HTTP',
                    direction: 'downstream',
                    bandwidth: Math.floor(Math.random() * 500) + 300,
                    latency: Math.floor(Math.random() * 5) + 1,
                    status: 'active',
                    protocol: 'HTTP',
                    port: 8080,
                    application: `${app.name} (${nodes[i].tier} → ${nodes[i + 1].tier})`,
                    info: `3-tier internal flow`,
                    isInternal: true
                });
            }
        }
        
        createEventDrivenLinks(nodes, links, app) {
            const messageQueue = nodes.find(n => n.tier === 'event-bus');
            if (messageQueue) {
                nodes.filter(n => n.tier !== 'event-bus').forEach(node => {
                    links.push({
                        source: node.id,
                        target: messageQueue.id,
                        type: 'AMQP',
                        direction: 'bidirectional',
                        bandwidth: Math.floor(Math.random() * 400) + 200,
                        latency: Math.floor(Math.random() * 3) + 1,
                        status: 'active',
                        protocol: 'AMQP',
                        port: 5672,
                        application: `${app.name} (event-driven)`,
                        info: `Event messaging`,
                        isInternal: true
                    });
                });
            } else {
                this.createDefaultLinks(nodes, links, app);
            }
        }
        
        createMicroserviceLinks(nodes, links, app) {
            const gateway = nodes.find(n => n.tier === 'gateway');
            if (gateway) {
                nodes.filter(n => n.tier !== 'gateway').forEach(service => {
                    links.push({
                        source: gateway.id,
                        target: service.id,
                        type: 'HTTP',
                        direction: 'downstream',
                        bandwidth: Math.floor(Math.random() * 300) + 100,
                        latency: Math.floor(Math.random() * 10) + 2,
                        status: 'active',
                        protocol: 'HTTP',
                        port: 3000,
                        application: `${app.name} (microservice)`,
                        info: `API Gateway routing`,
                        isInternal: true
                    });
                });
            }
        }
        
        createDefaultLinks(nodes, links, app) {
            for (let i = 0; i < nodes.length - 1; i++) {
                links.push({
                    source: nodes[i].id,
                    target: nodes[i + 1].id,
                    type: 'HTTP',
                    direction: 'downstream',
                    bandwidth: Math.floor(Math.random() * 400) + 100,
                    latency: Math.floor(Math.random() * 8) + 2,
                    status: 'active',
                    protocol: 'HTTP',
                    port: 8080,
                    application: `${app.name} (${nodes[i].name} → ${nodes[i + 1].name})`,
                    info: `Internal ${app.id} communication`,
                    isInternal: true
                });
            }
            
            if (nodes.length >= 3) {
                links.push({
                    source: nodes[0].id,
                    target: nodes[nodes.length - 1].id,
                    type: 'TCP',
                    direction: 'bidirectional',
                    bandwidth: Math.floor(Math.random() * 200) + 50,
                    latency: Math.floor(Math.random() * 5) + 1,
                    status: 'active',
                    protocol: 'TCP',
                    port: 3306,
                    application: `${app.name} (${nodes[0].name} ↔ ${nodes[nodes.length - 1].name})`,
                    info: `Direct access for ${app.id}`,
                    isInternal: true
                });
            }
        }
        
        // ===========================
        // DATA ACCESS METHODS (Enhanced)
        // ===========================
        
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
        
        getApplicationFlow(appId, includeUpstream = true, includeDownstream = true) {
            const app = this.getApplicationById(appId);
            if (!app) {
                return { nodes: [], links: [] };
            }
            
            return this.generateNetworkTopology([app.id], includeUpstream, includeDownstream);
        }
        
        // ===========================
        // EVENT SYSTEM
        // ===========================
        
        onDataLoaded(callback) {
            this.dataLoadedCallbacks.push(callback);
            // If data is already loaded, call immediately
            if (this.isDataLoaded) {
                callback();
            }
        }
        
        onFilterChange(callback) {
            this.filterChangeCallbacks.push(callback);
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
        
        notifyFilterChange(filterData) {
            this.filterChangeCallbacks.forEach(callback => {
                try {
                    callback(filterData);
                } catch (error) {
                    console.error('Error in filter change callback:', error);
                }
            });
        }
        
        setupFilterSync() {
            // Listen for custom events to sync filters across tabs
            window.addEventListener('appFilterChanged', (event) => {
                this.notifyFilterChange(event.detail);
            });
            
            // Sync filter changes across browser tabs using localStorage
            window.addEventListener('storage', (event) => {
                if (event.key === 'app_filter_sync') {
                    const filterData = JSON.parse(event.newValue || '{}');
                    this.notifyFilterChange(filterData);
                }
            });
        }
        
        syncFilterAcrossComponents(filterData) {
            // Dispatch event for current tab
            const customEvent = new CustomEvent('appFilterChanged', { detail: filterData });
            window.dispatchEvent(customEvent);
            
            // Sync across browser tabs
            localStorage.setItem('app_filter_sync', JSON.stringify({
                ...filterData,
                timestamp: Date.now()
            }));
        }
        
        // ===========================
        // CACHE MANAGEMENT METHODS
        // ===========================
        
        async refreshData() {
            console.log('🔄 Refreshing application data...');
            this.clearCache();
            await this.initializeWithSampleData();
            return {
                status: 'success',
                message: 'Data refreshed successfully',
                count: this.applications.length,
                timestamp: new Date().toISOString()
            };
        }
        
        getCacheInfo() {
            return {
                hasCache: this.hasCachedData(),
                isValid: this.isCacheValid(),
                lastUpdate: this.lastUpdate,
                version: this.DATA_VERSION,
                applicationCount: this.applications.length,
                nodeCount: this.networkTopology.nodes.length,
                linkCount: this.networkTopology.links.length
            };
        }
        
        exportData() {
            return {
                applications: this.applications,
                networkTopology: this.networkTopology,
                metadata: {
                    exportDate: new Date().toISOString(),
                    version: this.DATA_VERSION,
                    totalApplications: this.applications.length,
                    totalNodes: this.networkTopology.nodes.length,
                    totalLinks: this.networkTopology.links.length
                }
            };
        }
        
        importData(data) {
            if (data.applications) {
                this.applications = data.applications;
                this.applicationList = this.applications;
            }
            
            if (data.networkTopology) {
                this.networkTopology = data.networkTopology;
            }
            
            this.saveToCache();
            this.isDataLoaded = true;
            this.lastUpdate = new Date();
            this.notifyDataLoaded();
            
            console.log(`📥 Imported ${this.applications.length} applications`);
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
    
    // Notify topology dashboard that data is ready and update filter
    if (window.topologyDashboard) {
        window.topologyDashboard.populateApplicationFilter();
        window.topologyDashboard.updateNetworkData();
        window.topologyDashboard.render();
        window.topologyDashboard.updateStats();
    }
});

// Auto-refresh data periodically (every 30 minutes)
setInterval(() => {
    if (window.AppData && window.AppData.isDataLoaded) {
        const cacheAge = Date.now() - (window.AppData.lastUpdate?.getTime() || 0);
        const maxAge = 30 * 60 * 1000; // 30 minutes
        
        if (cacheAge > maxAge) {
            console.log('🔄 Auto-refreshing data due to age...');
            window.AppData.refreshData();
        }
    }
}, 5 * 60 * 1000); // Check every 5 minutes

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ApplicationDataManager };
}

console.log('📦 Enhanced Application Data Manager with localStorage caching and banking logic loaded');