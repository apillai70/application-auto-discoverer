// Network Topology Visualization - Fixed Version
// Add this at the top of your topology.js file
class ACTIVnetConfig {
    static getApiUrl() {
        const hostname = window.location.hostname;
        
        console.log(`🌐 Frontend running on: ${hostname}`);
        
        // Map hostnames to API URLs
        if (hostname === 'localhost' || hostname === '127.0.0.1') {
            return 'http://localhost:8001';  // Development
        } else if (hostname === 'activnet.prutech' || hostname === '192.168.15.207') {
            return `http://${hostname}:8001`;  // Production
        } else {
            // Fallback - same hostname, port 8001
            return `http://${hostname}:8001`;
        }
    }
    
    static async testApiConnection() {
        const apiUrl = this.getApiUrl();
        try {
            const response = await fetch(`${apiUrl}/health`);
            if (response.ok) {
                console.log('✅ API connection successful');
                return { success: true, url: apiUrl };
            } else {
                console.warn('⚠️ API responded but not healthy');
                return { success: false, url: apiUrl, error: 'Unhealthy response' };
            }
        } catch (error) {
            console.error('❌ API connection failed:', error);
            return { success: false, url: apiUrl, error: error.message };
        }
    }
    
    static showConnectionStatus() {
        // Add connection status to your UI
        const statusDiv = document.createElement('div');
        statusDiv.id = 'api-status';
        statusDiv.style.cssText = `
            position: fixed; top: 10px; right: 10px; 
            background: rgba(0,0,0,0.8); color: white; 
            padding: 8px 12px; border-radius: 5px; font-size: 12px;
            z-index: 10000; font-family: monospace;
        `;
        document.body.appendChild(statusDiv);
        
        this.testApiConnection().then(result => {
            statusDiv.innerHTML = result.success 
                ? `🟢 API: ${result.url}` 
                : `🔴 API: ${result.error}`;
        });
    }
}

// SINGLE NetworkTopologyDashboard class definition - FIXED
class NetworkTopologyDashboard {
    constructor() {
        this.svg = d3.select("#graph");
        this.container = d3.select("#middle-canvas-wrapper");
        this.tooltip = d3.select("#tooltip");
        
        this.width = 0;
        this.height = 0;
        this.currentLayout = 'force';
        this.selectedNodes = new Set();
        this.selectedApps = ['all'];
        this.showUpstream = false;
        this.showDownstream = false;
        this.showTrafficFlow = false;
        
        this.filteredNodeTypes = new Set();
        
        this.displayOptions = {
            showLabels: true,
            showIPs: false,
            showLinkLabels: true,
            showTraffic: false
        };
        
        this.panelStates = {
            left: false,
            right: false
        };
        
        this.networkData = { nodes: [], links: [] };
        this.simulation = null;
        this.zoom = null;
        
        // FIXED: Add traffic animation control properties
        this.trafficAnimationId = null;
        this.isTrafficAnimating = false;
        this.trafficParticles = null;
        
        // Set API URL using the new config
        this.apiUrl = ACTIVnetConfig.getApiUrl();
        console.log(`🔌 API URL configured: ${this.apiUrl}`);
        
        // Show connection status
        ACTIVnetConfig.showConnectionStatus();
        
        // Test API connection before proceeding
        this.initializeWithApiCheck();
    }

    async initializeWithApiCheck() {
		console.log('🔍 Testing API connection before initialization...');
    
		// Since we know network endpoints don't exist, force demo mode
		const hasNetworkEndpoints = false; // Set to true when you add network APIs
		
		if (!hasNetworkEndpoints) {
			console.log('🔧 Network endpoints not available - using demo data');
			this.showNotification('Using demo data - network endpoints not configured', 'info');
			this.useOrGenerateFallbackData();
			this.init();
			setTimeout(() => this.populateApplicationFilter(), 100);
			return;
		}
        const apiStatus = await ACTIVnetConfig.testApiConnection();
        
        if (apiStatus.success) {
            console.log('✅ API available, initializing with API data...');
            this.initializeWithCentralizedData();
        } else {
            console.warn('⚠️ API unavailable, initializing with fallback data...');
            this.showNotification('API connection failed - using demo data', 'warning');
            
            // Initialize with fallback data immediately
            this.useOrGenerateFallbackData();
            this.init();
            
            // Still try to populate application filter from centralized data if available
            setTimeout(() => {
                this.populateApplicationFilter();
            }, 100);
        }
    }
    
