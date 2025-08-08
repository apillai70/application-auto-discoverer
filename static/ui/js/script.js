// Load archetype data from the YAML
var archetypes = [
    {
        name: "Monolithic",
        description: "Single-tier application where UI, business logic, and data access are tightly integrated.",
        color: "#ef4444",
        indicators: ["direct DB access", "high port concentration", "no service boundary", "single process"],
        traffic_pattern: "inbound only",
        typical_ports: [3306, 8080],
        expected_tiers: ["App+DB combined"],
        apps: ["Legacy ERP System", "Old CRM Platform"]
    },
    {
        name: "3-Tier",
        description: "Standard enterprise structure with separate UI, API, and database components.",
        color: "#3b82f6",
        indicators: ["distinct UI/API/DB tiers", "north-south traffic", "port layering", "stateful backend"],
        traffic_pattern: "north-south",
        typical_ports: [80, 443, 3306, 5432],
        expected_tiers: ["Web UI", "API", "Database"],
        apps: ["Corporate Website", "HR Management System", "Finance Portal"]
    },
    {
        name: "Microservices",
        description: "Application composed of independent services communicating via REST/gRPC.",
        color: "#10b981",
        indicators: ["API gateway", "K8s/docker", "internal east-west traffic", "many services"],
        traffic_pattern: "east-west",
        typical_ports: [3000, 3001, 3002, 3003, 3004],
        expected_tiers: ["API Gateway", "Service mesh", "Shared DBs"],
        apps: ["E-commerce Platform", "Payment Processing", "User Management", "Order Service", "Inventory System"]
    },
    {
        name: "Event-Driven",
        description: "Decoupled services communicating through message queues or pub/sub systems.",
        color: "#f59e0b",
        indicators: ["Kafka/RabbitMQ", "asynchronous traffic", "low direct coupling", "non-HTTP ports"],
        traffic_pattern: "pub-sub / async",
        typical_ports: [5672, 9092],
        expected_tiers: ["Producer", "Broker", "Consumer"],
        apps: ["Real-time Analytics", "IoT Data Processing", "Event Streaming"]
    },
    {
        name: "SOA",
        description: "Enterprise services exposed via ESB, typically with SOAP/XML or legacy protocols.",
        color: "#8b5cf6",
        indicators: ["ESB", "SOAP", "WSDL", "XML over HTTP", "service registry"],
        traffic_pattern: "service bus mediated",
        typical_ports: [8080],
        expected_tiers: ["Service interface", "ESB", "Backend services"],
        apps: ["Enterprise Service Bus", "Legacy Integration Hub"]
    },
    {
        name: "Serverless",
        description: "Stateless compute units triggered by events, typically on cloud providers.",
        color: "#06b6d4",
        indicators: ["API Gateway", "AWS Lambda", "Azure Functions", "ephemeral endpoints"],
        traffic_pattern: "on-demand stateless",
        typical_ports: [443],
        expected_tiers: ["API Gateway", "Function", "Storage"],
        apps: ["Image Processing", "Data Transformation", "Notification Service"]
    },
    {
        name: "Client-Server",
        description: "Traditional fat client connecting directly to backend services or databases.",
        color: "#64748b",
        indicators: ["MS SQL", "RDP/Citrix", "desktop installs", "thick client"],
        traffic_pattern: "persistent session",
        typical_ports: [1433, 3389],
        expected_tiers: ["Client UI", "DB Server"],
        apps: ["Desktop CRM", "Financial Trading Platform"]
    },
    {
        name: "Edge Cloud Hybrid",
        description: "Applications split between local edge devices and cloud-based control/analytics.",
        color: "#84cc16",
        indicators: ["IoT", "cloud-REST targets", "gateway patterns", "remote sensor endpoints"],
        traffic_pattern: "device to cloud",
        typical_ports: [443, 1883, 8883],
        expected_tiers: ["Device", "Gateway", "Cloud"],
        apps: ["IoT Sensor Network", "Smart Building System"]
    },
    {
        name: "ETL Data Pipeline",
        description: "Batch or stream-based data processing flows for BI or analytics systems.",
        color: "#f97316",
        indicators: ["Airflow", "Spark", "batch ports", "cron traffic", "data lake/DWH targets"],
        traffic_pattern: "batch or streaming",
        typical_ports: [21, 8020],
        expected_tiers: ["Ingestion", "Processing", "Storage"],
        apps: ["Data Warehouse ETL", "Analytics Pipeline", "Reporting System"]
    },
    {
        name: "Web API Headless",
        description: "Decoupled frontend (SPA) and backend (REST API) layers deployed independently.",
        color: "#ec4899",
        indicators: ["CORS", "OAuth flows", "REST API", "React/Vue", "frontend-backend split"],
        traffic_pattern: "frontend-backend async",
        typical_ports: [80, 443],
        expected_tiers: ["Frontend SPA", "Backend API", "Auth"],
        apps: ["Modern Web App", "Mobile Backend"]
    },
    {
        name: "Cloud-Native",
        description: "Applications built specifically for cloud environments, leveraging elasticity, resilience, and scalability.",
        color: "#22d3ee",
        indicators: ["Kubernetes/EKS/GKE", "CI/CD pipelines", "automated scaling", "container registries", "managed cloud services", "service meshes"],
        traffic_pattern: "dynamic scaling",
        typical_ports: [80, 443, 8080],
        expected_tiers: ["Container Orchestration", "Microservices", "Managed Services"],
        apps: ["Cloud-native Platform", "Kubernetes Workloads"]
    },
    {
        name: "AI ML Application",
        description: "Systems that apply machine learning models for prediction, classification, or decision-making.",
        color: "#a855f7",
        indicators: ["GPU usage", "TensorFlow/PyTorch", "data drift monitoring", "feature stores", "inference endpoints", "model training pipelines"],
        traffic_pattern: "inference requests",
        typical_ports: [8080, 5000],
        expected_tiers: ["Model Serving", "Feature Store", "Training Pipeline"],
        apps: ["Recommendation Engine", "Fraud Detection", "Image Recognition"]
    }
];

