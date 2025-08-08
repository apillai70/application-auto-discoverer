// Integration Hub Manager
var IntegrationManager = {
    // State management
    connections: {
        splunk: { connected: false, client: null },
        dynatrace: { connected: false, client: null },
        extrahop: { connected: false, client: null },
        'custom-api': { connected: true, client: { endpoint: 'api.internal.com/v1' } },
        'file-upload': { connected: false, client: null },
        database: { connected: false, client: null }
    },
    
    realTimeCollection: {
        active: false,
        interval: null,
        processedCount: 0,
        errorCount: 0,
        lastUpdate: null
    },
    
    collectedData: [],
    processedData: [],
    dataFeedPaused: false,
    dataFeedInterval: null,

    // Initialize the integration manager
    initialize: function() {
        console.log('🔌 Initializing Integration Manager');
        
        try {
            this.setupEventListeners();
            this.startDataFeed();
            this.updateIntegrationStatuses();
            this.updateSystemStatus();
            
            if (window.AppDiscoverer && window.AppDiscoverer.showToast) {
                window.AppDiscoverer.showToast('✅ Integration Hub initialized', 'success');
            }
            console.log('✅ Integration Manager initialized successfully');
            
        } catch (error) {
            console.error('❌ Failed to initialize Integration Manager:', error);
            if (window.AppDiscoverer && window.AppDiscoverer.showToast) {
                window.AppDiscoverer.showToast('Failed to initialize Integration Hub', 'error');
            }
        }
    },

    // Setup event listeners
    setupEventListeners: function() {
        var uploadZone = document.getElementById('uploadZone');
        var fileInput = document.getElementById('fileInput');

        if (uploadZone && fileInput) {
            uploadZone.onclick = function() { fileInput.click(); };
            uploadZone.ondragover = this.handleDragOver;
            uploadZone.ondrop = this.handleDrop.bind(this);
            fileInput.onchange = this.handleFileSelect.bind(this);
        }

        console.log('✅ Event listeners setup complete');
    },

    // File handling
    handleDragOver: function(e) {
        e.preventDefault();
        e.currentTarget.classList.add('dragover');
    },

    handleDrop: function(e) {
        e.preventDefault();
        e.currentTarget.classList.remove('dragover');
        var files = e.dataTransfer.files;
        if (files.length > 0) {
            this.processFiles(files);
        }
    },

    handleFileSelect: function(e) {
        var files = e.target.files;
        if (files.length > 0) {
            this.processFiles(files);
        }
    },

    // Process uploaded files
    processFiles: function(files) {
        var self = this;
        var progressBar = document.getElementById('uploadProgress');
        var progressFill = document.getElementById('progressFill');
        var progressText = document.getElementById('progressText');
        var results = document.getElementById('uploadResults');

        if (progressBar) progressBar.style.display = 'block';
        if (results) results.innerHTML = '';

        var processFile = function(fileIndex) {
            if (fileIndex >= files.length) {
                if (progressText) progressText.textContent = 'Upload complete!';
                return;
            }

            var file = files[fileIndex];
            var progress = ((fileIndex + 1) / files.length) * 100;

            if (progressFill) progressFill.style.width = progress + '%';
            if (progressText) progressText.textContent = 'Processing ' + file.name + '...';

            setTimeout(function() {
                try {
                    self.addToDataFeed('File Upload', 'Successfully processed: ' + file.name, 'SUCCESS');
                    
                    if (results) {
                        results.innerHTML += '<div style="color: #10b981; margin: 5px 0;">✅ ' + file.name + ' - Processed successfully</div>';
                    }
                } catch (error) {
                    self.addToDataFeed('File Upload', 'Failed to process: ' + file.name, 'ERROR');
                    
                    if (results) {
                        results.innerHTML += '<div style="color: #ef4444; margin: 5px 0;">❌ ' + file.name + ' - ' + error.message + '</div>';
                    }
                }

                processFile(fileIndex + 1);
            }, 1000);
        };

        processFile(0);
    },

    // Data feed management
    startDataFeed: function() {
        var self = this;
        this.dataFeedInterval = setInterval(function() {
            if (!self.dataFeedPaused) {
                self.simulateDataFeedEvent();
            }
        }, 5000);
    },

    simulateDataFeedEvent: function() {
        var sources = ['ExtraHop', 'Custom API', 'Database', 'Splunk', 'File Upload'];
        var messages = [
            'Network topology updated',
            'New application discovered',
            'Configuration sync completed',
            'Performance metrics collected',
            'Security scan completed',
            'Data processing finished'
        ];
        var types = ['INFO', 'SUCCESS', 'ERROR'];

        var source = sources[Math.floor(Math.random() * sources.length)];
        var message = messages[Math.floor(Math.random() * messages.length)];
        var type = types[Math.floor(Math.random() * types.length)];

        this.addToDataFeed(source, message, type);
    },

    addToDataFeed: function(source, message, type) {
        var container = document.getElementById('dataFeedContainer');
        if (!container) return;

        var timestamp = new Date().toLocaleTimeString('en-US', { hour12: false });
        var feedItem = document.createElement('div');
        feedItem.className = 'feed-item new';
        
        feedItem.innerHTML = 
            '<span class="feed-timestamp">' + timestamp + '</span>' +
            '<span class="feed-source">' + source + '</span>' +
            '<span class="feed-message">' + message + '</span>' +
            '<span class="feed-type type-' + type.toLowerCase() + '">' + type + '</span>';

        container.insertBefore(feedItem, container.firstChild);

        // Remove old items (keep only latest 20)
        while (container.children.length > 20) {
            container.removeChild(container.lastChild);
        }

        // Remove 'new' class after animation
        setTimeout(function() {
            feedItem.classList.remove('new');
        }, 500);

        // Update processed count
        this.realTimeCollection.processedCount++;
        this.updateSystemStatus();
    },

    // Update system status
    updateSystemStatus: function() {
        var connectedCount = 0;
        for (var key in this.connections) {
            if (this.connections[key].connected) {
                connectedCount++;
            }
        }

        var systemActiveConnections = document.getElementById('systemActiveConnections');
        var totalProcessed = document.getElementById('totalProcessed');
        var processingRate = document.getElementById('processingRate');
        var errorCount = document.getElementById('errorCount');

        if (systemActiveConnections) systemActiveConnections.textContent = connectedCount;
        if (totalProcessed) totalProcessed.textContent = this.realTimeCollection.processedCount;
        if (processingRate) processingRate.textContent = Math.floor(Math.random() * 50) + '/sec';
        if (errorCount) errorCount.textContent = this.realTimeCollection.errorCount;

        // Update header stats
        var activeConnections = document.getElementById('activeConnections');
        var dataStreams = document.getElementById('dataStreams');
        var realTimeEvents = document.getElementById('realTimeEvents');
        var dataVolume = document.getElementById('dataVolume');

        if (activeConnections) activeConnections.textContent = connectedCount;
        if (dataStreams) dataStreams.textContent = (Math.random() * 3000 + 1000).toFixed(0) + 'k';
        if (realTimeEvents) realTimeEvents.textContent = (Math.random() * 1000 + 500).toFixed(0);
        if (dataVolume) dataVolume.textContent = (Math.random() * 20 + 10).toFixed(1) + ' GB';
    },

    updateIntegrationStatuses: function() {
        for (var integrationId in this.connections) {
            this.updateIntegrationCard(integrationId, this.connections[integrationId]);
        }
    },

    updateIntegrationCard: function(integrationId, config) {
        var card = document.querySelector('[data-integration="' + integrationId + '"]');
        if (!card) return;

        var statusElement = card.querySelector('.integration-status');
        if (statusElement) {
            statusElement.textContent = config.connected ? 'connected' : 'disconnected';
            statusElement.className = 'integration-status status-' + (config.connected ? 'connected' : 'disconnected');
        }
    },

    // Pipeline management
    updatePipelineStep: function(step, status) {
        var stepElement = document.getElementById('step' + step);
        if (stepElement) {
            stepElement.className = 'step-icon step-' + status;
        }
    },

    // Connection simulation
    simulateConnection: function(service, delay) {
        return new Promise(function(resolve, reject) {
            setTimeout(function() {
                if (Math.random() > 0.2) { // 80% success rate
                    resolve();
                } else {
                    reject(new Error('Connection timeout'));
                }
            }, delay);
        });
    },

    // Utility functions
    logToConsole: function(consoleId, message, type) {
        var console = document.getElementById(consoleId);
        if (!console) return;

        var timestamp = new Date().toLocaleTimeString();
        var prefix = type === 'error' ? '❌' : type === 'warning' ? '⚠️' : '>';
        var newMessage = '[' + timestamp + '] ' + prefix + ' ' + message + '\n';
        
        console.innerHTML += newMessage;
        console.scrollTop = console.scrollHeight;
    },

    logToAllConsoles: function(message, type) {
        var consoles = ['splunkLog', 'dynatraceLog', 'extrahopLog'];
        for (var i = 0; i < consoles.length; i++) {
            this.logToConsole(consoles[i], message, type);
        }
    },

    // Data processing functions
    addToCollectedData: function(source, data) {
        var timestamp = new Date().toISOString();
        var self = this;

        if (!Array.isArray(data)) {
            data = [data];
        }

        data.forEach(function(record, index) {
            var enrichedRecord = {
                id: source + '_' + timestamp + '_' + index,
                source: source,
                timestamp: timestamp,
                data: record
            };
            self.collectedData.push(enrichedRecord);
        });

        this.realTimeCollection.processedCount += data.length;
        this.updateSystemStatus();
    },

    normalizeCollectedData: function() {
        var self = this;
        this.updatePipelineStep(2, 'active');
        this.logToAllConsoles('🔄 Normalizing collected data...');

        try {
            var newData = this.collectedData.slice(this.processedData.length);

            newData.forEach(function(record) {
                var normalized = self.normalizeRecord(record);
                self.processedData.push(normalized);
            });

            this.updatePipelineStep(2, 'active');
            this.logToAllConsoles('✅ Normalized ' + newData.length + ' new records');

            if (document.getElementById('enableDeduplication') && document.getElementById('enableDeduplication').checked) {
                this.deduplicateData();
            }

            if (document.getElementById('enableVectorization') && document.getElementById('enableVectorization').checked) {
                this.generateVectors();
            }

        } catch (error) {
            this.updatePipelineStep(2, 'error');
            this.logToAllConsoles('❌ Normalization error: ' + error.message, 'error');
        }
    },

    normalizeRecord: function(record) {
        var normalized = {
            id: record.id,
            source: record.source,
            timestamp: record.timestamp,
            original_data: record.data
        };

        switch (record.source) {
            case 'splunk':
                normalized.normalized_data = this.normalizeSplunkRecord(record.data);
                break;
            case 'dynatrace':
                normalized.normalized_data = this.normalizeDynatraceRecord(record.data);
                break;
            case 'extrahop':
                normalized.normalized_data = this.normalizeExtraHopRecord(record.data);
                break;
            default:
                normalized.normalized_data = record.data;
        }

        return normalized;
    },

    normalizeSplunkRecord: function(data) {
        return {
            source_ip: data.src_ip || data.clientip || data.src,
            dest_ip: data.dest_ip || data.destip || data.dest,
            source_port: data.src_port || data.srcport,
            dest_port: data.dest_port || data.destport || data.port,
            protocol: data.protocol || data.proto,
            bytes: data.bytes || data.bytes_in || data.bytes_out,
            action: data.action || data.act,
            timestamp: data._time || data.timestamp
        };
    },

    normalizeDynatraceRecord: function(data) {
        return {
            source_ip: data['@network.client.ip'] || data.client_ip,
            dest_ip: data['@network.destination.ip'] || data.dest_ip,
            source_port: data['@network.client.port'] || data.client_port,
            dest_port: data['@network.destination.port'] || data.dest_port,
            protocol: data['@network.transport'] || data.protocol,
            bytes: data['@network.bytes_read'] || data.bytes,
            status: data['@http.status_code'] || data.status,
            timestamp: data.timestamp || data['@timestamp']
        };
    },

    normalizeExtraHopRecord: function(data) {
        return {
            source_ip: data.src_ip || data.client_ip,
            dest_ip: data.dest_ip || data.server_ip,
            source_port: data.src_port || data.client_port,
            dest_port: data.dest_port || data.server_port,
            protocol: data.protocol || data.l4_proto,
            bytes: data.bytes || data.req_bytes || data.rsp_bytes,
            packets: data.packets || data.req_pkts || data.rsp_pkts,
            timestamp: data.timestamp || data.time
        };
    },

    // Export functions
    exportToTopologyAnalyzer: function() {
        if (this.processedData.length === 0) {
            this.logToAllConsoles('❌ No processed data to export', 'error');
            return;
        }

        var topologyData = this.convertToTopologyFormat(this.processedData);

        if (window.NetworkAnalyzer) {
            window.NetworkAnalyzer.setData(topologyData);
            this.logToAllConsoles('✅ Data exported to Network Topology Analyzer');
        } else {
            this.logToAllConsoles('⚠️ Network Topology Analyzer not found', 'warning');
            this.downloadJSON(topologyData, 'topology-data.json');
        }

        this.updatePipelineStep(5, 'active');
    },

    convertToTopologyFormat: function(data) {
        var nodes = {};
        var edges = [];

        data.forEach(function(record) {
            var norm = record.normalized_data;
            if (norm.source_ip && norm.dest_ip) {
                // Add source node
                if (!nodes[norm.source_ip]) {
                    nodes[norm.source_ip] = {
                        id: norm.source_ip,
                        type: 'host',
                        connections: 0
                    };
                }
                
                // Add destination node
                if (!nodes[norm.dest_ip]) {
                    nodes[norm.dest_ip] = {
                        id: norm.dest_ip,
                        type: 'host',
                        connections: 0
                    };
                }

                // Add edge
                edges.push({
                    source: norm.source_ip,
                    target: norm.dest_ip,
                    protocol: norm.protocol,
                    bytes: norm.bytes || 0
                });

                nodes[norm.source_ip].connections++;
                nodes[norm.dest_ip].connections++;
            }
        });

        return {
            nodes: Object.values(nodes),
            edges: edges
        };
    },

    downloadJSON: function(data, filename) {
        var dataStr = JSON.stringify(data, null, 2);
        var dataBlob = new Blob([dataStr], {type: 'application/json'});
        var url = URL.createObjectURL(dataBlob);
        
        var link = document.createElement('a');
        link.href = url;
        link.download = filename;
        link.click();
        
        URL.revokeObjectURL(url);
    }
};

