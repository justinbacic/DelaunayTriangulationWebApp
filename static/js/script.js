document.addEventListener('DOMContentLoaded', function() {
    const canvas = document.getElementById('drawingCanvas');
    const ctx = canvas.getContext('2d');
    const clearBtn = document.getElementById('clearBtn');
    const runBtn = document.getElementById('runBtn');
    const pauseBtn = document.getElementById('pauseBtn');
    const speedSlider = document.getElementById('speed-slider');
    const speedValue = document.getElementById('speed-value');
    const featureToggle = document.getElementById('featureToggle');
    const onLabel = document.getElementById('on-or-off');
    const submitBtn = document.getElementById('submitBtn');
    const toggleLabel = document.getElementById('toggle-label');

    
    let points = [];
    let animationDelay = 1000; // Default delay (1 second)
    let currentAnimationStep = 0;
    let animationSequence = [];
    let animationTimeout = null;
    let manual = false;
    let paused = false;

    ///////
    //Event Handlers
    //////
    submitBtn.addEventListener('click', function(){
        animationSequence = [];
        currentAnimationStep = 0;
        getSequence();
        runBtn.disabled = false;
        paused = false;
        pauseBtn.textContent = "Pause";
    });
    featureToggle.addEventListener('change', function() {
        toggleState = this.checked;
        if (toggleState) {
            toggleLabel.textContent = "Manual";
            runBtn.textContent = "Next";
            manual = true;
            pauseBtn.disabled = true;
            paused = true;
            if(submitBtn.disabled != true){
                pauseBtn.textContent = "Resume";
            }
            
            if(animationSequence.length>0&&currentAnimationStep<animationSequence.length-1){
                runBtn.disabled = false;
            }
            
        } else {
            toggleLabel.textContent = "Automatic";
            runBtn.textContent = "Run";
            manual = false;
            
            if(pauseBtn.textContent == "Resume"){
                paused = true;
            }
            if(currentAnimationStep > 0){
                runBtn.disabled = true;
                if(currentAnimationStep<animationSequence.length-1){
                    pauseBtn.disabled = false;
                }
                
            }
        }
    });
    pauseBtn.addEventListener('click', function() {
        if(!paused){
            paused = true;
            this.textContent = 'Resume';
        }else{
            paused = false;
            this.textContent = 'Pause';
            drawStep();
        }
    });
    clearBtn.addEventListener('click', function() {
        if (animationTimeout) {
            clearTimeout(animationTimeout);
        }
        paused = false;
        pauseBtn.disabled = true;
        runBtn.disabled = true;
        pauseBtn.textContent = 'Pause';
        ctx.setTransform(1, 0, 0, 1, 0, 0);
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        points = [];
        animationSequence = [];
        currentAnimationStep = 0;
        submitBtn.disabled = true; // Disable button when clearing
        fetch('/clear_points', {
            method: 'POST',
        });
    });
    speedSlider.addEventListener('input', function() {
        animationDelay = 2010 - this.value; // Invert so higher slider = faster
        speedValue.textContent = animationDelay + 'ms';
    });
    canvas.addEventListener('click', function(e) {
        const rect = canvas.getBoundingClientRect();
        const x = roundToDecimal(e.clientX - rect.left,2);
        const y = roundToDecimal(e.clientY - rect.top,2);
        drawPoint(x, y,'red');
        // Check if any point in the array has the same x and y
        const pointExists = points.some(point => point.x === x && point.y === y);
        if (!pointExists) {
            points.push({x, y});
        }
        // Enable/disable run button based on point count
        submitBtn.disabled = points.length < 3;
        // Send to server
        fetch('/save_point', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({x, y}),
        });
    });
    runBtn.addEventListener('click', function() {
        if(!manual){
            runBtn.disabled = true;
            pauseBtn.disabled = false;
        }
        drawStep();
    });
    
    // Load existing points on page load
    // Modify your initial points load to check count
    fetch('/get_points')
        .then(response => response.json())
        .then(data => {
            points = data.points.map(p => ({x: p[0], y: p[1]}));
            points.forEach(p => drawPoint(p.x, p.y,'red'));
            // Set initial run button state
            submitBtn.disabled = points.length < 3;
        });
    ////////
    //Async Functions
    ////////
    async function getSequence() {
        const response = await fetch('/get_drawing_sequence');
        animationSequence = await response.json();
        zoomToFit(animationSequence);
    }
    ////////
    //Helper Functions
    ////////
    function drawStep(){
        if(currentAnimationStep >= animationSequence.length){return;}
        if(!manual && paused){return;}
        const step = animationSequence[currentAnimationStep];
        ctx.clearRect(-10000, -10000, 20000, 20000);
        
        // Draw points
        step.points.forEach(([x, y], idx) => {
            drawPoint(x, y);
        });
        
        // Draw uninserted points
        step.uninserted_points.forEach(([x, y], idx) => {
            drawPoint(x, y, 'red');
        });

        // Draw edges
        step.edges.forEach(([[x1, y1], [x2, y2]]) => {
            ctx.beginPath();
            ctx.moveTo(x1, y1);
            ctx.lineTo(x2, y2);
            ctx.strokeStyle = `black`;
            ctx.lineWidth = 2;
            ctx.stroke();
        });
        
        // Draw circles
        step.circles.forEach(([x, y, radius]) => {
            drawCircle(x, y, radius, `hsl(${currentAnimationStep * 60 + 180}, 100%, 50%)`);
        });
        
        currentAnimationStep++;
        if(!manual){
            animationTimeout = setTimeout(() => drawStep(), animationDelay);
        }
        
        if(currentAnimationStep >= animationSequence.length){
            runBtn.disabled = true;
            pauseBtn.disabled = true;
            return;
        }
    }
    function drawPoint(x, y, fill='blue') {
        ctx.beginPath();
        ctx.arc(x, y, 5, 0, Math.PI * 2);
        ctx.fillStyle = fill;
        ctx.fill();
        ctx.closePath();
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
    function roundToDecimal(num, decimals) {
      const factor = 10 ** decimals;
      return Math.round(num * factor) / factor;
    }
});