// Generate sample applications based on archetypes
var applications = [];
var applicationId = 1;

archetypes.forEach(function(archetype, archetypeIndex) {
    var appCount = archetype.apps.length;
    archetype.apps.forEach(function(appName, appIndex) {
        applications.push({
            id: 'app-' + applicationId++,
            name: appName,
            archetype: archetype.name,
            status: Math.random() > 0.8 ? 'Warning' : 'Healthy',
            color: archetype.color,
            indicators: archetype.indicators,
            traffic_pattern: archetype.traffic_pattern,
            typical_ports: archetype.typical_ports.slice(0, 5),
            x: 200 + (archetypeIndex % 5) * 150 + (appIndex * 30),
            y: 150 + Math.floor(archetypeIndex / 5) * 120 + (appIndex * 25),
            cluster: archetypeIndex
        });
    });
});

// Add more applications to reach 262 total
while (applications.length < 262) {
    var randomArchetype = archetypes[Math.floor(Math.random() * archetypes.length)];
    applications.push({
        id: 'app-' + applicationId++,
        name: randomArchetype.name + ' App ' + (applicationId - applications.length),
        archetype: randomArchetype.name,
        status: Math.random() > 0.8 ? 'Warning' : 'Healthy',
        color: randomArchetype.color,
        indicators: randomArchetype.indicators,
        traffic_pattern: randomArchetype.traffic_pattern,
        typical_ports: randomArchetype.typical_ports.slice(0, 5),
        x: Math.random() * 800 + 100,
        y: Math.random() * 500 + 100,
        cluster: archetypes.indexOf(randomArchetype)
    });
}