// Global functions for UI interactions
function toggleIntegration(integrationId) {
    var integration = IntegrationManager.connections[integrationId];
    if (!integration) return;

    integration.connected = !integration.connected;
    
    IntegrationManager.updateIntegrationCard(integrationId, integration);
    IntegrationManager.updateSystemStatus();
    
    var status = integration.connected ? 'connected' : 'disconnected';
    if (window.AppDiscoverer && window.AppDiscoverer.showToast) {
        window.AppDiscoverer.showToast(integrationId + ' ' + status, 'info');
    }
}

function configureIntegration(integrationId) {
    var modal = document.getElementById('configModal');
    var title = document.getElementById('configModalTitle');
    var body = document.getElementById('configModalBody');

    if (title) title.textContent = 'Configure ' + integrationId;
    if (body) {
        var config = IntegrationManager.connections[integrationId] || {};
        var endpoint = config.client ? config.client.endpoint || '' : '';
        
        body.innerHTML = 
            '<div style="margin-bottom: 20px;">' +
                '<label style="display: block; margin-bottom: 5px; color: #60a5fa;">Endpoint URL:</label>' +
                '<input type="text" style="width: 100%; padding: 10px; background: #0f172a; border: 1px solid #334155; border-radius: 6px; color: #e2e8f0;" value="' + endpoint + '">' +
            '</div>' +
            '<div style="margin-bottom: 20px;">' +
                '<label style="display: block; margin-bottom: 5px; color: #60a5fa;">API Key:</label>' +
                '<input type="password" style="width: 100%; padding: 10px; background: #0f172a; border: 1px solid #334155; border-radius: 6px; color: #e2e8f0;" placeholder="Enter API key">' +
            '</div>' +
            '<div style="margin-bottom: 20px;">' +
                '<label style="display: block; margin-bottom: 5px; color: #60a5fa;">Sync Interval (minutes):</label>' +
                '<input type="number" style="width: 100%; padding: 10px; background: #0f172a; border: 1px solid #334155; border-radius: 6px; color: #e2e8f0;" value="5" min="1" max="60">' +
            '</div>';
    }
    
    if (modal) modal.style.display = 'flex';
}

