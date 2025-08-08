// static/ui/js/main.js - Core Application Logic
const AppDiscoverer = {
    currentTab: 'topology',
    initialized: false,
    
    // Initialize the application
    init() {
        if (this.initialized) return;
        
        console.log('🚀 Initializing Application Auto Discoverer...');
        
        // Load initial tab content
        this.loadTabContent('topology');
        
        // Initialize modules
        this.initializeModules();
        
        // Set up event listeners
        this.setupEventListeners();
        
        this.initialized = true;
        console.log('✅ Application Auto Discoverer initialized successfully');
    },
    
    // Initialize all modules
    initializeModules() {
        if (typeof NetworkTopology !== 'undefined') {
            NetworkTopology.init();
        }
        
        if (typeof Integration !== 'undefined') {
            Integration.init();
        }
        
        if (typeof FileUpload !== 'undefined') {
            FileUpload.init();
        }
    },
    
    // Set up global event listeners
    setupEventListeners() {
        // Tab switching
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('tab-btn')) {
                const tabName = e.target.onclick.toString().match(/switchMainTab\('(\w+)'\)/)?.[1];
                if (tabName) {
                    this.switchTab(tabName);
                }
            }
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            this.handleKeyboardShortcuts(e);
        });
        
        // Window resize
        window.addEventListener('resize', () => {
            this.handleResize();
        });
    },
    
    // Handle keyboard shortcuts
    handleKeyboardShortcuts(e) {
        // Ctrl/Cmd + Number keys for tab switching
        if ((e.ctrlKey || e.metaKey) && e.key >= '1' && e.key <= '4') {
            e.preventDefault();
            const tabIndex = parseInt(e.key) - 1;
            const tabs = ['topology', 'integration', 'documentation', 'deployment'];
            if (tabs[tabIndex]) {
                this.switchTab(tabs[tabIndex]);
            }
        }
        
        // Pass to topology module for additional shortcuts
        if (this.currentTab === 'topology' && typeof NetworkTopology !== 'undefined') {
            NetworkTopology.handleKeyboard(e);
        }
    },
    
    // Handle window resize
    handleResize() {
        if (this.currentTab === 'topology' && typeof NetworkTopology !== 'undefined') {
            NetworkTopology.handleResize();
        }
    },
    
    // Switch between main tabs
    switchTab(tabName) {
        if (this.currentTab === tabName) return;
        
        console.log(`🔄 Switching to ${tabName} tab`);
        
        // Update tab buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        
        const activeBtn = document.querySelector(`[onclick*="${tabName}"]`);
        if (activeBtn) {
            activeBtn.classList.add('active');
        }
        
        // Hide all tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        
        // Show target tab
        const targetTab = document.getElementById(`${tabName}-tab`);
        if (targetTab) {
            targetTab.classList.add('active');
            
            // Load content if not already loaded
            if (!targetTab.dataset.loaded) {
                this.loadTabContent(tabName);
            }
        }
        
        this.currentTab = tabName;
        
        // Initialize tab-specific functionality
        this.initializeTabContent(tabName);
    },
    
    // Load tab content dynamically
    async loadTabContent(tabName) {
        try {
            const response = await fetch(`static/ui/html/components/${tabName}-tab.html`);
            if (!response.ok) {
                throw new Error(`Failed to load ${tabName} tab content`);
            }
            
            const html = await response.text();
            const tabElement = document.getElementById(`${tabName}-tab`);
            if (tabElement) {
                tabElement.innerHTML = html;
                tabElement.dataset.loaded = 'true';
            }
        } catch (error) {
            console.error(`Error loading ${tabName} tab:`, error);
            this.showToast(`Failed to load ${tabName} tab content`, 'error');
        }
    },
    
    // Initialize tab-specific content
    initializeTabContent(tabName) {
        switch (tabName) {
            case 'topology':
                if (typeof NetworkTopology !== 'undefined') {
                    NetworkTopology.initialize();
                }
                break;
            case 'integration':
                if (typeof Integration !== 'undefined') {
                    Integration.initialize();
                }
                break;
            case 'documentation':
                if (typeof Documentation !== 'undefined') {
                    Documentation.initialize();
                }
                break;
            case 'deployment':
                if (typeof Deployment !== 'undefined') {
                    Deployment.initialize();
                }
                break;
        }
    },
    
    // Show toast notification
    showToast(message, type = 'success') {
        const container = document.getElementById('toast-container');
        if (!container) return;
        
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        
        container.appendChild(toast);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 5000);
    },
    
    // Show loading spinner
    showLoading() {
        const spinner = document.getElementById('loading-spinner');
        if (spinner) {
            spinner.style.display = 'block';
        }
    },
    
    // Hide loading spinner
    hideLoading() {
        const spinner = document.getElementById('loading-spinner');
        if (spinner) {
            spinner.style.display = 'none';
        }
    }
};