// Application state
var canvas, ctx;
var filteredApps = applications.slice();
var selectedApp = null;
var selectedArchetypes = new Set();
var currentView = 'cluster';
var searchTerm = '';

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    canvas = document.getElementById('appCanvas');
    ctx = canvas.getContext('2d');
    
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);
    
    populateArchetypeList();
    populateLegend();
    updateStats();
    
    // Event listeners
    document.getElementById('archetypeSearch').addEventListener('input', handleSearch);
    canvas.addEventListener('click', handleCanvasClick);
    canvas.addEventListener('mousemove', handleMouseMove);
    
    renderGraph();
});

function resizeCanvas() {
    var container = canvas.parentElement;
    canvas.width = container.clientWidth - 40;
    canvas.height = 640;
    if (ctx) renderGraph();
}

function populateArchetypeList() {
    var container = document.getElementById('archetypeList');
    var html = '';
    archetypes.forEach(function(archetype) {
        var appCount = applications.filter(function(app) { return app.archetype === archetype.name; }).length;
        var safeName = archetype.name.replace(/\s+/g, '-').replace(/[^\w-]/g, '');
        html += '<div class="archetype-item" onclick="toggleArchetype(\'' + archetype.name + '\')" id="archetype-' + safeName + '">';
        html += '<div class="archetype-name" style="color: ' + archetype.color + ';">' + archetype.name + '</div>';
        html += '<div class="archetype-description">' + archetype.description + '</div>';
        html += '<div class="archetype-apps">' + appCount + ' applications</div>';
        html += '</div>';
    });
    container.innerHTML = html;
}

function populateLegend() {
    var container = document.getElementById('archetypeLegend');
    var html = '';
    archetypes.slice(0, 10).forEach(function(archetype) {
        html += '<div class="legend-item">';
        html += '<div class="legend-color" style="background: ' + archetype.color + ';"></div>';
        html += '<span>' + archetype.name + '</span>';
        html += '</div>';
    });
    container.innerHTML = html;
}

function handleSearch(e) {
    searchTerm = e.target.value.toLowerCase();
    updateFilters();
}

function toggleArchetype(archetypeName) {
    var safeName = archetypeName.replace(/\s+/g, '-').replace(/[^\w-]/g, '');
    var element = document.getElementById('archetype-' + safeName);
    
    if (selectedArchetypes.has(archetypeName)) {
        selectedArchetypes.delete(archetypeName);
        element.classList.remove('active');
    } else {
        selectedArchetypes.add(archetypeName);
        element.classList.add('active');
    }
    
    updateFilters();
}

function resetFilters() {
    document.getElementById('archetypeSearch').value = '';
    searchTerm = '';
    selectedArchetypes.clear();
    
    document.querySelectorAll('.archetype-item').forEach(function(item) {
        item.classList.remove('active');
    });
    
    updateFilters();
}

function updateFilters() {
    filteredApps = applications.filter(function(app) {
        // Search filter
        if (searchTerm && app.name.toLowerCase().indexOf(searchTerm) === -1 && 
            app.archetype.toLowerCase().indexOf(searchTerm) === -1) {
            return false;
        }
        
        // Archetype filter
        if (selectedArchetypes.size > 0 && !selectedArchetypes.has(app.archetype)) {
            return false;
        }
        
        return true;
    });
    
    updateStats();
    renderGraph();
}

function updateStats() {
    document.getElementById('totalApps').textContent = applications.length;
    document.getElementById('classifiedApps').textContent = applications.filter(function(app) { return app.archetype !== 'Unknown'; }).length;
    document.getElementById('archetypeCount').textContent = archetypes.length;
    document.getElementById('visibleApps').textContent = filteredApps.length;
}

function setView(viewType) {
    currentView = viewType;
    
    // Update button states
    document.querySelectorAll('.view-controls .btn').forEach(function(btn) { btn.classList.remove('active'); });
    document.getElementById(viewType + 'Btn').classList.add('active');
    
    // Arrange applications based on view
    switch(viewType) {
        case 'cluster':
            arrangeClusterView();
            break;
        case 'network':
            arrangeNetworkView();
            break;
        case 'hierarchy':
            arrangeHierarchyView();
            break;
    }
    
    renderGraph();
}

