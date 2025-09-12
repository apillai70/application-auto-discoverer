/**
 * PortScope Excel Integration for Dashboard - Fixed WebSocket Version
 * Handles 100K+ row Excel processing via FastAPI
 * Integrates with existing archetype.js dashboard
 */

class PortScopeExcelProcessor {
    constructor(config = {}) {
        this.apiUrl = config.apiUrl || 'http://localhost:8001';
        // Fixed WebSocket URL to match backend router path
        this.wsUrl = config.wsUrl || 'ws://localhost:8001/api/v1/excel/ws';
        this.currentJob = null;
        this.websocket = null;
        this.progressCallbacks = [];
        this.maxFileSize = 500 * 1024 * 1024; // 500MB
        
        // WebSocket connection management
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 2000; // Start with 2 seconds
        this.maxReconnectDelay = 30000; // Max 30 seconds
        this.connectionTimeout = 10000; // 10 seconds
        this.isConnecting = false;
        
        // UI elements
        this.uploadArea = null;
        this.progressBar = null;
        this.statusDisplay = null;
        
        this.initializeUI();
        // Delay WebSocket connection to allow UI to load
        setTimeout(() => this.connectWebSocket(), 1000);
    }
    
    initializeUI() {
        // Add Excel upload UI to existing dashboard
        const container = document.createElement('div');
        container.className = 'excel-processor-container';
        container.innerHTML = `
            <div class="excel-upload-panel">
                <div class="panel-header">
                    <h3>📊 Excel Processor (100K+ rows)</h3>
                    <span class="status-badge" id="processor-status">Initializing...</span>
                </div>
                
                <div class="upload-area" id="excel-upload-area">
                    <div class="upload-icon">📄</div>
                    <div class="upload-text">
                        <p>Drag & Drop Excel file here</p>
                        <p class="upload-hint">or click to browse (max 500MB)</p>
                    </div>
                    <input type="file" id="excel-file-input" accept=".xlsx,.xls,.csv" style="display: none;">
                </div>
                
                <div class="processing-status" id="processing-status" style="display: none;">
                    <div class="progress-container">
                        <div class="progress-bar-bg">
                            <div class="progress-bar-fill" id="progress-fill" style="width: 0%"></div>
                        </div>
                        <div class="progress-text">
                            <span id="progress-percentage">0%</span>
                            <span id="progress-message">Initializing...</span>
                        </div>
                    </div>
                    
                    <div class="processing-stats">
                        <div class="stat-item">
                            <span class="stat-label">Rows:</span>
                            <span class="stat-value" id="row-count">0</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Time:</span>
                            <span class="stat-value" id="process-time">0s</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Status:</span>
                            <span class="stat-value" id="job-status">Queued</span>
                        </div>
                    </div>
                </div>
                
                <div class="results-section" id="results-section" style="display: none;">
                    <h4>📈 Processing Results</h4>
                    <div class="results-grid" id="results-grid"></div>
                    <button class="btn btn-primary" id="download-btn">
                        💾 Download Processed File
                    </button>
                </div>
                
                <div class="excel-settings">
                    <h4>⚙️ Column Mappings</h4>
                    <p class="settings-help">Specify column names (comma-separated for multiple options). System tries dedicated columns first, then parses info field as fallback.</p>
                    
                    <div class="settings-grid">
                        <div class="setting-item">
                            <label>Port Columns:</label>
                            <input type="text" id="port-column" value="port,dst_port,destination_port,dport" class="setting-input" placeholder="port,dst_port,destination_port">
                        </div>
                        <div class="setting-item">
                            <label>Protocol Columns:</label>
                            <input type="text" id="protocol-column" value="protocol,proto,ip_proto" class="setting-input" placeholder="protocol,proto,transport_protocol">
                        </div>
                        <div class="setting-item">
                            <label>App ID Columns:</label>
                            <input type="text" id="app-column" value="app_id,application_id,id" class="setting-input" placeholder="app_id,application_id">
                        </div>
                        <div class="setting-item">
                            <label>Info Field Column:</label>
                            <input type="text" id="info-column" value="info,description,details" class="setting-input" placeholder="info,description,details">
                        </div>
                        <div class="setting-item">
                            <label>Sheet Name:</label>
                            <input type="text" id="sheet-name" placeholder="Optional (uses first sheet)" class="setting-input">
                        </div>
                        <div class="setting-item">
                            <label>
                                <input type="checkbox" id="fallback-parsing" checked> 
                                Enable info field parsing as fallback
                            </label>
                        </div>
                    </div>
                </div>
                
                <div class="connection-status" id="connection-status">
                    <div class="ws-status">
                        <span class="ws-indicator" id="ws-indicator"></span>
                        <span id="ws-status-text">WebSocket: Connecting...</span>
                    </div>
                </div>
            </div>
        `;
        
        // Create collapsible side panel
        const sidePanel = document.createElement('div');
        sidePanel.className = 'excel-side-panel';
        sidePanel.innerHTML = `
            <button class="panel-toggle" id="excel-panel-toggle">
                Excel Processor
            </button>
            <div class="panel-content" id="excel-panel-content">
                ${container.innerHTML}
            </div>
        `;
        
        // Add to page
        document.body.appendChild(sidePanel);
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Add styles
        this.injectStyles();
    }
    