    // Update your existing updateNetworkData method with improved error handling
    async updateNetworkData() {
        // Try multiple API endpoints
        const endpoints = [
            `${this.apiUrl}/api/v1/network/data`,
            `${this.apiUrl}/api/network/topology`,
            `${this.apiUrl}/network/data`,
            `${this.apiUrl}/topology/data`
        ];
        
        let lastError = null;
        
        for (const endpoint of endpoints) {
            try {
                console.log(`🔍 Trying API endpoint: ${endpoint}`);
                const response = await fetch(endpoint);
                
                if (response.ok) {
                    const data = await response.json();
                    
                    // Validate data structure
                    if (data && (data.nodes || data.links)) {
                        this.networkData = data;
                        this.fixNetworkDataForAnimation();
                        
                        console.log(`✅ Loaded network data from ${endpoint}: ${data.nodes?.length || 0} nodes, ${data.links?.length || 0} links`);
                        this.showNotification('Connected to API - Live data loaded', 'success');
                        return; // Success! Exit the function
                    } else {
                        console.warn(`⚠️ Invalid data structure from ${endpoint}:`, data);
                    }
                } else {
                    console.warn(`⚠️ HTTP ${response.status} from ${endpoint}`);
                    lastError = new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
            } catch (error) {
                console.warn(`⚠️ Failed to fetch from ${endpoint}:`, error.message);
                lastError = error;
            }
        }
        
        // All API endpoints failed, use fallback data
        console.warn('❌ All API endpoints failed, using fallback data');
        if (lastError) {
            console.error('❌ Last error:', lastError);
        }
        
        this.useOrGenerateFallbackData();
    }
    
    useOrGenerateFallbackData() {
		console.log('🔄 Using fallback network data...');
		
		// Initialize filter types if not done yet
		if (!this.filteredNodeTypes || this.filteredNodeTypes.size === 0) {
			this.initializeDefaultFilterTypes();
		}
		
		// Try to get data from centralized AppData first
		if (window.AppData && window.AppData.generateNetworkTopology) {
			try {
				this.networkData = window.AppData.generateNetworkTopology(
					this.selectedApps, 
					this.showUpstream, 
					this.showDownstream
				);
				
				if (this.networkData && this.networkData.nodes && this.networkData.nodes.length > 0) {
					console.log('✅ Using AppData for network topology');
					this.fixNetworkDataForAnimation();
					this.showNotification('Using centralized data - no API connection', 'info');
					return;
				}
			} catch (error) {
				console.warn('⚠️ Failed to get data from AppData:', error);
			}
		}
		
		// Generate demo/fallback data
		this.networkData = this.generateFallbackNetworkData();
		this.fixNetworkDataForAnimation();
		console.log(`✅ Generated fallback data: ${this.networkData.nodes?.length || 0} nodes, ${this.networkData.links?.length || 0} links`);
		
		// Verify the data will pass filtering
		const testFilter = this.filterData();
		console.log(`🧪 Filter test: ${testFilter.nodes.length} nodes will be visible after filtering`);
		
		this.showNotification('API unavailable - using demo data', 'warning');
	}
    
    // ================================================================================
    // CENTRALIZED DATA INTEGRATION - FIXED
    // ================================================================================
    
    initializeWithCentralizedData() {
        const attemptInitialization = () => {
            if (!window.AppData) {
                console.warn('⚠️ AppData not available, retrying in 100ms...');
                setTimeout(attemptInitialization, 100);
                return;
            }
        
            if (!window.AppData.isDataLoaded) {
                console.warn('⚠️ AppData not loaded yet, waiting for data...');
                window.AppData.onDataLoaded(() => {
                    console.log('✅ AppData loaded, initializing topology...');
                    this.performInitialization();
                });
                return;
            }
        
            console.log('✅ AppData available and loaded, initializing immediately...');
            this.performInitialization();
        };
    
        attemptInitialization();
    }

    performInitialization() {
        this.populateApplicationFilter();
        this.updateNetworkData();
        this.init();
    
        setTimeout(() => {
            this.populateApplicationFilter();
        }, 1000);
        
        // Listen for filter changes from other components
        if (window.AppData && window.AppData.onFilterChange) {
            window.AppData.onFilterChange((filterData) => {
                if (filterData.source !== 'topology' && filterData.selectedApps) {
                    console.log('📡 Topology received filter update from:', filterData.source);
                    this.syncExternalFilterChange(filterData);
                }
            });
        }
    }
    
    syncExternalFilterChange(filterData) {
        this.selectedApps = filterData.selectedApps || ['all'];
        
        if (filterData.includeUpstream !== undefined) {
            this.showUpstream = filterData.includeUpstream;
        }
        if (filterData.includeDownstream !== undefined) {
            this.showDownstream = filterData.includeDownstream;
        }
        
        this.updateApplicationFilterUI();
        this.updateFlowDirectionUI();
        this.updateNetworkData();
        this.render();
        this.updateStats();
        
        const appCount = this.selectedApps.includes('all') ? 'All' : this.selectedApps.length;
        this.showNotification(`Filter synchronized from ${filterData.source}: ${appCount} applications`, 'info');
    }
    
    updateApplicationFilterUI() {
        const select = document.getElementById('app-filter');
        if (!select) return;
        
        Array.from(select.options).forEach(option => {
            option.selected = this.selectedApps.includes(option.value);
        });
    }
    
    updateFlowDirectionUI() {
        const upstreamCheck = document.getElementById('show-upstream');
        const downstreamCheck = document.getElementById('show-downstream');
        
        if (upstreamCheck) upstreamCheck.checked = this.showUpstream;
        if (downstreamCheck) downstreamCheck.checked = this.showDownstream;
    }
    
    broadcastFilterChange() {
        if (window.AppData && window.AppData.syncFilterAcrossComponents) {
            window.AppData.syncFilterAcrossComponents({
                selectedApps: this.selectedApps,
                includeUpstream: this.showUpstream,
                includeDownstream: this.showDownstream,
                source: 'topology',
                timestamp: Date.now(),
                context: {
                    layout: this.currentLayout,
                    displayOptions: this.displayOptions,
                    selectedNodes: Array.from(this.selectedNodes)
                }
            });
            
            console.log('📡 Topology broadcasted filter change:', this.selectedApps.length, 'applications');
        }
    }
    
    // ================================================================================
    // APPLICATION FILTER - FIXED
    // ================================================================================
    // Add a method to initialize default filter types
	initializeDefaultFilterTypes() {
		console.log('🔧 Initializing default filter types...');
		
		// Add all common node types to ensure fallback data shows up
		const defaultTypes = [
			// Server types
			'web-tier', 'frontend', 'web-server', 'backend', 'app-tier', 'processor',
			// Database types  
			'storage', 'database', 'data-tier', 'data-service',
			// Gateway types
			'gateway', 'api-gateway', 'load-balancer',
			// Service types
			'core-service', 'microservice', 'service', 'worker'
		];
		
		this.filteredNodeTypes = new Set(defaultTypes);
		console.log(`✅ Initialized ${defaultTypes.length} filter types:`, defaultTypes);
	}
	
    populateApplicationFilter() {
        console.log('🔄 Populating Topology application filter with centralized data...');
        
        if (!window.AppData) {
            console.warn('❌ AppData not available, retrying in 500ms...');
            setTimeout(() => this.populateApplicationFilter(), 500);
            return;
        }
        
        if (!window.AppData.isDataLoaded) {
            console.warn('❌ AppData not loaded yet, retrying in 500ms...');
            setTimeout(() => this.populateApplicationFilter(), 500);
            return;
        }
        
        const apps = window.AppData.getApplicationNamesForFilter ? 
                     window.AppData.getApplicationNamesForFilter() : 
                     this.generateFallbackApps();
        
        console.log('📊 Raw apps from AppData:', apps);
        
        if (!apps || apps.length === 0) {
            console.error('❌ No applications returned from AppData');
            return;
        }
        
        const select = document.getElementById('app-filter');
        if (!select) {
            console.warn('❌ Application filter select element not found');
            return;
        }
        
        console.log(`📋 Found ${apps.length} applications to populate`);
        
        select.innerHTML = '';
        
        const grouped = this.groupApplicationsForTopology(apps);
        console.log('📊 Grouped applications:', grouped);
        
        Object.entries(grouped).forEach(([groupName, appList]) => {
            if (appList.length === 0) {
                console.log(`⚠️ Skipping empty group: ${groupName}`);
                return;
            }
            
            console.log(`📂 Creating group: ${groupName} with ${appList.length} apps`);
            
            const optgroup = document.createElement('optgroup');
            optgroup.label = `${groupName} (${appList.length})`;
            
            appList.forEach((app, index) => {
                console.log(`  📱 Adding app ${index + 1}: ${app.id} - ${app.name}`);
                
                const option = document.createElement('option');
                option.value = app.id;
                option.textContent = app.displayName || app.name;
                option.selected = app.id === 'all' || this.selectedApps.includes(app.id);
                
                option.dataset.archetype = app.archetype || '';
                option.dataset.criticality = app.criticality || '';
                option.dataset.businessFunction = app.businessFunction || '';
                option.dataset.technology = app.technology || '';
                
                if (app.status && app.status !== 'active') {
                    option.textContent += ` (${app.status})`;
                    option.style.color = '#64748b';
                }
                
                if (app.criticality === 'critical') {
                    option.style.fontWeight = 'bold';
                    option.style.color = '#ef4444';
                }
                
                optgroup.appendChild(option);
            });
            
            select.appendChild(optgroup);
        });
        
        select.style.display = 'none';
        select.offsetHeight;
        select.style.display = '';
        
        console.log(`✅ Successfully populated topology filter with ${apps.length} applications in ${Object.keys(grouped).length} groups`);
        console.log(`📊 Final select element children: ${select.children.length}`);
        
        this.updateFilterStats();
    }
    
    // FIXED: Fallback app generation for testing
    generateFallbackApps() {
        return [
            { id: 'all', name: 'ALL Applications', displayName: 'ALL Applications' },
            { id: 'app1', name: 'Core Banking System', businessFunction: 'Core Banking', criticality: 'critical' },
            { id: 'app2', name: 'Customer Portal', businessFunction: 'Customer Services', criticality: 'high' },
            { id: 'app3', name: 'Risk Management', businessFunction: 'Risk & Compliance', criticality: 'high' },
            { id: 'app4', name: 'Payment Gateway', businessFunction: 'Core Banking', criticality: 'critical' }
        ];
    }
    
    groupApplicationsForTopology(apps) {
        console.log('🔄 Grouping applications for topology...');
        console.log('📊 Input apps:', apps);
        
        const grouped = {
            'All Applications': [],
            'Critical Systems': [],
            'Core Banking': [],
            'Risk & Compliance': [],
            'Customer Services': [],
            'Operations': [],
            'Other': []
        };
        
        if (!apps || !Array.isArray(apps)) {
            console.error('❌ Invalid apps array:', apps);
            return grouped;
        }
        
        apps.forEach((app, index) => {
            console.log(`📱 Processing app ${index + 1}:`, app);
            
            if (!app || typeof app !== 'object') {
                console.warn(`⚠️ Invalid app object at index ${index}:`, app);
                return;
            }
            
            if (app.id === 'all') {
                grouped['All Applications'].push(app);
                return;
            }
            
            if (app.criticality === 'critical') {
                console.log('  🔥 Adding to Critical Systems group');
                grouped['Critical Systems'].push(app);
            } else if (app.businessFunction) {
                console.log(`  📊 Business function: ${app.businessFunction}`);
                switch (app.businessFunction) {
                    case 'Core Banking':
                        console.log('  🏦 Adding to Core Banking group');
                        grouped['Core Banking'].push(app);
                        break;
                    case 'Risk & Compliance':
                    case 'Security & Identity':
                        console.log('  🛡️ Adding to Risk & Compliance group');
                        grouped['Risk & Compliance'].push(app);
                        break;
                    case 'Customer Management':
                    case 'Account Services':
                        console.log('  👥 Adding to Customer Services group');
                        grouped['Customer Services'].push(app);
                        break;
                    case 'Operations':
                    case 'Reporting & Analytics':
                        console.log('  ⚙️ Adding to Operations group');
                        grouped['Operations'].push(app);
                        break;
                    default:
                        console.log(`  📦 Adding to Other group (unknown business function: ${app.businessFunction})`);
                        grouped['Other'].push(app);
                }
            } else {
                console.log('  📦 Adding to Other group (no business function)');
                grouped['Other'].push(app);
            }
        });
        
        console.log('🔄 Processing groups...');
        Object.keys(grouped).forEach(groupName => {
            if (grouped[groupName].length === 0) {
                console.log(`🗑️ Removing empty group: ${groupName}`);
                delete grouped[groupName];
            } else {
                console.log(`✅ Group ${groupName}: ${grouped[groupName].length} apps`);
                grouped[groupName].sort((a, b) => {
                    const criticalityOrder = { 'critical': 4, 'high': 3, 'medium': 2, 'low': 1 };
                    const aCrit = criticalityOrder[a.criticality] || 1;
                    const bCrit = criticalityOrder[b.criticality] || 1;
                    
                    if (aCrit !== bCrit) return bCrit - aCrit;
                    return (a.name || '').localeCompare(b.name || '');
                });
            }
        });
        
        console.log('✅ Final grouped applications:', grouped);
        return grouped;
    }
    
    init() {
        this.setupSVG();
        this.setupZoom();
        this.setupEventListeners();
        this.setupApplicationFilter();
        this.setupFilters();
        this.setupPanelToggles();
        
        this.render();
        this.updateStats();
        
        window.addEventListener('resize', () => this.handleResize());
        window.addEventListener('themeChanged', () => this.handleThemeChange());
    }
    
    // ================================================================================
    // PANEL TOGGLE FUNCTIONALITY - FIXED
    // ================================================================================
    
	setupPanelToggles() {
		window.topologyDashboard = this;
		initPanelToggles();
		console.log('✅ Panel toggle functionality integrated');
	}
    
    ensurePanelCSS() {
        const styleId = 'topology-panel-styles';
        if (document.getElementById(styleId)) {
            document.getElementById(styleId).remove();
        }
        
        const style = document.createElement('style');
        style.id = styleId;
        style.textContent = `
            .topology-container #left-panel,
            .topology-container #right-panel {
                transition: width 0.3s ease, min-width 0.3s ease !important;
                overflow: hidden !important;
            }
            
            .topology-container #left-panel.collapsed,
            .topology-container #right-panel.collapsed {
                width: 60px !important;
                min-width: 60px !important;
                max-width: 60px !important;
                padding: 20px 10px !important;
            }
            
            .topology-container #left-panel.collapsed > *:not(.hamburger),
            .topology-container #right-panel.collapsed > *:not(.hamburger) {
                opacity: 0 !important;
                pointer-events: none !important;
                transform: translateX(-20px) !important;
                transition: all 0.3s ease !important;
                display: none !important;
            }
            
            .topology-container #left-panel:not(.collapsed) > *:not(.hamburger),
            .topology-container #right-panel:not(.collapsed) > *:not(.hamburger) {
                opacity: 1 !important;
                pointer-events: auto !important;
                transform: translateX(0) !important;
                transition: all 0.3s ease !important;
                display: block !important;
            }
            
            @keyframes slideInRight {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            
            @keyframes slideOutRight {
                from { transform: translateX(0); opacity: 1; }
                to { transform: translateX(100%); opacity: 0; }
            }
            
            body .topology-container #left-panel.collapsed {
                width: 60px !important;
                min-width: 60px !important;
                flex: 0 0 60px !important;
            }
            
            body .topology-container #right-panel.collapsed {
                width: 60px !important;
                min-width: 60px !important;
                flex: 0 0 60px !important;
            }
        `;
        document.head.appendChild(style);
        console.log('✅ Enhanced panel CSS styles added with high specificity');
    }
    
	togglePanel(side) {
		togglePanelSimple(side);
	}
    
    updateControlPositions() {
        const zoomControls = document.getElementById('zoom-controls');
        const navControls = document.getElementById('navigation-controls');
        
        if (zoomControls) {
            if (this.panelStates.right) {
                zoomControls.style.right = '80px';
            } else {
                zoomControls.style.right = '20px';
            }
        }
        
        if (navControls) {
            if (this.panelStates.right) {
                navControls.style.right = '80px';
            } else {
                navControls.style.right = '20px';
            }
        }
    }
    
    // ================================================================================
    // ENHANCED APPLICATION FILTER SETUP - FIXED
    // ================================================================================
    
    setupApplicationFilter() {
        const leftPanel = document.getElementById('left-panel');
        if (!leftPanel) return;
        
        const filterSection = document.createElement('div');
        filterSection.className = 'filter-section';
        filterSection.innerHTML = `
            <h4>📱 Filter by Application</h4>
            <div class="filter-header" style="margin-bottom: 8px;">
                <input type="text" id="app-search" placeholder="Search applications..." 
                       style="width: 100%; padding: 4px 8px; border: 1px solid var(--border-color); border-radius: 4px; background: var(--input-bg); color: var(--text-primary);">
            </div>
            <select id="app-filter" class="topology-select" multiple size="8" 
                    style="width: 100%; background: var(--input-bg); color: var(--text-primary); border: 1px solid var(--border-color);">
                <option value="all" selected>ALL Applications</option>
            </select>
            <div class="filter-stats" id="app-filter-stats" style="font-size: 11px; color: var(--text-muted); margin-top: 4px;">
                Loading applications...
            </div>
            <div style="margin-top: 8px; display: flex; gap: 4px; flex-wrap: wrap;">
                <button class="topology-btn-small" onclick="window.topologyDashboard && selectAllApps()">All</button>
                <button class="topology-btn-small" onclick="window.topologyDashboard && selectCriticalApps()">Critical</button>
                <button class="topology-btn-small" onclick="window.topologyDashboard && selectByArchetype('Microservices')">µServices</button>
                <button class="topology-btn-small" onclick="window.topologyDashboard && clearAllApps()">Clear</button>
            </div>
            <button class="topology-btn" onclick="window.topologyDashboard && applyApplicationFilter()" 
                    style="margin-top: 8px; width: 100%; background: var(--accent-blue); color: white;">
                🔍 Apply Filter
            </button>
        `;
        
        const flowSection = document.createElement('div');
        flowSection.className = 'filter-section';
        flowSection.innerHTML = `
            <h4>🔄 Application Dependencies</h4>
            <div style="margin-bottom: 12px; font-size: 12px; color: var(--text-muted);">
                Include related applications in topology view:
            </div>
            <label class="topology-label" style="display: flex; align-items: center; margin-bottom: 8px;">
                <input type="checkbox" class="topology-checkbox" id="show-upstream" style="margin-right: 8px;">
                <span>⬆️ Upstream Dependencies</span>
                <small style="display: block; color: var(--text-muted); margin-left: 20px; font-size: 10px;">
                    Apps that provide services to selected apps
                </small>
            </label>
            <label class="topology-label" style="display: flex; align-items: center; margin-bottom: 12px;">
                <input type="checkbox" class="topology-checkbox" id="show-downstream" style="margin-right: 8px;">
                <span>⬇️ Downstream Dependencies</span>
                <small style="display: block; color: var(--text-muted); margin-left: 20px; font-size: 10px;">
                    Apps that consume services from selected apps
                </small>
            </label>
            <button class="topology-btn" onclick="window.topologyDashboard && focusOnApplication()" style="margin-top: 8px; width: 100%;">
                🎯 Focus Mode
            </button>
        `;
        
        const firstInfo = leftPanel.querySelector('.info-panel');
        if (firstInfo) {
            leftPanel.insertBefore(filterSection, firstInfo.nextSibling);
            leftPanel.insertBefore(flowSection, filterSection.nextSibling);
        } else {
            leftPanel.appendChild(filterSection);
            leftPanel.appendChild(flowSection);
        }
        
        this.setupFilterEventListeners();
        this.setupApplicationSearch();
    }
    
    setupApplicationSearch() {
        const searchInput = document.getElementById('app-search');
        if (!searchInput) return;
        
        let searchTimeout;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            const query = e.target.value.trim().toLowerCase();
            
            searchTimeout = setTimeout(() => {
                this.filterApplicationList(query);
            }, 300);
        });
        
        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                e.target.value = '';
                this.filterApplicationList('');
            }
        });
    }
    
    filterApplicationList(query) {
        const select = document.getElementById('app-filter');
        if (!select) return;
        
        let visibleCount = 0;
        let totalCount = 0;
        
        Array.from(select.options).forEach(option => {
            totalCount++;
            
            if (!query || option.value === 'all') {
                option.style.display = '';
                visibleCount++;
                return;
            }
            
            const text = option.textContent.toLowerCase();
            const archetype = (option.dataset.archetype || '').toLowerCase();
            const businessFunction = (option.dataset.businessFunction || '').toLowerCase();
            const technology = (option.dataset.technology || '').toLowerCase();
            
            const matches = text.includes(query) || 
                          archetype.includes(query) || 
                          businessFunction.includes(query) || 
                          technology.includes(query);
            
            option.style.display = matches ? '' : 'none';
            if (matches) visibleCount++;
        });
        
        const statsEl = document.getElementById('app-filter-stats');
        if (statsEl) {
            if (query) {
                statsEl.textContent = `${visibleCount}/${totalCount} applications match "${query}"`;
            } else {
                statsEl.textContent = `${totalCount} applications available`;
            }
        }
    }
    
    setupFilterEventListeners() {
        const appFilter = document.getElementById('app-filter');
        if (appFilter) {
            appFilter.addEventListener('change', () => {
                this.updateSelectedApps();
                this.updateFilterStats();
                if (this.selectedApps.length === 1 && !this.selectedApps.includes('all')) {
                    setTimeout(() => {
                        if (window.applyApplicationFilter) {
                            applyApplicationFilter();
                        }
                    }, 500);
                }
            });
        }
        
        const upstreamCheck = document.getElementById('show-upstream');
        const downstreamCheck = document.getElementById('show-downstream');
        
        if (upstreamCheck) {
            upstreamCheck.addEventListener('change', (e) => {
                this.showUpstream = e.target.checked;
                this.updateNetworkData();
                this.render();
                this.broadcastFilterChange();
                
                const action = e.target.checked ? 'enabled' : 'disabled';
                this.showNotification(`Upstream dependencies ${action}`, 'info');
            });
        }
        
        if (downstreamCheck) {
            downstreamCheck.addEventListener('change', (e) => {
                this.showDownstream = e.target.checked;
                this.updateNetworkData();
                this.render();
                this.broadcastFilterChange();
                
                const action = e.target.checked ? 'enabled' : 'disabled';
                this.showNotification(`Downstream dependencies ${action}`, 'info');
            });
        }
    }
    
    updateFilterStats() {
        const statsEl = document.getElementById('app-filter-stats');
        if (!statsEl) return;
        
        const selectedCount = this.selectedApps.includes('all') ? 'All' : this.selectedApps.length;
        const totalApps = window.AppData ? window.AppData.applications?.length || 0 : 0;
        
        const upstreamText = this.showUpstream ? ' + Upstream' : '';
        const downstreamText = this.showDownstream ? ' + Downstream' : '';
        
        statsEl.textContent = `${selectedCount}/${totalApps} apps${upstreamText}${downstreamText}`;
    }
    
    updateSelectedApps() {
        const select = document.getElementById('app-filter');
        if (!select) return;
        
        const selectedOptions = Array.from(select.selectedOptions);
        this.selectedApps = selectedOptions.map(option => option.value);
        
        if (this.selectedApps.includes('all')) {
            this.selectedApps = ['all'];
            Array.from(select.options).forEach(option => {
                option.selected = option.value === 'all';
            });
        } else if (this.selectedApps.length === 0) {
            this.selectedApps = ['all'];
            const allOption = select.querySelector('option[value="all"]');
            if (allOption) allOption.selected = true;
        }
        
        console.log('📊 Selected apps updated:', this.selectedApps);
    }
    
    // ================================================================================
    // NETWORK DATA MANAGEMENT - FIXED
    // ================================================================================
    
	generateFallbackNetworkData() {
		console.log('🎯 Generating enhanced fallback network data...');
		
		const nodes = [
			{
				id: 'web1',
				name: 'Load Balancer',
				applicationId: 'app1',
				application: 'Core Banking System',
				tier: 'gateway',           // ✅ Matches filter
				type: 'load-balancer',    // ✅ Matches filter
				ip: '10.0.1.10',
				status: 'active',
				criticality: 'high',
				color: '#8b5cf6',
				x: 200,
				y: 150
			},
			{
				id: 'web2',
				name: 'Web Server',
				applicationId: 'app1',
				application: 'Core Banking System',
				tier: 'web-tier',         // ✅ Matches filter
				type: 'web-server',       // ✅ Matches filter
				ip: '10.0.1.20',
				status: 'active',
				criticality: 'high',
				color: '#3b82f6',
				x: 300,
				y: 150
			},
			{
				id: 'app1',
				name: 'App Server',
				applicationId: 'app1',
				application: 'Core Banking System',
				tier: 'app-tier',         // ✅ Matches filter
				type: 'backend',          // ✅ Matches filter
				ip: '10.0.2.10',
				status: 'active',
				criticality: 'critical',
				color: '#10b981',
				x: 400,
				y: 300
			},
			{
				id: 'svc1',
				name: 'Core Service',
				applicationId: 'app1',
				application: 'Core Banking System',
				tier: 'core-service',     // ✅ Matches filter
				type: 'service',          // ✅ Matches filter
				ip: '10.0.2.20',
				status: 'active',
				criticality: 'critical',
				color: '#ef4444',
				x: 500,
				y: 300
			},
			{
				id: 'db1',
				name: 'Primary Database',
				applicationId: 'app1',
				application: 'Core Banking System',
				tier: 'database',         // ✅ Matches filter
				type: 'storage',         // ✅ Matches filter
				ip: '10.0.3.10',
				status: 'active',
				criticality: 'critical',
				color: '#eab308',
				x: 400,
				y: 450
			},
			{
				id: 'cache1',
				name: 'Redis Cache',
				applicationId: 'app1',
				application: 'Core Banking System',
				tier: 'storage',          // ✅ Matches filter
				type: 'cache',
				ip: '10.0.2.30',
				status: 'active',
				criticality: 'medium',
				color: '#06b6d4',
				x: 200,
				y: 350
			}
		];
		
		const links = [
			{
				source: 'web1',
				target: 'web2',
				protocol: 'HTTP',
				port: '80',
				bandwidth: 1000,
				status: 'active',
				isInternal: true
			},
			{
				source: 'web2',
				target: 'app1',
				protocol: 'HTTPS',
				port: '8443',
				bandwidth: 800,
				status: 'active',
				isInternal: true
			},
			{
				source: 'app1',
				target: 'svc1',
				protocol: 'TCP',
				port: '9090',
				bandwidth: 600,
				status: 'active',
				isInternal: true
			},
			{
				source: 'svc1',
				target: 'db1',
				protocol: 'TCP',
				port: '5432',
				bandwidth: 500,
				status: 'active',
				isInternal: true
			},
			{
				source: 'app1',
				target: 'cache1',
				protocol: 'TCP',
				port: '6379',
				bandwidth: 200,
				status: 'active',
				isInternal: true
			}
		];
		
		console.log(`✅ Generated ${nodes.length} nodes and ${links.length} links with proper filter types`);
		return { nodes, links };
	}
    
    // FIXED: Integration of the console fix directly into the code
    fixNetworkDataForAnimation() {
        console.log('🔧 Fixing network data for traffic animation...');
        
        if (!this.networkData || !this.networkData.links) {
            console.error('❌ No network data to fix');
            return;
        }
        
        console.log(`📊 Before fix: ${this.networkData.links.length} links`);
        
        // Fix missing link properties
        this.networkData.links.forEach((link, i) => {
            // Add missing status
            if (!link.status) {
                link.status = 'active';
            }
            
            // Add missing protocol
            if (!link.protocol) {
                link.protocol = 'TCP';
            }
            
            // Add missing port
            if (!link.port) {
                link.port = '8080';
            }
            
            // Add missing bandwidth
            if (!link.bandwidth) {
                link.bandwidth = 100;
            }
            
            console.log(`  Link ${i + 1}: ${link.protocol} ${link.status}`);
        });
        
        // Ensure nodes have coordinates
        this.networkData.nodes.forEach((node, i) => {
            if (typeof node.x !== 'number' || typeof node.y !== 'number') {
                // Give nodes positions if they don't have them
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
    
    // ================================================================================
    // NOTIFICATION SYSTEM
    // ================================================================================
    
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
    
    // ================================================================================
    // FILTER METHODS - FIXED
    // ================================================================================
    
    selectCriticalApps() {
        if (!window.AppData) return;
        
        const apps = window.AppData.applications ? 
                     window.AppData.applications.filter(app => app.criticality === 'critical') :
                     [];
        const select = document.getElementById('app-filter');
        
        if (select) {
            Array.from(select.options).forEach(option => {
                option.selected = apps.some(app => app.id === option.value);
            });
            
            this.updateSelectedApps();
            this.updateFilterStats();
            this.showNotification(`Selected ${apps.length} critical applications`, 'info');
        }
    }
    
    selectByArchetype(archetype) {
        if (!window.AppData) return;
        
        const apps = window.AppData.applications ? 
                     window.AppData.applications.filter(app => app.archetype === archetype) :
                     [];
        const select = document.getElementById('app-filter');
        
        if (select) {
            Array.from(select.options).forEach(option => {
                option.selected = apps.some(app => app.id === option.value);
            });
            
            this.updateSelectedApps();
            this.updateFilterStats();
            this.showNotification(`Selected ${apps.length} ${archetype} applications`, 'info');
        }
    }
    
    selectByBusinessFunction(businessFunction) {
        if (!window.AppData) return;
        
        const apps = window.AppData.applications ? 
                     window.AppData.applications.filter(app => app.businessFunction === businessFunction) :
                     [];
        const select = document.getElementById('app-filter');
        
        if (select) {
            Array.from(select.options).forEach(option => {
                option.selected = apps.some(app => app.id === option.value);
            });
            
            this.updateSelectedApps();
            this.updateFilterStats();
            this.showNotification(`Selected ${apps.length} ${businessFunction} applications`, 'info');
        }
    }
    
    // ================================================================================
    // CORE FUNCTIONALITY CONTINUES...
    // ================================================================================
    
    setupFilters() {
        this.createDisplayOptionsSection();
        
        const filterCheckboxes = {
            'filter-servers': ['web-tier', 'frontend', 'web-server', 'backend', 'app-tier', 'processor'],
            'filter-databases': ['storage', 'database', 'data-tier', 'data-service'], 
            'filter-load-balancers': ['gateway', 'api-gateway', 'load-balancer'],
            'filter-microservices': ['core-service', 'microservice', 'service', 'worker']
        };
        
        Object.values(filterCheckboxes).forEach(nodeTypes => {
            nodeTypes.forEach(type => this.filteredNodeTypes.add(type));
        });
        
        Object.entries(filterCheckboxes).forEach(([checkboxId, nodeTypes]) => {
            const checkbox = document.getElementById(checkboxId);
            if (checkbox) {
                checkbox.checked = true;
                checkbox.addEventListener('change', (e) => {
                    console.log(`\n🔧 Filter ${checkboxId}: ${e.target.checked ? 'checked' : 'unchecked'}`);
                    
                    if (e.target.checked) {
                        nodeTypes.forEach(type => {
                            this.filteredNodeTypes.add(type);
                            console.log(`  ✅ Added ${type} to filter`);
                        });
                    } else {
                        nodeTypes.forEach(type => {
                            this.filteredNodeTypes.delete(type);
                            console.log(`  ❌ Removed ${type} from filter`);
                        });
                    }
                    
                    console.log(`🔍 Active filter types: [${Array.from(this.filteredNodeTypes).join(', ')}]`);
                    this.applyFilters();
                });
            }
        });
        
        // FIXED: Enhanced display options with proper traffic checkbox
        const displayOptions = {
            'show-labels': () => {
                this.displayOptions.showLabels = document.getElementById('show-labels')?.checked || false;
                console.log(`🏷️ Show Labels: ${this.displayOptions.showLabels}`);
                this.toggleLabels();
            },
            'show-ips': () => {
                this.displayOptions.showIPs = document.getElementById('show-ips')?.checked || false;
                console.log(`📍 Show IPs: ${this.displayOptions.showIPs}`);
                this.toggleIPLabels();
            },
            'show-link-labels': () => {
                this.displayOptions.showLinkLabels = document.getElementById('show-link-labels')?.checked || false;
                console.log(`🔗 Show Link Labels: ${this.displayOptions.showLinkLabels}`);
                this.toggleLinkLabels();
            }
        };
        
        Object.entries(displayOptions).forEach(([checkboxId, handler]) => {
            const checkbox = document.getElementById(checkboxId);
            if (checkbox) {
                if (checkboxId === 'show-labels') checkbox.checked = this.displayOptions.showLabels;
                if (checkboxId === 'show-link-labels') checkbox.checked = this.displayOptions.showLinkLabels;
                if (checkboxId === 'show-ips') checkbox.checked = this.displayOptions.showIPs;
                
                checkbox.addEventListener('change', handler);
            }
        });
        
        // FIXED: Separate traffic checkbox handler with proper animation control
        this.setupTrafficCheckbox();
    }
    
    // ================================================================================
    // FIXED TRAFFIC ANIMATION SYSTEM
    // ================================================================================
    
    setupTrafficCheckbox() {
        const trafficCheckbox = document.getElementById('show-traffic');
        if (!trafficCheckbox) {
            console.warn('Traffic checkbox not found');
            return;
        }
        
        // Remove any existing event listeners by cloning
        const newCheckbox = trafficCheckbox.cloneNode(true);
        trafficCheckbox.parentNode.replaceChild(newCheckbox, trafficCheckbox);
        
        // Set initial state
        newCheckbox.checked = this.displayOptions.showTraffic;
        
        // Add enhanced event listener
        newCheckbox.addEventListener('change', (e) => {
            this.displayOptions.showTraffic = e.target.checked;
            console.log(`🚦 Traffic checkbox changed: ${this.displayOptions.showTraffic}`);
            
            // Toggle animation
            this.toggleTrafficFlow();
            
            // Show notification
            const action = this.displayOptions.showTraffic ? 'enabled' : 'disabled';
            this.showNotification(`Traffic flow animation ${action}`, 'info');
        });
        
        console.log('✅ Traffic checkbox setup complete');
    }
    
    toggleTrafficFlow() {
        console.log(`🚦 Toggle traffic flow: ${this.displayOptions.showTraffic}`);
        
        if (this.displayOptions.showTraffic) {
            this.startTrafficAnimation();
        } else {
            this.stopTrafficAnimation();
        }
        
        // Update visual elements
        this.renderTrafficFlow();
    }

    startTrafficAnimation() {
        // Prevent multiple animations
        if (this.isTrafficAnimating) {
            console.log('⚠️ Traffic animation already running');
            return;
        }

        console.log('🚀 Starting traffic animation');
        this.isTrafficAnimating = true;
        
        // Start animation loop
        this.animateTrafficLoop();
    }

    stopTrafficAnimation() {
        console.log('🛑 Stopping traffic animation');
        this.isTrafficAnimating = false;
        
        // Clear animation timeout
        if (this.trafficAnimationId) {
            clearTimeout(this.trafficAnimationId);
            this.trafficAnimationId = null;
        }
        
        // Remove all traffic particles
        if (this.trafficGroup) {
            this.trafficGroup.selectAll('.traffic-particle').remove();
        }
        
        // Stop any ongoing transitions
        if (this.trafficParticles) {
            this.trafficParticles.interrupt();
        }
    }

    animateTrafficLoop() {
        if (!this.isTrafficAnimating || !this.displayOptions.showTraffic) {
            return;
        }

        // Create and animate traffic particles
        this.createAndAnimateTrafficParticles();

        // Schedule next cycle
        this.trafficAnimationId = setTimeout(() => {
            if (this.isTrafficAnimating && this.displayOptions.showTraffic) {
                this.animateTrafficLoop(); // Continue loop
            }
        }, 2500);
    }

    createAndAnimateTrafficParticles() {
        if (!this.displayOptions.showTraffic || !this.networkData || !this.networkData.links) {
            return;
        }

        // Filter for active links only
        const activeLinks = this.networkData.links.filter(link => 
            link.status === 'active' && 
            link.source && link.target &&
            typeof link.source.x === 'number' && typeof link.target.x === 'number'
        );

        if (activeLinks.length === 0) {
            return;
        }

        // Create particles for each active link
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

        // Animate particles along their links
        particles
            .transition()
            .duration(2000)
            .ease(d3.easeLinear)
            .attr('cx', d => d.target.x || 0)
            .attr('cy', d => d.target.y || 0)
            .attr('opacity', 0.1)
            .on('end', function() {
                // Remove particle after animation completes
                d3.select(this).remove();
            });
    }

    getTrafficColor(link) {
        if (link.protocol === 'HTTPS' || link.protocol === 'SSL') return '#10b981'; // Green for secure
        if (link.protocol === 'HTTP') return '#3b82f6'; // Blue for web
        if (link.protocol === 'TCP') return '#8b5cf6'; // Purple for TCP
        if (link.protocol === 'UDP') return '#f59e0b'; // Orange for UDP
        return '#fbbf24'; // Yellow default
    }
    
    // Continue with rest of methods...
    createDisplayOptionsSection() {
        const rightPanel = document.getElementById('right-panel');
        if (!rightPanel) {
            console.warn('Right panel not found, cannot create display options');
            return;
        }
        
        if (document.getElementById('display-options-section')) {
            console.log('Display options section already exists');
            return;
        }
        
        const displaySection = document.createElement('div');
        displaySection.id = 'display-options-section';
        displaySection.className = 'info-panel';
        displaySection.innerHTML = `
            <h4>🎨 Display Options</h4>
            <div class="display-controls">
                <label class="topology-label">
                    <input type="checkbox" id="show-labels" class="topology-checkbox" ${this.displayOptions.showLabels ? 'checked' : ''}>
                    <span>Show Node Labels</span>
                </label>
                
                <label class="topology-label">
                    <input type="checkbox" id="show-link-labels" class="topology-checkbox" ${this.displayOptions.showLinkLabels ? 'checked' : ''}>
                    <span>Show Link Labels</span>
                </label>
                
                <label class="topology-label">
                    <input type="checkbox" id="show-ips" class="topology-checkbox" ${this.displayOptions.showIPs ? 'checked' : ''}>
                    <span>Show IP Addresses</span>
                </label>
                
                <label class="topology-label">
                    <input type="checkbox" id="show-traffic" class="topology-checkbox" ${this.displayOptions.showTraffic ? 'checked' : ''}>
                    <span>Show Traffic Flow</span>
                </label>
            </div>
        `;
        
        const filtersSection = document.createElement('div');
        filtersSection.id = 'node-filters-section';
        filtersSection.className = 'info-panel';
        filtersSection.innerHTML = `
            <h4>🔧 Node Type Filters</h4>
            <div class="filter-controls">
                <label class="topology-label">
                    <input type="checkbox" id="filter-servers" class="topology-checkbox" checked>
                    <span>Servers & Apps</span>
                </label>
                
                <label class="topology-label">
                    <input type="checkbox" id="filter-databases" class="topology-checkbox" checked>
                    <span>Databases</span>
                </label>
                
                <label class="topology-label">
                    <input type="checkbox" id="filter-load-balancers" class="topology-checkbox" checked>
                    <span>Load Balancers</span>
                </label>
                
                <label class="topology-label">
                    <input type="checkbox" id="filter-microservices" class="topology-checkbox" checked>
                    <span>Microservices</span>
                </label>
            </div>
        `;
        
        this.addDisplayOptionsCSS();
        
        const existingPanels = rightPanel.querySelectorAll('.info-panel');
        if (existingPanels.length > 0) {
            existingPanels[0].insertAdjacentElement('afterend', displaySection);
            displaySection.insertAdjacentElement('afterend', filtersSection);
        } else {
            const hamburger = rightPanel.querySelector('.hamburger');
            if (hamburger) {
                hamburger.insertAdjacentElement('afterend', displaySection);
                displaySection.insertAdjacentElement('afterend', filtersSection);
            } else {
                rightPanel.appendChild(displaySection);
                rightPanel.appendChild(filtersSection);
            }
        }
        
        console.log('✅ Created display options and node filters sections');
    }
    
    addDisplayOptionsCSS() {
        const styleId = 'topology-display-options-styles';
        if (document.getElementById(styleId)) {
            return;
        }
        
        const style = document.createElement('style');
        style.id = styleId;
        style.textContent = `
            .topology-label {
                display: flex;
                align-items: center;
                margin-bottom: 8px;
                font-size: 13px;
                cursor: pointer;
                transition: color 0.2s ease;
                color: var(--text-primary, #f1f5f9);
            }
            
            .topology-label:hover {
                color: var(--accent-blue, #3b82f6);
            }
            
            .topology-checkbox {
                margin-right: 8px;
                accent-color: var(--accent-blue, #3b82f6);
                width: 16px;
                height: 16px;
            }
            
            .display-controls,
            .filter-controls {
                display: flex;
                flex-direction: column;
                gap: 4px;
                margin-top: 8px;
            }
            
            .info-panel h4 {
                margin-bottom: 12px;
                color: var(--text-primary, #f1f5f9);
                font-size: 14px;
                font-weight: 600;
                border-bottom: 1px solid var(--border-color, #475569);
                padding-bottom: 4px;
            }
            
            #display-options-section,
            #node-filters-section {
                background: var(--panel-bg, rgba(15, 23, 42, 0.8));
                border: 1px solid var(--border-color, #475569);
                border-radius: 8px;
                padding: 12px;
                margin-bottom: 12px;
                backdrop-filter: blur(10px);
            }
            
            /* Traffic animation styles */
            .traffic-particle {
                filter: drop-shadow(0 0 3px currentColor);
            }
            
            .traffic-flow {
                pointer-events: none;
            }
            
            .traffic-particle {
                animation: traffic-glow 2s ease-in-out infinite alternate;
            }
            
            @keyframes traffic-glow {
                from { filter: drop-shadow(0 0 2px currentColor); }
                to { filter: drop-shadow(0 0 6px currentColor); }
            }
            
            /* Enhanced traffic checkbox styling */
            #show-traffic {
                accent-color: #fbbf24;
            }
            
            #show-traffic:checked + span {
                color: #fbbf24;
                font-weight: 600;
            }
        `;
        document.head.appendChild(style);
        console.log('✅ Added display options CSS styles');
    }
    
	filterData() {
		if (!this.networkData || !this.networkData.nodes) {
			console.log('❌ No network data available for filtering');
			return { nodes: [], links: [] };
		}
		
		// Initialize filteredNodeTypes if it's empty
		if (!this.filteredNodeTypes || this.filteredNodeTypes.size === 0) {
			console.log('⚠️ filteredNodeTypes is empty, initializing with default types');
			this.initializeDefaultFilterTypes();
		}
		
		console.log(`\n🔍 FILTERING ${this.networkData.nodes.length} nodes with types:`, Array.from(this.filteredNodeTypes));
		
		const filteredNodes = this.networkData.nodes.filter(node => {
			// If filteredNodeTypes is still empty, show all nodes
			if (this.filteredNodeTypes.size === 0) {
				console.log(`  Showing all nodes (no filters active)`);
				return true;
			}
			
			const nodeTypeMatch = this.filteredNodeTypes.has(node.tier) || 
								  this.filteredNodeTypes.has(node.type) ||
								  this.filteredNodeTypes.has(node.componentType);
			
			// Debug logging for first few nodes
			if (this.networkData.nodes.indexOf(node) < 3) {
				console.log(`  Node: ${node.name} (tier: ${node.tier}, type: ${node.type}) -> ${nodeTypeMatch ? 'SHOW' : 'HIDE'}`);
			}
			
			return nodeTypeMatch;
		});
		
		const nodeIds = new Set(filteredNodes.map(n => n.id));
		const filteredLinks = this.networkData.links.filter(link => 
			nodeIds.has(link.source.id || link.source) && 
			nodeIds.has(link.target.id || link.target)
		);
		
		console.log(`✅ Filtered result: ${filteredNodes.length}/${this.networkData.nodes.length} nodes, ${filteredLinks.length}/${this.networkData.links.length} links`);
		
		return { nodes: filteredNodes, links: filteredLinks };
	}
    
    // ================================================================================
    // RENDERING METHODS (Simplified and Fixed)
    // ================================================================================
    
    setupSVG() {
        const containerRect = this.container.node().getBoundingClientRect();
        this.width = containerRect.width;
        this.height = containerRect.height;
        
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
        this.labelGroup = this.mainGroup.append("g").attr("class", "node-labels");
        this.ipLabelGroup = this.mainGroup.append("g").attr("class", "ip-labels");
        
        console.log(`SVG setup: ${this.width}x${this.height}`);
    }
    
    setupZoom() {
		this.zoom = d3.zoom()
			.scaleExtent([0.1, 4])
			.on("zoom", (event) => {
				this.mainGroup.attr("transform", event.transform);
			});
		
		// Apply zoom with passive event options
		this.svg.call(this.zoom);
		
		// Fix for passive event listener warning
		this.addPassiveEventSupport();
	}
    
	// Add this new method to handle passive events:
	addPassiveEventSupport() {
		// Override default event options for better performance
		const svgNode = this.svg.node();
		
		if (svgNode) {
			// Remove default listeners and add passive ones
			const events = ['touchstart', 'touchmove', 'touchend', 'wheel'];
			
			events.forEach(eventType => {
				// Add passive event listeners for better scroll performance
				svgNode.addEventListener(eventType, function(e) {
					// Let D3 handle the actual functionality
					// This is just to mark events as passive
				}, { passive: true, capture: false });
			});
		}
	}
	
    setupEventListeners() {
        window.addEventListener('dashboardResize', () => {
            setTimeout(() => this.handleResize(), 100);
        });
        
        const searchInput = document.getElementById('node-search');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                if (e.target.value.trim() === '') {
                    this.searchNodes('');
                }
            });
            
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    console.log('🔍 Search triggered by Enter key');
                    this.searchNodes(e.target.value);
                }
            });
            
            let searchTimeout;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                const query = e.target.value.trim();
                
                if (query.length >= 2) {
                    searchTimeout = setTimeout(() => {
                        console.log('🔍 Search triggered by typing');
                        this.searchNodes(query);
                    }, 500);
                } else if (query.length === 0) {
                    this.searchNodes('');
                }
            });
        }
        
        const nodeSelector = document.getElementById('node-selector');
        if (nodeSelector) {
            nodeSelector.addEventListener('change', (e) => {
                this.selectNode(e.target.value);
            });
        }
    }
    
    render() {
        const filteredData = this.filterData();
        
        if (!filteredData.nodes || filteredData.nodes.length === 0) {
            this.renderEmptyState();
            return;
        }
        
        this.svg.selectAll(".empty-state").remove();
        
        const originalData = this.networkData;
        this.networkData = filteredData;
        
        this.setupSimulation();
        this.renderLinks();
        this.renderLinkLabels();
        this.renderNodes();
        this.renderLabels();
        this.renderTrafficFlow();
        
        this.networkData = originalData;
        
        console.log(`Rendered ${filteredData.nodes.length} nodes and ${filteredData.links.length} links`);
    }
    
    renderEmptyState() {
        this.svg.selectAll("*").remove();
        
        this.mainGroup = this.svg.append("g").attr("class", "main-group");
        this.linkGroup = this.mainGroup.append("g").attr("class", "links");
        this.linkLabelGroup = this.mainGroup.append("g").attr("class", "link-labels");
        this.trafficGroup = this.mainGroup.append("g").attr("class", "traffic-flow");
        this.nodeGroup = this.mainGroup.append("g").attr("class", "nodes");
        this.labelGroup = this.mainGroup.append("g").attr("class", "node-labels");
        this.ipLabelGroup = this.mainGroup.append("g").attr("class", "ip-labels");
        
        const emptyGroup = this.svg.append("g")
            .attr("class", "empty-state");
        
        emptyGroup.append("text")
            .attr("x", this.width / 2)
            .attr("y", this.height / 2 - 20)
            .attr("text-anchor", "middle")
            .attr("font-size", "18px")
            .attr("font-weight", "600")
            .attr("fill", "var(--text-muted)")
            .text("No Nodes Match Current Filters");
        
        emptyGroup.append("text")
            .attr("x", this.width / 2)
            .attr("y", this.height / 2 + 10)
            .attr("text-anchor", "middle")
            .attr("font-size", "14px")
            .attr("fill", "var(--text-muted)")
            .text("Adjust filters to view network topology");
    }
    
    setupSimulation() {
        if (this.simulation) {
            this.simulation.stop();
        }
        
        this.networkData.nodes.forEach(node => {
            if (isNaN(node.x) || node.x === undefined) {
                node.x = this.width / 2 + (Math.random() - 0.5) * 200;
            }
            if (isNaN(node.y) || node.y === undefined) {
                node.y = this.height / 2 + (Math.random() - 0.5) * 200;
            }
        });
        
        this.simulation = d3.forceSimulation(this.networkData.nodes)
            .force("link", d3.forceLink(this.networkData.links)
                .id(d => d.id)
                .distance(80)
                .strength(0.5))
            .force("charge", d3.forceManyBody()
                .strength(-300)
                .distanceMax(200))
            .force("center", d3.forceCenter(this.width / 2, this.height / 2))
            .force("collision", d3.forceCollide().radius(d => (d.size || 12) + 5))
            .on("tick", () => this.updatePositions());
        
        this.simulation.tick(10);
        this.applyLayout();
    }
    
    applyLayout() {
        if (!this.networkData || !this.networkData.nodes || this.networkData.nodes.length === 0) {
            return;
        }
        
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
                if (this.simulation) {
                    const hasLayers = this.networkData.nodes.some(n => n.layer !== undefined);
                    if (hasLayers) {
                        this.simulation
                            .force("y", d3.forceY().y(d => this.getLayerY(d.layer || 0)).strength(0.5))
                            .alpha(0.3).restart();
                    } else {
                        this.simulation.alpha(0.3).restart();
                    }
                }
                break;
        }
    }
    
    applyHierarchicalLayout() {
        if (!this.networkData || !this.networkData.nodes) return;
        
        const layers = {};
        this.networkData.nodes.forEach(node => {
            const layer = node.layer || Math.floor(Math.random() * 4);
            if (!layers[layer]) layers[layer] = [];
            layers[layer].push(node);
        });
        
        Object.entries(layers).forEach(([layer, nodes]) => {
            const layerNum = parseInt(layer);
            const y = this.getLayerY(layerNum);
            nodes.forEach((node, i) => {
                node.fx = 100 + (i * (this.width - 200) / (nodes.length - 1 || 1));
                node.fy = y;
            });
        });
        
        this.simulation.alpha(0.3).restart();
    }
    
    applyCircularLayout() {
        if (!this.networkData || !this.networkData.nodes) return;
        
        const radius = Math.min(this.width, this.height) * 0.3;
        const centerX = this.width / 2;
        const centerY = this.height / 2;
        
        this.networkData.nodes.forEach((node, i) => {
            const angle = (i / this.networkData.nodes.length) * 2 * Math.PI;
            node.fx = centerX + Math.cos(angle) * radius;
            node.fy = centerY + Math.sin(angle) * radius;
        });
        
        this.simulation.alpha(0.3).restart();
    }
    
    applyGridLayout() {
        if (!this.networkData || !this.networkData.nodes) return;
        
        const cols = Math.ceil(Math.sqrt(this.networkData.nodes.length));
        const cellWidth = (this.width - 100) / cols;
        const cellHeight = (this.height - 100) / Math.ceil(this.networkData.nodes.length / cols);
        
        this.networkData.nodes.forEach((node, i) => {
            const row = Math.floor(i / cols);
            const col = i % cols;
            node.fx = 50 + col * cellWidth + cellWidth / 2;
            node.fy = 50 + row * cellHeight + cellHeight / 2;
        });
        
        this.simulation.alpha(0.3).restart();
    }
    
    getLayerY(layer) {
        const layerSpacing = this.height / 6;
        return layer * layerSpacing + layerSpacing;
    }
    
    renderLinks() {
        if (!this.networkData || !this.networkData.links) {
            console.log('No link data available for rendering');
            return;
        }
        
        const links = this.linkGroup.selectAll("line")
            .data(this.networkData.links, d => `${d.source.id || d.source}-${d.target.id || d.target}`);
        
        links.exit().remove();
        
        const linksEnter = links.enter().append("line")
            .attr("stroke", d => this.getLinkColor(d))
            .attr("stroke-opacity", d => d.status === 'active' ? 0.8 : 0.3)
            .attr("stroke-width", d => this.getLinkWidth(d))
            .style("stroke-dasharray", d => d.status === 'degraded' ? "5,5" : "none");
        
        linksEnter.append("title")
            .text(d => `${d.protocol} - ${d.bandwidth} Mbps - ${d.latency}ms`);
        
        this.linkElements = links.merge(linksEnter);
    }
    
    renderLinkLabels() {
        console.log(`🔗 renderLinkLabels called - showLinkLabels: ${this.displayOptions.showLinkLabels}`);
        
        if (!this.displayOptions.showLinkLabels || !this.networkData || !this.networkData.links) {
            console.log(`❌ Not rendering link labels - showLinkLabels: ${this.displayOptions.showLinkLabels}, links: ${this.networkData?.links?.length || 0}`);
            this.linkLabelGroup.selectAll("*").remove();
            return;
        }
        
        console.log(`✅ Rendering ${this.networkData.links.length} link labels`);
        
        const linkLabels = this.linkLabelGroup.selectAll("text.link-label")
            .data(this.networkData.links, d => `${d.source.id || d.source}-${d.target.id || d.target}`);
        
        linkLabels.exit().remove();
        
        const linkLabelsEnter = linkLabels.enter().append("text")
            .attr("class", "link-label")
            .attr("text-anchor", "middle")
            .attr("font-size", "12px")
            .attr("font-weight", "bold")
            .attr("fill", "#fbbf24")
            .style("pointer-events", "none")
            .style("text-shadow", "2px 2px 4px rgba(0,0,0,1)")
            .style("stroke", "rgba(0,0,0,0.9)")
            .style("stroke-width", "3px")
            .style("paint-order", "stroke fill");
        
        this.linkLabelElements = linkLabels.merge(linkLabelsEnter)
            .text(d => {
                const protocol = d.protocol || 'TCP';
                const port = d.port || '8080';
                const bandwidth = d.bandwidth ? ` ${Math.round(d.bandwidth)}M` : '';
                const label = `${protocol}:${port}${bandwidth}`;
                console.log(`Link label text: ${label}`);
                return label;
            })
            .attr("x", d => {
                const sourceX = (d.source.x || this.width / 2);
                const targetX = (d.target.x || this.width / 2);
                const midX = (sourceX + targetX) / 2;
                return midX;
            })
            .attr("y", d => {
                const sourceY = (d.source.y || this.height / 2);
                const targetY = (d.target.y || this.height / 2);
                const midY = (sourceY + targetY) / 2 - 8;
                return midY;
            });
            
        console.log(`✅ Link labels created: ${this.linkLabelElements.size()} elements`);
        this.linkLabelElements.style("opacity", 1);
    }
    
    getLinkColor(link) {
        if (link.direction === 'upstream') return '#10b981';
        if (link.direction === 'downstream') return '#3b82f6';
        return '#8b5cf6';
    }
    
    getLinkWidth(link) {
        if (link.bandwidth > 800) return 3;
        if (link.bandwidth > 400) return 2;
        return 1;
    }
    
    renderNodes() {
        if (!this.networkData || !this.networkData.nodes) {
            console.log('No node data available for rendering');
            return;
        }
        
        const nodes = this.nodeGroup.selectAll("circle")
            .data(this.networkData.nodes, d => d.id);
        
        nodes.exit().remove();
        
        const nodesEnter = nodes.enter().append("circle")
            .attr("r", d => this.getNodeRadius(d))
            .attr("fill", d => this.getNodeColor(d))
            .attr("stroke", "#ffffff")
            .attr("stroke-width", 2)
            .style("cursor", "pointer")
            .call(this.drag())
            .on("mouseover", (event, d) => this.showTooltip(event, d))
            .on("mouseout", () => this.hideTooltip())
            .on("click", (event, d) => this.selectNode(d.id));
        
        this.nodeElements = nodes.merge(nodesEnter)
            .attr("fill", d => this.getNodeColor(d))
            .attr("stroke-width", d => this.selectedNodes.has(d.id) ? 4 : 2)
            .attr("stroke", d => this.selectedNodes.has(d.id) ? "#fbbf24" : "#ffffff")
            .attr("r", d => this.getNodeRadius(d));
    }
    
    getNodeRadius(node) {
        const baseRadius = 8;
        if (node.traffic === 'high') return baseRadius + 4;
        if (node.traffic === 'medium') return baseRadius + 2;
        return baseRadius;
    }
    
    getNodeColor(node) {
		// Handle inactive nodes first
		if (node.status === 'inactive') return '#64748b';
    
		// Handle high CPU/performance indicators
		if (node.cpu > 90) return '#ef4444';
		if (node.cpu > 70) return '#f59e0b';
    
		// Color by node type/tier to match your legend
		const nodeType = (node.tier || node.type || node.componentType || '').toLowerCase();
		const nodeName = (node.name || '').toLowerCase();
    
		// 🔵 Blue = Web Servers
		if (nodeType.includes('web') || nodeType.includes('frontend') || 
			nodeType.includes('web-tier') || nodeName.includes('web')) {
			return '#3b82f6';
		}
    
		// 🟡 Yellow = Databases (NOT orange!)
		if (nodeType.includes('database') || nodeType.includes('storage') || 
			nodeType.includes('data') || nodeName.includes('data') || 
			nodeName.includes('storage') || nodeType.includes('db')) {
			return '#eab308'; // True yellow instead of orange
		}
    
		// 🟣 Purple = Gateways
		if (nodeType.includes('gateway') || nodeType.includes('api') || 
			nodeName.includes('gateway')) {
			return '#8b5cf6';
		}
    
		// 🔴 Red = Core Services
		if (nodeType.includes('core') || nodeType.includes('engine') || 
			nodeType.includes('service') || nodeName.includes('engine') ||
			node.criticality === 'critical') {
			return '#ef4444';
		}
    
		// 🟢 Green = Processors
		if (nodeType.includes('processor') || nodeType.includes('worker') || 
			nodeType.includes('compute')) {
			return '#10b981';
		}
    
		// 🟦 Cyan = Cache/Messaging
		if (nodeType.includes('cache') || nodeType.includes('message') || 
			nodeType.includes('queue') || nodeType.includes('redis')) {
			return '#06b6d4';
		}
    
		// Default: Use existing color or blue
		return node.color || '#3b82f6';
	}
    
    renderLabels() {
        if (!this.networkData || !this.networkData.nodes) {
            console.log('No node data available for label rendering');
            return;
        }
        
        const labels = this.labelGroup.selectAll("text")
            .data(this.networkData.nodes, d => d.id);
        
        labels.exit().remove();
        
        const labelsEnter = labels.enter().append("text")
            .attr("text-anchor", "middle")
            .attr("dy", "-15px")
            .attr("font-size", "9px")
            .attr("font-weight", "600")
            .attr("fill", "var(--text-primary)")
            .style("pointer-events", "none")
            .style("text-shadow", "1px 1px 2px rgba(0,0,0,0.8)");
        
        this.labelElements = labels.merge(labelsEnter)
            .text(d => d.name)
            .style("display", this.displayOptions.showLabels ? "block" : "none");
        
        const ipLabels = this.ipLabelGroup.selectAll("text")
            .data(this.networkData.nodes, d => d.id);
        
        ipLabels.exit().remove();
        
        const ipLabelsEnter = ipLabels.enter().append("text")
            .attr("text-anchor", "middle")
            .attr("dy", "25px")
            .attr("font-size", "7px")
            .attr("fill", "var(--text-muted)")
            .style("pointer-events", "none")
            .style("text-shadow", "1px 1px 2px rgba(0,0,0,0.8)");
        
        this.ipLabelElements = ipLabels.merge(ipLabelsEnter)
            .text(d => d.ip)
            .style("display", this.displayOptions.showIPs ? "block" : "none");
    }
    
    renderTrafficFlow() {
        if (!this.displayOptions.showTraffic || !this.networkData || !this.networkData.links) {
            // Clean up when traffic is disabled
            if (this.trafficGroup) {
                this.trafficGroup.selectAll("*").remove();
            }
            this.stopTrafficAnimation();
            return;
        }

        console.log('🌊 Rendering traffic flow elements');
        
        // Ensure traffic group exists
        if (!this.trafficGroup) {
            this.trafficGroup = this.mainGroup.append("g").attr("class", "traffic-flow");
        }

        // Start animation if not already running
        if (!this.isTrafficAnimating) {
            this.startTrafficAnimation();
        }
    }
    
    updatePositions() {
        if (this.linkElements) {
            this.linkElements
                .attr("x1", d => {
                    const x = d.source.x;
                    return isNaN(x) ? 0 : x;
                })
                .attr("y1", d => {
                    const y = d.source.y;
                    return isNaN(y) ? 0 : y;
                })
                .attr("x2", d => {
                    const x = d.target.x;
                    return isNaN(x) ? 0 : x;
                })
                .attr("y2", d => {
                    const y = d.target.y;
                    return isNaN(y) ? 0 : y;
                });
        }
        
        if (this.linkLabelElements) {
            this.updateLinkLabelPositions();
        }
        
        if (this.nodeElements) {
            this.nodeElements
                .attr("cx", d => {
                    const x = d.x;
                    return isNaN(x) ? this.width / 2 : x;
                })
                .attr("cy", d => {
                    const y = d.y;
                    return isNaN(y) ? this.height / 2 : y;
                });
        }
        
        if (this.labelElements) {
            this.labelElements
                .attr("x", d => {
                    const x = d.x;
                    return isNaN(x) ? this.width / 2 : x;
                })
                .attr("y", d => {
                    const y = d.y;
                    return isNaN(y) ? this.height / 2 : y;
                });
        }
        
        if (this.ipLabelElements) {
            this.ipLabelElements
                .attr("x", d => {
                    const x = d.x;
                    return isNaN(x) ? this.width / 2 : x;
                })
                .attr("y", d => {
                    const y = d.y;
                    return isNaN(y) ? this.height / 2 : y;
                });
        }
    }
    
    updateLinkLabelPositions() {
        if (this.linkLabelElements) {
            this.linkLabelElements
                .attr("x", d => {
                    const sourceX = d.source.x || 0;
                    const targetX = d.target.x || 0;
                    return (sourceX + targetX) / 2;
                })
                .attr("y", d => {
                    const sourceY = d.source.y || 0;
                    const targetY = d.target.y || 0;
                    return (sourceY + targetY) / 2 - 5;
                });
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
    
    showTooltip(event, node) {
        const tooltip = document.getElementById('tooltip');
        if (!tooltip) return;
        
        const statusColor = node.status === 'active' ? '#10b981' : '#ef4444';
        const criticalityColor = node.criticality === 'critical' ? '#ef4444' : 
                                node.criticality === 'high' ? '#f59e0b' : '#10b981';
        
        const componentInfo = node.description ? 
            `<div><strong>Component:</strong> ${node.description}</div>` : '';
        
        const roleInfo = node.role ? 
            `<div><strong>Role:</strong> ${node.role}</div>` : '';
        
        const architectureInfo = node.realArchitecture ? 
            `<div><strong>Architecture:</strong> ${node.realArchitecture}</div>` : '';
        
        const appInfo = node.applicationId && node.applicationId !== node.name ? 
            `<div><strong>Application:</strong> ${node.application} (${node.applicationId})</div>` : 
            `<div><strong>Application:</strong> ${node.application || 'Unknown'}</div>`;
        
        tooltip.style.opacity = '1';
        tooltip.style.left = (event.pageX + 10) + 'px';
        tooltip.style.top = (event.pageY - 10) + 'px';
        tooltip.innerHTML = `
            <div style="font-weight: bold; margin-bottom: 8px; color: ${node.color}">${node.name}</div>
            <div style="font-size: 11px; line-height: 1.4;">
                ${appInfo}
                ${componentInfo}
                ${roleInfo}
                ${architectureInfo}
                <div><strong>Technology:</strong> ${node.technology || 'N/A'}</div>
                <div><strong>Status:</strong> <span style="color: ${statusColor}">${node.status}</span></div>
                <div><strong>Criticality:</strong> <span style="color: ${criticalityColor}">${node.criticality || 'Medium'}</span></div>
                <div><strong>IP Address:</strong> ${node.ip}</div>
                <div><strong>Ports:</strong> ${node.ports ? node.ports.join(', ') : 'N/A'}</div>
                <div><strong>Uptime:</strong> ${node.uptime || 'N/A'}%</div>
                <div><strong>Response Time:</strong> ${node.responseTime || 'N/A'}ms</div>
                <div><strong>Connections:</strong> ${node.connections || 0}</div>
                ${node.requestsPerSecond ? `<div><strong>Requests/sec:</strong> ${node.requestsPerSecond}</div>` : ''}
            </div>
        `;
    }
    
    hideTooltip() {
        const tooltip = document.getElementById('tooltip');
        if (tooltip) {
            tooltip.style.opacity = '0';
        }
    }
    
    selectNode(nodeId) {
        if (this.selectedNodes.has(nodeId)) {
            this.selectedNodes.delete(nodeId);
        } else {
            this.selectedNodes.add(nodeId);
        }
        this.renderNodes();
        this.updateNodeSelector();
        this.highlightRelatedNodes(nodeId);
    }
    
    highlightRelatedNodes(nodeId) {
        if (!this.networkData || !this.networkData.links) return;
        
        const relatedLinks = this.networkData.links.filter(link => 
            link.source.id === nodeId || link.target.id === nodeId
        );
        
        if (this.linkElements) {
            this.linkElements
                .style("stroke-opacity", d => 
                    relatedLinks.includes(d) ? 1 : 0.3
                )
                .style("stroke-width", d => 
                    relatedLinks.includes(d) ? this.getLinkWidth(d) + 1 : this.getLinkWidth(d)
                );
        }
    }
    
    searchNodes(query) {
        if (!query) {
            this.selectedNodes.clear();
            this.renderNodes();
            this.linkElements?.style("stroke-opacity", 0.8);
            return;
        }
        
        console.log(`🔍 Searching for: "${query}"`);
        
        const filteredData = this.filterData();
        const searchableNodes = filteredData.nodes || [];
        
        console.log(`🔍 Searching in ${searchableNodes.length} visible nodes`);
        
        const matchingNodes = searchableNodes.filter(node => {
            const nameMatch = node.name.toLowerCase().includes(query.toLowerCase());
            const ipMatch = node.ip.includes(query);
            const tierMatch = node.tier && node.tier.toLowerCase().includes(query.toLowerCase());
            const appMatch = node.applicationId && node.applicationId.toLowerCase().includes(query.toLowerCase());
            const roleMatch = node.role && node.role.toLowerCase().includes(query.toLowerCase());
            
            return nameMatch || ipMatch || tierMatch || appMatch || roleMatch;
        });
        
        console.log(`📊 Search results: ${matchingNodes.length}/${searchableNodes.length} visible nodes found`);
        
        this.selectedNodes.clear();
        matchingNodes.forEach(node => this.selectedNodes.add(node.id));
        this.renderNodes();
        this.updateNodeSelector();
        
        if (matchingNodes.length > 0) {
            const nodeTypes = [...new Set(matchingNodes.map(n => n.tier))];
            const apps = [...new Set(matchingNodes.map(n => n.applicationId))];
            this.showNotification(`Found ${matchingNodes.length}/${searchableNodes.length} visible nodes: ${nodeTypes.join(', ')} from ${apps.join(', ')}`, 'success');
        } else {
            this.showNotification(`No visible nodes found matching "${query}" (${searchableNodes.length} nodes searched)`, 'warning');
        }
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
    
    updateStats() {
        const filteredData = this.filterData();
        const nodes = filteredData.nodes || [];
        const links = filteredData.links || [];
        
        const activeNodes = nodes.filter(n => n.status === 'active').length;
        const activeLinks = links.filter(l => l.status === 'active').length;
        
        const stats = {
            'stat-nodes': nodes.length,
            'stat-links': activeLinks,
            'stat-avg-degree': nodes.length > 0 ? (activeLinks * 2 / nodes.length).toFixed(1) : '0.0',
            'stat-density': nodes.length > 1 ? 
                ((activeLinks * 2) / (nodes.length * (nodes.length - 1)) * 100).toFixed(1) + '%' : '0.0%',
            'stat-clustering': (Math.random() * 0.5 + 0.4).toFixed(2)
        };
        
        Object.entries(stats).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) element.textContent = value;
        });
        
        const totalNodesEl = document.getElementById('totalNodes');
        const activeConnectionsEl = document.getElementById('activeConnections');
        const networkClustersEl = document.getElementById('networkClusters');
        const criticalPathsEl = document.getElementById('criticalPaths');
        
        if (totalNodesEl) totalNodesEl.textContent = nodes.length;
        if (activeConnectionsEl) activeConnectionsEl.textContent = activeLinks.toLocaleString();
        if (networkClustersEl) networkClustersEl.textContent = this.selectedApps.length;
        if (criticalPathsEl) criticalPathsEl.textContent = this.selectedNodes.size;
    }
    
    applyFilters() {
        console.log('Applying filters with types:', Array.from(this.filteredNodeTypes));
        
        const searchInput = document.getElementById('node-search');
        if (searchInput && searchInput.value.trim() !== '') {
            console.log('🧹 Clearing search due to filter change');
            searchInput.value = '';
            this.selectedNodes.clear();
        }
        
        this.render();
        this.updateStats();
    }
    
    setLayout(layout) {
        document.querySelectorAll('.topology-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.getElementById(`${layout}-btn`)?.classList.add('active');
        
        this.currentLayout = layout;
        this.applyLayout();
    }
    
    toggleLabels() {
        console.log(`Toggling labels: ${this.displayOptions.showLabels}`);
        if (this.labelElements) {
            this.labelElements.style("display", this.displayOptions.showLabels ? "block" : "none");
        }
    }
    
    toggleIPLabels() {
        console.log(`Toggling IP labels: ${this.displayOptions.showIPs}`);
        if (this.ipLabelElements) {
            this.ipLabelElements.style("display", this.displayOptions.showIPs ? "block" : "none");
        }
    }
    
    toggleLinkLabels() {
        console.log(`Toggling link labels: ${this.displayOptions.showLinkLabels}`);
        this.renderLinkLabels();
        
        if (this.linkLabelElements && this.networkData?.links) {
            this.updateLinkLabelPositions();
        }
    }
    
    handleResize() {
        const containerRect = this.container.node().getBoundingClientRect();
        this.width = containerRect.width;
        this.height = containerRect.height;
        
        this.svg
            .attr("width", this.width)
            .attr("height", this.height);
        
        if (this.simulation) {
            this.simulation
                .force("center", d3.forceCenter(this.width / 2, this.height / 2))
                .alpha(0.3)
                .restart();
        }
        
        this.updateControlPositions();
    }
    
    handleThemeChange() {
        this.svg.style("background", "var(--bg-primary)");
        
        if (this.labelElements) {
            this.labelElements.attr("fill", "var(--text-primary)");
        }
        if (this.ipLabelElements) {
            this.ipLabelElements.attr("fill", "var(--text-muted)");
        }
    }
    
    // Zoom Controls
    zoomIn() {
        this.svg.transition().duration(300).call(this.zoom.scaleBy, 1.5);
    }
    
    zoomOut() {
        this.svg.transition().duration(300).call(this.zoom.scaleBy, 1 / 1.5);
    }
    
    resetView() {
        this.svg.transition().duration(500).call(this.zoom.transform, d3.zoomIdentity);
    }
    
    centerView() {
        const transform = d3.zoomTransform(this.svg.node());
        const centerTransform = d3.zoomIdentity
            .translate(this.width / 2, this.height / 2)
            .scale(transform.k);
        
        this.svg.transition().duration(500).call(this.zoom.transform, centerTransform);
    }
    
    panDirection(direction) {
        const transform = d3.zoomTransform(this.svg.node());
        const panDistance = 50;
        
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
        }
        
        if (newTransform) {
            this.svg.transition().duration(300).call(this.zoom.transform, newTransform);
        }
    }
    
    // ================================================================================
    // TRAFFIC ANIMATION DEBUGGING METHODS
    // ================================================================================
    
    debugTrafficAnimation() {
        console.log('🔍 Traffic Animation Debug Info:');
        console.log('- Show Traffic:', this.displayOptions.showTraffic);
        console.log('- Is Animating:', this.isTrafficAnimating);
        console.log('- Animation ID:', this.trafficAnimationId);
        console.log('- Active Links:', this.networkData?.links?.filter(l => l.status === 'active').length || 0);
        console.log('- Traffic Particles:', this.trafficGroup?.selectAll('.traffic-particle').size() || 0);
        
        const checkbox = document.getElementById('show-traffic');
        console.log('- Checkbox State:', checkbox?.checked);
        console.log('- Checkbox Exists:', !!checkbox);
    }

    forceStartTrafficAnimation() {
        console.log('🔧 Force starting traffic animation');
        this.displayOptions.showTraffic = true;
        const checkbox = document.getElementById('show-traffic');
        if (checkbox) checkbox.checked = true;
        this.toggleTrafficFlow();
    }

    forceStopTrafficAnimation() {
        console.log('🔧 Force stopping traffic animation');
        this.displayOptions.showTraffic = false;
        const checkbox = document.getElementById('show-traffic');
        if (checkbox) checkbox.checked = false;
        this.toggleTrafficFlow();
    }
}

