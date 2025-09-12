// Network Topology Visualization - Enhanced with Working Display Options
// Updated from topology.js with complete checkbox functionality from topology2.js

class NetworkTopologyDashboard {
    constructor() {
        this.initializeProperties();
        this.initializeDOM();
        this.waitForData();
    }

    initializeProperties() {
        // Core properties
        this.width = 0;
        this.height = 0;
        this.currentLayout = 'force';
        
        // Data
        this.networkData = { nodes: [], links: [] };
        this.rawApplications = [];
        
        // State
        this.selectedNodes = new Set();
        this.selectedApps = ['all'];
        this.showUpstream = false;
        this.showDownstream = false;
        this.filteredNodeTypes = new Set([
            'web-tier', 'frontend', 'web-server', 'backend', 'app-tier', 
            'processor', 'storage', 'database', 'data-tier', 'data-service',
            'gateway', 'api-gateway', 'load-balancer', 'core-service', 
            'microservice', 'service', 'worker'
        ]);
        
        // Display options - Enhanced
        this.displayOptions = {
            showLabels: true,
            showIPs: false,
            showLinkLabels: false,
            showTraffic: false
        };
        
        // Traffic animation properties
        this.trafficAnimationId = null;
        this.isTrafficAnimating = false;
        this.trafficParticles = null;
        
        // D3 elements
        this.simulation = null;
        this.zoom = null;
        this.svg = null;
        this.mainGroup = null;
        
        // Panel states
        this.panelStates = { left: false, right: false };
    }

    initializeDOM() {
        this.svg = d3.select("#graph");
        this.container = d3.select("#middle-canvas-wrapper");
        this.tooltip = d3.select("#tooltip");
        
        if (!this.svg.node() || !this.container.node()) {
            console.error('Required DOM elements not found');
            return false;
        }
        
        return true;
    }

    waitForData() {
        let attempts = 0;
        const maxAttempts = 20;
        
        const checkData = () => {
            attempts++;
            
            if (attempts > maxAttempts) {
                console.warn('Using fallback data after timeout');
                this.useFallbackData();
                this.initialize();
                return;
            }
            
            if (window.AppData && window.AppData.isDataLoaded) {
                console.log('AppData ready, initializing');
                this.loadFromAppData();
                this.initialize();
                return;
            }
            
            if (window.AppData && window.AppData.loadData && attempts === 1) {
                console.log('Triggering AppData load');
                window.AppData.loadData().then(() => {
                    this.loadFromAppData();
                    this.initialize();
                }).catch(() => {
                    this.useFallbackData();
                    this.initialize();
                });
                return;
            }
            
            setTimeout(checkData, 200);
        };
        
        checkData();
    }

    loadFromAppData() {
        if (!window.AppData) {
            this.useFallbackData();
            return;
        }
        
        if (window.AppData.getApplicationNamesForFilter) {
            this.rawApplications = window.AppData.getApplicationNamesForFilter();
        }
        
        if (window.AppData.generateNetworkTopology) {
            this.networkData = window.AppData.generateNetworkTopology(
                this.selectedApps,
                this.showUpstream,
                this.showDownstream
            );
        }
        
        if (!this.networkData.nodes || this.networkData.nodes.length === 0) {
            console.warn('No network data from AppData, using fallback');
            this.useFallbackData();
        }
        
        console.log(`Loaded ${this.networkData.nodes.length} nodes, ${this.networkData.links.length} links`);
    }

    useFallbackData() {
        this.rawApplications = [
            { id: 'all', name: 'ALL Applications', displayName: 'ALL Applications' },
            { id: 'app1', name: 'Core Banking', businessFunction: 'Banking', criticality: 'critical' },
            { id: 'app2', name: 'Customer Portal', businessFunction: 'Customer', criticality: 'high' },
            { id: 'app3', name: 'Risk System', businessFunction: 'Risk', criticality: 'high' }
        ];
        
        this.networkData = {
            nodes: [
                {
                    id: 'web1',
                    name: 'Web Server 1',
                    applicationId: 'app1',
                    application: 'Core Banking',
                    tier: 'web-tier',
                    ip: '10.0.1.10',
                    status: 'active',
                    criticality: 'high'
                },
                {
                    id: 'app1-server',
                    name: 'App Server 1',
                    applicationId: 'app1',
                    application: 'Core Banking',
                    tier: 'app-tier',
                    ip: '10.0.2.10',
                    status: 'active',
                    criticality: 'critical'
                },
                {
                    id: 'db1',
                    name: 'Database 1',
                    applicationId: 'app1',
                    application: 'Core Banking',
                    tier: 'database',
                    ip: '10.0.3.10',
                    status: 'active',
                    criticality: 'critical'
                }
            ],
            links: [
                {
                    source: 'web1',
                    target: 'app1-server',
                    protocol: 'HTTP',
                    port: '8080',
                    bandwidth: 500,
                    status: 'active'
                },
                {
                    source: 'app1-server',
                    target: 'db1',
                    protocol: 'TCP',
                    port: '3306',
                    bandwidth: 300,
                    status: 'active'
                }
            ]
        };
    }

    initialize() {
        console.log('Initializing topology dashboard');
        
        this.setupSVG();
        this.setupZoom();
        this.setupEventListeners();
        this.setupPanels();
        this.setupFilters();
        this.populateApplicationFilter();
        
        this.render();
        this.updateStats();
        this.updateNodeSelector();
		this.broadcastFilterChange();
		
        window.addEventListener('resize', () => this.handleResize());
        
        window.topologyDashboard = this;
    }

    // ============= SVG SETUP =============
    
