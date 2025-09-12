/**
 * Application Data Manager - Complete Rewrite
 * Handles CSV loading, application management, and network topology generation
 * Self-contained with robust error handling and no external dependencies
 */

console.log('Loading rewritten app-data.js...');

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
        
        // Configuration
        this.config = {
            maxTrafficRows: 50000, // Limit for performance
            csvPaths: {
                applications: '/data_staging/applicationList.csv',
                traffic: '/data_staging/updated_normalized_synthetic_traffic.csv'
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
        console.log('Initializing Application Data Manager...');
        this.updateProgress(0, 'Starting initialization...');
        
        try {
            // Load applications first (always required)
            await this.loadApplications();
            this.updateProgress(50, 'Applications loaded, loading traffic data...');
            
            // Load traffic data (optional)
            await this.loadTrafficData();
            this.updateProgress(75, 'Generating network topology...');
            
            // Generate initial topology
            this.generateNetworkTopology();
            this.updateProgress(100, 'Initialization complete');
            
            this.isDataLoaded = true;
            this.lastUpdate = new Date();
            
            console.log(`Initialization complete: ${this.applications.length} apps, ${this.trafficData.length} traffic records`);
            
        } catch (error) {
            console.error('Initialization failed:', error);
            this.errors.push(`Initialization failed: ${error.message}`);
            this.createFallbackData();
        }
    }
    
    updateProgress(percentage, message) {
        this.loadingProgress = percentage;
        console.log(`Progress: ${percentage}% - ${message}`);
    }
    
    async loadApplications() {
        console.log('Loading applications from CSV...');
        
        try {
            const response = await fetch(this.config.csvPaths.applications);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const csvText = await response.text();
            console.log(`Applications CSV loaded: ${csvText.length} characters`);
            
            this.applications = this.parseApplicationsCSV(csvText);
            console.log(`Parsed ${this.applications.length} applications`);
            
        } catch (error) {
            console.error('Failed to load applications CSV:', error);
            this.errors.push(`Applications loading failed: ${error.message}`);
            this.createFallbackApplications();
        }
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
                            connectionCount: Math.floor(Math.random() * 100) + 10,
                            trafficVolume: Math.floor(Math.random() * 1000) + 100,
                            responseTime: Math.floor(Math.random() * 100) + 10
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
        console.log('Loading traffic data from CSV...');
        
        try {
            const response = await fetch(this.config.csvPaths.traffic);
            if (!response.ok) {
                console.warn(`Traffic data not available: HTTP ${response.status}`);
                return;
            }
            
            const csvText = await response.text();
            console.log(`Traffic CSV loaded: ${csvText.length} characters`);
            
            this.trafficData = this.parseTrafficCSV(csvText);
            console.log(`Parsed ${this.trafficData.length} traffic records`);
            
            // Enrich applications with traffic data
            this.enrichApplicationsWithTraffic();
            
        } catch (error) {
            console.warn('Traffic data loading failed (non-critical):', error);
            this.errors.push(`Traffic loading failed: ${error.message}`);
        }
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
        
        // Parse data rows with progress tracking
        for (let i = 1; i <= maxRows; i++) {
            if (i % 5000 === 0) {
                console.log(`Parsing traffic data: ${i}/${maxRows} rows`);
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
                
                // Only keep rows with meaningful data
                if (row.source_ip || row.destination_ip || row.protocol) {
                    trafficData.push(row);
                }
                
            } catch (rowError) {
                // Skip problematic rows silently
                if (i % 10000 === 0) {
                    console.warn(`Traffic parsing issues around row ${i}`);
                }
            }
        }
        
        return trafficData;
    }
    
    enrichApplicationsWithTraffic() {
        if (!this.trafficData.length) {
            console.log('No traffic data available for enrichment');
            return;
        }
        
        console.log('Enriching applications with traffic data...');
        
        // Create traffic summaries by application
        const trafficByApp = {};
        
        this.trafficData.forEach(record => {
            // Try to match traffic to applications (this is simplified)
            const appId = record.app_id || record.application_id || record.application;
            
            if (appId && !trafficByApp[appId]) {
                trafficByApp[appId] = {
                    totalRecords: 0,
                    uniqueIPs: new Set(),
                    protocols: new Set(),
                    ports: new Set()
                };
            }
            
            if (appId) {
                const summary = trafficByApp[appId];
                summary.totalRecords++;
                
                if (record.source_ip) summary.uniqueIPs.add(record.source_ip);
                if (record.destination_ip) summary.uniqueIPs.add(record.destination_ip);
                if (record.protocol) summary.protocols.add(record.protocol);
                if (record.port || record.dst_port) {
                    summary.ports.add(record.port || record.dst_port);
                }
            }
        });
        
        // Apply traffic data to applications
        this.applications.forEach(app => {
            const trafficSummary = trafficByApp[app.id];
            if (trafficSummary) {
                app.trafficRecords = trafficSummary.totalRecords;
                app.uniqueIPs = trafficSummary.uniqueIPs.size;
                app.observedProtocols = Array.from(trafficSummary.protocols);
                app.observedPorts = Array.from(trafficSummary.ports);
            }
        });
        
        console.log(`Enriched ${Object.keys(trafficByApp).length} applications with traffic data`);
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
            ? this.applications 
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
                    ip: `10.${Math.floor(appIndex / 254) + 1}.${(appIndex % 254) + 1}.${tierIndex + 10}`,
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
    
    // Fallback methods
    createFallbackData() {
        console.log('Creating fallback data...');
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
            dataSource: this.trafficData.length > 0 ? 'CSV with traffic' : 'CSV applications only'
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
            dataSource: 'applicationList.csv + traffic data',
            lastUpdate: this.lastUpdate ? this.lastUpdate.toISOString() : null,
            applicationCount: this.applications.length,
            trafficRecordCount: this.trafficData.length,
            hasTrafficData: this.trafficData.length > 0,
            version: '2.0.0',
            loadTime: this.lastUpdate ? this.lastUpdate.toISOString() : null,
            archetypeDistribution: this.getArchetypeDistribution(),
            criticalityDistribution: this.getCriticalityDistribution(),
            businessFunctionDistribution: this.getBusinessFunctionDistribution()
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
        console.log('Refreshing application data...');
        this.isDataLoaded = false;
        this.applications = [];
        this.trafficData = [];
        this.errors = [];
        await this.init();
        return this.getStatus();
    }
    
    // Topology management methods
    saveTopologyToFile() {
        const topologyData = {
            metadata: {
                generated: new Date().toISOString(),
                nodeCount: this.networkTopology.nodes?.length || 0,
                linkCount: this.networkTopology.links?.length || 0,
                applications: this.applications.length,
                version: '2.0.0',
                source: 'ApplicationDataManager'
            },
            topology: this.networkTopology,
            applications: this.applications.map(app => ({
                id: app.id,
                name: app.name,
                archetype: app.archetype,
                businessFunction: app.businessFunction,
                criticality: app.criticality
            })),
            selectedApps: window.topologyDashboard?.selectedApps || [],
            displayOptions: window.topologyDashboard?.displayOptions || {},
            showUpstream: window.topologyDashboard?.showUpstream || true,
            showDownstream: window.topologyDashboard?.showDownstream || true,
            layout: window.topologyDashboard?.currentLayout || 'force'
        };
        
        const blob = new Blob([JSON.stringify(topologyData, null, 2)], 
                             { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `topology_${new Date().toISOString().slice(0,19).replace(/:/g,'-')}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        
        URL.revokeObjectURL(url);
        console.log('Topology saved to file');
    }
    
    async loadSpecificTopology(filename) {
        try {
            const response = await fetch(`/saved_topologies/${filename}`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const topologyData = await response.json();
            
            // Load the network topology
            this.networkTopology = topologyData.topology;
            
            // Restore dashboard settings if available
            if (window.topologyDashboard && topologyData) {
                if (topologyData.selectedApps) {
                    window.topologyDashboard.selectedApps = topologyData.selectedApps;
                }
                
                if (topologyData.displayOptions) {
                    window.topologyDashboard.displayOptions = topologyData.displayOptions;
                }
                
                if (topologyData.showUpstream !== undefined) {
                    window.topologyDashboard.showUpstream = topologyData.showUpstream;
                }
                
                if (topologyData.showDownstream !== undefined) {
                    window.topologyDashboard.showDownstream = topologyData.showDownstream;
                }
                
                if (topologyData.layout) {
                    window.topologyDashboard.setLayout(topologyData.layout);
                }
                
                // Update the visualization
                window.topologyDashboard.render();
                window.topologyDashboard.updateStats();
            }
            
            console.log(`Loaded topology from ${filename}`);
            return true;
            
        } catch (error) {
            console.error('Failed to load topology:', error);
            this.errors.push(`Topology loading failed: ${error.message}`);
            return false;
        }
    }
}

// Initialize global AppData instance
console.log('Initializing global AppData...');

try {
    window.AppData = new ApplicationDataManager();
    console.log('AppData initialized successfully');
} catch (error) {
    console.error('Failed to initialize AppData:', error);
    
    // Create minimal fallback
    window.AppData = {
        isDataLoaded: false,
        applications: [],
        networkTopology: { nodes: [], links: [] },
        errors: [error.message],
        
        isReady: () => false,
        getStatus: () => ({ 
            isReady: false, 
            error: error.message,
            applicationCount: 0,
            trafficRecordCount: 0 
        }),
        loadData: () => Promise.reject(error),
        getApplicationNamesForFilter: () => [
            { id: 'all', name: 'ALL Applications', displayName: 'ALL Applications (0 total)' }
        ],
        generateNetworkTopology: () => ({ nodes: [], links: [] }),
        getMetadata: () => ({ error: error.message, version: '2.0.0' })
    };
}

// Auto-load on DOM ready
document.addEventListener('DOMContentLoaded', async () => {
    if (window.AppData && !window.AppData.isDataLoaded && window.AppData.loadData) {
        console.log('Auto-loading data on DOM ready...');
        try {
            await window.AppData.loadData();
            console.log('Auto-load completed successfully');
        } catch (error) {
            console.error('Auto-load failed:', error);
        }
    }
});

// Debug utilities
window.AppDataUtils = {
    refresh: () => window.AppData.refreshData(),
    status: () => window.AppData.getStatus(),
    apps: () => window.AppData.applications,
    search: (query) => window.AppData.searchApplications(query),
    metadata: () => window.AppData.getMetadata(),
    topology: () => window.AppData.networkTopology,
    generateTopology: (apps, options) => window.AppData.generateNetworkTopology(apps, options),
    saveTopology: () => window.AppData.saveTopologyToFile(),
    errors: () => window.AppData.errors
};

console.log('Rewritten app-data.js loaded successfully');
console.log('Features: CSV loading, traffic analysis, network topology, archetype classification');
console.log('Debug: Use AppDataUtils.status() to check status or AppDataUtils.errors() to see any issues');