// Global functions for backwards compatibility
window.switchMainTab = (tabName) => AppDiscoverer.switchTab(tabName);
window.showToast = (message, type) => AppDiscoverer.showToast(message, type);

// static/ui/js/topology.js - Network Topology Module
const NetworkTopology = {
    svg: null,
    svgGroup: null,
    tooltip: null,
    zoom: null,
    simulation: null,
    originalData: { nodes: [], links: [] },
    currentData: { nodes: [], links: [] },
    
    // Initialize topology module
    init() {
        console.log('🌐 Initializing Network Topology module...');
    },
    
    // Initialize topology interface
    initialize() {
        this.setupD3Elements();
        this.setupEventListeners();
        this.loadDefaultData();
        this.setupPanelToggles();
        console.log('✅ Network Topology initialized');
    },
    
    // Setup D3 elements
    setupD3Elements() {
        this.svg = d3.select('#graph');
        if (this.svg.empty()) {
            console.error('SVG element not found');
            return;
        }
        
        this.svgGroup = this.svg.append('g');
        this.tooltip = d3.select('#tooltip');
        
        // Setup zoom behavior
        this.zoom = d3.zoom().on('zoom', (event) => {
            this.svgGroup.attr('transform', event.transform);
        });
        
        this.svg.call(this.zoom);
        
        // Add selection functionality
        this.setupRubberBandSelection();
    },
    
    // Setup event listeners
    setupEventListeners() {
        // Zoom controls
        const zoomIn = document.getElementById('zoom-in');
        const zoomOut = document.getElementById('zoom-out');
        const resetZoom = document.getElementById('reset-zoom');
        
        if (zoomIn) {
            zoomIn.addEventListener('click', () => {
                this.svg.transition().duration(300).call(this.zoom.scaleBy, 1.2);
            });
        }
        
        if (zoomOut) {
            zoomOut.addEventListener('click', () => {
                this.svg.transition().duration(300).call(this.zoom.scaleBy, 0.8);
            });
        }
        
        if (resetZoom) {
            resetZoom.addEventListener('click', () => {
                this.svg.transition().duration(500).call(
                    this.zoom.transform,
                    d3.zoomIdentity
                );
            });
        }
        
        // Filter controls
        const applyFilterBtn = document.getElementById('applyFilterBtn');
        if (applyFilterBtn) {
            applyFilterBtn.addEventListener('click', () => this.applyFilter());
        }
        
        // Protocol toggle
        const protocolToggle = document.getElementById('toggle-protocol-labels');
        if (protocolToggle) {
            protocolToggle.addEventListener('change', (e) => {
                this.toggleProtocolLabels(e.target.checked);
            });
        }
        
        // Discovery button
        const discoveryBtn = document.querySelector('[onclick*="startAutoDiscovery"]');
        if (discoveryBtn) {
            discoveryBtn.addEventListener('click', () => this.startAutoDiscovery());
        }
    },
    
    // Setup panel toggles
    setupPanelToggles() {
        const leftPanel = document.getElementById('left-panel');
        const rightPanel = document.getElementById('right-panel');
        const leftToggle = leftPanel?.querySelector('.hamburger');
        const rightToggle = rightPanel?.querySelector('.hamburger');
        
        if (leftToggle) {
            leftToggle.addEventListener('click', () => this.togglePanel('left'));
        }
        
        if (rightToggle) {
            rightToggle.addEventListener('click', () => this.togglePanel('right'));
        }
    },
    
    // Toggle panel
    togglePanel(side) {
        const panel = document.getElementById(`${side}-panel`);
        const zoomControls = document.getElementById('zoom-controls');
        
        if (panel) {
            panel.classList.toggle('collapsed');
            
            // Adjust zoom controls position for right panel
            if (side === 'right' && zoomControls) {
                zoomControls.classList.toggle('right-collapsed');
            }
        }
    },
    
    // Load default network data
    loadDefaultData() {
        // Create sample financial network topology
        this.originalData = {
            nodes: [
                { id: "web-server-1", label: "Web Server 1", application: "Frontend", group: 1, archetype: "Web Application" },
                { id: "api-gateway", label: "API Gateway", application: "Gateway", group: 2, archetype: "API Gateway" },
                { id: "auth-service", label: "Auth Service", application: "Authentication", group: 3, archetype: "Microservice" },
                { id: "user-db", label: "User Database", application: "Database", group: 4, archetype: "Database" },
                { id: "payment-service", label: "Payment Service", application: "Payment", group: 5, archetype: "Financial Service" },
                { id: "notification-queue", label: "Notification Queue", application: "Messaging", group: 6, archetype: "Message Queue" }
            ],
            links: [
                { source: "web-server-1", target: "api-gateway", protocol: "HTTPS", port: 443, value: 8 },
                { source: "api-gateway", target: "auth-service", protocol: "HTTP", port: 8080, value: 6 },
                { source: "auth-service", target: "user-db", protocol: "TCP", port: 5432, value: 7 },
                { source: "api-gateway", target: "payment-service", protocol: "HTTPS", port: 443, value: 9 },
                { source: "payment-service", target: "notification-queue", protocol: "AMQP", port: 5672, value: 4 }
            ]
        };
        
        this.currentData = JSON.parse(JSON.stringify(this.originalData));
        this.populateAppFilter();
        this.updateGraph();
    },
    
    // Populate application filter
    populateAppFilter() {
        const appSelect = document.getElementById('app-select');
        if (!appSelect || !this.originalData.nodes) return;
        
        const apps = [...new Set(this.originalData.nodes.map(n => n.application))].sort();
        
        appSelect.innerHTML = '<option value="">-- All Applications --</option>';
        apps.forEach(app => {
            const option = document.createElement('option');
            option.value = app;
            option.textContent = app;
            appSelect.appendChild(option);
        });
    },
    
    // Apply filter
    applyFilter() {
        const appSelect = document.getElementById('app-select');
        const selectedApps = Array.from(appSelect.selectedOptions).map(o => o.value);
        
        if (selectedApps.includes('') || selectedApps.length === 0) {
            this.currentData = JSON.parse(JSON.stringify(this.originalData));
        } else {
            this.currentData.nodes = this.originalData.nodes.filter(n => 
                selectedApps.includes(n.application)
            );
            
            const nodeIds = new Set(this.currentData.nodes.map(n => n.id));
            this.currentData.links = this.originalData.links.filter(l => 
                nodeIds.has(l.source) && nodeIds.has(l.target)
            );
        }
        
        this.updateGraph();
        AppDiscoverer.showToast(`Filter applied: ${this.currentData.nodes.length} nodes`);
    },
    
    // Update graph visualization
    updateGraph() {
        if (!this.svg || !this.currentData) return;
        
        // Clear existing elements
        this.svgGroup.selectAll('*').remove();
        
        // Create simulation
        this.simulation = d3.forceSimulation(this.currentData.nodes)
            .force('link', d3.forceLink(this.currentData.links).id(d => d.id).distance(120))
            .force('charge', d3.forceManyBody().strength(-400))
            .force('center', d3.forceCenter(400, 300))
            .force('collision', d3.forceCollide().radius(25));
        
        // Create links
        const link = this.svgGroup.append('g')
            .attr('class', 'links')
            .selectAll('line')
            .data(this.currentData.links)
            .join('line')
            .attr('stroke', 'rgba(64, 224, 208, 0.4)')
            .attr('stroke-width', d => Math.sqrt(d.value || 1) * 2)
            .attr('marker-end', 'url(#arrowhead)');
        
        // Create link labels
        const linkLabels = this.svgGroup.append('g')
            .attr('class', 'link-labels')
            .selectAll('text')
            .data(this.currentData.links)
            .join('text')
            .attr('font-size', '10px')
            .attr('fill', '#a0a0a0')
            .attr('text-anchor', 'middle')
            .style('pointer-events', 'none')
            .text(d => `${d.protocol}:${d.port}`);
        
        // Create nodes
        const node = this.svgGroup.append('g')
            .attr('class', 'nodes')
            .selectAll('circle')
            .data(this.currentData.nodes)
            .join('circle')
            .attr('r', 12)
            .attr('fill', d => this.getNodeColor(d.archetype))
            .attr('stroke', '#40E0D0')
            .attr('stroke-width', 2)
            .call(this.createDragBehavior())
            .on('mouseover', (event, d) => this.showTooltip(event, d))
            .on('mouseout', () => this.hideTooltip());
        
        // Create node labels
        const nodeLabels = this.svgGroup.append('g')
            .attr('class', 'node-labels')
            .selectAll('text')
            .data(this.currentData.nodes)
            .join('text')
            .attr('font-size', '12px')
            .attr('fill', '#e0e0e0')
            .attr('text-anchor', 'middle')
            .attr('dy', '0.3em')
            .style('pointer-events', 'none')
            .style('font-weight', 'bold')
            .text(d => d.label);
        
        // Simulation tick
        this.simulation.on('tick', () => {
            link
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);
            
            linkLabels
                .attr('x', d => (d.source.x + d.target.x) / 2)
                .attr('y', d => (d.source.y + d.target.y) / 2);
            
            node
                .attr('cx', d => d.x)
                .attr('cy', d => d.y);
            
            nodeLabels
                .attr('x', d => d.x)
                .attr('y', d => d.y + 20);
        });
    },
    
    // Get node color based on archetype
    getNodeColor(archetype) {
        const colors = {
            'Web Application': '#4CAF50',
            'API Gateway': '#2196F3',
            'Microservice': '#FF9800',
            'Database': '#9C27B0',
            'Financial Service': '#E91E63',
            'Message Queue': '#607D8B'
        };
        return colors[archetype] || '#40E0D0';
    },
    
    // Create drag behavior
    createDragBehavior() {
        return d3.drag()
            .on('start', (event, d) => {
                if (!event.active) this.simulation.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            })
            .on('drag', (event, d) => {
                d.fx = event.x;
                d.fy = event.y;
            })
            .on('end', (event, d) => {
                if (!event.active) this.simulation.alphaTarget(0);
                d.fx = null;
                d.fy = null;
            });
    },
    
    // Show tooltip
    showTooltip(event, d) {
        if (!this.tooltip) return;
        
        this.tooltip
            .style('display', 'block')
            .style('left', (event.pageX + 10) + 'px')
            .style('top', (event.pageY - 28) + 'px')
            .html(`
                <strong>${d.label}</strong><br/>
                Application: ${d.application}<br/>
                Archetype: ${d.archetype}<br/>
                ID: ${d.id}
            `);
    },
    
    // Hide tooltip
    hideTooltip() {
        if (this.tooltip) {
            this.tooltip.style('display', 'none');
        }
    },
    
    // Toggle protocol labels
    toggleProtocolLabels(show) {
        this.svgGroup.selectAll('.link-labels text')
            .style('display', show ? 'block' : 'none');
    },
    
    // Setup rubber band selection
    setupRubberBandSelection() {
        let isSelecting = false;
        let startPoint = null;
        let selectionRect = null;
        let rubberBandMode = false;
        
        // Toggle with R key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'r' || e.key === 'R') {
                if (document.activeElement.tagName === 'INPUT' || 
                    document.activeElement.tagName === 'TEXTAREA') {
                    return;
                }
                
                rubberBandMode = !rubberBandMode;
                this.svg.style('cursor', rubberBandMode ? 'crosshair' : 'default');
                AppDiscoverer.showToast(
                    rubberBandMode ? 'Rubber band mode ON' : 'Rubber band mode OFF'
                );
            }
        });
        
        // Mouse events for selection
        this.svg.on('mousedown.rubberband', (event) => {
            if (!rubberBandMode) return;
            
            isSelecting = true;
            startPoint = d3.pointer(event, this.svgGroup.node());
            
            selectionRect = this.svgGroup
                .append('rect')
                .attr('class', 'selection-rect')
                .attr('x', startPoint[0])
                .attr('y', startPoint[1])
                .attr('width', 0)
                .attr('height', 0);
            
            event.preventDefault();
        });
        
        this.svg.on('mousemove.rubberband', (event) => {
            if (!rubberBandMode || !isSelecting || !selectionRect) return;
            
            const currentPoint = d3.pointer(event, this.svgGroup.node());
            const x = Math.min(startPoint[0], currentPoint[0]);
            const y = Math.min(startPoint[1], currentPoint[1]);
            const width = Math.abs(currentPoint[0] - startPoint[0]);
            const height = Math.abs(currentPoint[1] - startPoint[1]);
            
            selectionRect
                .attr('x', x)
                .attr('y', y)
                .attr('width', width)
                .attr('height', height);
        });
        
        this.svg.on('mouseup.rubberband', (event) => {
            if (!rubberBandMode || !isSelecting || !selectionRect) return;
            
            const currentPoint = d3.pointer(event, this.svgGroup.node());
            const x = Math.min(startPoint[0], currentPoint[0]);
            const y = Math.min(startPoint[1], currentPoint[1]);
            const width = Math.abs(currentPoint[0] - startPoint[0]);
            const height = Math.abs(currentPoint[1] - startPoint[1]);
            
            if (width > 10 && height > 10) {
                this.zoomToArea(x, y, width, height);
            }
            
            selectionRect.remove();
            selectionRect = null;
            isSelecting = false;
        });
    },
    
    // Zoom to selected area
    zoomToArea(x, y, width, height) {
        const svgRect = this.svg.node().getBoundingClientRect();
        const scaleX = svgRect.width / width;
        const scaleY = svgRect.height / height;
        const scale = Math.min(scaleX, scaleY) * 0.9;
        
        const centerX = x + width / 2;
        const centerY = y + height / 2;
        const translateX = svgRect.width / 2 - centerX * scale;
        const translateY = svgRect.height / 2 - centerY * scale;
        
        this.svg.transition()
            .duration(750)
            .call(
                this.zoom.transform,
                d3.zoomIdentity.translate(translateX, translateY).scale(scale)
            );
    },
    
    // Start auto discovery
    startAutoDiscovery() {
        const statusPanel = document.getElementById('discovery-status');
        if (!statusPanel) return;
        
        AppDiscoverer.showLoading();
        statusPanel.innerHTML = 'Starting network discovery...\n';
        
        // Simulate discovery process
        const steps = [
            'Scanning network ranges...',
            'Discovering active hosts...',
            'Identifying services...',
            'Mapping dependencies...',
            'Analyzing traffic patterns...',
            'Discovery complete!'
        ];
        
        let currentStep = 0;
        const interval = setInterval(() => {
            if (currentStep < steps.length) {
                statusPanel.innerHTML += `${steps[currentStep]}\n`;
                statusPanel.scrollTop = statusPanel.scrollHeight;
                currentStep++;
            } else {
                clearInterval(interval);
                AppDiscoverer.hideLoading();
                AppDiscoverer.showToast('Network discovery completed', 'success');
                
                // Add discovered nodes
                this.addDiscoveredNodes();
            }
        }, 1000);
    },
    
    // Add discovered nodes to the graph
    addDiscoveredNodes() {
        const newNodes = [
            { id: "cache-server", label: "Cache Server", application: "Cache", group: 7, archetype: "Cache" },
            { id: "load-balancer", label: "Load Balancer", application: "Infrastructure", group: 8, archetype: "Load Balancer" }
        ];
        
        const newLinks = [
            { source: "load-balancer", target: "web-server-1", protocol: "HTTP", port: 80, value: 10 },
            { source: "api-gateway", target: "cache-server", protocol: "TCP", port: 6379, value: 5 }
        ];
        
        this.originalData.nodes.push(...newNodes);
        this.originalData.links.push(...newLinks);
        
        this.currentData = JSON.parse(JSON.stringify(this.originalData));
        this.populateAppFilter();
        this.updateGraph();
    },
    
    // Handle keyboard shortcuts
    handleKeyboard(e) {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
        
        const step = 50;
        let dx = 0, dy = 0;
        
        switch (e.key) {
            case 'ArrowLeft':
                dx = step;
                break;
            case 'ArrowRight':
                dx = -step;
                break;
            case 'ArrowUp':
                dy = step;
                break;
            case 'ArrowDown':
                dy = -step;
                break;
            default:
                return;
        }
        
        e.preventDefault();
        this.svg.transition().duration(200).call(this.zoom.translateBy, dx, dy);
    },
    
    // Handle window resize
    handleResize() {
        if (this.svg && this.simulation) {
            const rect = this.svg.node().getBoundingClientRect();
            this.simulation.force('center', d3.forceCenter(rect.width / 2, rect.height / 2));
            this.simulation.alpha(0.3).restart();
        }
    }
};