function arrangeClusterView() {
    var clustersPerRow = 4;
    var clusterWidth = canvas.width / clustersPerRow;
    var clusterHeight = canvas.height / Math.ceil(archetypes.length / clustersPerRow);
    
    archetypes.forEach(function(archetype, index) {
        var clusterX = (index % clustersPerRow) * clusterWidth + clusterWidth / 2;
        var clusterY = Math.floor(index / clustersPerRow) * clusterHeight + clusterHeight / 2;
        
        var appsInCluster = filteredApps.filter(function(app) { return app.archetype === archetype.name; });
        var radius = Math.min(clusterWidth, clusterHeight) * 0.3;
        
        appsInCluster.forEach(function(app, appIndex) {
            var angle = (appIndex / appsInCluster.length) * 2 * Math.PI;
            var appRadius = radius * Math.sqrt(appIndex / appsInCluster.length);
            app.x = clusterX + Math.cos(angle) * appRadius;
            app.y = clusterY + Math.sin(angle) * appRadius;
        });
    });
}

function arrangeNetworkView() {
    filteredApps.forEach(function(app) {
        app.x = Math.random() * (canvas.width - 100) + 50;
        app.y = Math.random() * (canvas.height - 100) + 50;
    });
}

function arrangeHierarchyView() {
    var levels = ['Edge Cloud Hybrid', 'Web API Headless', 'Microservices', '3-Tier', 'Monolithic'];
    var levelHeight = canvas.height / levels.length;
    
    levels.forEach(function(level, levelIndex) {
        var appsInLevel = filteredApps.filter(function(app) { return app.archetype === level; });
        var appWidth = canvas.width / (appsInLevel.length + 1);
        
        appsInLevel.forEach(function(app, appIndex) {
            app.x = (appIndex + 1) * appWidth;
            app.y = (levelIndex + 0.5) * levelHeight;
        });
    });
}

function renderGraph() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw cluster backgrounds in cluster view
    if (currentView === 'cluster') {
        drawClusterBackgrounds();
    }
    
    // Draw applications
    filteredApps.forEach(function(app) {
        drawApplication(app);
    });
    
    // Draw archetype labels in cluster view
    if (currentView === 'cluster') {
        drawArchetypeLabels();
    }
}

function drawClusterBackgrounds() {
    var clustersPerRow = 4;
    var clusterWidth = canvas.width / clustersPerRow;
    var clusterHeight = canvas.height / Math.ceil(archetypes.length / clustersPerRow);
    
    archetypes.forEach(function(archetype, index) {
        var clusterX = (index % clustersPerRow) * clusterWidth;
        var clusterY = Math.floor(index / clustersPerRow) * clusterHeight;
        
        ctx.fillStyle = archetype.color + '15';
        ctx.strokeStyle = archetype.color + '40';
        ctx.lineWidth = 1;
        ctx.fillRect(clusterX + 10, clusterY + 10, clusterWidth - 20, clusterHeight - 20);
        ctx.strokeRect(clusterX + 10, clusterY + 10, clusterWidth - 20, clusterHeight - 20);
    });
}

function drawArchetypeLabels() {
    var clustersPerRow = 4;
    var clusterWidth = canvas.width / clustersPerRow;
    var clusterHeight = canvas.height / Math.ceil(archetypes.length / clustersPerRow);
    
    archetypes.forEach(function(archetype, index) {
        var clusterX = (index % clustersPerRow) * clusterWidth + clusterWidth / 2;
        var clusterY = Math.floor(index / clustersPerRow) * clusterHeight + 30;
        
        ctx.fillStyle = archetype.color;
        ctx.font = 'bold 12px Inter';
        ctx.textAlign = 'center';
        ctx.fillText(archetype.name, clusterX, clusterY);
    });
}

