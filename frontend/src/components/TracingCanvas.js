import React, { useRef, useState, useEffect, forwardRef, useImperativeHandle } from 'react';

// Default line width and color if not provided
const DEFAULT_LINE_WIDTH = 5;
const DEFAULT_LINE_COLOR = 'black';

const TracingCanvas = forwardRef(({ lineWidth = DEFAULT_LINE_WIDTH, lineColor = DEFAULT_LINE_COLOR, onDrawEnd, onClear }, ref) => {
    const canvasRef = useRef(null);
    const contextRef = useRef(null);
    const [isDrawing, setIsDrawing] = useState(false);
    const pointsRef = useRef([]); // Store points for smoothing

    // Store dimensions in state to potentially use elsewhere if needed, though primarily used for setup
    const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

    // Effect to setup canvas and observer
    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        // --- Setup function --- 
        const setupCanvas = (width, height) => {
            if (width <= 0 || height <= 0) return; // Don't setup if dimensions are invalid
            
            setDimensions({ width, height });
            
            const scale = window.devicePixelRatio || 1;
            canvas.width = width * scale; // Set internal buffer size
            canvas.height = height * scale; // Set internal buffer size
            // canvas.style.width = `${width}px`; // CSS handles this now
            // canvas.style.height = `${height}px`; // CSS handles this now

            const context = canvas.getContext('2d');
            context.scale(scale, scale); // Scale context for drawing
            context.lineCap = 'round';
            context.lineJoin = 'round'; // Use round joins for smoother curves
            context.strokeStyle = lineColor;
            context.lineWidth = lineWidth;
            contextRef.current = context;
            console.log(`Canvas setup/resized: Buffer ${canvas.width}x${canvas.height}, Observed ${width}x${height}`);
        };

        // --- Resize Observer --- 
        const resizeObserver = new ResizeObserver(entries => {
            if (!entries || entries.length === 0) return;
            const entry = entries[0];
            const { width, height } = entry.contentRect;
            // Store current drawing to re-apply after resize? (More complex)
            // For now, just resize, which clears the canvas implicitly by resizing buffer.
            setupCanvas(width, height); 
        });

        // Observe the canvas element itself
        resizeObserver.observe(canvas);

        // --- Cleanup --- 
        return () => {
            resizeObserver.unobserve(canvas);
        };

    }, [lineColor, lineWidth]); // Rerun setup if line color/width changes

    const startDrawing = ({ nativeEvent }) => {
        if (!contextRef.current) return;
        const coords = getCoordinates(nativeEvent);
        if (!coords) return;
        
        setIsDrawing(true);
        pointsRef.current = [coords]; // Start with the first point
        
        // Begin path, move to the starting point
        contextRef.current.beginPath();
        contextRef.current.moveTo(coords.offsetX, coords.offsetY); 
    };

    const finishDrawing = () => {
        if (!isDrawing || !contextRef.current) return;
        
        // Draw the last segment if needed (can sometimes be missed)
        if (pointsRef.current.length > 1) {
             // Optionally draw a final lineTo the very last point? Or rely on curve?
             // Let's ensure the path is stroked completely
             contextRef.current.stroke(); 
        }
        
        contextRef.current.closePath(); // Close the path
        setIsDrawing(false);
        
        if (onDrawEnd) {
            onDrawEnd(getImageData()); 
        }
        pointsRef.current = []; // Clear points
    };

    const draw = ({ nativeEvent }) => {
        if (!isDrawing || !contextRef.current) return;
        const currentPoint = getCoordinates(nativeEvent);
        if (!currentPoint) return;

        const points = pointsRef.current;
        points.push(currentPoint); // Add current point

        if (points.length < 3) {
            // Not enough points for a quadratic curve yet, draw a line
            const lastPoint = points[points.length - 1];
             // Ensure path is started before lineTo
             if (points.length === 2) {
                 contextRef.current.beginPath(); // Start path if not already started? Might cause issues.
                 contextRef.current.moveTo(points[0].offsetX, points[0].offsetY);
             }
            contextRef.current.lineTo(lastPoint.offsetX, lastPoint.offsetY);
            contextRef.current.stroke(); // Stroke the line segment
        } else {
            // Calculate midpoint for quadratic curve
            const p1 = points[points.length - 3]; // Point before the previous one
            const p2 = points[points.length - 2]; // Previous point (Control Point)
            const p3 = points[points.length - 1]; // Current point

            // Calculate control point (previous point) and end point (midpoint)
            const midX = (p2.offsetX + p3.offsetX) / 2;
            const midY = (p2.offsetY + p3.offsetY) / 2;

            // Start a new path segment for the curve? No, continue the existing path.
            // contextRef.current.beginPath(); // DON'T begin path here, continue existing
            contextRef.current.moveTo(p1.offsetX, p1.offsetY); // Ensure starting point is correct? Check this. It should already be positioned.
            
            // Draw the curve from the previous midpoint (or p1 if it's the first curve)
            // to the current midpoint, using p2 as the control point.
            
            // Let's rethink: Use p2 as control point, draw TO mid(p2, p3)
            contextRef.current.quadraticCurveTo(p2.offsetX, p2.offsetY, midX, midY);
            
            contextRef.current.stroke(); // Stroke the curve segment
            contextRef.current.moveTo(midX, midY); // Move to the end of the curve for the next segment
        }
    };


    const getCoordinates = (event) => {
        const canvas = canvasRef.current;
        if (!canvas) return null;
        const rect = canvas.getBoundingClientRect();
        let clientX, clientY;

        if (event.touches && event.touches.length > 0) {
            clientX = event.touches[0].clientX;
            clientY = event.touches[0].clientY;
        } else if (event.clientX && event.clientY) {
            clientX = event.clientX;
            clientY = event.clientY;
        } else {
            return null; // No valid coordinates found
        }
        
        let offsetX = clientX - rect.left;
        let offsetY = clientY - rect.top;
        
        // Clamp coordinates to be within the canvas bounds
        offsetX = Math.max(0, Math.min(offsetX, dimensions.width));
        offsetY = Math.max(0, Math.min(offsetY, dimensions.height));
        return { offsetX, offsetY };
    };

    const clearCanvas = () => {
        // const canvas = canvasRef.current; // This variable is unused
        const context = contextRef.current;
        if (context && dimensions.width > 0 && dimensions.height > 0) {
            // Use the actual pixel dimensions for clearing
            context.clearRect(0, 0, dimensions.width, dimensions.height);
            console.log(`Canvas cleared: ${dimensions.width}x${dimensions.height}`);
        } else {
            console.log("Clear attempt failed: context or dimensions invalid");
        }
        if (onClear) {
            onClear();
        }
    };

    const getImageData = () => {
        const canvas = canvasRef.current;
        if (!canvas || dimensions.width === 0 || dimensions.height === 0) {
            console.warn("Attempted to get image data from uninitialized canvas");
            return null; // Or return a default blank image data URL?
        }
        return canvas.toDataURL('image/png');
    };

    useImperativeHandle(ref, () => ({ 
        clearCanvas, 
        getImageData 
    }));

    return (
        <canvas
            ref={canvasRef}
            onMouseDown={startDrawing}
            onMouseUp={finishDrawing}
            onMouseMove={draw}
            onMouseLeave={finishDrawing} // Use MouseLeave instead of MouseOut for better edge case handling
            onTouchStart={startDrawing}
            onTouchEnd={finishDrawing}
            onTouchMove={draw}
            style={{ 
                display: 'block', 
                border: '1px solid #ccc', 
                touchAction: 'none', 
                width: '100%', 
                height: '100%' 
            }}
        />
    );
});

export default TracingCanvas; 