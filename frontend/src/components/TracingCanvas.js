import React, { useRef, useState, useEffect, forwardRef, useImperativeHandle } from 'react';

// Default line width and color if not provided
const DEFAULT_LINE_WIDTH = 5;
const DEFAULT_LINE_COLOR = 'black';

const TracingCanvas = forwardRef(({ lineWidth = DEFAULT_LINE_WIDTH, lineColor = DEFAULT_LINE_COLOR, onDrawEnd, onClear }, ref) => {
    const canvasRef = useRef(null);
    const contextRef = useRef(null);
    const [isDrawing, setIsDrawing] = useState(false);

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
            // Remove setting style width/height here, as it might cause the loop
            // canvas.style.width = `${width}px`; 
            // canvas.style.height = `${height}px`;

            const context = canvas.getContext('2d');
            context.scale(scale, scale); // Scale context for drawing
            context.lineCap = 'round';
            context.strokeStyle = lineColor;
            context.lineWidth = lineWidth;
            contextRef.current = context;
            console.log(`Canvas setup/resized: Buffer ${canvas.width}x${canvas.height}, Observed ${width}x${height}`);
        };

        // --- Resize Observer --- 
        const resizeObserver = new ResizeObserver(entries => {
            if (!entries || entries.length === 0) return;
            const entry = entries[0];
            // Use contentRect for size, ensures padding/border doesn't affect drawing area
            const { width, height } = entry.contentRect;
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
        if (!contextRef.current) return; // Don't draw if context isn't ready
        const { offsetX, offsetY } = getCoordinates(nativeEvent);
        contextRef.current.beginPath();
        contextRef.current.moveTo(offsetX, offsetY);
        setIsDrawing(true);
    };

    const finishDrawing = () => {
        if (!isDrawing || !contextRef.current) return;
        contextRef.current.closePath();
        setIsDrawing(false);
        if (onDrawEnd) {
            onDrawEnd(getImageData()); 
        }
    };

    const draw = ({ nativeEvent }) => {
        if (!isDrawing || !contextRef.current) return;
        const { offsetX, offsetY } = getCoordinates(nativeEvent);
        contextRef.current.lineTo(offsetX, offsetY);
        contextRef.current.stroke();
    };

    const getCoordinates = (event) => {
        const canvas = canvasRef.current;
        const rect = canvas.getBoundingClientRect();
        let offsetX, offsetY;

        if (event.touches && event.touches.length > 0) {
            offsetX = event.touches[0].clientX - rect.left;
            offsetY = event.touches[0].clientY - rect.top;
        } else {
            offsetX = event.clientX - rect.left;
            offsetY = event.clientY - rect.top;
        }
        // Clamp coordinates to be within the canvas bounds, adjusting for potential style vs buffer size differences
        // Note: getBoundingClientRect gives styled size, which setupCanvas syncs style to.
        offsetX = Math.max(0, Math.min(offsetX, dimensions.width));
        offsetY = Math.max(0, Math.min(offsetY, dimensions.height));
        return { offsetX, offsetY };
    };

    const clearCanvas = () => {
        const canvas = canvasRef.current;
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
            onMouseOut={finishDrawing} 
            onTouchStart={startDrawing}
            onTouchEnd={finishDrawing}
            onTouchMove={draw}
            style={{ 
                display: 'block', /* Ensure canvas behaves like a block element */
                border: '1px solid #ccc', 
                touchAction: 'none', 
                width: '100%', /* Let CSS control the display size via container */
                height: '100%' /* Let CSS control the display size via container */
            }}
        />
    );
});

export default TracingCanvas; 