// static/ui/js/integration.js - Integration Module
const Integration = {
    connections: {
        splunk: { connected: false, client: null },
        dynatrace: { connected: false, client: null },
        extrahop: { connected: false, client: null }
    },
    
    collectionActive: false,
    collectionInterval: null,
    collectedData: [],
    
    // Initialize integration module
    init() {
        console.log('📡 Initializing Integration module...');
    },
    
    // Initialize integration interface
    initialize() {
        this.setupEventListeners();
        this.updateSystemStatus();
        console.log('✅ Integration module initialized');
    },
    
    // Setup event listeners
    setupEventListeners() {
        // Connection buttons will be set up when tab content is loaded
        console.log('Setting up integration event listeners...');
    },
    
    // Connect to Splunk
    async connectSplunk() {
        const url = document.getElementById('splunkUrl')?.value;
        const username = document.getElementById('splunkUser')?.value;
        const password = document.getElementById('splunkPass')?.value;
        
        if (!url || !username || !password) {
            this.logToConsole('splunkLog', '❌ Please fill in all connection fields', 'error');
            return;
        }
        
        this.updateConnectionStatus('splunk', 'connecting');
        this.logToConsole('splunkLog', '🔄 Connecting to Splunk...');
        
        try {
            // Simulate connection
            await this.simulateConnection(2000);
            
            this.connections.splunk.connected = true;
            this.connections.splunk.client = { url, username };
            
            this.updateConnectionStatus('splunk', 'connected');
            this.logToConsole('splunkLog', '✅ Successfully connected to Splunk');
            this.updateSystemStatus();
            
            AppDiscoverer.showToast('Connected to Splunk', 'success');
        } catch (error) {
            this.updateConnectionStatus('splunk', 'disconnected');
            this.logToConsole('splunkLog', `❌ Connection failed: ${error.message}`, 'error');
            AppDiscoverer.showToast('Splunk connection failed', 'error');
        }
    },
    
    // Disconnect from Splunk
    disconnectSplunk() {
        this.connections.splunk.connected = false;
        this.connections.splunk.client = null;
        this.updateConnectionStatus('splunk', 'disconnected');
        this.logToConsole('splunkLog', '🔌 Disconnected from Splunk');
        this.updateSystemStatus();
        AppDiscoverer.showToast('Disconnected from Splunk', 'warning');
    },
    
    // Execute Splunk query
    async executeSplunkQuery() {
        if (!this.connections.splunk.connected) {
            this.logToConsole('splunkLog', '❌ Not connected to Splunk', 'error');
            return;
        }
        
        const query = document.getElementById('splunkQuery')?.value;
        if (!query) {
            this.logToConsole('splunkLog', '❌ Please enter a query', 'error');
            return;
        }
        
        this.logToConsole('splunkLog', `🔍 Executing query: ${query.substring(0, 50)}...`);
        
        try {
            const results = await this.simulateSplunkQuery(query);
            
            // Update metrics
            const eventsElement = document.getElementById('splunkEvents');
            const lastUpdateElement = document.getElementById('splunkLastUpdate');
            
            if (eventsElement) eventsElement.textContent = results.length;
            if (lastUpdateElement) lastUpdateElement.textContent = new Date().toLocaleTimeString();
            
            this.logToConsole('splunkLog', `✅ Query completed: ${results.length} events retrieved`);
            this.addToCollectedData('splunk', results);
            
            AppDiscoverer.showToast(`Retrieved ${results.length} events from Splunk`, 'success');
        } catch (error) {
            this.logToConsole('splunkLog', `❌ Query failed: ${error.message}`, 'error');
            AppDiscoverer.showToast('Splunk query failed', 'error');
        }
    },
    
    // Start real-time collection
    startCollection() {
        if (this.collectionActive) {
            AppDiscoverer.showToast('Collection already active', 'warning');
            return;
        }
        
        const interval = 30000; // 30 seconds
        this.collectionActive = true;
        this.collectionInterval = setInterval(() => {
            this.collectFromAllSources();
        }, interval);
        
        AppDiscoverer.showToast('Real-time collection started', 'success');
        this.updatePipelineStep(1, 'active');
    },
    
    // Stop real-time collection
    stopCollection() {
        if (!this.collectionActive) return;
        
        this.collectionActive = false;
        if (this.collectionInterval) {
            clearInterval(this.collectionInterval);
            this.collectionInterval = null;
        }
        
        AppDiscoverer.showToast('Real-time collection stopped', 'warning');
        this.updatePipelineStep(1, 'inactive');
    },
    
    // Collect from all connected sources
    async collectFromAllSources() {
        const promises = [];
        
        if (this.connections.splunk.connected) {
            promises.push(this.executeSplunkQuery());
        }
        
        if (this.connections.dynatrace.connected) {
            promises.push(this.executeDynatraceQuery());
        }
        
        if (this.connections.extrahop.connected) {
            promises.push(this.executeExtraHopQuery());
        }
        
        if (promises.length === 0) {
            console.log('No active connections for collection');
            return;
        }
        
        try {
            await Promise.all(promises);
            this.updatePipelineStep(2, 'active');
        } catch (error) {
            console.error('Collection error:', error);
            this.updatePipelineStep(2, 'error');
        }
    },
    
    // Generate report
    generateReport() {
        const report = {
            timestamp: new Date().toISOString(),
            connections: Object.keys(this.connections).filter(k => this.connections[k].connected),
            totalRecords: this.collectedData.length,
            collectionActive: this.collectionActive
        };
        
        this.downloadJSON(report, 'integration-report.json');
        AppDiscoverer.showToast('Report generated', 'success');
    },
    
    // Export data
    exportData() {
        if (this.collectedData.length === 0) {
            AppDiscoverer.showToast('No data to export', 'warning');
            return;
        }
        
        this.downloadJSON(this.collectedData, 'exported-data.json');
        AppDiscoverer.showToast(`Exported ${this.collectedData.length} records`, 'success');
    },
    
    // Helper methods
    simulateConnection(delay) {
        return new Promise((resolve, reject) => {
            setTimeout(() => {
                if (Math.random() > 0.1) { // 90% success rate
                    resolve();
                } else {
                    reject(new Error('Connection timeout'));
                }
            }, delay);
        });
    },
    
    async simulateSplunkQuery(query) {
        return new Promise((resolve) => {
            setTimeout(() => {
                const mockResults = [];
                const count = Math.floor(Math.random() * 100) + 10;
                
                for (let i = 0; i < count; i++) {
                    mockResults.push({
                        timestamp: new Date().toISOString(),
                        source_ip: `192.168.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}`,
                        dest_ip: `10.0.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}`,
                        protocol: ['TCP', 'UDP', 'HTTP'][Math.floor(Math.random() * 3)],
                        port: [80, 443, 22, 3389][Math.floor(Math.random() * 4)]
                    });
                }
                
                resolve(mockResults);
            }, 1000);
        });
    },
    
    updateConnectionStatus(service, status) {
        const statusIndicator = document.getElementById(`${service}Status`);
        const statusText = document.getElementById(`${service}StatusText`);
        
        if (statusIndicator) {
            statusIndicator.className = `status-indicator status-${status}`;
        }
        
        if (statusText) {
            statusText.textContent = status.charAt(0).toUpperCase() + status.slice(1);
        }
    },
    
    logToConsole(consoleId, message, type = 'info') {
        const console = document.getElementById(consoleId);
        if (console) {
            const timestamp = new Date().toLocaleTimeString();
            console.innerHTML += `<div style="color: ${type === 'error' ? '#f44336' : '#40E0D0'}">[${timestamp}] ${message}</div>`;
            console.scrollTop = console.scrollHeight;
        }
    },
    
    addToCollectedData(source, data) {
        const enrichedData = data.map((record, index) => ({
            id: `${source}_${Date.now()}_${index}`,
            source: source,
            timestamp: new Date().toISOString(),
            data: record
        }));
        
        this.collectedData.push(...enrichedData);
        this.updateSystemStatus();
    },
    
    updateSystemStatus() {
        const activeConnections = Object.values(this.connections).filter(c => c.connected).length;
        const activeElement = document.getElementById('activeConnections');
        const totalElement = document.getElementById('totalProcessed');
        
        if (activeElement) activeElement.textContent = activeConnections;
        if (totalElement) totalElement.textContent = this.collectedData.length;
    },
    
    updatePipelineStep(step, status) {
        const stepElement = document.getElementById(`step${step}`);
        if (stepElement) {
            stepElement.className = `step-icon step-${status}`;
        }
    },
    
    downloadJSON(data, filename) {
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
    }
};