function testConnection(integrationId) {
    if (window.AppDiscoverer && window.AppDiscoverer.showToast) {
        window.AppDiscoverer.showToast('Testing ' + integrationId + ' connection...', 'info');
    }
    
    IntegrationManager.simulateConnection(integrationId, 2000).then(function() {
        if (window.AppDiscoverer && window.AppDiscoverer.showToast) {
            window.AppDiscoverer.showToast(integrationId + ' connection successful!', 'success');
        }
        IntegrationManager.addToDataFeed(integrationId, 'Connection test successful', 'SUCCESS');
    }).catch(function() {
        if (window.AppDiscoverer && window.AppDiscoverer.showToast) {
            window.AppDiscoverer.showToast(integrationId + ' connection failed', 'error');
        }
        IntegrationManager.addToDataFeed(integrationId, 'Connection test failed', 'ERROR');
    });
}

function connectIntegration(integrationId) {
    if (window.AppDiscoverer && window.AppDiscoverer.showToast) {
        window.AppDiscoverer.showToast('Connecting to ' + integrationId + '...', 'info');
    }
    
    IntegrationManager.simulateConnection(integrationId, 3000).then(function() {
        var integration = IntegrationManager.connections[integrationId];
        if (integration) {
            integration.connected = true;
            IntegrationManager.updateIntegrationCard(integrationId, integration);
            IntegrationManager.updateSystemStatus();
            if (window.AppDiscoverer && window.AppDiscoverer.showToast) {
                window.AppDiscoverer.showToast('Connected to ' + integrationId + '!', 'success');
            }
        }
    });
}