    setupSVG() {
        const rect = this.container.node().getBoundingClientRect();
        this.width = rect.width || 800;
        this.height = rect.height || 600;
        
        console.log('SVG dimensions:', this.width, 'x', this.height);
        if (this.width === 0 || this.height === 0) {
            console.error('Container has no dimensions!');
            this.width = 800;
            this.height = 600;
        }
        
        if (this.height < 400) {
            console.warn('Container height too small:', this.height, 'px. Forcing 600px');
            this.height = 600;
        }
        
        this.svg
            .attr("width", this.width)
            .attr("height", this.height)
            .style("background", "var(--bg-primary)");
        
        this.svg.selectAll("*").remove();
        
        this.mainGroup = this.svg.append("g").attr("class", "main-group");
        this.linkGroup = this.mainGroup.append("g").attr("class", "links");
        this.linkLabelGroup = this.mainGroup.append("g").attr("class", "link-labels");
        this.trafficGroup = this.mainGroup.append("g").attr("class", "traffic-flow");
        this.nodeGroup = this.mainGroup.append("g").attr("class", "nodes");
        this.labelGroup = this.mainGroup.append("g").attr("class", "labels");
        this.ipLabelGroup = this.mainGroup.append("g").attr("class", "ip-labels");
    }

    setupZoom() {
        this.zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on("zoom", (event) => {
                this.mainGroup.attr("transform", event.transform);
            });
        
        this.svg.call(this.zoom);
    }

    // ============= EVENT LISTENERS =============
    