// ================================================================================
// GLOBAL FUNCTIONS - FIXED
// ================================================================================

function togglePanel(side) {
    togglePanelSimple(side);
}

function applyApplicationFilter() {
    if (window.topologyDashboard) {
        window.topologyDashboard.updateSelectedApps();
        window.topologyDashboard.updateNetworkData();
        window.topologyDashboard.render();
        window.topologyDashboard.updateStats();
        window.topologyDashboard.broadcastFilterChange();
        
        const selectedCount = window.topologyDashboard.selectedApps.includes('all') ? 
            'All' : window.topologyDashboard.selectedApps.length;
        
        createToast(`Filter applied: ${selectedCount} applications selected`, 'success');
    }
}

function selectAllApps() {
    if (window.topologyDashboard) {
        const select = document.getElementById('app-filter');
        if (select) {
            Array.from(select.options).forEach(option => {
                option.selected = option.value === 'all';
            });
            window.topologyDashboard.updateSelectedApps();
            window.topologyDashboard.updateFilterStats();
            createToast('All applications selected', 'info');
        }
    }
}

function selectCriticalApps() {
    if (window.topologyDashboard) {
        window.topologyDashboard.selectCriticalApps();
    }
}

function selectByArchetype(archetype) {
    if (window.topologyDashboard) {
        window.topologyDashboard.selectByArchetype(archetype);
    }
}

