// ================================================================================
// CSV DATA LOADER FOR TOPOLOGY VISUALIZATION
// File: js/csv-data-loader.js
// ================================================================================

class CSVDataLoader {
    constructor() {
        this.csvData = null;
        this.processedData = null;
        this.applications = new Map();
        this.nodes = new Map();
        this.links = new Map();
        this.isLoaded = false;
    }

    // Load CSV file from the specified path
    async loadCSVData(filePath = '../data_staging/updated_normalized_synthetic_traffic.csv') {
        try {
            console.log('📂 Loading CSV data from:', filePath);
            
            // For web environment, we need to fetch the file
            const response = await fetch(filePath);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const csvText = await response.text();
            
            // Parse CSV using PapaParse
            const results = Papa.parse(csvText, {
                header: true,
                dynamicTyping: true,
                skipEmptyLines: true,
                transformHeader: (header) => header.trim() // Clean headers
            });

            if (results.errors.length > 0) {
                console.warn('⚠️ CSV parsing warnings:', results.errors);
            }

            this.csvData = results.data;
            console.log(`✅ Loaded ${this.csvData.length} records from CSV`);
            
            // Process the data for topology visualization
            this.processCSVData();
            this.isLoaded = true;
            
            return this.processedData;
            
        } catch (error) {
            console.error('❌ Error loading CSV data:', error);
            // Fallback to demo data
            this.generateFallbackData();
            return this.processedData;
        }
    }

    // Process CSV data into topology format
    processCSVData() {
        console.log('🔄 Processing CSV data for topology visualization...');
        
        if (!this.csvData || this.csvData.length === 0) {
            console.warn('No CSV data to process');
            this.generateFallbackData();
            return;
        }

        // Reset data structures
        this.applications.clear();
        this.nodes.clear();
        this.links.clear();

        // Group data by application
        const appGroups = new Map();
        
        this.csvData.forEach((row, index) => {
            if (!row.application || !row.src || !row.dst) {
                return; // Skip invalid rows
            }

            const appName = row.application.trim();
            
            if (!appGroups.has(appName)) {
                appGroups.set(appName, {
                    name: appName,
                    archetype: row.archetype || 'Unknown',
                    records: []
                });
            }
            
            appGroups.get(appName).records.push({
                ...row,
                index: index
            });
        });

        console.log(`📊 Found ${appGroups.size} unique applications`);

        // Process applications
        Array.from(appGroups.entries()).forEach(([appName, appData]) => {
            this.processApplication(appName, appData);
        });

        // Build final data structure
        this.processedData = {
            applications: Array.from(this.applications.values()),
            nodes: Array.from(this.nodes.values()),
            links: Array.from(this.links.values()),
            metadata: {
                totalRecords: this.csvData.length,
                uniqueApplications: this.applications.size,
                uniqueNodes: this.nodes.size,
                uniqueConnections: this.links.size,
                archetypes: [...new Set(this.csvData.map(r => r.archetype))],
                protocols: [...new Set(this.csvData.map(r => r.protocol))]
            }
        };

        console.log('✅ Data processing complete:', this.processedData.metadata);
    }

    // Process individual application data
    processApplication(appName, appData) {
        const { records, archetype } = appData;
        
        // Create application entry
        const application = {
            id: this.sanitizeId(appName),
            name: appName,
            displayName: appName,
            archetype: archetype,
            criticality: this.determineCriticality(records),
            businessFunction: this.determineBusinessFunction(appName, archetype),
            technology: this.determineTechnology(records),
            status: 'active',
            nodeCount: 0,
            connectionCount: 0,
            totalTraffic: records.reduce((sum, r) => sum + (r.bytes || 0), 0)
        };

        this.applications.set(application.id, application);

        // Process nodes and connections for this application
        const appNodes = new Set();
        const appConnections = new Map();

        records.forEach(record => {
            // Create source node
            const srcNodeId = `${application.id}_${record.src}`;
            if (!this.nodes.has(srcNodeId)) {
                this.createNode(srcNodeId, record.src, application, record, 'source');
                appNodes.add(srcNodeId);
            }

            // Create destination node
            const dstNodeId = `${application.id}_${record.dst}`;
            if (!this.nodes.has(dstNodeId)) {
                this.createNode(dstNodeId, record.dst, application, record, 'destination');
                appNodes.add(dstNodeId);
            }

            // Create connection
            const connectionKey = `${srcNodeId}|${dstNodeId}`;
            if (!appConnections.has(connectionKey)) {
                this.createConnection(srcNodeId, dstNodeId, record, application);
                appConnections.set(connectionKey, true);
            }
        });

        // Update application stats
        application.nodeCount = appNodes.size;
        application.connectionCount = appConnections.size;
    }

