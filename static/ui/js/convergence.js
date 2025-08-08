// Application Convergence Dashboard
class ConvergenceDashboard {
    constructor() {
        this.canvas = document.getElementById('convergenceCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.currentView = 'flow';
        this.selectedItem = null;
        this.animationFrame = null;
        this.time = 0;
        
        // Convergence data
        this.migrationData = {
            targetArchitectures: [
                { name: 'Cloud Native', progress: 78, target: 100 },
                { name: 'Microservices', progress: 65, target: 90 },
                { name: 'API-First', progress: 82, target: 95 },
                { name: 'Event-Driven', progress: 45, target: 80 },
                { name: 'Container-Based', progress: 71, target: 100 }
            ],
            timelinePhases: [
                { name: 'Assessment', date: 'Q1 2024', status: 'completed' },
                { name: 'Planning', date: 'Q2 2024', status: 'completed' },
                { name: 'Pilot Migration', date: 'Q3 2024', status: 'active' },
                { name: 'Full Migration', date: 'Q4 2024', status: 'planned' },
                { name: 'Optimization', date: 'Q1 2025', status: 'planned' }
            ],
            costBreakdown: [
                { category: 'Infrastructure', amount: '$2.4M' },
                { category: 'Development', amount: '$1.8M' },
                { category: 'Training', amount: '$450K' },
                { category: 'Tools & Licenses', amount: '$320K' },
                { category: 'Consulting', amount: '$680K' }
            ],
            migrationStages: [
                { name: 'Legacy', count: 64, status: 'legacy' },
                { name: 'Assessment', count: 45, status: 'assessment' },
                { name: 'Migration', count: 38, status: 'current' },
                { name: 'Modernized', count: 124, status: 'completed' },
                { name: 'Optimized', count: 91, status: 'completed' }
            ]
        };
        
        this.applications = this.generateApplicationData();
        this.migrationPaths = this.generateMigrationPaths();
        
        this.init();
    }
    
    generateApplicationData() {
        const states = ['Legacy', 'Assessment', 'In Progress', 'Modernized', 'Optimized'];
        const targetStates = ['Cloud Native', 'Microservices', 'Serverless', 'Container-based'];
        const apps = [];
        
        for (let i = 0; i < 200; i++) {
            const currentStateIndex = Math.floor(Math.random() * states.length);
            const app = {
                id: `app-${i}`,
                name: `Application-${String(i + 1).padStart(3, '0')}`,
                currentState: states[currentStateIndex],
                targetState: targetStates[Math.floor(Math.random() * targetStates.length)],
                progress: Math.min(100, (currentStateIndex / (states.length - 1)) * 100 + Math.random() * 20),
                complexity: Math.random(),
                dependencies: Math.floor(Math.random() * 8) + 1,
                timeline: `Q${Math.floor(Math.random() * 4) + 1} 202${Math.floor(Math.random() * 2) + 4}`,
                risk: ['Low', 'Medium', 'High'][Math.floor(Math.random() * 3)],
                x: Math.random() * 800,
                y: Math.random() * 600,
                targetX: Math.random() * 800,
                targetY: Math.random() * 600
            };
            apps.push(app);
        }
        
        return apps;
    }
    
    generateMigrationPaths() {
        const paths = [];
        const stages = ['Legacy', 'Assessment', 'Planning', 'Migration', 'Testing', 'Deployment', 'Optimization'];
        
        this.applications.forEach(app => {
            const path = {
                appId: app.id,
                stages: stages.map((stage, index) => ({
                    name: stage,
                    completed: index < (app.progress / 100) * stages.length,
                    current: index === Math.floor((app.progress / 100) * stages.length),
                    x: 100 + index * 120,
                    y: 200 + Math.random() * 200
                }))
            };
            paths.push(path);
        });
        
        return paths;
    }
    
    init() {
        this.setupCanvas();
        this.setupEventListeners();
        this.renderMetrics();
        this.updateStats();
        this.startAnimation();
        
        window.addEventListener('resize', () => this.setupCanvas());
    }
    
    setupCanvas() {
        const rect = this.canvas.getBoundingClientRect();
        this.canvas.width = rect.width * window.devicePixelRatio;
        this.canvas.height = rect.height * window.devicePixelRatio;
        this.ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
        this.canvas.style.width = rect.width + 'px';
        this.canvas.style.height = rect.height + 'px';
        this.canvasWidth = rect.width;
        this.canvasHeight = rect.height;
    }
    
    setupEventListeners() {
        this.canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        this.canvas.addEventListener('click', (e) => this.handleClick(e));
        this.canvas.addEventListener('mouseleave', () => this.hideDetails());
    }
    
    renderMetrics() {
        this.renderTargetProgress();
        this.renderTimelineTracking();
        this.renderCostBreakdown();
        this.renderMigrationStages();
    }
    
    renderTargetProgress() {
        const container = document.getElementById('targetProgress');
        container.innerHTML = '';
        
        this.migrationData.targetArchitectures.forEach(target => {
            const item = document.createElement('div');
            item.className = 'progress-item';
            
            const percentage = Math.round((target.progress / target.target) * 100);
            
            item.innerHTML = `
                <div class="progress-header">
                    <div class="progress-name">${target.name}</div>
                    <div class="progress-percentage">${percentage}%</div>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${percentage}%"></div>
                </div>
            `;
            
            container.appendChild(item);
        });
    }
    
    renderTimelineTracking() {
        const container = document.getElementById('timelineTracking');
        container.innerHTML = '';
        
        this.migrationData.timelinePhases.forEach(phase => {
            const item = document.createElement('div');
            item.className = `timeline-item ${phase.status}`;
            
            item.innerHTML = `
                <div class="timeline-phase">${phase.name}</div>
                <div class="timeline-date">${phase.date}</div>
            `;
            
            container.appendChild(item);
        });
    }
    
    renderCostBreakdown() {
        const container = document.getElementById('costBreakdown');
        container.innerHTML = '';
        
        this.migrationData.costBreakdown.forEach(cost => {
            const item = document.createElement('div');
            item.className = 'cost-item';
            
            item.innerHTML = `
                <div class="cost-category">${cost.category}</div>
                <div class="cost-amount">${cost.amount}</div>
            `;
            
            container.appendChild(item);
        });
    }
    
    renderMigrationStages() {
        const container = document.getElementById('migrationStages');
        container.innerHTML = '';
        
        this.migrationData.migrationStages.forEach(stage => {
            const item = document.createElement('div');
            item.className = `stage-item ${stage.status}`;
            
            item.innerHTML = `
                <div class="stage-name">${stage.name}</div>
                <div class="stage-count">${stage.count}</div>
            `;
            
            container.appendChild(item);
        });
    }
    
    updateStats() {
        const convergenceScore = Math.round(
            this.migrationData.targetArchitectures.reduce((acc, target) => 
                acc + (target.progress / target.target), 0
            ) / this.migrationData.targetArchitectures.length * 100
        );
        
        document.getElementById('convergenceScore').textContent = `${convergenceScore}%`;
        document.getElementById('modernizedApps').textContent = 
            this.migrationData.migrationStages.find(s => s.name === 'Modernized').count;
        document.getElementById('inProgress').textContent = 
            this.migrationData.migrationStages.find(s => s.name === 'Migration').count;
        document.getElementById('planned').textContent = 
            this.applications.filter(app => app.progress < 30).length;
    }
    
    startAnimation() {
        const animate = () => {
            this.time += 0.016; // ~60fps
            this.render();
            this.animationFrame = requestAnimationFrame(animate);
        };
        animate();
    }
    
    render() {
        this.ctx.clearRect(0, 0, this.canvasWidth, this.canvasHeight);
        
        switch (this.currentView) {
            case 'flow':
                this.renderMigrationFlow();
                break;
            case 'timeline':
                this.renderTimelineView();
                break;
            case 'heatmap':
                this.renderHeatmapView();
                break;
        }
    }
    
    renderMigrationFlow() {
        const margin = 50;
        const stageWidth = (this.canvasWidth - 2 * margin) / 5;
        const stageHeight = this.canvasHeight - 2 * margin;
        
        // Draw migration stages
        const stages = ['Legacy', 'Assessment', 'In Progress', 'Testing', 'Modernized'];
        const stageColors = ['#64748b', '#f59e0b', '#3b82f6', '#8b5cf6', '#10b981'];
        
        stages.forEach((stage, index) => {
            const x = margin + index * stageWidth;
            const y = margin;
            
            // Draw stage background
            this.ctx.fillStyle = 'rgba(51, 65, 85, 0.3)';
            this.ctx.fillRect(x + 10, y, stageWidth - 20, stageHeight);
            
            // Draw stage border
            this.ctx.strokeStyle = '#334155';
            this.ctx.lineWidth = 1;
            this.ctx.strokeRect(x + 10, y, stageWidth - 20, stageHeight);
            
            // Draw stage label
            this.ctx.fillStyle = '#e2e8f0';
            this.ctx.font = '14px system-ui';
            this.ctx.textAlign = 'center';
            this.ctx.fillText(stage, x + stageWidth / 2, y - 10);
            
            // Draw applications in this stage
            const appsInStage = this.applications.filter(app => {
                const progressStage = Math.floor(app.progress / 20);
                return progressStage === index;
            });
            
            appsInStage.forEach((app, appIndex) => {
                const appX = x + 20 + (appIndex % 8) * 15;
                const appY = y + 20 + Math.floor(appIndex / 8) * 15;
                
                // Animate apps
                const wave = Math.sin(this.time * 2 + appIndex * 0.1) * 2;
                
                this.ctx.beginPath();
                this.ctx.arc(appX, appY + wave, 5, 0, 2 * Math.PI);
                this.ctx.fillStyle = stageColors[index];
                this.ctx.fill();
                
                if (app === this.selectedItem) {
                    this.ctx.strokeStyle = '#ffffff';
                    this.ctx.lineWidth = 2;
                    this.ctx.stroke();
                }
            });
        });
        
        // Draw flow arrows
        this.drawFlowArrows(margin, stageWidth, stageHeight);
    }
    
    drawFlowArrows(margin, stageWidth, stageHeight) {
        this.ctx.strokeStyle = '#64748b';
        this.ctx.lineWidth = 2;
        this.ctx.setLineDash([5, 5]);
        
        for (let i = 0; i < 4; i++) {
            const startX = margin + (i + 1) * stageWidth - 10;
            const endX = margin + (i + 1) * stageWidth + 10;
            const y = margin + stageHeight / 2;
            
            // Animated arrow flow
            const offset = (this.time * 50) % 20;
            this.ctx.setLineDash([5, 5]);
            this.ctx.lineDashOffset = -offset;
            
            this.ctx.beginPath();
            this.ctx.moveTo(startX, y);
            this.ctx.lineTo(endX, y);
            this.ctx.stroke();
            
            // Arrow head
            this.ctx.setLineDash([]);
            this.ctx.beginPath();
            this.ctx.moveTo(endX - 5, y - 3);
            this.ctx.lineTo(endX, y);
            this.ctx.lineTo(endX - 5, y + 3);
            this.ctx.stroke();
        }
        
        this.ctx.setLineDash([]);
    }
    
    renderTimelineView() {
        const margin = 50;
        const timelineY = this.canvasHeight / 2;
        const timelineWidth = this.canvasWidth - 2 * margin;
        
        // Draw timeline axis
        this.ctx.strokeStyle = '#475569';
        this.ctx.lineWidth = 2;
        this.ctx.beginPath();
        this.ctx.moveTo(margin, timelineY);
        this.ctx.lineTo(margin + timelineWidth, timelineY);
        this.ctx.stroke();
        
        // Draw timeline milestones
        const milestones = this.migrationData.timelinePhases;
        milestones.forEach((milestone, index) => {
            const x = margin + (index / (milestones.length - 1)) * timelineWidth;
            
            // Milestone marker
            this.ctx.beginPath();
            this.ctx.arc(x, timelineY, 8, 0, 2 * Math.PI);
            this.ctx.fillStyle = milestone.status === 'completed' ? '#10b981' : 
                               milestone.status === 'active' ? '#f59e0b' : '#64748b';
            this.ctx.fill();
            this.ctx.strokeStyle = '#ffffff';
            this.ctx.lineWidth = 2;
            this.ctx.stroke();
            
            // Milestone label
            this.ctx.fillStyle = '#e2e8f0';
            this.ctx.font = '12px system-ui';
            this.ctx.textAlign = 'center';
            this.ctx.fillText(milestone.name, x, timelineY - 25);
            this.ctx.fillText(milestone.date, x, timelineY + 25);
        });
        
        // Draw applications on timeline
        this.applications.forEach((app, index) => {
            const progressX = margin + (app.progress / 100) * timelineWidth;
            const y = timelineY + 50 + (index % 20) * 15 - 150;
            
            this.ctx.beginPath();
            this.ctx.arc(progressX, y, 3, 0, 2 * Math.PI);
            this.ctx.fillStyle = this.getProgressColor(app.progress);
            this.ctx.fill();
            
            if (app === this.selectedItem) {
                this.ctx.strokeStyle = '#ffffff';
                this.ctx.lineWidth = 2;
                this.ctx.stroke();
            }
        });
    }
    
    renderHeatmapView() {
        const margin = 50;
        const cellSize = 20;
        const cols = Math.floor((this.canvasWidth - 2 * margin) / cellSize);
        const rows = Math.floor((this.canvasHeight - 2 * margin) / cellSize);
        
        // Create heatmap grid
        const grid = Array(rows).fill().map(() => Array(cols).fill(0));
        
        // Map applications to grid
        this.applications.forEach(app => {
            const col = Math.floor((app.x / 800) * cols);
            const row = Math.floor((app.y / 600) * rows);
            if (row >= 0 && row < rows && col >= 0 && col < cols) {
                grid[row][col] += app.progress / 100;
            }
        });
        
        // Draw heatmap
        for (let row = 0; row < rows; row++) {
            for (let col = 0; col < cols; col++) {
                const x = margin + col * cellSize;
                const y = margin + row * cellSize;
                const intensity = Math.min(1, grid[row][col]);
                
                this.ctx.fillStyle = `rgba(59, 130, 246, ${intensity * 0.8})`;
                this.ctx.fillRect(x, y, cellSize - 1, cellSize - 1);
            }
        }
        
        // Draw legend
        this.drawHeatmapLegend(margin);
    }
    
    drawHeatmapLegend(margin) {
        const legendX = this.canvasWidth - margin - 150;
        const legendY = margin;
        
        this.ctx.fillStyle = 'rgba(15, 23, 42, 0.9)';
        this.ctx.fillRect(legendX, legendY, 140, 100);
        this.ctx.strokeStyle = '#334155';
        this.ctx.strokeRect(legendX, legendY, 140, 100);
        
        this.ctx.fillStyle = '#e2e8f0';
        this.ctx.font = '12px system-ui';
        this.ctx.textAlign = 'left';
        this.ctx.fillText('Convergence Intensity', legendX + 10, legendY + 20);
        
        for (let i = 0; i < 5; i++) {
            const intensity = i / 4;
            const y = legendY + 35 + i * 12;
            
            this.ctx.fillStyle = `rgba(59, 130, 246, ${intensity * 0.8})`;
            this.ctx.fillRect(legendX + 10, y, 20, 10);
            
            this.ctx.fillStyle = '#e2e8f0';
            this.ctx.font = '10px system-ui';
            this.ctx.fillText(`${Math.round(intensity * 100)}%`, legendX + 35, y + 7);
        }
    }
    
    getProgressColor(progress) {
        if (progress < 20) return '#64748b';
        if (progress < 40) return '#f59e0b';
        if (progress < 60) return '#3b82f6';
        if (progress < 80) return '#8b5cf6';
        return '#10b981';
    }
    
    handleMouseMove(e) {
        const rect = this.canvas.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;
        
        let hoveredItem = null;
        
        if (this.currentView === 'flow') {
            hoveredItem = this.findItemInFlow(mouseX, mouseY);
        } else if (this.currentView === 'timeline') {
            hoveredItem = this.findItemInTimeline(mouseX, mouseY);
        }
        
        if (hoveredItem !== this.selectedItem) {
            this.selectedItem = hoveredItem;
            
            if (hoveredItem) {
                this.showDetails(hoveredItem);
            } else {
                this.hideDetails();
            }
        }
        
        this.canvas.style.cursor = hoveredItem ? 'pointer' : 'default';
    }
    
    findItemInFlow(mouseX, mouseY) {
        const margin = 50;
        const stageWidth = (this.canvasWidth - 2 * margin) / 5;
        
        for (let stageIndex = 0; stageIndex < 5; stageIndex++) {
            const appsInStage = this.applications.filter(app => {
                const progressStage = Math.floor(app.progress / 20);
                return progressStage === stageIndex;
            });
            
            appsInStage.forEach((app, appIndex) => {
                const appX = margin + stageIndex * stageWidth + 20 + (appIndex % 8) * 15;
                const appY = margin + 20 + Math.floor(appIndex / 8) * 15;
                
                const distance = Math.sqrt((mouseX - appX) ** 2 + (mouseY - appY) ** 2);
                if (distance <= 8) {
                    return app;
                }
            });
        }
        
        return null;
    }
    
    findItemInTimeline(mouseX, mouseY) {
        const margin = 50;
        const timelineWidth = this.canvasWidth - 2 * margin;
        const timelineY = this.canvasHeight / 2;
        
        return this.applications.find((app, index) => {
            const progressX = margin + (app.progress / 100) * timelineWidth;
            const y = timelineY + 50 + (index % 20) * 15 - 150;
            
            const distance = Math.sqrt((mouseX - progressX) ** 2 + (mouseY - y) ** 2);
            return distance <= 5;
        });
    }
    
    handleClick(e) {
        if (this.selectedItem) {
            console.log('Clicked on:', this.selectedItem.name);
            // Could implement detailed view or editing functionality
        }
    }
    
    showDetails(item) {
        const details = document.getElementById('convergenceDetails');
        
        document.getElementById('detailTitle').textContent = item.name;
        document.getElementById('detailCurrentState').textContent = item.currentState;
        document.getElementById('detailTargetState').textContent = item.targetState;
        document.getElementById('detailProgress').textContent = `${Math.round(item.progress)}%`;
        document.getElementById('detailTimeline').textContent = item.timeline;
        
        // Generate milestones
        const milestones = ['Planning', 'Development', 'Testing', 'Deployment'];
        document.getElementById('detailMilestones').innerHTML = milestones.map(milestone => 
            `<span class="milestone-tag">${milestone}</span>`
        ).join('');
        
        // Generate dependencies
        const dependencies = Array.from({length: item.dependencies}, (_, i) => `Dep-${i + 1}`);
        document.getElementById('detailDependencies').innerHTML = dependencies.map(dep => 
            `<span class="dependency-tag">${dep}</span>`
        ).join('');
        
        details.classList.add('visible');
    }
    
    hideDetails() {
        document.getElementById('convergenceDetails').classList.remove('visible');
    }
    
    cleanup() {
        if (this.animationFrame) {
            cancelAnimationFrame(this.animationFrame);
        }
    }
}

// View control functions
function setConvergenceView(viewType) {
    if (dashboard) {
        dashboard.currentView = viewType;
        
        // Update button states
        document.querySelectorAll('.view-controls .btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.getElementById(viewType + 'Btn').classList.add('active');
    }
}

// Initialize dashboard when DOM is loaded
let dashboard;
document.addEventListener('DOMContentLoaded', () => {
    dashboard = new ConvergenceDashboard();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (dashboard) {
        dashboard.cleanup();
    }
});

// Export for potential external use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ConvergenceDashboard };
}