function setupIntegration(integrationId) {
    if (window.AppDiscoverer && window.AppDiscoverer.showToast) {
        window.AppDiscoverer.showToast('Opening ' + integrationId + ' setup wizard...', 'info');
    }
}

function viewLogs(integrationId) {
    if (window.AppDiscoverer && window.AppDiscoverer.showToast) {
        window.AppDiscoverer.showToast('Opening ' + integrationId + ' logs...', 'info');
    }
}

function viewDocumentation(integrationId) {
    if (window.AppDiscoverer && window.AppDiscoverer.showToast) {
        window.AppDiscoverer.showToast('Opening ' + integrationId + ' documentation...', 'info');
    }
}

function viewSchema(integrationId) {
    if (window.AppDiscoverer && window.AppDiscoverer.showToast) {
        window.AppDiscoverer.showToast('Opening ' + integrationId + ' schema viewer...', 'info');
    }
}

function openFileUpload() {
    var modal = document.getElementById('uploadModal');
    if (modal) modal.style.display = 'flex';
}

function viewDataStaging() {
    if (window.AppDiscoverer && window.AppDiscoverer.showToast) {
        window.AppDiscoverer.showToast('Opening data staging directory...', 'info');
    }
}

// Real-time collection functions
function startRealTimeCollection() {
    if (IntegrationManager.realTimeCollection.active) {
        IntegrationManager.logToAllConsoles('⚠️ Real-time collection already active', 'warning');
        return;
    }

    var interval = parseInt(document.getElementById('collectionInterval').value) * 1000;

    IntegrationManager.realTimeCollection.active = true;
    IntegrationManager.realTimeCollection.interval = setInterval(collectFromAllSources, interval);

    IntegrationManager.updatePipelineStep(1, 'active');
    IntegrationManager.logToAllConsoles('🚀 Real-time collection started');

    collectFromAllSources();
}