    // Create network node
    createNode(nodeId, ipAddress, application, record, role) {
        const node = {
            id: nodeId,
            name: this.generateNodeName(ipAddress, record, role),
            ip: ipAddress,
            applicationId: application.id,
            application: application.name,
            archetype: application.archetype,
            tier: this.determineTier(record, role),
            type: this.determineNodeType(record),
            componentType: this.determineComponentType(record),
            role: role,
            technology: this.determineTechnology([record]),
            status: 'active',
            criticality: application.criticality,
            color: this.getNodeColor(record, role),
            size: this.getNodeSize(record),
            
            // Performance metrics (simulated)
            cpu: Math.random() * 100,
            memory: Math.random() * 100,
            uptime: 95 + Math.random() * 5,
            responseTime: 50 + Math.random() * 200,
            connections: Math.floor(Math.random() * 50),
            requestsPerSecond: Math.floor(Math.random() * 1000),
            
            // Position (will be calculated by force simulation)
            x: undefined,
            y: undefined,
            
            // Additional metadata
            ports: this.extractPorts(record),
            protocols: [record.protocol],
            lastSeen: new Date().toISOString(),
            description: this.generateNodeDescription(record, role)
        };

        this.nodes.set(nodeId, node);
        return node;
    }

    // Create network connection
    createConnection(sourceId, targetId, record, application) {
        const linkId = `${sourceId}|${targetId}`;
        
        if (this.links.has(linkId)) {
            // Update existing link with additional data
            const existingLink = this.links.get(linkId);
            existingLink.bandwidth += (record.bytes || 0);
            existingLink.requestCount += 1;
            return existingLink;
        }

        const link = {
            id: linkId,
            source: sourceId,
            target: targetId,
            applicationId: application.id,
            application: application.name,
            
            // Connection details
            protocol: record.protocol || 'TCP',
            port: this.extractPort(record),
            bandwidth: record.bytes || 0,
            status: 'active',
            direction: 'bidirectional',
            isInternal: true,
            
            // Performance metrics
            latency: 10 + Math.random() * 100,
            packetLoss: Math.random() * 0.1,
            requestCount: 1,
            errorRate: Math.random() * 0.05,
            
            // Visual properties
            color: this.getLinkColor(record),
            width: this.getLinkWidth(record),
            opacity: 0.8,
            
            // Additional metadata
            info: record.info || `${record.protocol} connection`,
            behavior: record.behavior || 'standard',
            lastActivity: new Date().toISOString()
        };

        this.links.set(linkId, link);
        return link;
    }

    // Utility methods for data processing
    sanitizeId(name) {
        return name.toLowerCase()
                  .replace(/[^a-z0-9]/g, '_')
                  .replace(/_+/g, '_')
                  .replace(/^_|_$/g, '');
    }

    generateNodeName(ip, record, role) {
        // Try to create meaningful names based on the data
        const behavior = record.behavior || '';
        const protocol = record.protocol || '';
        
        if (behavior.toLowerCase().includes('web')) return `Web-${ip.split('.').pop()}`;
        if (behavior.toLowerCase().includes('db') || behavior.toLowerCase().includes('database')) return `DB-${ip.split('.').pop()}`;
        if (behavior.toLowerCase().includes('api')) return `API-${ip.split('.').pop()}`;
        if (behavior.toLowerCase().includes('gateway')) return `GW-${ip.split('.').pop()}`;
        if (protocol === 'SQL') return `SQL-${ip.split('.').pop()}`;
        
        return `Node-${ip.split('.').pop()}`;
    }