function clearAllApps() {
    if (window.topologyDashboard) {
        const select = document.getElementById('app-filter');
        if (select) {
            Array.from(select.options).forEach(option => {
                option.selected = false;
            });
            window.topologyDashboard.selectedApps = [];
            window.topologyDashboard.updateFilterStats();
            createToast('All applications cleared', 'info');
        }
    }
}

function focusOnApplication() {
    if (!window.topologyDashboard) return;
    
    const select = document.getElementById('app-filter');
    if (!select) return;
    
    const selectedValues = Array.from(select.selectedOptions).map(option => option.value);
    const singleApp = selectedValues.find(val => val !== 'all');
    
    if (!singleApp) {
        createToast('Please select a single application to focus on', 'warning');
        return;
    }
    
    if (!window.AppData) {
        window.topologyDashboard.networkData = window.topologyDashboard.generateFallbackNetworkData();
        window.topologyDashboard.render();
        createToast('Using demo data - AppData not available', 'info');
        return;
    }
    
    const upstreamEnabled = document.getElementById('show-upstream')?.checked || true;
    const downstreamEnabled = document.getElementById('show-downstream')?.checked || true;
    
    const focusedData = window.AppData.getApplicationFlow ? 
                        window.AppData.getApplicationFlow(singleApp, upstreamEnabled, downstreamEnabled) :
                        window.topologyDashboard.generateFallbackNetworkData();
    
    if (focusedData.nodes.length === 0) {
        createToast('No connections found for this application', 'info');
        return;
    }
    
    window.topologyDashboard.networkData = focusedData;
    window.topologyDashboard.render();
    window.topologyDashboard.updateStats();
    
    window.topologyDashboard.selectedApps = [singleApp];
    window.topologyDashboard.broadcastFilterChange();
    
    const focusedAppName = focusedData.nodes.find(n => n.applicationId === singleApp)?.application || 'application';
    createToast(`Focused on ${focusedAppName} and its connections`, 'success');
}

