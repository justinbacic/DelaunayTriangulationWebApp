class TriangulationVisualizer {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.points = [];
        this.edges = [];
        this.vertices = [];
        
        this.setupEventListeners();
        this.draw();
    }
    
    setupEventListeners() {
        this.canvas.addEventListener('click', (e) => this.handleCanvasClick(e));
        document.getElementById('addPointBtn').addEventListener('click', () => this.addRandomPoint());
        document.getElementById('runTriangulationBtn').addEventListener('click', () => this.runTriangulation());
    }
    
    handleCanvasClick(e) {
        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        this.points.push({x, y});
        this.draw();
    }
    
    addRandomPoint() {
        const x = Math.random() * this.canvas.width;
        const y = Math.random() * this.canvas.height;
        this.points.push({x, y});
        this.draw();
    }
    
    async runTriangulation() {
        if (this.points.length < 3) {
            alert("Need at least 3 points for triangulation");
            return;
        }
        
        try {
            // Send points to server
            const response = await fetch('/init_triangulation', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    points: this.points.map(p => [p.x, p.y])
                })
            });
            
            if (!response.ok) throw new Error('Network response was not ok');
            
            // Start polling for updates
            this.pollTriangulation();
        } catch (error) {
            console.error('Error:', error);
        }
    }
    
    async pollTriangulation() {
        try {
            const response = await fetch('/get_triangulation_state');
            const data = await response.json();
            
            if (data.error) {
                console.error(data.error);
                return;
            }
            
            this.vertices = data.vertices;
            this.edges = data.edges;
            this.draw();
            
            // Continue polling if triangulation is in progress
            // setTimeout(() => this.pollTriangulation(), 100);
        } catch (error) {
            console.error('Error polling triangulation:', error);
        }
    }
    
    draw() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw edges
        this.ctx.strokeStyle = '#000';
        this.ctx.lineWidth = 1;
        this.edges.forEach(edge => {
            this.ctx.beginPath();
            this.ctx.moveTo(edge.x1, edge.y1);
            this.ctx.lineTo(edge.x2, edge.y2);
            this.ctx.stroke();
        });
        
        // Draw vertices
        this.ctx.fillStyle = 'blue';
        this.vertices.forEach(vertex => {
            this.ctx.beginPath();
            this.ctx.arc(vertex[0], vertex[1], 3, 0, Math.PI * 2);
            this.ctx.fill();
        });
        
        // Draw input points
        this.ctx.fillStyle = 'red';
        this.points.forEach(point => {
            this.ctx.beginPath();
            this.ctx.arc(point.x, point.y, 3, 0, Math.PI * 2);
            this.ctx.fill();
        });
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new TriangulationVisualizer('triangulationCanvas');
});