    determineTier(record, role) {
        const info = (record.info || '').toLowerCase();
        const behavior = (record.behavior || '').toLowerCase();
        const protocol = (record.protocol || '').toLowerCase();

        if (behavior.includes('web') || info.includes('web')) return 'web-tier';
        if (behavior.includes('db') || behavior.includes('database') || protocol === 'sql') return 'database';
        if (behavior.includes('api') || info.includes('api')) return 'app-tier';
        if (behavior.includes('gateway')) return 'gateway';
        if (behavior.includes('service')) return 'service';
        
        return 'app-tier'; // default
    }

    determineNodeType(record) {
        const tier = this.determineTier(record);
        const tierMapping = {
            'web-tier': 'web-server',
            'database': 'database',
            'app-tier': 'application-server',
            'gateway': 'api-gateway',
            'service': 'microservice'
        };
        return tierMapping[tier] || 'server';
    }

    determineComponentType(record) {
        const behavior = (record.behavior || '').toLowerCase();
        if (behavior.includes('producer')) return 'message-producer';
        if (behavior.includes('consumer')) return 'message-consumer';
        if (behavior.includes('lambda')) return 'lambda-function';
        if (behavior.includes('etl')) return 'etl-job';
        return this.determineNodeType(record);
    }

    determineCriticality(records) {
        // Determine criticality based on traffic volume and archetype
        const totalBytes = records.reduce((sum, r) => sum + (r.bytes || 0), 0);
        const avgBytes = totalBytes / records.length;
        
        if (avgBytes > 1000) return 'critical';
        if (avgBytes > 500) return 'high';
        if (avgBytes > 100) return 'medium';
        return 'low';
    }

    determineBusinessFunction(appName, archetype) {
        const name = appName.toLowerCase();
        
        if (name.includes('core') || name.includes('banking')) return 'Core Banking';
        if (name.includes('risk') || name.includes('compliance')) return 'Risk & Compliance';
        if (name.includes('customer') || name.includes('portal')) return 'Customer Services';
        if (name.includes('payment') || name.includes('gateway')) return 'Payment Processing';
        if (name.includes('reporting') || name.includes('analytics')) return 'Reporting & Analytics';
        if (name.includes('security') || name.includes('identity')) return 'Security & Identity';
        
        // Map by archetype
        if (archetype === 'Database-Centric') return 'Data Management';
        if (archetype === 'Microservices' || archetype === 'Cloud-Native') return 'Digital Services';
        if (archetype === 'ETL/Data Pipeline') return 'Data Processing';
        
        return 'Operations';
    }

    determineTechnology(records) {
        const protocols = [...new Set(records.map(r => r.protocol))];
        const behaviors = [...new Set(records.map(r => r.behavior))];
        
        if (protocols.includes('SQL')) return 'SQL Database';
        if (protocols.includes('HTTP') || protocols.includes('HTTPS')) return 'Web Service';
        if (protocols.includes('gRPC')) return 'gRPC Service';
        if (behaviors.some(b => b && b.includes('Lambda'))) return 'AWS Lambda';
        if (behaviors.some(b => b && b.includes('Kafka'))) return 'Apache Kafka';
        
        return 'Enterprise Application';
    }

    extractPorts(record) {
        const info = record.info || '';
        const portMatch = info.match(/port (\d+)/g);
        if (portMatch) {
            return portMatch.map(p => p.replace('port ', ''));
        }
        return ['8080']; // default
    }

    extractPort(record) {
        const ports = this.extractPorts(record);
        return ports[0] || '8080';
    }

    getNodeColor(record, role) {
        const tier = this.determineTier(record, role);
        const colorMap = {
            'web-tier': '#3b82f6',     // Blue
            'database': '#eab308',      // Yellow (Fixed from orange)
            'app-tier': '#10b981',      // Green
            'gateway': '#8b5cf6',       // Purple
            'service': '#ef4444'        // Red
        };
        return colorMap[tier] || '#6b7280';
    }