// static/ui/js/file-upload.js - File Upload Module
const FileUpload = {
    supportedTypes: ['.json', '.csv', '.xlsx', '.xls'],
    maxFileSize: 100 * 1024 * 1024, // 100MB
    
    // Initialize file upload module
    init() {
        console.log('📁 Initializing File Upload module...');
        this.setupDragAndDrop();
    },
    
    // Setup drag and drop functionality
    setupDragAndDrop() {
        document.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.stopPropagation();
        });
        
        document.addEventListener('drop', (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            const files = Array.from(e.dataTransfer.files);
            if (files.length > 0) {
                this.handleFile({ target: { files } });
            }
        });
    },
    
    // Handle file upload
    handleFile(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        // Validate file
        if (!this.validateFile(file)) {
            return;
        }
        
        AppDiscoverer.showLoading();
        
        // Process file based on type
        if (file.name.endsWith('.json')) {
            this.processJSONFile(file);
        } else if (file.name.endsWith('.csv')) {
            this.processCSVFile(file);
        } else if (file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
            this.processExcelFile(file);
        }
    },
    
    // Validate file
    validateFile(file) {
        if (file.size > this.maxFileSize) {
            AppDiscoverer.showToast(`File too large. Maximum size: ${this.maxFileSize / 1024 / 1024}MB`, 'error');
            return false;
        }
        
        const isSupported = this.supportedTypes.some(type => file.name.toLowerCase().endsWith(type));
        if (!isSupported) {
            AppDiscoverer.showToast(`Unsupported file type. Supported: ${this.supportedTypes.join(', ')}`, 'error');
            return false;
        }
        
        return true;
    },
    
    // Process JSON file
    processJSONFile(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const data = JSON.parse(e.target.result);
                this.handleNetworkData(data);
                AppDiscoverer.showToast(`JSON file loaded: ${file.name}`, 'success');
            } catch (error) {
                AppDiscoverer.showToast(`Error parsing JSON: ${error.message}`, 'error');
            } finally {
                AppDiscoverer.hideLoading();
            }
        };
        reader.readAsText(file);
    },
    
    // Process CSV file
    processCSVFile(file) {
        Papa.parse(file, {
            header: true,
            dynamicTyping: true,
            skipEmptyLines: true,
            complete: (results) => {
                try {
                    const networkData = this.convertCSVToNetworkData(results.data);
                    this.handleNetworkData(networkData);
                    AppDiscoverer.showToast(`CSV file loaded: ${file.name}`, 'success');
                } catch (error) {
                    AppDiscoverer.showToast(`Error processing CSV: ${error.message}`, 'error');
                } finally {
                    AppDiscoverer.hideLoading();
                }
            },
            error: (error) => {
                AppDiscoverer.showToast(`Error reading CSV: ${error.message}`, 'error');
                AppDiscoverer.hideLoading();
            }
        });
    },
    
    // Process Excel file
    processExcelFile(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                // This would require SheetJS library
                // For now, show a message about Excel support
                AppDiscoverer.showToast('Excel file support coming soon. Please use CSV format.', 'warning');
            } catch (error) {
                AppDiscoverer.showToast(`Error processing Excel: ${error.message}`, 'error');
            } finally {
                AppDiscoverer.hideLoading();
            }
        };
        reader.readAsArrayBuffer(file);
    },
    
    // Convert CSV data to network format
    convertCSVToNetworkData(csvData) {
        const nodes = new Map();
        const links = [];
        
        csvData.forEach(row => {
            if (row.source && row.target) {
                // Add source node
                if (!nodes.has(row.source)) {
                    nodes.set(row.source, {
                        id: row.source,
                        label: row.source_label || row.source,
                        application: row.source_app || 'Unknown',
                        archetype: row.source_archetype || 'Unknown',
                        group: row.source_group || 0
                    });
                }
                
                // Add target node
                if (!nodes.has(row.target)) {
                    nodes.set(row.target, {
                        id: row.target,
                        label: row.target_label || row.target,
                        application: row.target_app || 'Unknown',
                        archetype: row.target_archetype || 'Unknown',
                        group: row.target_group || 0
                    });
                }
                
                // Add link
                links.push({
                    source: row.source,
                    target: row.target,
                    protocol: row.protocol || 'TCP',
                    port: row.port || 80,
                    value: row.value || 1
                });
            }
        });
        
        return {
            nodes: Array.from(nodes.values()),
            links: links
        };
    },
    
    // Handle network data
    handleNetworkData(data) {
        if (!data.nodes || !data.links) {
            AppDiscoverer.showToast('Invalid network data format', 'error');
            return;
        }
        
        // Update topology if available
        if (typeof NetworkTopology !== 'undefined' && NetworkTopology.initialized) {
            NetworkTopology.originalData = data;
            NetworkTopology.currentData = JSON.parse(JSON.stringify(data));
            NetworkTopology.populateAppFilter();
            NetworkTopology.updateGraph();
        }
        
        console.log(`Loaded network data: ${data.nodes.length} nodes, ${data.links.length} links`);
    }
};