function createToast(message, type = 'info') {
    if (window.topologyDashboard) {
        window.topologyDashboard.showNotification(message, type);
    } else {
        console.log(`${type.toUpperCase()}: ${message}`);
    }
}

// Control Functions
function zoomIn() { if (window.topologyDashboard) window.topologyDashboard.zoomIn(); }
function zoomOut() { if (window.topologyDashboard) window.topologyDashboard.zoomOut(); }
function resetView() { if (window.topologyDashboard) window.topologyDashboard.resetView(); }
function centerView() { if (window.topologyDashboard) window.topologyDashboard.centerView(); }
function panDirection(direction) { if (window.topologyDashboard) window.topologyDashboard.panDirection(direction); }
function setLayout(layout) { if (window.topologyDashboard) window.topologyDashboard.setLayout(layout); }

// Analysis Functions (Simplified)
function analyzeTraffic() {
    createToast('Traffic analysis feature - check console for details', 'info');
    console.log('🌐 Traffic Analysis: Feature available in full implementation');
}

function findCriticalPaths() {
    createToast('Critical paths analysis feature - check console for details', 'info');
    console.log('🎯 Critical Paths: Feature available in full implementation');
}

function detectClusters() {
    createToast('Cluster detection feature - check console for details', 'info');
    console.log('🌐 Cluster Detection: Feature available in full implementation');
}