function stopRealTimeCollection() {
    if (!IntegrationManager.realTimeCollection.active) return;

    IntegrationManager.realTimeCollection.active = false;
    if (IntegrationManager.realTimeCollection.interval) {
        clearInterval(IntegrationManager.realTimeCollection.interval);
        IntegrationManager.realTimeCollection.interval = null;
    }

    IntegrationManager.updatePipelineStep(1, 'inactive');
    IntegrationManager.logToAllConsoles('⏹️ Real-time collection stopped');
}

function collectFromAllSources() {
    IntegrationManager.logToAllConsoles('🔄 Collecting data from all sources...');

    var promises = [];

    if (IntegrationManager.connections.splunk.connected) {
        promises.push(executeSplunkQuery());
    }

    if (IntegrationManager.connections.dynatrace.connected) {
        promises.push(executeDynatraceQuery());
    }

    if (IntegrationManager.connections.extrahop.connected) {
        promises.push(executeExtraHopQuery());
    }

    if (promises.length === 0) {
        IntegrationManager.logToAllConsoles('⚠️ No active connections for data collection', 'warning');
        return;
    }

    Promise.all(promises).then(function() {
        IntegrationManager.logToAllConsoles('✅ Data collection cycle completed');

        if (document.getElementById('enableNormalization') && document.getElementById('enableNormalization').checked) {
            IntegrationManager.normalizeCollectedData();
        }
    }).catch(function(error) {
        IntegrationManager.logToAllConsoles('❌ Collection error: ' + error.message, 'error');
        IntegrationManager.realTimeCollection.errorCount++;
        IntegrationManager.updateSystemStatus();
    });
}