    getNodeSize(record) {
        const bytes = record.bytes || 0;
        if (bytes > 1000) return 16;
        if (bytes > 500) return 14;
        if (bytes > 100) return 12;
        return 10;
    }

    getLinkColor(record) {
        const protocol = record.protocol;
        const colorMap = {
            'HTTP': '#3b82f6',
            'HTTPS': '#10b981',
            'SQL': '#f59e0b',
            'TCP': '#8b5cf6',
            'gRPC': '#ef4444'
        };
        return colorMap[protocol] || '#6b7280';
    }

    getLinkWidth(record) {
        const bytes = record.bytes || 0;
        if (bytes > 1000) return 3;
        if (bytes > 500) return 2;
        return 1;
    }

    generateNodeDescription(record, role) {
        const protocol = record.protocol || 'TCP';
        const behavior = record.behavior || 'Service';
        return `${behavior} node (${protocol}) - ${role}`;
    }

    // Generate fallback data if CSV loading fails
    generateFallbackData() {
        console.log('🔄 Generating fallback demo data...');
        
        this.processedData = {
            applications: [
                {
                    id: 'core_banking',
                    name: 'Core Banking System',
                    archetype: 'Database-Centric',
                    criticality: 'critical',
                    businessFunction: 'Core Banking'
                },
                {
                    id: 'customer_portal',
                    name: 'Customer Portal',
                    archetype: 'Web + API Headless',
                    criticality: 'high',
                    businessFunction: 'Customer Services'
                }
            ],
            nodes: [
                {
                    id: 'web1',
                    name: 'Web Server',
                    ip: '10.0.1.10',
                    applicationId: 'core_banking',
                    tier: 'web-tier',
                    color: '#3b82f6'
                },
                {
                    id: 'db1',
                    name: 'Database',
                    ip: '10.0.3.10',
                    applicationId: 'core_banking',
                    tier: 'database',
                    color: '#eab308'
                }
            ],
            links: [
                {
                    source: 'web1',
                    target: 'db1',
                    protocol: 'SQL',
                    bandwidth: 500
                }
            ],
            metadata: {
                totalRecords: 2,
                uniqueApplications: 2,
                uniqueNodes: 2,
                uniqueConnections: 1
            }
        };
    }

    // Get applications for filter dropdown
    getApplicationsForFilter() {
        if (!this.isLoaded || !this.processedData) {
            return [{ id: 'all', name: 'ALL Applications' }];
        }

        return [
            { id: 'all', name: 'ALL Applications' },
            ...this.processedData.applications.map(app => ({
                id: app.id,
                name: app.name,
                displayName: app.displayName || app.name,
                archetype: app.archetype,
                criticality: app.criticality,
                businessFunction: app.businessFunction,
                technology: app.technology,
                status: app.status
            }))
        ];
    }

    // Generate network topology for specific applications
    generateNetworkTopology(selectedApps = ['all'], includeUpstream = false, includeDownstream = false) {
        if (!this.isLoaded || !this.processedData) {
            return { nodes: [], links: [] };
        }

        let filteredNodes = [...this.processedData.nodes];
        let filteredLinks = [...this.processedData.links];

        // Filter by selected applications
        if (!selectedApps.includes('all') && selectedApps.length > 0) {
            filteredNodes = filteredNodes.filter(node => 
                selectedApps.includes(node.applicationId)
            );
            
            const nodeIds = new Set(filteredNodes.map(n => n.id));
            filteredLinks = filteredLinks.filter(link => 
                nodeIds.has(link.source) && nodeIds.has(link.target)
            );
        }

        return {
            nodes: filteredNodes,
            links: filteredLinks
        };
    }

    // Get metadata about the loaded data
    getMetadata() {
        return this.processedData?.metadata || {
            totalRecords: 0,
            uniqueApplications: 0,
            uniqueNodes: 0,
            uniqueConnections: 0
        };
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CSVDataLoader;
}