function exportTopology() {
    createToast('Export feature - check console for details', 'info');
    console.log('📤 Export: Feature available in full implementation');
}

function closeOverlay() {
    const overlayCanvas = document.getElementById('overlay-canvas');
    if (overlayCanvas) {
        overlayCanvas.style.display = 'none';
    }
}

// ================================================================================
// TRAFFIC ANIMATION TESTING FUNCTIONS
// ================================================================================

function testTrafficAnimation() {
    if (!window.topologyDashboard) {
        console.error('❌ Topology dashboard not found');
        return;
    }
    
    console.log('🧪 Testing traffic animation...');
    window.topologyDashboard.debugTrafficAnimation();
    
    // Test start
    setTimeout(() => {
        console.log('🧪 Testing START animation');
        window.topologyDashboard.forceStartTrafficAnimation();
    }, 1000);
    
    // Test stop  
    setTimeout(() => {
        console.log('🧪 Testing STOP animation');
        window.topologyDashboard.forceStopTrafficAnimation();
    }, 6000);
}

function toggleTrafficFromConsole() {
    if (!window.topologyDashboard) {
        console.error('❌ Topology dashboard not found');
        return;
    }
    
    const current = window.topologyDashboard.displayOptions.showTraffic;
    window.topologyDashboard.displayOptions.showTraffic = !current;
    
    const checkbox = document.getElementById('show-traffic');
    if (checkbox) checkbox.checked = !current;
    
    window.topologyDashboard.toggleTrafficFlow();
    console.log(`🔧 Traffic animation ${!current ? 'enabled' : 'disabled'} from console`);
}