// Query execution functions
function executeSplunkQuery() {
    return new Promise(function(resolve, reject) {
        if (!IntegrationManager.connections.splunk.connected) {
            IntegrationManager.logToConsole('splunkLog', '❌ Not connected to Splunk', 'error');
            reject(new Error('Not connected'));
            return;
        }

        var query = document.getElementById('splunkQuery').value;
        if (!query.trim()) {
            IntegrationManager.logToConsole('splunkLog', '❌ Please enter a SPL query', 'error');
            reject(new Error('No query'));
            return;
        }

        IntegrationManager.logToConsole('splunkLog', '🔍 Executing query: ' + query.substring(0, 50) + '...');

        setTimeout(function() {
            var results = generateSampleSplunkData();
            document.getElementById('splunkLastUpdate').textContent = new Date().toLocaleTimeString();
            IntegrationManager.logToConsole('splunkLog', '✅ Query completed: ' + results.length + ' events retrieved');
            IntegrationManager.addToCollectedData('splunk', results);
            resolve(results);
        }, 1000);
    });
}

function executeDynatraceQuery() {
    return new Promise(function(resolve, reject) {
        if (!IntegrationManager.connections.dynatrace.connected) {
            IntegrationManager.logToConsole('dynatraceLog', '❌ Not connected to Dynatrace', 'error');
            reject(new Error('Not connected'));
            return;
        }

        var query = document.getElementById('dynatraceQuery').value;
        IntegrationManager.logToConsole('dynatraceLog', '🔍 Executing query: ' + query.substring(0, 50) + '...');

        setTimeout(function() {
            var results = generateSampleDynatraceData();
            document.getElementById('dynatraceLastUpdate').textContent = new Date().toLocaleTimeString();
            IntegrationManager.logToConsole('dynatraceLog', '✅ Query completed: ' + results.length + ' logs retrieved');
            IntegrationManager.addToCollectedData('dynatrace', results);
            resolve(results);
        }, 1200);
    });
}