    setupEventListeners() {
        // Panel toggle
        const toggleBtn = document.getElementById('excel-panel-toggle');
        const sidePanel = document.querySelector('.excel-side-panel');
        
        if (toggleBtn && sidePanel) {
            toggleBtn.addEventListener('click', function() {
                sidePanel.classList.toggle('open');
                toggleBtn.classList.toggle('active');
            });
        }
        
        // File upload
        const uploadArea = document.getElementById('excel-upload-area');
        const fileInput = document.getElementById('excel-file-input');
        
        uploadArea?.addEventListener('click', () => fileInput?.click());
        
        uploadArea?.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('drag-over');
        });
        
        uploadArea?.addEventListener('dragleave', () => {
            uploadArea.classList.remove('drag-over');
        });
        
        uploadArea?.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('drag-over');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.processFile(files[0]);
            }
        });
        
        fileInput?.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.processFile(e.target.files[0]);
            }
        });
        
        // Download button
        const downloadBtn = document.getElementById('download-btn');
        downloadBtn?.addEventListener('click', () => this.downloadResults());
    }
    
    connectWebSocket() {
        if (this.isConnecting || (this.websocket && this.websocket.readyState === WebSocket.CONNECTING)) {
            console.log('WebSocket connection already in progress');
            return;
        }

        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.log('Max WebSocket reconnection attempts reached');
            this.updateConnectionStatus('failed', 'Connection failed - max attempts reached');
            return;
        }

        this.isConnecting = true;
        console.log(`Attempting WebSocket connection to: ${this.wsUrl} (attempt ${this.reconnectAttempts + 1})`);
        
        // Close existing connection if any
        if (this.websocket) {
            this.websocket.close();
        }
        
        try {
            this.websocket = new WebSocket(this.wsUrl);
            
            // Connection timeout
            const connectionTimeout = setTimeout(() => {
                if (this.websocket && this.websocket.readyState === WebSocket.CONNECTING) {
                    console.log('WebSocket connection timeout');
                    this.websocket.close();
                    this.handleConnectionFailure();
                }
            }, this.connectionTimeout);
            
            this.websocket.onopen = () => {
                clearTimeout(connectionTimeout);
                this.isConnecting = false;
                this.reconnectAttempts = 0;
                this.reconnectDelay = 2000; // Reset delay
                console.log('WebSocket connected successfully');
                this.updateConnectionStatus('connected', 'Connected');
                
                // Send initial ping
                this.sendWebSocketMessage({
                    type: 'ping',
                    timestamp: new Date().toISOString()
                });
            };
            
            this.websocket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleWebSocketMessage(data);
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error, event.data);
                }
            };
            
            this.websocket.onerror = (error) => {
                clearTimeout(connectionTimeout);
                console.error('WebSocket error:', error);
                this.updateConnectionStatus('error', 'Connection error');
            };
            
            this.websocket.onclose = (event) => {
                clearTimeout(connectionTimeout);
                this.isConnecting = false;
                console.log('WebSocket disconnected:', event.code, event.reason);
                
                if (event.code !== 1000) { // Not a normal closure
                    this.handleConnectionFailure();
                } else {
                    this.updateConnectionStatus('disconnected', 'Disconnected');
                }
            };
            
        } catch (error) {
            this.isConnecting = false;
            console.error('Error creating WebSocket connection:', error);
            this.handleConnectionFailure();
        }
    }
    
    handleConnectionFailure() {
        this.reconnectAttempts++;
        this.updateConnectionStatus('reconnecting', `Reconnecting... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            setTimeout(() => {
                this.connectWebSocket();
            }, this.reconnectDelay);
            
            // Exponential backoff
            this.reconnectDelay = Math.min(this.reconnectDelay * 1.5, this.maxReconnectDelay);
        } else {
            this.updateConnectionStatus('failed', 'Connection failed');
        }
    }
    
    handleWebSocketMessage(data) {
        console.log('WebSocket message received:', data.type, data);
        
        switch (data.type) {
            case 'pong':
                console.log('WebSocket pong received');
                break;
                
            case 'job_update':
                if (data.job_id === this.currentJob) {
                    this.updateProgress(data);
                }
                break;
                
            case 'job_status':
                if (data.job_id === this.currentJob) {
                    this.updateProgress(data);
                }
                break;
                
            case 'heartbeat':
                console.log('WebSocket heartbeat:', data.active_jobs, 'active jobs');
                break;
                
            case 'all_jobs':
                console.log('All jobs status:', data.jobs);
                break;
                
            default:
                // Handle legacy format (direct job updates)
                if (data.job_id === this.currentJob && !data.type) {
                    this.updateProgress(data);
                }
        }
        
        // Trigger callbacks
        this.progressCallbacks.forEach(callback => {
            try {
                callback(data);
            } catch (error) {
                console.error('Error in progress callback:', error);
            }
        });
    }
    
    sendWebSocketMessage(message) {
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            try {
                this.websocket.send(JSON.stringify(message));
                return true;
            } catch (error) {
                console.error('Error sending WebSocket message:', error);
                return false;
            }
        } else {
            console.warn('WebSocket not connected, cannot send message:', message);
            return false;
        }
    }
    
    updateConnectionStatus(status, message) {
        const indicator = document.getElementById('ws-indicator');
        const statusText = document.getElementById('ws-status-text');
        const processorStatus = document.getElementById('processor-status');
        
        if (indicator) {
            indicator.className = `ws-indicator ws-${status}`;
        }
        
        if (statusText) {
            statusText.textContent = `WebSocket: ${message}`;
        }
        
        if (processorStatus) {
            let processorMessage = 'Ready';
            let processorClass = 'status-info';
            
            switch (status) {
                case 'connected':
                    processorMessage = 'Connected';
                    processorClass = 'status-success';
                    break;
                case 'reconnecting':
                    processorMessage = 'Reconnecting';
                    processorClass = 'status-warning';
                    break;
                case 'error':
                case 'failed':
                    processorMessage = 'Offline';
                    processorClass = 'status-error';
                    break;
            }
            
            processorStatus.textContent = processorMessage;
            processorStatus.className = `status-badge ${processorClass}`;
        }
    }
    
    async processFile(file) {
        // Validate file
        if (!file.name.match(/\.(xlsx|xls|csv)$/i)) {
            this.showError('Invalid file type. Please upload Excel or CSV file.');
            return;
        }
        
        if (file.size > this.maxFileSize) {
            this.showError(`File too large. Maximum size is ${this.maxFileSize / 1024 / 1024}MB`);
            return;
        }
        
        // Prepare form data
        const formData = new FormData();
        formData.append('file', file);
        
        // Get settings
        const portColumn = document.getElementById('port-column')?.value || 'port,dst_port,destination_port,dport';
        const protocolColumn = document.getElementById('protocol-column')?.value || 'protocol,proto,ip_proto';
        const appColumn = document.getElementById('app-column')?.value || 'app_id,application_id,id';
        const infoColumn = document.getElementById('info-column')?.value || 'info,description,details';
        const sheetName = document.getElementById('sheet-name')?.value || '';
        const fallbackParsing = document.getElementById('fallback-parsing')?.checked !== false;
        
        // Add settings to form data
        formData.append('port_column', portColumn);
        formData.append('protocol_column', protocolColumn);
        formData.append('app_column', appColumn);
        formData.append('info_column', infoColumn);
        formData.append('fallback_parsing', fallbackParsing);
        if (sheetName) {
            formData.append('sheet_name', sheetName);
        }
        
        // Show processing UI
        this.showProcessingUI();
        this.startTimer();
        
        try {
            console.log('Starting file processing...');
            const response = await fetch(`${this.apiUrl}/api/v1/excel/api/process/excel`, {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Processing failed: ${response.status} - ${errorText}`);
            }
            
            const result = await response.json();
            this.currentJob = result.job_id;
            
            console.log('Job created:', this.currentJob, 'WebSocket available:', result.websocket_available);
            
            // Update UI
            document.getElementById('row-count').textContent = result.total_rows.toLocaleString();
            
            // Request job status via WebSocket if available
            if (result.websocket_available && this.websocket && this.websocket.readyState === WebSocket.OPEN) {
                this.sendWebSocketMessage({
                    type: 'get_job_status',
                    job_id: this.currentJob
                });
            }
            
            // Start polling as backup (in case WebSocket fails)
            setTimeout(() => this.pollJobStatus(), 2000);
            
        } catch (error) {
            console.error('Error processing file:', error);
            this.showError(error.message);
            this.stopTimer();
        }
    }
    
    async pollJobStatus() {
        if (!this.currentJob) return;
        
        try {
            const response = await fetch(`${this.apiUrl}/api/v1/excel/api/job/${this.currentJob}`);
            
            if (!response.ok) {
                throw new Error(`Status check failed: ${response.status}`);
            }
            
            const job = await response.json();
            
            // Only update from polling if WebSocket is not connected
            if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
                this.updateProgress(job);
            }
            
            if (job.status === 'processing' || job.status === 'queued') {
                // Continue polling
                setTimeout(() => this.pollJobStatus(), 2000);
            } else if (job.status === 'completed') {
                this.showResults(job);
                this.stopTimer();
            } else if (job.status === 'error') {
                this.showError(job.error || 'Processing failed');
                this.stopTimer();
            }
            
        } catch (error) {
            console.error('Error polling job status:', error);
            // Retry with exponential backoff
            setTimeout(() => this.pollJobStatus(), 5000);
        }
    }
    
    updateProgress(data) {
        const progressFill = document.getElementById('progress-fill');
        const progressPercentage = document.getElementById('progress-percentage');
        const progressMessage = document.getElementById('progress-message');
        const jobStatus = document.getElementById('job-status');
        
        if (progressFill && data.progress !== undefined) {
            progressFill.style.width = `${data.progress || 0}%`;
        }
        
        if (progressPercentage && data.progress !== undefined) {
            progressPercentage.textContent = `${data.progress || 0}%`;
        }
        
        if (progressMessage && data.message) {
            progressMessage.textContent = data.message;
        }
        
        if (jobStatus && data.status) {
            jobStatus.textContent = data.status;
            jobStatus.className = `stat-value status-${data.status}`;
        }
        
        // Update row count if available
        if (data.total_rows && document.getElementById('row-count')) {
            document.getElementById('row-count').textContent = data.total_rows.toLocaleString();
        }
        
        console.log('Progress update:', data.progress + '%', data.message, data.status);
    }
    
    showResults(job) {
        const resultsSection = document.getElementById('results-section');
        const resultsGrid = document.getElementById('results-grid');
        
        if (!resultsSection || !resultsGrid) return;
        
        resultsSection.style.display = 'block';
        
        const summary = job.result?.summary || {};
        
        resultsGrid.innerHTML = `
            <div class="result-card">
                <h5>Total Processed</h5>
                <p class="result-value">${job.result?.rows_processed?.toLocaleString() || 0}</p>
            </div>
            <div class="result-card">
                <h5>Applications Found</h5>
                <p class="result-value">${job.result?.applications_identified?.toLocaleString() || 0}</p>
            </div>
            <div class="result-card">
                <h5>Architecture Distribution</h5>
                <div class="mini-chart">
                    ${this.createMiniChart(summary.architecture_distribution || {})}
                </div>
            </div>
            <div class="result-card">
                <h5>Risk Assessment</h5>
                <div class="risk-breakdown">
                    ${this.createRiskBreakdown(summary.risk_distribution || {})}
                </div>
            </div>
            <div class="result-card">
                <h5>Processing Time</h5>
                <p class="result-value">${this.formatTime(job.result?.processing_time || 0)}</p>
            </div>
            <div class="result-card">
                <h5>Parsing Methods</h5>
                <div class="parsing-breakdown">
                    ${this.createParsingBreakdown(summary.parsing_methods || {})}
                </div>
            </div>
        `;
        
        // Update dashboard if available
        if (window.dashboard && job.result?.applications) {
            this.updateDashboard(job.result.applications);
        }
        
        console.log('Processing completed successfully');
    }
    
    updateDashboard(applications) {
        // Integrate with existing dashboard
        if (!window.dashboard) {
            console.warn('Dashboard not available for integration');
            return;
        }
        
        // Convert to dashboard format
        const dashboardApps = applications.map(app => ({
            id: app.app_id,
            name: app.app_name || app.app_id,
            archetype: app.architecture,
            color: this.getArchetypeColor(app.architecture),
            status: 'active',
            flow_count: app.flow_count || 0,
            traffic_pattern: this.getTrafficPattern(app.architecture),
            primary_ports: (app.ports || []).slice(0, 3).map(p => ({ port: parseInt(p), count: Math.floor(Math.random() * 1000) + 100 })),
            network_evidence: [
                `Risk level: ${app.risk_level || 'unknown'}`,
                `Protocols: ${(app.protocols || []).join(', ') || 'N/A'}`,
                `Parsing: ${app.parsing_method || 'standard'}`
            ],
            x: Math.random() * 800,
            y: Math.random() * 600
        }));
        
        // Add to dashboard
        window.dashboard.applications = [
            ...window.dashboard.applications,
            ...dashboardApps
        ];
        
        window.dashboard.filteredApps = window.dashboard.applications.slice();
        window.dashboard.archetypes = window.dashboard.generateArchetypeSummary();
        window.dashboard.render();
        
        console.log(`Added ${dashboardApps.length} applications to dashboard`);
    }
    
    getArchetypeColor(archetype) {
        const colors = {
            'Microservices': '#10b981',
            '3-Tier': '#3b82f6',
            'Monolithic': '#8b5cf6',
            'Event-Driven': '#f59e0b',
            'SOA': '#ef4444',
            'Web + API Headless': '#06b6d4',
            'Client-Server': '#84cc16',
            'Database-Centric': '#ec4899'
        };
        return colors[archetype] || '#64748b';
    }
    
    getTrafficPattern(archetype) {
        const patterns = {
            'Microservices': 'East-West Service Communication',
            '3-Tier': 'North-South Layered',
            'Monolithic': 'Centralized Processing',
            'Event-Driven': 'Event Streaming',
            'SOA': 'Service Bus Communication',
            'Web + API Headless': 'API-First Communication',
            'Client-Server': 'Direct Client Communication',
            'Database-Centric': 'Data-Centric Communication'
        };
        return patterns[archetype] || 'Standard Communication';
    }
    
    async downloadResults() {
        if (!this.currentJob) return;
        
        try {
            console.log('Downloading results for job:', this.currentJob);
            const response = await fetch(`${this.apiUrl}/api/v1/excel/api/download/${this.currentJob}`);
            
            if (!response.ok) {
                throw new Error('Download failed');
            }
            
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `processed_${new Date().getTime()}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            console.log('Download completed');
            
        } catch (error) {
            console.error('Download error:', error);
            this.showError('Failed to download file: ' + error.message);
        }
    }
    
    createMiniChart(data) {
        if (!data || Object.keys(data).length === 0) {
            return '<p class="no-data">No data</p>';
        }
        
        const total = Object.values(data).reduce((sum, val) => sum + val, 0);
        
        return Object.entries(data)
            .sort(([,a], [,b]) => b - a) // Sort by count descending
            .map(([arch, count]) => {
                const percentage = ((count / total) * 100).toFixed(1);
                const color = this.getArchetypeColor(arch);
                return `
                    <div class="chart-bar">
                        <span class="bar-label">${arch}</span>
                        <div class="bar-container">
                            <div class="bar-fill" style="width: ${percentage}%; background-color: ${color}"></div>
                        </div>
                        <span class="bar-value">${count}</span>
                    </div>
                `;
            })
            .join('');
    }
    
    createRiskBreakdown(data) {
        const riskColors = {
            critical: '#dc2626',
            high: '#ea580c',
            medium: '#d97706',
            low: '#65a30d',
            minimal: '#16a34a'
        };
        
        return Object.entries(data)
            .sort(([,a], [,b]) => b - a)
            .map(([risk, count]) => `
                <div class="risk-item">
                    <span class="risk-indicator" style="background: ${riskColors[risk] || '#6b7280'}"></span>
                    <span class="risk-label">${risk}</span>
                    <span class="risk-count">${count}</span>
                </div>
            `)
            .join('') || '<p class="no-data">No risk data</p>';
    }
    
    createParsingBreakdown(data) {
        return Object.entries(data)
            .map(([method, count]) => `
                <div class="parsing-item">
                    <span class="parsing-label">${method.replace('_', ' ')}</span>
                    <span class="parsing-count">${count}</span>
                </div>
            `)
            .join('') || '<p class="no-data">No parsing data</p>';
    }
    
    showProcessingUI() {
        document.getElementById('excel-upload-area').style.display = 'none';
        document.getElementById('processing-status').style.display = 'block';
        document.getElementById('results-section').style.display = 'none';
    }
    
    showError(message) {
        const toast = document.createElement('div');
        toast.className = 'error-toast';
        toast.textContent = message;
        document.body.appendChild(toast);
        
        setTimeout(() => toast.remove(), 8000);
        
        this.updateStatus('Error', 'error');
        console.error('Excel Processor Error:', message);
    }
    
    updateStatus(status, type = 'info') {
        const statusBadge = document.getElementById('processor-status');
        if (statusBadge) {
            statusBadge.textContent = status;
            statusBadge.className = `status-badge status-${type}`;
        }
    }
    
    startTimer() {
        this.startTime = Date.now();
        this.timerInterval = setInterval(() => {
            const elapsed = Math.floor((Date.now() - this.startTime) / 1000);
            const timeElement = document.getElementById('process-time');
            if (timeElement) {
                timeElement.textContent = this.formatTime(elapsed);
            }
        }, 1000);
    }
    
    stopTimer() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
    }
    
    formatTime(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;
        
        if (hours > 0) {
            return `${hours}h ${minutes}m ${secs}s`;
        } else if (minutes > 0) {
            return `${minutes}m ${secs}s`;
        }
        return `${secs}s`;
    }
    
    injectStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .excel-side-panel {
                position: fixed;
                top: 0;
                right: -360px;
                height: 100vh;
                width: 360px;
                background: white;
                border-left: 1px solid #e5e7eb;
                box-shadow: -4px 0 12px rgba(0, 0, 0, 0.1);
                transition: right 0.3s ease;
                z-index: 1000;
            }

            .excel-side-panel.open {
                right: 0;
            }

            .panel-toggle {
                position: absolute;
                left: -140px;
                top: 20px;
                background: #4f46e5;
                color: white;
                border: none;
                padding: 8px 12px;
                border-radius: 8px 0 0 8px;
                cursor: pointer;
                writing-mode: vertical-lr;
                text-orientation: mixed;
                transition: all 0.3s ease;
            }
            
            .panel-toggle:hover {
                background: #2563eb;
                transform: translateX(5px);
            }
            
            .panel-toggle.active {
                background: #4338ca;
            }
            
            .excel-side-panel .panel-content {
                display: none;
                padding: 20px;
                max-height: calc(100vh - 20px);
                overflow-y: auto;
                background: #1e293b;
                color: #e2e8f0;
            }

            .excel-side-panel.open .panel-content {
                display: block;
            }
            
            .excel-upload-panel {
                color: #e2e8f0;
            }
            
            .panel-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
                padding-bottom: 10px;
                border-bottom: 1px solid #475569;
            }
            
            .panel-header h3 {
                margin: 0;
                font-size: 18px;
            }
            
            .status-badge {
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 12px;
                background: #475569;
            }
            
            .status-badge.status-success {
                background: #10b981;
            }
            
            .status-badge.status-error {
                background: #ef4444;
            }
            
            .status-badge.status-warning {
                background: #f59e0b;
            }
            
            .status-badge.status-processing {
                background: #3b82f6;
                animation: pulse 2s infinite;
            }
            
            .upload-area {
                border: 2px dashed #475569;
                border-radius: 12px;
                padding: 30px;
                text-align: center;
                cursor: pointer;
                transition: all 0.3s;
                margin-bottom: 20px;
            }
            
            .upload-area:hover {
                border-color: #3b82f6;
                background: rgba(59, 130, 246, 0.1);
            }
            
            .upload-area.drag-over {
                border-color: #10b981;
                background: rgba(16, 185, 129, 0.1);
            }
            
            .upload-icon {
                font-size: 48px;
                margin-bottom: 10px;
            }
            
            .upload-hint {
                font-size: 12px;
                color: #94a3b8;
                margin-top: 5px;
            }
            
            .processing-status {
                margin: 20px 0;
            }
            
            .progress-container {
                margin-bottom: 20px;
            }
            
            .progress-bar-bg {
                background: #334155;
                height: 24px;
                border-radius: 12px;
                overflow: hidden;
            }
            
            .progress-bar-fill {
                height: 100%;
                background: linear-gradient(90deg, #3b82f6, #10b981);
                transition: width 0.3s ease;
            }
            
            .progress-text {
                display: flex;
                justify-content: space-between;
                margin-top: 8px;
                font-size: 12px;
                color: #94a3b8;
            }
            
            .processing-stats {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 10px;
                margin-top: 15px;
            }
            
            .stat-item {
                background: #334155;
                padding: 8px;
                border-radius: 8px;
                text-align: center;
            }
            
            .stat-label {
                display: block;
                font-size: 10px;
                color: #94a3b8;
                margin-bottom: 4px;
            }
            
            .stat-value {
                display: block;
                font-size: 16px;
                font-weight: bold;
                color: #f1f5f9;
            }
            
            .stat-value.status-queued {
                color: #f59e0b;
            }
            
            .stat-value.status-processing {
                color: #3b82f6;
                animation: pulse 2s infinite;
            }
            
            .stat-value.status-completed {
                color: #10b981;
            }
            
            .stat-value.status-error {
                color: #ef4444;
            }
            
            .results-section {
                margin-top: 20px;
                padding-top: 20px;
                border-top: 1px solid #475569;
            }
            
            .results-grid {
                display: grid;
                gap: 10px;
                margin: 15px 0;
            }
            
            .result-card {
                background: #334155;
                padding: 12px;
                border-radius: 8px;
            }
            
            .result-card h5 {
                margin: 0 0 8px 0;
                font-size: 12px;
                color: #94a3b8;
            }
            
            .result-value {
                font-size: 20px;
                font-weight: bold;
                color: #3b82f6;
                margin: 0;
            }
            
            .mini-chart {
                font-size: 11px;
            }
            
            .chart-bar {
                display: grid;
                grid-template-columns: 1fr 2fr auto;
                align-items: center;
                gap: 8px;
                margin: 4px 0;
            }
            
            .bar-label {
                font-size: 10px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            
            .bar-container {
                background: #1e293b;
                height: 16px;
                border-radius: 8px;
                overflow: hidden;
            }
            
            .bar-fill {
                height: 100%;
                transition: width 0.3s ease;
            }
            
            .bar-value {
                font-size: 10px;
                font-weight: bold;
                min-width: 20px;
                text-align: right;
            }
            
            .risk-item,
            .parsing-item {
                display: flex;
                align-items: center;
                gap: 8px;
                margin: 4px 0;
                font-size: 11px;
            }
            
            .risk-indicator {
                width: 12px;
                height: 12px;
                border-radius: 50%;
            }
            
            .risk-label,
            .parsing-label {
                flex: 1;
            }
            
            .risk-count,
            .parsing-count {
                font-weight: bold;
                min-width: 20px;
                text-align: right;
            }
            
            .excel-settings {
                margin-top: 20px;
                padding-top: 20px;
                border-top: 1px solid #475569;
            }
            
            .excel-settings h4 {
                font-size: 14px;
                margin-bottom: 12px;
            }
            
            .settings-grid {
                display: grid;
                gap: 12px;
            }
            
            .settings-help {
                font-size: 11px;
                color: #94a3b8;
                margin-bottom: 12px;
                line-height: 1.4;
            }

            .setting-item label {
                font-size: 12px;
                color: #94a3b8;
                display: block;
                margin-bottom: 4px;
            }

            .setting-item input[type="checkbox"] {
                margin-right: 6px;
                transform: scale(0.9);
            }

            .setting-input {
                width: 100%;
                padding: 6px 8px;
                background: #334155;
                border: 1px solid #475569;
                border-radius: 4px;
                color: #f1f5f9;
                font-size: 11px;
            }

            .setting-input::placeholder {
                color: #64748b;
                font-size: 10px;
            }
            
            .connection-status {
                margin-top: 15px;
                padding-top: 15px;
                border-top: 1px solid #475569;
            }
            
            .ws-status {
                display: flex;
                align-items: center;
                gap: 8px;
                font-size: 11px;
            }
            
            .ws-indicator {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: #6b7280;
            }
            
            .ws-indicator.ws-connected {
                background: #10b981;
                animation: pulse-green 2s infinite;
            }
            
            .ws-indicator.ws-reconnecting {
                background: #f59e0b;
                animation: pulse-yellow 1s infinite;
            }
            
            .ws-indicator.ws-error,
            .ws-indicator.ws-failed {
                background: #ef4444;
            }
            
            .btn-primary {
                width: 100%;
                padding: 10px;
                background: #3b82f6;
                color: white;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-size: 14px;
                margin-top: 10px;
                transition: background 0.3s ease;
            }
            
            .btn-primary:hover {
                background: #2563eb;
            }
            
            .btn-primary:disabled {
                background: #6b7280;
                cursor: not-allowed;
            }
            
            .error-toast {
                position: fixed;
                bottom: 20px;
                right: 20px;
                background: #ef4444;
                color: white;
                padding: 12px 20px;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
                z-index: 10001;
                animation: slideIn 0.3s ease;
                max-width: 350px;
                word-wrap: break-word;
            }
            
            .no-data {
                color: #94a3b8;
                font-size: 11px;
                font-style: italic;
                margin: 0;
            }
            
            @keyframes slideIn {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
            
            @keyframes pulse {
                0%, 100% {
                    opacity: 1;
                }
                50% {
                    opacity: 0.7;
                }
            }
            
            @keyframes pulse-green {
                0%, 100% {
                    box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
                }
                50% {
                    box-shadow: 0 0 0 4px rgba(16, 185, 129, 0);
                }
            }
            
            @keyframes pulse-yellow {
                0%, 100% {
                    box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.7);
                }
                50% {
                    box-shadow: 0 0 0 4px rgba(245, 158, 11, 0);
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    // API helper methods
    async classifyBatch(applications) {
        try {
            const response = await fetch(`${this.apiUrl}/api/v1/excel/api/classify/batch`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ applications })
            });
            
            if (!response.ok) {
                throw new Error('Classification failed');
            }
            
            return await response.json();
            
        } catch (error) {
            console.error('Batch classification error:', error);
            throw error;
        }
    }
    
    onProgress(callback) {
        this.progressCallbacks.push(callback);
    }
    
    // Cleanup method
    destroy() {
        if (this.websocket) {
            this.websocket.close();
        }
        
        this.stopTimer();
        
        // Remove UI elements
        const sidePanel = document.querySelector('.excel-side-panel');
        if (sidePanel) {
            sidePanel.remove();
        }
        
        console.log('Excel Processor destroyed');
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // Check if dashboard exists
    if (window.dashboard) {
        console.log('Initializing Excel Processor integration...');
        
        // Create processor instance
        window.excelProcessor = new PortScopeExcelProcessor({
            apiUrl: window.PORTSCOPE_API_URL || 'http://localhost:8001',
            wsUrl: window.PORTSCOPE_WS_URL || 'ws://localhost:8001/api/v1/excel/ws'
        });
        
        // Add integration with dashboard
        window.excelProcessor.onProgress((data) => {
            // Update dashboard stats if processing completes
            if (data.status === 'completed' && window.dashboard) {
                window.dashboard.updateStats();
            }
        });
        
        console.log('Excel Processor ready with WebSocket support');
    } else {
        console.warn('Dashboard not found, Excel Processor running standalone');
    }
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.excelProcessor) {
        window.excelProcessor.destroy();
    }
});

// Export for external use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PortScopeExcelProcessor;
}