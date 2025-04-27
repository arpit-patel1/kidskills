import React, { useRef, useState, useEffect, forwardRef, useImperativeHandle } from 'react';

const TracingCanvas = forwardRef(({ width = 300, height = 300, lineWidth = 5, lineColor = 'black', onDrawEnd, onClear }, ref) => {
    const canvasRef = useRef(null);
    const contextRef = useRef(null);
    const [isDrawing, setIsDrawing] = useState(false);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        
        // Adjust for device pixel ratio for sharper drawing
        const scale = window.devicePixelRatio || 1;
        canvas.width = width * scale;
        canvas.height = height * scale;
        canvas.style.width = `${width}px`;
        canvas.style.height = `${height}px`;

        const context = canvas.getContext('2d');
        context.scale(scale, scale);
        context.lineCap = 'round';
        context.strokeStyle = lineColor;
        context.lineWidth = lineWidth;
        contextRef.current = context;
    }, [width, height, lineColor, lineWidth]);

    const startDrawing = ({ nativeEvent }) => {
        const { offsetX, offsetY } = getCoordinates(nativeEvent);
        contextRef.current.beginPath();
        contextRef.current.moveTo(offsetX, offsetY);
        setIsDrawing(true);
    };

    const finishDrawing = () => {
        if (!isDrawing) return;
        contextRef.current.closePath();
        setIsDrawing(false);
        if (onDrawEnd) {
            onDrawEnd(getImageData()); // Optionally notify parent when drawing stops
        }
    };

    const draw = ({ nativeEvent }) => {
        if (!isDrawing) return;
        const { offsetX, offsetY } = getCoordinates(nativeEvent);
        contextRef.current.lineTo(offsetX, offsetY);
        contextRef.current.stroke();
    };

    // Helper to get correct coordinates for both mouse and touch events
    const getCoordinates = (event) => {
        const canvas = canvasRef.current;
        const rect = canvas.getBoundingClientRect();
        let offsetX, offsetY;

        if (event.touches && event.touches.length > 0) {
            // Touch event
            offsetX = event.touches[0].clientX - rect.left;
            offsetY = event.touches[0].clientY - rect.top;
        } else {
            // Mouse event
            offsetX = event.clientX - rect.left;
            offsetY = event.clientY - rect.top;
        }
        return { offsetX, offsetY };
    };

    const clearCanvas = () => {
        const canvas = canvasRef.current;
        const context = contextRef.current;
        context.clearRect(0, 0, canvas.width / window.devicePixelRatio, canvas.height / window.devicePixelRatio);
        if (onClear) {
            onClear();
        }
    };

    // Function to be called by parent component to get image data
    const getImageData = () => {
        const canvas = canvasRef.current;
        // Return as PNG with transparent background if needed, otherwise default is black
        return canvas.toDataURL('image/png');
    };

    // Expose clearCanvas and getImageData to parent via ref
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
            onMouseOut={finishDrawing} // Stop drawing if mouse leaves canvas
            onTouchStart={startDrawing}
            onTouchEnd={finishDrawing}
            onTouchMove={draw}
            style={{ border: '1px solid #ccc', touchAction: 'none' }} // touchAction none prevents scrolling on touch devices
        />
    );
});

export default TracingCanvas; 