function executeExtraHopQuery() {
    return new Promise(function(resolve, reject) {
        if (!IntegrationManager.connections.extrahop.connected) {
            IntegrationManager.logToConsole('extrahopLog', '❌ Not connected to ExtraHop', 'error');
            reject(new Error('Not connected'));
            return;
        }

        IntegrationManager.logToConsole('extrahopLog', '🔍 Executing ExtraHop query...');

        setTimeout(function() {
            var results = generateSampleExtraHopData();
            document.getElementById('extrahopLastUpdate').textContent = new Date().toLocaleTimeString();
            IntegrationManager.logToConsole('extrahopLog', '✅ Query completed: ' + results.length + ' records retrieved');
            IntegrationManager.addToCollectedData('extrahop', results);
            resolve(results);
        }, 800);
    });
}

// Sample data generators
function generateSampleSplunkData() {
    var data = [];
    for (var i = 0; i < 10; i++) {
        data.push({
            _time: new Date().toISOString(),
            src_ip: '192.168.1.' + (Math.floor(Math.random() * 254) + 1),
            dest_ip: '10.0.0.' + (Math.floor(Math.random() * 254) + 1),
            src_port: Math.floor(Math.random() * 65535),
            dest_port: [80, 443, 22, 3389][Math.floor(Math.random() * 4)],
            protocol: ['tcp', 'udp'][Math.floor(Math.random() * 2)],
            bytes: Math.floor(Math.random() * 10000)
        });
    }
    return data;
}

function generateSampleDynatraceData() {
    var data = [];
    for (var i = 0; i < 8; i++) {
        data.push({
            '@timestamp': new Date().toISOString(),
            '@network.client.ip': '172.16.0.' + (Math.floor(Math.random() * 254) + 1),
            '@network.destination.ip': '10.1.0.' + (Math.floor(Math.random() * 254) + 1),
            '@network.client.port': Math.floor(Math.random() * 65535),
            '@network.destination.port': [80, 443, 8080][Math.floor(Math.random() * 3)],
            '@http.status_code': [200, 404, 500][Math.floor(Math.random() * 3)]
        });
    }
    return data;
}

function generateSampleExtraHopData() {
    var data = [];
    for (var i = 0; i < 12; i++) {
        data.push({
            timestamp: Date.now(),
            src_ip: '10.2.0.' + (Math.floor(Math.random() * 254) + 1),
            dest_ip: '192.168.10.' + (Math.floor(Math.random() * 254) + 1),
            src_port: Math.floor(Math.random() * 65535),
            dest_port: [80, 443, 22][Math.floor(Math.random() * 3)],
            protocol: 'tcp',
            bytes: Math.floor(Math.random() * 50000),
            packets: Math.floor(Math.random() * 100)
        });
    }
    return data;
}

// Control functions
function configurePipeline() {
    if (window.AppDiscoverer && window.AppDiscoverer.showToast) {
        window.AppDiscoverer.showToast('Pipeline configuration saved', 'success');
    }
}

function exportToTopologyAnalyzer() {
    IntegrationManager.exportToTopologyAnalyzer();
}

function exportToPinecone() {
    if (IntegrationManager.processedData.length === 0) {
        IntegrationManager.logToAllConsoles('❌ No processed data to export', 'error');
        return;
    }

    var pineconeData = IntegrationManager.processedData.map(function(record) {
        return {
            id: record.id,
            values: record.vector || [],
            metadata: {
                source: record.source,
                timestamp: record.timestamp,
                has_source_ip: record.normalized_data.source_ip ? true : false,
                has_dest_ip: record.normalized_data.dest_ip ? true : false
            }
        };
    });

    IntegrationManager.downloadJSON(pineconeData, 'pinecone-export.json');
    IntegrationManager.logToAllConsoles('✅ Exported ' + pineconeData.length + ' records to Pinecone format');
}