    setupEventListeners() {
        const appFilter = document.getElementById('app-filter');
        if (appFilter) {
            appFilter.addEventListener('change', () => {
                this.updateSelectedApps();
                this.updateFilterStats();
				this.broadcastFilterChange();
            });
        }
        
        const searchInput = document.getElementById('node-search');
        if (searchInput) {
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.searchNodes(e.target.value);
                }
            });
        }
        
        const upstreamCheck = document.getElementById('show-upstream');
        if (upstreamCheck) {
            upstreamCheck.addEventListener('change', (e) => {
                this.showUpstream = e.target.checked;
                this.updateNetworkData();
                this.render();
            });
        }
        
        const downstreamCheck = document.getElementById('show-downstream');
        if (downstreamCheck) {
            downstreamCheck.addEventListener('change', (e) => {
                this.showDownstream = e.target.checked;
                this.updateNetworkData();
                this.render();
            });
        }
        
        // Enhanced display options setup
        this.setupDisplayOptions();
        this.setupNodeTypeFilters();
    }

    // ============= ENHANCED DISPLAY OPTIONS =============
    
    setupDisplayOptions() {
        console.log('Setting up enhanced display options...');
        
        const options = [
            { 
                id: 'show-labels', 
                prop: 'showLabels', 
                handler: () => this.toggleLabels(),
                description: 'Node Labels'
            },
            { 
                id: 'show-ips', 
                prop: 'showIPs', 
                handler: () => this.toggleIPs(),
                description: 'IP Addresses'
            },
            { 
                id: 'show-link-labels', 
                prop: 'showLinkLabels', 
                handler: () => this.toggleLinkLabels(),
                description: 'Connection Types'
            },
            { 
                id: 'show-traffic', 
                prop: 'showTraffic', 
                handler: () => this.toggleTraffic(),
                description: 'Traffic Flow Animation'
            }
        ];
        
        options.forEach(opt => {
            const checkbox = document.getElementById(opt.id);
            if (checkbox) {
                console.log(`✓ Found checkbox: ${opt.id} (${opt.description})`);
                
                // Set initial state
                checkbox.checked = this.displayOptions[opt.prop];
                
                // Remove any existing handlers by cloning
                const newCheckbox = checkbox.cloneNode(true);
                checkbox.parentNode.replaceChild(newCheckbox, checkbox);
                
                // Add new event handler
                newCheckbox.addEventListener('change', (e) => {
                    console.log(`${opt.description} toggled to:`, e.target.checked);
                    this.displayOptions[opt.prop] = e.target.checked;
                    opt.handler();
                    
                    // Show notification
                    const action = e.target.checked ? 'enabled' : 'disabled';
                    this.showNotification(`${opt.description} ${action}`, 'info');
                });
                
                console.log(`✅ ${opt.description} checkbox setup complete`);
            } else {
                console.error(`✗ Missing checkbox: ${opt.id} (${opt.description})`);
            }
        });
        
        console.log('✅ All display options configured');
    }

    // ============= TOGGLE FUNCTIONS =============
    
    toggleLabels() {
        console.log(`Toggling node labels: ${this.displayOptions.showLabels}`);
        if (this.labelElements) {
            this.labelElements.style("display", this.displayOptions.showLabels ? "block" : "none");
        }
    }
    
    toggleIPs() {
        console.log(`Toggling IP labels: ${this.displayOptions.showIPs}`);
        if (this.ipLabelElements) {
            this.ipLabelElements.style("display", this.displayOptions.showIPs ? "block" : "none");
        }
    }
    
    toggleLinkLabels() {
        console.log(`Toggling connection type labels: ${this.displayOptions.showLinkLabels}`);
        
        if (this.displayOptions.showLinkLabels) {
            this.renderLinkLabels(this.filterData());
        } else {
            // Hide all link labels
            if (this.linkLabelGroup) {
                this.linkLabelGroup.selectAll("*").remove();
            }
        }
        
        // Update positions if labels are visible
        if (this.linkLabelElements && this.displayOptions.showLinkLabels) {
            this.updateLinkLabelPositions();
        }
    }

    toggleTraffic() {
        console.log(`Toggling traffic flow animation: ${this.displayOptions.showTraffic}`);
        
        if (this.displayOptions.showTraffic) {
            this.startTrafficAnimation();
        } else {
            this.stopTrafficAnimation();
        }
        
        this.renderTrafficFlow();
    }

    // ============= TRAFFIC ANIMATION SYSTEM =============
    
    startTrafficAnimation() {
        if (this.isTrafficAnimating) {
            console.log('Traffic animation already running');
            return;
        }

        console.log('Starting traffic animation');
        this.isTrafficAnimating = true;
        this.animateTrafficLoop();
    }

    stopTrafficAnimation() {
        console.log('Stopping traffic animation');
        this.isTrafficAnimating = false;
        
        if (this.trafficAnimationId) {
            clearTimeout(this.trafficAnimationId);
            this.trafficAnimationId = null;
        }
        
        // Remove all traffic particles
        if (this.trafficGroup) {
            this.trafficGroup.selectAll('.traffic-particle').remove();
        }
        
        if (this.trafficParticles) {
            this.trafficParticles.interrupt();
        }
    }

    animateTrafficLoop() {
        if (!this.isTrafficAnimating || !this.displayOptions.showTraffic) {
            return;
        }

        this.createAndAnimateTrafficParticles();

        this.trafficAnimationId = setTimeout(() => {
            if (this.isTrafficAnimating && this.displayOptions.showTraffic) {
                this.animateTrafficLoop();
            }
        }, 2500);
    }

    createAndAnimateTrafficParticles() {
        if (!this.displayOptions.showTraffic || !this.networkData || !this.networkData.links) {
            return;
        }

        const data = this.filterData();
        const activeLinks = data.links.filter(link => 
            link.status === 'active' && 
            link.source && link.target &&
            typeof link.source.x === 'number' && typeof link.target.x === 'number'
        );

        if (activeLinks.length === 0) {
            return;
        }

        const particles = this.trafficGroup.selectAll('.traffic-particle')
            .data(activeLinks, d => `traffic-${d.source.id || d.source}-${d.target.id || d.target}`)
            .enter()
            .append('circle')
            .attr('class', 'traffic-particle')
            .attr('r', 3)
            .attr('fill', d => this.getTrafficColor(d))
            .attr('opacity', 0.9)
            .attr('cx', d => d.source.x || 0)
            .attr('cy', d => d.source.y || 0)
            .style('pointer-events', 'none');

        particles
            .transition()
            .duration(2000)
            .ease(d3.easeLinear)
            .attr('cx', d => d.target.x || 0)
            .attr('cy', d => d.target.y || 0)
            .attr('opacity', 0.1)
            .on('end', function() {
                d3.select(this).remove();
            });
    }

    getTrafficColor(link) {
        if (link.protocol === 'HTTPS' || link.protocol === 'SSL') return '#10b981';
        if (link.protocol === 'HTTP') return '#3b82f6';
        if (link.protocol === 'TCP') return '#8b5cf6';
        if (link.protocol === 'UDP') return '#f59e0b';
        return '#fbbf24';
    }
	
	
    renderTrafficFlow() {
        if (!this.displayOptions.showTraffic || !this.networkData || !this.networkData.links) {
            if (this.trafficGroup) {
                this.trafficGroup.selectAll("*").remove();
            }
            this.stopTrafficAnimation();
            return;
        }

        console.log('Rendering traffic flow elements');
        
        if (!this.trafficGroup) {
            this.trafficGroup = this.mainGroup.append("g").attr("class", "traffic-flow");
        }

        if (!this.isTrafficAnimating) {
            this.startTrafficAnimation();
        }
    }

    // ============= NOTIFICATION SYSTEM =============
    
    showNotification(message, type = 'info') {
        let container = document.getElementById('topology-notifications');
        if (!container) {
            container = document.createElement('div');
            container.id = 'topology-notifications';
            container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
                display: flex;
                flex-direction: column;
                align-items: flex-end;
                gap: 8px;
                pointer-events: none;
            `;
            document.body.appendChild(container);
        }
        
        const notification = document.createElement('div');
        notification.className = `topology-notification ${type}`;
        
        const typeColors = {
            'success': '#10b981',
            'info': '#3b82f6', 
            'warning': '#f59e0b',
            'error': '#ef4444'
        };
        
        const typeIcons = {
            'success': '✅',
            'info': 'ℹ️',
            'warning': '⚠️',
            'error': '❌'
        };
        
        notification.style.cssText = `
            background: rgba(15, 23, 42, 0.95);
            color: #f1f5f9;
            padding: 8px 12px;
            border-radius: 6px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(8px);
            border-left: 3px solid ${typeColors[type] || typeColors.info};
            font-size: 12px;
            max-width: 300px;
            animation: slideInRight 0.3s ease;
            pointer-events: auto;
            cursor: pointer;
        `;
        
        notification.innerHTML = `${typeIcons[type] || typeIcons.info} ${message}`;
        notification.onclick = () => notification.remove();
        
        container.appendChild(notification);
        
        setTimeout(() => {
            if (notification.parentNode) {
                notification.style.animation = 'slideOutRight 0.3s ease';
                setTimeout(() => notification.remove(), 300);
            }
        }, 3000);
    }

    setupNodeTypeFilters() {
        const filters = {
            'filter-servers': ['web-tier', 'frontend', 'backend', 'app-tier'],
            'filter-databases': ['database', 'storage', 'data-tier'],
            'filter-load-balancers': ['gateway', 'api-gateway', 'load-balancer'],
            'filter-microservices': ['service', 'microservice', 'worker']
        };
        
        Object.entries(filters).forEach(([checkboxId, types]) => {
            const checkbox = document.getElementById(checkboxId);
            if (checkbox) {
                checkbox.addEventListener('change', (e) => {
                    if (e.target.checked) {
                        types.forEach(t => this.filteredNodeTypes.add(t));
                    } else {
                        types.forEach(t => this.filteredNodeTypes.delete(t));
                    }
                    this.render();
                });
            }
        });
    }

    // ============= PANELS =============
    
    setupPanels() {
        document.querySelectorAll('.hamburger').forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const side = button.getAttribute('data-panel') || 
                           (button.closest('#left-panel') ? 'left' : 'right');
                this.togglePanel(side);
            });
        });
    }

    togglePanel(side) {
        const panel = document.getElementById(`${side}-panel`);
        if (!panel) return;
        
        const isCollapsed = this.panelStates[side];
        
        if (isCollapsed) {
            panel.classList.remove('collapsed');
            this.panelStates[side] = false;
        } else {
            panel.classList.add('collapsed');
            this.panelStates[side] = true;
        }
        
        setTimeout(() => this.handleResize(), 300);
    }

    // ============= FILTERS =============
    
    setupFilters() {
        const searchInput = document.getElementById('app-search');
        if (searchInput) {
            let timeout;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(timeout);
                timeout = setTimeout(() => {
                    this.filterApplicationList(e.target.value);
                }, 300);
            });
        }
    }

    populateApplicationFilter() {
        const select = document.getElementById('app-filter');
        if (!select) return;
        
        select.innerHTML = '';
        
        const allOption = document.createElement('option');
        allOption.value = 'all';
        allOption.textContent = 'ALL Applications';
        allOption.selected = true;
        select.appendChild(allOption);
        
        this.rawApplications.forEach(app => {
            if (app.id === 'all') return;
            
            const option = document.createElement('option');
            option.value = app.id;
            option.textContent = app.displayName || app.name;
            option.dataset.criticality = app.criticality || '';
            option.dataset.businessFunction = app.businessFunction || '';
            
            if (app.criticality === 'critical') {
                option.style.color = '#ef4444';
                option.style.fontWeight = 'bold';
            }
            
            select.appendChild(option);
        });
        
        this.updateFilterStats();
    }

    filterApplicationList(query) {
        const select = document.getElementById('app-filter');
        if (!select) return;
        
        const lowerQuery = query.toLowerCase();
        let visible = 0;
        
        Array.from(select.options).forEach(option => {
            if (option.value === 'all' || !query) {
                option.style.display = '';
                visible++;
            } else {
                const matches = option.textContent.toLowerCase().includes(lowerQuery) ||
                              option.dataset.businessFunction?.toLowerCase().includes(lowerQuery);
                option.style.display = matches ? '' : 'none';
                if (matches) visible++;
            }
        });
        
        const stats = document.getElementById('app-filter-stats');
        if (stats) {
            stats.textContent = query ? 
                `${visible} apps match "${query}"` : 
                `${select.options.length} applications`;
        }
    }

    updateSelectedApps() {
        const select = document.getElementById('app-filter');
        if (!select) return;
        
        this.selectedApps = Array.from(select.selectedOptions).map(opt => opt.value);
        
        if (this.selectedApps.includes('all') || this.selectedApps.length === 0) {
            this.selectedApps = ['all'];
        }
    }

    updateFilterStats() {
        const stats = document.getElementById('app-filter-stats');
        if (stats) {
            const count = this.selectedApps.includes('all') ? 'All' : this.selectedApps.length;
            stats.textContent = `${count} applications selected`;
        }
    }
	
	broadcastFilterChange() {
		// Dispatch a custom event with current filter state
		const event = new CustomEvent('topologyFilterChanged', {
			detail: {
				selectedApps: this.selectedApps,
				showUpstream: this.showUpstream,
				showDownstream: this.showDownstream,
				filteredNodeTypes: Array.from(this.filteredNodeTypes),
				displayOptions: this.displayOptions,
				nodeCount: this.networkData.nodes ? this.networkData.nodes.length : 0,
				linkCount: this.networkData.links ? this.networkData.links.length : 0,
				timestamp: new Date().toISOString()
			},
			bubbles: true,
			cancelable: false
		});
		
		window.dispatchEvent(event);
		
		// Log for debugging
		console.log('Filter change broadcasted:', {
			apps: this.selectedApps.length,
			upstream: this.showUpstream,
			downstream: this.showDownstream
		});
	}
	
    // ============= DATA MANAGEMENT =============
    
    updateNetworkData() {
        if (window.AppData && window.AppData.generateNetworkTopology) {
            console.log('=== UPDATE NETWORK DATA ===');
            console.log('Selected Apps:', this.selectedApps);
            console.log('Show Upstream:', this.showUpstream);
            console.log('Show Downstream:', this.showDownstream);
            this.networkData = window.AppData.generateNetworkTopology(
                this.selectedApps,
                this.showUpstream,
                this.showDownstream
            );
            
            console.log('Generated nodes:', this.networkData.nodes.length);
            console.log('Generated links:', this.networkData.links.length);
            
            this.fixNetworkDataForAnimation();
            
            const linkTypes = {};
            this.networkData.links.forEach(link => {
                const type = link.linkType || 'unknown';
                linkTypes[type] = (linkTypes[type] || 0) + 1;
            });
            console.log('Link types:', linkTypes);
        }
        
        if (!this.networkData.nodes || this.networkData.nodes.length === 0) {
            console.warn('No valid network data, using fallback');
            this.useFallbackData();
        }
    }

    fixNetworkDataForAnimation() {
        console.log('🔧 Fixing network data for traffic animation...');
        
        if (!this.networkData || !this.networkData.links) {
            console.error('❌ No network data to fix');
            return;
        }
        
        console.log(`📊 Before fix: ${this.networkData.links.length} links`);
        
        this.networkData.links.forEach((link, i) => {
            if (!link.status) {
                link.status = 'active';
            }
            
            if (!link.protocol) {
                link.protocol = 'TCP';
            }
            
            if (!link.port) {
                link.port = '8080';
            }
            
            if (!link.bandwidth) {
                link.bandwidth = 100;
            }
            
            console.log(`  Link ${i + 1}: ${link.protocol} ${link.status}`);
        });
        
        this.networkData.nodes.forEach((node, i) => {
            if (typeof node.x !== 'number' || typeof node.y !== 'number') {
                const angle = (i / this.networkData.nodes.length) * 2 * Math.PI;
                const radius = 150;
                const centerX = this.width / 2 || 400;
                const centerY = this.height / 2 || 300;
                
                node.x = centerX + Math.cos(angle) * radius;
                node.y = centerY + Math.sin(angle) * radius;
                
                console.log(`  Node ${node.name}: positioned at (${node.x.toFixed(0)}, ${node.y.toFixed(0)})`);
            }
        });
        
        console.log('✅ Network data fixed for animation!');
    }
	
	updateNodeSelector() {
		const selector = document.getElementById('node-selector');
		if (!selector || !this.networkData || !this.networkData.nodes) return;
		
		const nodesByType = {};
		this.networkData.nodes.forEach(node => {
			const typeName = node.role || node.tier || node.type || 'Unknown';
			if (!nodesByType[typeName]) {
				nodesByType[typeName] = [];
			}
			nodesByType[typeName].push(node);
		});
		
		selector.innerHTML = '';
		Object.entries(nodesByType).forEach(([typeName, nodes]) => {
			const optgroup = document.createElement('optgroup');
			optgroup.label = typeName;
			
			nodes.forEach(node => {
				const option = document.createElement('option');
				option.value = node.id;
				option.textContent = `${node.name} (${node.ip})`;
				option.selected = this.selectedNodes.has(node.id);
				optgroup.appendChild(option);
			});
			
			selector.appendChild(optgroup);
		});
	}

    filterData() {
        if (!this.networkData.nodes) return { nodes: [], links: [] };
        
        const filteredNodes = this.networkData.nodes.filter(node => {
            return this.filteredNodeTypes.has(node.tier) || 
                   this.filteredNodeTypes.has(node.type);
        });
        
        const nodeIds = new Set(filteredNodes.map(n => n.id));
        const filteredLinks = this.networkData.links.filter(link => {
            const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
            const targetId = typeof link.target === 'object' ? link.target.id : link.target;
            return nodeIds.has(sourceId) && nodeIds.has(targetId);
        });
        
        return { nodes: filteredNodes, links: filteredLinks };
    }

    // ============= RENDERING =============
    
    render() {
        this.svg.selectAll(".empty-state").remove();
        
        const data = this.filterData();
        
        if (!data.nodes || data.nodes.length === 0) {
            this.renderEmptyState();
            return;
        }
        
        this.setupSimulation(data);
        this.renderLinks(data);
        this.renderNodes(data);
        this.renderLabels(data);
        this.renderTrafficFlow();
        
        if (this.displayOptions.showLinkLabels) {
            this.renderLinkLabels(data);
        }
		
		 // Update the node selector dropdown with current nodes
        this.updateNodeSelector();
    }

    renderEmptyState() {
        const g = this.svg.append("g").attr("class", "empty-state");
        
        g.append("text")
            .attr("x", this.width / 2)
            .attr("y", this.height / 2)
            .attr("text-anchor", "middle")
            .attr("fill", "var(--text-muted)")
            .text("No nodes to display");
    }

    setupSimulation(data) {
        console.log('Setting up simulation with', data.nodes.length, 'nodes');
        
        if (this.simulation) {
            this.simulation.stop();
        }
        
        data.nodes.forEach(node => {
            if (!node.x) node.x = this.width / 2 + (Math.random() - 0.5) * 100;
            if (!node.y) node.y = this.height / 2 + (Math.random() - 0.5) * 100;
        });
        
        this.simulation = d3.forceSimulation(data.nodes)
            .force("link", d3.forceLink(data.links)
                .id(d => d.id)
                .distance(100)
                .strength(0.5))
            .force("charge", d3.forceManyBody().strength(-300))
            .force("center", d3.forceCenter(this.width / 2, this.height / 2))
            .on("tick", () => this.updatePositions());
        
        this.simulation.tick(50);
    }

    applyLayout() {
        if (!this.simulation) return;
        
        switch (this.currentLayout) {
            case 'hierarchical':
                this.applyHierarchicalLayout();
                break;
            case 'circular':
                this.applyCircularLayout();
                break;
            case 'grid':
                this.applyGridLayout();
                break;
            default:
                this.simulation.alpha(0.3).restart();
        }
    }

    applyHierarchicalLayout() {
        const data = this.filterData();
        const layers = {};
        
        data.nodes.forEach(node => {
            const layer = node.tier === 'web-tier' ? 0 :
                         node.tier === 'app-tier' ? 1 :
                         node.tier === 'database' ? 2 : 3;
            if (!layers[layer]) layers[layer] = [];
            layers[layer].push(node);
        });
        
        Object.entries(layers).forEach(([layer, nodes]) => {
            const y = 100 + parseInt(layer) * 150;
            nodes.forEach((node, i) => {
                node.fx = 100 + i * ((this.width - 200) / (nodes.length || 1));
                node.fy = y;
            });
        });
        
        this.simulation.alpha(0.3).restart();
    }

    applyCircularLayout() {
        const data = this.filterData();
        const radius = Math.min(this.width, this.height) * 0.3;
        const center = { x: this.width / 2, y: this.height / 2 };
        
        data.nodes.forEach((node, i) => {
            const angle = (i / data.nodes.length) * 2 * Math.PI;
            node.fx = center.x + Math.cos(angle) * radius;
            node.fy = center.y + Math.sin(angle) * radius;
        });
        
        this.simulation.alpha(0.3).restart();
    }

    applyGridLayout() {
        const data = this.filterData();
        const cols = Math.ceil(Math.sqrt(data.nodes.length));
        const cellWidth = this.width / cols;
        const cellHeight = this.height / Math.ceil(data.nodes.length / cols);
        
        data.nodes.forEach((node, i) => {
            const col = i % cols;
            const row = Math.floor(i / cols);
            node.fx = cellWidth * (col + 0.5);
            node.fy = cellHeight * (row + 0.5);
        });
        
        this.simulation.alpha(0.3).restart();
    }

    renderLinks(data) {
        const links = this.linkGroup.selectAll("line")
            .data(data.links, d => `${d.source.id || d.source}-${d.target.id || d.target}`);
        
        links.exit().remove();
        
        const enter = links.enter().append("line")
            .attr("stroke", "#8b5cf6")
            .attr("stroke-opacity", 0.6)
            .attr("stroke-width", d => Math.sqrt(d.bandwidth / 100) || 1);
        
        this.linkElements = links.merge(enter);
    }

    renderNodes(data) {
        const nodes = this.nodeGroup.selectAll("circle")
            .data(data.nodes, d => d.id);
        
        nodes.exit().remove();
        
        const enter = nodes.enter().append("circle")
            .attr("r", 8)
            .attr("fill", d => this.getNodeColor(d))
            .attr("stroke", "#fff")
            .attr("stroke-width", 2)
            .call(this.drag())
            .on("mouseover", (event, d) => this.showTooltip(event, d))
            .on("mouseout", () => this.hideTooltip())
            .on("click", (event, d) => this.selectNode(d));
        
        this.nodeElements = nodes.merge(enter)
            .attr("fill", d => this.getNodeColor(d))
            .attr("stroke", d => this.selectedNodes.has(d.id) ? "#fbbf24" : "#fff");
    }

    renderLabels(data) {
        // Node labels
        const labels = this.labelGroup.selectAll("text")
            .data(data.nodes, d => d.id);
        
        labels.exit().remove();
        
        const enter = labels.enter().append("text")
            .attr("text-anchor", "middle")
            .attr("dy", -12)
            .attr("font-size", "10px")
            .attr("fill", "var(--text-primary)")
            .style("pointer-events", "none");
        
        this.labelElements = labels.merge(enter)
            .text(d => d.name)
            .style("display", this.displayOptions.showLabels ? "block" : "none");
        
        // IP labels
        const ipLabels = this.ipLabelGroup.selectAll("text")
            .data(data.nodes, d => d.id);
        
        ipLabels.exit().remove();
        
        const ipEnter = ipLabels.enter().append("text")
            .attr("text-anchor", "middle")
            .attr("dy", 25)
            .attr("font-size", "8px")
            .attr("fill", "var(--text-muted)")
            .style("pointer-events", "none");
        
        this.ipLabelElements = ipLabels.merge(ipEnter)
            .text(d => d.ip)
            .style("display", this.displayOptions.showIPs ? "block" : "none");
    }

    renderLinkLabels(data) {
        console.log(`🔗 renderLinkLabels called - showLinkLabels: ${this.displayOptions.showLinkLabels}`);
        
        if (!this.displayOptions.showLinkLabels || !data || !data.links) {
            console.log(`❌ Not rendering link labels - showLinkLabels: ${this.displayOptions.showLinkLabels}, links: ${data?.links?.length || 0}`);
            this.linkLabelGroup.selectAll("*").remove();
            return;
        }
        
        console.log(`✅ Rendering ${data.links.length} link labels`);
        
        const linkLabels = this.linkLabelGroup.selectAll("text.link-label")
            .data(data.links, d => `${d.source.id || d.source}-${d.target.id || d.target}`);
        
        linkLabels.exit().remove();
        
        const linkLabelsEnter = linkLabels.enter().append("text")
            .attr("class", "link-label")
            .attr("text-anchor", "middle")
            .attr("font-size", "9px")
            .attr("fill", "#fbbf24")
            .style("pointer-events", "none");
        
        this.linkLabelElements = linkLabels.merge(linkLabelsEnter)
            .text(d => `${d.protocol || 'TCP'}:${d.port || '80'}`)
            .style("display", this.displayOptions.showLinkLabels ? "block" : "none");
            
        console.log(`✅ Link labels created: ${this.linkLabelElements.size()} elements`);
    }

    updatePositions() {
        if (this.linkElements) {
            this.linkElements
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);
        }
        
        if (this.nodeElements) {
            this.nodeElements
                .attr("cx", d => d.x)
                .attr("cy", d => d.y);
        }
        
        if (this.labelElements) {
            this.labelElements
                .attr("x", d => d.x)
                .attr("y", d => d.y);
        }
        
        if (this.ipLabelElements) {
            this.ipLabelElements
                .attr("x", d => d.x)
                .attr("y", d => d.y);
        }
        
        if (this.linkLabelElements) {
            this.updateLinkLabelPositions();
        }
    }

    updateLinkLabelPositions() {
        if (this.linkLabelElements) {
            this.linkLabelElements
                .attr("x", d => (d.source.x + d.target.x) / 2)
                .attr("y", d => (d.source.y + d.target.y) / 2 - 5);
        }
    }

    drag() {
        return d3.drag()
            .on("start", (event, d) => {
                if (!event.active) this.simulation.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            })
            .on("drag", (event, d) => {
                d.fx = event.x;
                d.fy = event.y;
            })
            .on("end", (event, d) => {
                if (!event.active) this.simulation.alphaTarget(0);
                d.fx = null;
                d.fy = null;
            });
    }

    getNodeColor(node) {
        if (node.status === 'inactive') return '#64748b';
        
        const tier = (node.tier || '').toLowerCase();
        const name = (node.name || '').toLowerCase();
        
        if (tier.includes('web')) return '#3b82f6';
        if (tier.includes('database') || name.includes('data')) return '#eab308';
        if (tier.includes('gateway')) return '#8b5cf6';
        if (node.criticality === 'critical') return '#ef4444';
        if (tier.includes('app')) return '#10b981';
        
        return '#94a3b8';
    }

    // ============= INTERACTIONS =============
    
    selectNode(node) {
        if (this.selectedNodes.has(node.id)) {
            this.selectedNodes.delete(node.id);
        } else {
            this.selectedNodes.add(node.id);
        }
        this.render();
        this.updateStats();
    }

    searchNodes(query) {
        if (!query) {
            this.selectedNodes.clear();
            this.render();
            return;
        }
        
        const data = this.filterData();
        const matches = data.nodes.filter(n => 
            n.name.toLowerCase().includes(query.toLowerCase()) ||
            n.ip.includes(query)
        );
        
        this.selectedNodes.clear();
        matches.forEach(n => this.selectedNodes.add(n.id));
        this.render();
    }

    showTooltip(event, node) {
        const tooltip = document.getElementById('tooltip');
        if (!tooltip) return;
        
        tooltip.style.opacity = '1';
        tooltip.style.left = (event.pageX + 10) + 'px';
        tooltip.style.top = (event.pageY - 10) + 'px';
        tooltip.innerHTML = `
            <div><strong>${node.name}</strong></div>
            <div>Application: ${node.application || 'Unknown'}</div>
            <div>IP: ${node.ip}</div>
            <div>Status: ${node.status}</div>
            <div>Criticality: ${node.criticality || 'Medium'}</div>
        `;
    }

    hideTooltip() {
        const tooltip = document.getElementById('tooltip');
        if (tooltip) {
            tooltip.style.opacity = '0';
        }
    }

    // ============= STATS =============
    
    updateStats() {
        const data = this.filterData();
        const nodes = data.nodes || [];
        const links = data.links || [];
		
		console.log('Updating stats with:', nodes.length, 'nodes and', links.length, 'links');
		
		// Basic counts
        const nodeCount = nodes.length;
        const linkCount = links.length;
        const activeNodes = nodes.filter(n => n.status === 'active').length;
        const activeLinks = links.filter(l => l.status === 'active').length;
        
        // Calculate average degree (average number of connections per node)
        const avgDegree = nodeCount > 0 ? (linkCount * 2 / nodeCount).toFixed(1) : '0.0';
        
        // Calculate network density (how connected the network is)
        const maxPossibleLinks = nodeCount > 1 ? (nodeCount * (nodeCount - 1)) / 2 : 0;
        const density = maxPossibleLinks > 0 ? 
            ((linkCount / maxPossibleLinks) * 100).toFixed(1) + '%' : '0.0%';
        
        // Calculate clustering coefficient (simplified version)
        const clusteringCoeff = this.calculateClusteringCoefficient(nodes, links);
		
		const statUpdates = {
			'stat-nodes': nodeCount,
			'stat-links': activeLinks,
			'stat-avg-degree': avgDegree,
			'stat-density': density,
			'stat-clustering': clusteringCoeff,
			'totalNodes': nodeCount,
			'activeConnections': activeLinks.toLocaleString(),
			'networkClusters': this.selectedApps.length,
			'criticalPaths': this.selectedNodes.size
		};
		
		// Apply updates with error handling
		Object.entries(statUpdates).forEach(([id, value]) => {
			const element = document.getElementById(id);
			if (element) {
				element.textContent = value;
				console.log(`Updated ${id}: ${value}`);
			} else {
				console.warn(`Stats element not found: ${id}`);
			}
		});
		
		console.log('Stats update complete');
	}
	
	calculateClusteringCoefficient(nodes, links) {
        if (nodes.length < 3) return '0.00';
        
        try {
            // Build adjacency list
            const adjacency = {};
            nodes.forEach(node => {
                adjacency[node.id] = new Set();
            });
            
            links.forEach(link => {
                const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
                const targetId = typeof link.target === 'object' ? link.target.id : link.target;
                
                if (adjacency[sourceId] && adjacency[targetId]) {
                    adjacency[sourceId].add(targetId);
                    adjacency[targetId].add(sourceId);
                }
            });
            
            let totalCoefficient = 0;
            let nodeCount = 0;
            
            // Calculate clustering for each node
            Object.entries(adjacency).forEach(([nodeId, neighbors]) => {
                const neighborArray = Array.from(neighbors);
                const k = neighborArray.length;
                
                if (k < 2) return; // Need at least 2 neighbors
                
                let connectedPairs = 0;
                for (let i = 0; i < neighborArray.length; i++) {
                    for (let j = i + 1; j < neighborArray.length; j++) {
                        if (adjacency[neighborArray[i]].has(neighborArray[j])) {
                            connectedPairs++;
                        }
                    }
                }
                
                const possiblePairs = (k * (k - 1)) / 2;
                const coefficient = possiblePairs > 0 ? connectedPairs / possiblePairs : 0;
                totalCoefficient += coefficient;
                nodeCount++;
            });
            
            const avgClusteringCoeff = nodeCount > 0 ? totalCoefficient / nodeCount : 0;
            return avgClusteringCoeff.toFixed(2);
            
        } catch (error) {
            console.warn('Error calculating clustering coefficient:', error);
            return '0.00';
        }
    }

    // ============= UTILITIES =============
    
    handleResize() {
        const rect = this.container.node().getBoundingClientRect();
        this.width = rect.width;
        this.height = rect.height;
        
        this.svg.attr("width", this.width).attr("height", this.height);
        
        if (this.simulation) {
            this.simulation.force("center", d3.forceCenter(this.width / 2, this.height / 2));
            this.simulation.alpha(0.3).restart();
        }
    }

    zoomIn() {
        this.svg.transition().call(this.zoom.scaleBy, 1.5);
    }

    zoomOut() {
        this.svg.transition().call(this.zoom.scaleBy, 0.67);
    }

    resetView() {
        this.svg.transition().call(this.zoom.transform, d3.zoomIdentity);
    }
	
	panDirection(direction) {
        // Get current transform
        const transform = d3.zoomTransform(this.svg.node());
        const panDistance = 50; // Distance to pan in pixels
        
        let newTransform;
        switch (direction) {
            case 'up':
                newTransform = transform.translate(0, panDistance);
                break;
            case 'down':
                newTransform = transform.translate(0, -panDistance);
                break;
            case 'left':
                newTransform = transform.translate(panDistance, 0);
                break;
            case 'right':
                newTransform = transform.translate(-panDistance, 0);
                break;
            default:
                console.warn('Invalid pan direction:', direction);
                return;
        }
        
        if (newTransform) {
            this.svg.transition().duration(300).call(this.zoom.transform, newTransform);
        }
    }
	centerView() {
        // Get current transform
        const transform = d3.zoomTransform(this.svg.node());
        
        // Create centered transform that maintains current zoom level
        const centerTransform = d3.zoomIdentity
            .translate(this.width / 2, this.height / 2)
            .scale(transform.k);
        
        this.svg.transition().duration(500).call(this.zoom.transform, centerTransform);
    }

    setLayout(layout) {
        this.currentLayout = layout;
        document.querySelectorAll('.topology-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.getElementById(`${layout}-btn`)?.classList.add('active');
        this.applyLayout();
    }
}

// ============= GLOBAL FUNCTIONS =============
function createToast(message, type = 'info') {
    if (window.topologyDashboard) {
        window.topologyDashboard.showNotification(message, type);
    } else {
        console.log(`${type.toUpperCase()}: ${message}`);
    }
}

function applyApplicationFilter() {
    if (window.topologyDashboard) {
        window.topologyDashboard.updateSelectedApps();
	//	window.topologyDashboard.broadcastFilterChange();
        window.topologyDashboard.updateNetworkData();
        window.topologyDashboard.render();
        window.topologyDashboard.updateStats();

    }
}

function selectAllApps() {
    const select = document.getElementById('app-filter');
    if (select) {
        Array.from(select.options).forEach(opt => {
            opt.selected = opt.value === 'all';
        });
    }
}

function selectCriticalApps() {
    const select = document.getElementById('app-filter');
    if (select) {
        Array.from(select.options).forEach(opt => {
            opt.selected = opt.dataset.criticality === 'critical';
        });
    }
}

function clearAllApps() {
    const select = document.getElementById('app-filter');
    if (select) {
        // Clear all selections
        Array.from(select.options).forEach(opt => {
            opt.selected = false;
        });
        
        // Force the first option (should be "all") to be selected
        // since the dashboard requires at least one selection
        //if (select.options[0]) {
        //    select.options[0].selected = true;
       // }
        
        // Update the dashboard
        if (window.topologyDashboard) {
            window.topologyDashboard.updateSelectedApps();
            window.topologyDashboard.updateNetworkData();
            window.topologyDashboard.render();
            window.topologyDashboard.updateStats();
           // window.topologyDashboard.broadcastFilterChange();
        }
    }
}

function selectByArchetype(archetype) {
    // Implementation would go here
}

function focusOnApplication() {
    if (window.topologyDashboard) {
        window.topologyDashboard.updateNetworkData();
        window.topologyDashboard.render();
    }
}

// Control functions
function zoomIn() { window.topologyDashboard?.zoomIn(); }
function zoomOut() { window.topologyDashboard?.zoomOut(); }
function resetView() { window.topologyDashboard?.resetView(); }
function centerView() { window.topologyDashboard?.resetView(); }
function panDirection(dir) { window.topologyDashboard?.panDirection(dir); }
function setLayout(layout) { window.topologyDashboard?.setLayout(layout); }

// Placeholder functions
function analyzeTraffic() { console.log('Traffic analysis'); }
function findCriticalPaths() { console.log('Critical paths'); }
function detectClusters() { console.log('Cluster detection'); }
function exportTopology() { console.log('Export topology'); }
function closeOverlay() { document.getElementById('overlay-canvas').style.display = 'none'; }

// ============= INITIALIZATION =============

document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing Network Topology Dashboard');
    new NetworkTopologyDashboard();
});