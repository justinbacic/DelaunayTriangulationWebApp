document.addEventListener('DOMContentLoaded', function() {
    const canvas = document.getElementById('drawingCanvas');
    const ctx = canvas.getContext('2d');
    const clearBtn = document.getElementById('clearBtn');
    const coordinatesDiv = document.getElementById('coordinates');
    const runBtn = document.getElementById('runBtn');
    const pauseBtn = document.getElementById('pauseBtn');
    const speedSlider = document.getElementById('speed-slider');
    const speedValue = document.getElementById('speed-value');
    
    let points = [];
    let animationDelay = 1000; // Default delay (1 second)
    let currentAnimationStep = 0;
    let animationSequence = [];
    let isAnimating = false;
    let animationTimeout = null;
    // Add these variables at the top with your other declarations
    let isPaused = false;
    let pauseResumeCallback = null;


    ///////
    //Event Handlers
    //////
    pauseBtn.addEventListener('click', function() {
        if (isAnimating) {
            if (isPaused) {
                // Resume animation
                isPaused = false;
                this.textContent = 'Pause';
                if (pauseResumeCallback) {
                    pauseResumeCallback();
                }
            } else {
                // Pause animation
                isPaused = true;
                this.textContent = 'Resume';
                clearTimeout(animationTimeout);
            }
        }
    });
    clearBtn.addEventListener('click', function() {
        stopAnimation();
        ctx.setTransform(1, 0, 0, 1, 0, 0);
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        points = [];
        coordinatesDiv.innerHTML = '';
        runBtn.disabled = true; // Disable run button when clearing
        
        fetch('/clear_points', {
            method: 'POST',
        });
    });
    speedSlider.addEventListener('input', function() {
        animationDelay = 1010 - this.value; // Invert so higher slider = faster
        speedValue.textContent = animationDelay + 'ms';
        
        // If animation is running, update the delay immediately
        if (isAnimating) {
            // No need to stop/restart, the next step will use the new delay
        }
    });
    canvas.addEventListener('click', function(e) {
        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        drawPoint(x, y);
        points.push({x, y});
        
        // Enable/disable run button based on point count
        runBtn.disabled = points.length < 3;
        
        // Send to server
        fetch('/save_point', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({x, y}),
        });
    });
    runBtn.addEventListener('click', drawSequence);
    
    // Load existing points on page load
    // Modify your initial points load to check count
    fetch('/get_points')
        .then(response => response.json())
        .then(data => {
            points = data.points.map(p => ({x: p[0], y: p[1]}));
            points.forEach(p => drawPoint(p.x, p.y));
            // Set initial run button state
            runBtn.disabled = points.length < 3;
        });
    ////////
    //Async Functions
    ////////
    async function drawSequence() {
        if (isAnimating) return; // Prevent multiple clicks
        
        runBtn.disabled = true;
        isAnimating = true;
        currentAnimationStep = 0;
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        coordinatesDiv.innerHTML = '';
        
        const response = await fetch('/get_drawing_sequence');
        animationSequence = await response.json();
        
        const statusDiv = document.createElement('div');
        statusDiv.style.marginTop = '10px';
        statusDiv.style.fontWeight = 'bold';
        coordinatesDiv.appendChild(statusDiv);
        
        zoomToFit(animationSequence);
        animateStep(statusDiv);
    }
    ////////
    //Helper Functions
    ////////
    function drawPoint(x, y, fill='red') {
        ctx.beginPath();
        ctx.arc(x, y, 5, 0, Math.PI * 2);
        ctx.fillStyle = fill;
        ctx.fill();
        ctx.closePath();
        
        // Display coordinates
        coordinatesDiv.innerHTML += `Point: (${x}, ${y})<br>`;
    }
    function animateStep(statusDiv) {
        if (currentAnimationStep >= animationSequence.length) {
            statusDiv.textContent = 'Drawing complete!';
            runBtn.disabled = false;
            isAnimating = false;
            isPaused = false;
            document.getElementById('pauseBtn').textContent = 'Pause';
            return;
        }
        
        if (isPaused) {
            // Store the callback to resume from this point
            pauseResumeCallback = () => {
                pauseResumeCallback = null;
                animationTimeout = setTimeout(() => animateStep(statusDiv), animationDelay);
            };
            return;
        }
        
        const step = animationSequence[currentAnimationStep];
        ctx.clearRect(-10000, -10000, 20000, 20000);
        
        statusDiv.textContent = `Drawing step ${currentAnimationStep + 1} of ${animationSequence.length}...`;
        
        // Draw points
        step.points.forEach(([x, y], idx) => {
            drawPoint(x, y);
            coordinatesDiv.innerHTML += `Point ${idx}: (${x}, ${y})<br>`;
        });
        
        // Draw uninserted points
        step.uninserted_points.forEach(([x, y], idx) => {
            drawPoint(x, y, 'blue');
            coordinatesDiv.innerHTML += `Point ${idx}: (${x}, ${y})<br>`;
        });

        // Draw edges
        step.edges.forEach(([[x1, y1], [x2, y2]]) => {
            ctx.beginPath();
            ctx.moveTo(x1, y1);
            ctx.lineTo(x2, y2);
            ctx.strokeStyle = `blue`;
            ctx.lineWidth = 2;
            ctx.stroke();
        });
        
        // Draw circles
        step.circles.forEach(([x, y, radius]) => {
            drawCircle(x, y, radius, `hsl(${currentAnimationStep * 60 + 180}, 100%, 50%)`);
            coordinatesDiv.innerHTML += `Circle: center (${x}, ${y}), radius ${radius}<br>`;
        });
        
        currentAnimationStep++;
        animationTimeout = setTimeout(() => animateStep(statusDiv), animationDelay);
    }
    function stopAnimation() {
        if (animationTimeout) {
            clearTimeout(animationTimeout);
        }
        isAnimating = false;
        isPaused = false;
        runBtn.disabled = false;
        pauseBtn.textContent = 'Pause';
    }
    function drawCircle(x, y, radius) {
        ctx.beginPath();
        ctx.arc(x, y, radius, 0, Math.PI * 2);
        
        // Set dotted line style
        ctx.setLineDash([5, 3]); // 5px dash, 3px gap
        ctx.strokeStyle = 'black';
        ctx.lineWidth = 1;
        ctx.stroke();
        
        // Reset line dash for other drawings
        ctx.setLineDash([]);
        ctx.closePath();
    }
    function zoomToFit(sequence) {
        const bbox = calculateBoundingBox(sequence);
        const canvas = document.getElementById('drawingCanvas');
        
        // Calculate scale factors
        const scaleX = canvas.width / bbox.width;
        const scaleY = canvas.height / bbox.height;
        const scale = Math.min(scaleX, scaleY) * 0.95; // 5% margin
        
        // Calculate offset to center the content
        const offsetX = (canvas.width - bbox.width * scale) / 2 - bbox.minX * scale;
        const offsetY = (canvas.height - bbox.height * scale) / 2 - bbox.minY * scale;
        
        // Apply transformation
        ctx.setTransform(scale, 0, 0, scale, offsetX, offsetY);
    }
    function calculateBoundingBox(sequence) {
        let minX = Infinity, minY = Infinity;
        let maxX = -Infinity, maxY = -Infinity;

        sequence.forEach(step => {
            // Check points
            step.points?.forEach(([x, y]) => {
                minX = Math.min(minX, x);
                minY = Math.min(minY, y);
                maxX = Math.max(maxX, x);
                maxY = Math.max(maxY, y);
            });

            // Check edges
            step.edges?.forEach(([[x1, y1], [x2, y2]]) => {
                minX = Math.min(minX, x1, x2);
                minY = Math.min(minY, y1, y2);
                maxX = Math.max(maxX, x1, x2);
                maxY = Math.max(maxY, y1, y2);
            });

        });

        // Add some padding
        const padding = 20;
        return {
            minX: minX - padding,
            minY: minY - padding,
            maxX: maxX + padding,
            maxY: maxY + padding,
            width: (maxX - minX) + padding * 2,
            height: (maxY - minY) + padding * 2
        };
    }
});