function exportUnifiedData() {
    var exportData = {
        metadata: {
            export_timestamp: new Date().toISOString(),
            total_records: IntegrationManager.processedData.length,
            sources: Object.keys(IntegrationManager.connections).filter(function(k) { 
                return IntegrationManager.connections[k].connected; 
            }),
            processing_stats: {
                processed_count: IntegrationManager.realTimeCollection.processedCount,
                error_count: IntegrationManager.realTimeCollection.errorCount
            }
        },
        raw_data: IntegrationManager.collectedData,
        processed_data: IntegrationManager.processedData
    };

    IntegrationManager.downloadJSON(exportData, 'unified-export.json');
    IntegrationManager.logToAllConsoles('✅ Exported unified dataset: ' + IntegrationManager.processedData.length + ' processed records');
}

function generateReport() {
    var report = {
        report_timestamp: new Date().toISOString(),
        summary: {
            active_connections: Object.values(IntegrationManager.connections).filter(function(c) { return c.connected; }).length,
            total_records_collected: IntegrationManager.collectedData.length,
            total_records_processed: IntegrationManager.processedData.length,
            error_count: IntegrationManager.realTimeCollection.errorCount,
            collection_active: IntegrationManager.realTimeCollection.active
        },
        connection_status: {
            splunk: IntegrationManager.connections.splunk.connected,
            dynatrace: IntegrationManager.connections.dynatrace.connected,
            extrahop: IntegrationManager.connections.extrahop.connected
        }
    };

    IntegrationManager.downloadJSON(report, 'integration-report.json');
    IntegrationManager.logToAllConsoles('✅ Integration report generated');
}

// Feed control functions
function pauseDataFeed() {
    IntegrationManager.dataFeedPaused = !IntegrationManager.dataFeedPaused;
    
    var btn = document.getElementById('pauseFeedBtn');
    if (btn) {
        btn.innerHTML = IntegrationManager.dataFeedPaused ? '▶️ Resume' : '⏸️ Pause';
    }
    
    if (window.AppDiscoverer && window.AppDiscoverer.showToast) {
        window.AppDiscoverer.showToast(
            IntegrationManager.dataFeedPaused ? 'Data feed paused' : 'Data feed resumed', 
            'info'
        );
    }
}

function clearDataFeed() {
    var container = document.getElementById('dataFeedContainer');
    if (container) {
        container.innerHTML = '';
        if (window.AppDiscoverer && window.AppDiscoverer.showToast) {
            window.AppDiscoverer.showToast('Data feed cleared', 'info');
        }
    }
}

function exportDataFeed() {
    var container = document.getElementById('dataFeedContainer');
    if (!container) return;

    var feedItems = Array.from(container.children).map(function(item) {
        return {
            timestamp: item.querySelector('.feed-timestamp').textContent,
            source: item.querySelector('.feed-source').textContent,
            message: item.querySelector('.feed-message').textContent,
            type: item.querySelector('.feed-type').textContent
        };
    });

    IntegrationManager.downloadJSON(feedItems, 'integration_feed_' + new Date().toISOString().split('T')[0] + '.json');
    if (window.AppDiscoverer && window.AppDiscoverer.showToast) {
        window.AppDiscoverer.showToast('Data feed exported', 'success');
    }
}

// Modal functions
function closeConfigModal() {
    var modal = document.getElementById('configModal');
    if (modal) modal.style.display = 'none';
}

function closeUploadModal() {
    var modal = document.getElementById('uploadModal');
    if (modal) modal.style.display = 'none';
}

function saveIntegrationConfig() {
    if (window.AppDiscoverer && window.AppDiscoverer.showToast) {
        window.AppDiscoverer.showToast('Configuration saved successfully', 'success');
    }
    closeConfigModal();
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    IntegrationManager.initialize();
});

console.log('✅ Integration Hub JavaScript loaded');