// ================================================================================
// SIMPLE PANEL TOGGLE SOLUTION
// ================================================================================

// Global panel state tracking
window.panelStates = {
    left: false,   // false = expanded, true = collapsed
    right: false
};

// Simple panel toggle function
function initPanelToggles() {
    console.log('🔧 Initializing simple panel toggles...');
    
    // Find all hamburger buttons and add click handlers
    document.querySelectorAll('.hamburger').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            console.log('🍔 Hamburger clicked');
            
            // Determine which panel this button belongs to
            let panelSide = button.getAttribute('data-panel');
            
            if (!panelSide) {
                // Fallback: check parent panel
                const panel = button.closest('#left-panel, #right-panel');
                if (panel) {
                    panelSide = panel.id.includes('left') ? 'left' : 'right';
                }
            }
            
            if (panelSide) {
                togglePanelSimple(panelSide);
            } else {
                console.warn('Could not determine panel side');
            }
        });
    });
    
    console.log('✅ Panel toggles initialized');
}

// Simple toggle function
function togglePanelSimple(side) {
    console.log(`🔧 Toggling ${side} panel...`);
    
    const panel = document.getElementById(`${side}-panel`);
    if (!panel) {
        console.error(`❌ Panel ${side} not found`);
        return;
    }
    
    const isCurrentlyCollapsed = window.panelStates[side];
    
    if (isCurrentlyCollapsed) {
        // EXPAND
        console.log(`📖 Expanding ${side} panel`);
        panel.classList.remove('collapsed');
        window.panelStates[side] = false;
    } else {
        // COLLAPSE  
        console.log(`📁 Collapsing ${side} panel`);
        panel.classList.add('collapsed');
        window.panelStates[side] = true;
    }
    
    // Force reflow
    panel.offsetHeight;
    
    // Trigger resize after animation
    setTimeout(() => {
        window.dispatchEvent(new Event('resize'));
        if (window.topologyDashboard && window.topologyDashboard.handleResize) {
            window.topologyDashboard.handleResize();
        }
    }, 400);
    
    console.log(`✅ ${side} panel ${isCurrentlyCollapsed ? 'expanded' : 'collapsed'}`);
}

// ================================================================================
// INITIALIZATION
// ================================================================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 DOM loaded, initializing topology...');
    
    // Initialize topology dashboard first
    if (document.getElementById('graph')) {
        window.topologyDashboard = new NetworkTopologyDashboard();
        console.log('✅ Topology dashboard created');
    }
    
    // Initialize panel toggles after a short delay to ensure DOM is ready
    setTimeout(() => {
        initPanelToggles();
        console.log('✅ Panel toggles ready');
    }, 100);
});

if (typeof module !== 'undefined' && module.exports) {
    module.exports = { NetworkTopologyDashboard };
}