// Additional modules for Documentation and Deployment would be added here
const Documentation = {
    init() {
        console.log('📚 Initializing Documentation module...');
    },
    
    initialize() {
        console.log('✅ Documentation module initialized');
    },
    
    generateArchDiagram() {
        AppDiscoverer.showToast('Architecture diagram generation coming soon', 'warning');
    },
    
    generateDepMatrix() {
        AppDiscoverer.showToast('Dependency matrix generation coming soon', 'warning');
    },
    
    generateTechDoc() {
        AppDiscoverer.showToast('Technical documentation generation coming soon', 'warning');
    }
};

const Deployment = {
    init() {
        console.log('🚀 Initializing Deployment module...');
    },
    
    initialize() {
        console.log('✅ Deployment module initialized');
    },
    
    generateConfig() {
        AppDiscoverer.showToast('Configuration generation coming soon', 'warning');
    },
    
    generateScript() {
        AppDiscoverer.showToast('Script generation coming soon', 'warning');
    },
    
    downloadScript() {
        AppDiscoverer.showToast('Script download coming soon', 'warning');
    }
};

// Global function exports for backwards compatibility
window.toggleLeftPanel = () => NetworkTopology.togglePanel('left');
window.toggleRightPanel = () => NetworkTopology.togglePanel('right');
window.startAutoDiscovery = () => NetworkTopology.startAutoDiscovery();

// Integration global functions
window.Integration = Integration;

// File upload global functions
window.FileUpload = FileUpload;

// Documentation global functions
window.Documentation = Documentation;

// Deployment global functions
window.Deployment = Deployment;