function drawApplication(app) {
    // Calculate node size based on archetype complexity
    var complexityScore = app.indicators.length + (app.typical_ports.length / 10);
    var nodeSize = Math.max(6, Math.min(16, 6 + complexityScore));
    
    // Draw node
    ctx.beginPath();
    ctx.arc(app.x, app.y, nodeSize, 0, 2 * Math.PI);
    ctx.fillStyle = app.color;
    ctx.fill();
    
    // Add border for selected app
    if (selectedApp && selectedApp.id === app.id) {
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 3;
        ctx.stroke();
    }
    
    // Add status indicator
    if (app.status === 'Warning') {
        ctx.beginPath();
        ctx.arc(app.x + nodeSize - 3, app.y - nodeSize + 3, 3, 0, 2 * Math.PI);
        ctx.fillStyle = '#f59e0b';
        ctx.fill();
    }
    
    // Draw app name (only for selected or in network view)
    if (selectedApp === app || currentView === 'network') {
        ctx.fillStyle = '#e2e8f0';
        ctx.font = '10px Inter';
        ctx.textAlign = 'center';
        ctx.fillText(app.name, app.x, app.y + nodeSize + 15);
    }
}

function handleCanvasClick(e) {
    var rect = canvas.getBoundingClientRect();
    var x = e.clientX - rect.left;
    var y = e.clientY - rect.top;
    
    var clickedApp = null;
    for (var i = 0; i < filteredApps.length; i++) {
        var app = filteredApps[i];
        var distance = Math.sqrt((x - app.x) * (x - app.x) + (y - app.y) * (y - app.y));
        var nodeSize = Math.max(6, Math.min(16, 6 + app.indicators.length + (app.typical_ports.length / 10)));
        
        if (distance <= nodeSize + 3) {
            clickedApp = app;
            break;
        }
    }
    
    if (clickedApp) {
        selectedApp = clickedApp;
        showAppDetails(clickedApp);
    } else {
        selectedApp = null;
        hideAppDetails();
    }
    
    renderGraph();
}

function handleMouseMove(e) {
    var rect = canvas.getBoundingClientRect();
    var x = e.clientX - rect.left;
    var y = e.clientY - rect.top;
    
    var hoveredApp = null;
    for (var i = 0; i < filteredApps.length; i++) {
        var app = filteredApps[i];
        var distance = Math.sqrt((x - app.x) * (x - app.x) + (y - app.y) * (y - app.y));
        var nodeSize = Math.max(6, Math.min(16, 6 + app.indicators.length + (app.typical_ports.length / 10)));
        
        if (distance <= nodeSize + 3) {
            hoveredApp = app;
            break;
        }
    }
    
    canvas.style.cursor = hoveredApp ? 'pointer' : 'grab';
}

function showAppDetails(app) {
    var detailsPanel = document.getElementById('appDetails');
    
    document.getElementById('detailAppName').textContent = app.name;
    document.getElementById('detailArchetype').textContent = app.archetype;
    document.getElementById('detailTraffic').textContent = app.traffic_pattern;
    document.getElementById('detailStatus').textContent = app.status;
    
    // Show indicators
    var indicatorsContainer = document.getElementById('detailIndicators');
    var indicatorsHtml = '';
    app.indicators.forEach(function(indicator) {
        indicatorsHtml += '<div class="indicator-item">' + indicator + '</div>';
    });
    indicatorsContainer.innerHTML = indicatorsHtml;
    
    // Show ports
    var portsContainer = document.getElementById('detailPorts');
    var portsHtml = '';
    app.typical_ports.forEach(function(port) {
        portsHtml += '<span class="port-item">' + port + '</span>';
    });
    portsContainer.innerHTML = portsHtml;
    
    detailsPanel.style.display = 'block';
}

function hideAppDetails() {
    document.getElementById('appDetails').style.display = 'none';
}

// Initialize with cluster view
arrangeClusterView();