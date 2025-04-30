import React, { useState, useEffect, useRef } from 'react';
import TracingCanvas from './TracingCanvas';
import { getGujaratiLetter, submitGujaratiTrace } from '../services/api'; // Assuming api service functions exist
import { Button, Row, Col, Card, Alert, Spinner } from 'react-bootstrap';
import Confetti from 'react-confetti'; // Assuming react-confetti is installed

// Kid-friendly color palette
const TRACING_COLORS = [
    '#FF6347', // Tomato
    '#4682B4', // SteelBlue
    '#32CD32', // LimeGreen
    '#FFD700', // Gold
    '#6A5ACD', // SlateBlue
    '#FF69B4', // HotPink
    '#20B2AA', // LightSeaGreen
    '#FFA500', // Orange
];

const GujaratiTracingActivity = ({ playerId }) => {
    const [targetLetter, setTargetLetter] = useState(null);
    const [feedback, setFeedback] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState(null);
    const [showConfetti, setShowConfetti] = useState(false);
    const [canvasReady, setCanvasReady] = useState(false);
    const [currentColorIndex, setCurrentColorIndex] = useState(0); // State for color index
    const canvasRef = useRef(null); // Ref to access TracingCanvas methods

    // --- Fetching Letter --- 
    const fetchLetter = async () => {
        setIsLoading(true);
        setError(null);
        setFeedback(null);
        setShowConfetti(false); // Hide confetti for new letter
        // Cycle through colors
        setCurrentColorIndex(prevIndex => (prevIndex + 1) % TRACING_COLORS.length);

        try {
            console.log("Fetching new Gujarati letter...");
            const data = await getGujaratiLetter();
            console.log("Received letter data:", data);
            setTargetLetter(data);
            
            // Only try to clear canvas if it's ready and has clearCanvas method
            if (canvasReady && canvasRef.current && typeof canvasRef.current.clearCanvas === 'function') {
                canvasRef.current.clearCanvas();
            }
        } catch (err) {
            console.error("Error fetching Gujarati letter:", err);
            setError('Failed to load the letter. Please try again.');
            setTargetLetter(null); // Clear target on error
        } finally {
            setIsLoading(false);
        }
    };

    // Effect to set canvas ready when component is mounted
    useEffect(() => {
        // Set a short delay to ensure canvas is fully initialized
        const timer = setTimeout(() => {
            setCanvasReady(true);
        }, 100);
        
        return () => clearTimeout(timer);
    }, []);

    useEffect(() => {
        fetchLetter();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [playerId, canvasReady]); // Refetch if player changes or canvas becomes ready

    // --- Canvas Interaction ---
    const handleClear = () => {
        if (canvasRef.current && typeof canvasRef.current.clearCanvas === 'function') {
            canvasRef.current.clearCanvas();
            setFeedback(null); // Clear feedback when canvas is cleared
        }
    };

    // --- Submission Logic ---
    const handleSubmit = async () => {
        if (!canvasRef.current || !targetLetter || !canvasReady) return;
        
        if (!canvasRef.current.getImageData) {
            console.error("getImageData method not available on canvas ref");
            setError('Canvas not properly initialized. Please reload the page.');
            return;
        }

        setIsSubmitting(true);
        setError(null);
        setFeedback(null);
        try {
            const imageData = canvasRef.current.getImageData();
            
            // Basic check if canvas is empty (completely transparent)
            if (isCanvasEmpty(imageData)) {
                 setFeedback({ message: "Please trace the letter first!", score: 0 });
                 setIsSubmitting(false);
                 return;
            }

            console.log("Submitting trace for letter:", targetLetter.letter_id);
            const result = await submitGujaratiTrace({
                player_id: playerId,
                letter_id: targetLetter.letter_id,
                image_data: imageData,
            });
            console.log("Received trace feedback:", result);
            setFeedback({ 
                message: result.feedback, 
                score: result.similarity_score 
            });

            // Trigger confetti for high scores
            if (result.similarity_score >= 75) { 
                setShowConfetti(true);
                setTimeout(() => setShowConfetti(false), 5000); // Confetti for 5 seconds
            }

        } catch (err) {
            console.error("Error submitting trace:", err);
            setError('Failed to submit the tracing. Please try again.');
        } finally {
            setIsSubmitting(false);
        }
    };
    
    // Helper to check if canvas data is essentially empty (all transparent)
    // This is a basic check and might need refinement.
    const isCanvasEmpty = (imageDataUrl) => {
        if (!imageDataUrl || !imageDataUrl.startsWith('data:image/png;base64,')) {
            return true; // Invalid data url
        }
        // Create an image element to check pixels (might be overkill, could analyze base64)
        // For simplicity, we'll just check if it's the default blank canvas URL length
        // A more robust check would involve drawing to a temp canvas and checking pixel data.
        // This is a heuristic:
        const base64Data = imageDataUrl.split(',')[1];
        // A truly blank 300x300 canvas PNG is usually small.
        // Adjust threshold based on actual blank canvas output size.
        return base64Data.length < 500; 
    }

    // --- Rendering --- 
    return (
        <div className="container py-4">
            <div className="text-center mb-3">
                <h2>ગુજરાતી - Gujarati Letter Tracing</h2>
            </div>
            {showConfetti && <Confetti recycle={false} numberOfPieces={200} />}
            <Card className="mt-4">
                <Card.Body>
                    {isLoading && <div className="text-center"><Spinner animation="border" role="status"><span className="visually-hidden">Loading...</span></Spinner></div>}
                    {error && <Alert variant="danger">{error}</Alert>}
                    
                    {targetLetter && !isLoading && (
                        <div className="d-flex justify-content-center">
                            <Row className="justify-content-center align-items-stretch g-0" style={{ maxWidth: '800px' }}>
                                <Col xs={12} md={6} className="text-center d-flex flex-column align-items-center">
                                    <h5>Trace this letter:</h5>
                                    <div className="mx-auto px-2 target-letter-image">
                                        <img 
                                            src={targetLetter.image_url} 
                                            alt={`Gujarati letter ${targetLetter.letter_id}`} 
                                            style={{ 
                                                objectFit: 'contain',
                                                border: '1px solid #ccc'
                                            }} 
                                        />
                                    </div>
                                </Col>
                                <Col xs={12} md={6} className="text-center d-flex flex-column align-items-center">
                                    <h5>Your tracing:</h5>
                                    <div className="mx-auto px-2 tracing-canvas-container">
                                        <TracingCanvas 
                                            ref={canvasRef} 
                                            lineColor={TRACING_COLORS[currentColorIndex]}
                                            style={{ border: '1px solid #ccc' }}
                                        />
                                    </div>
                                    <div className="mt-3 d-flex justify-content-center">
                                       {!feedback ? (
                                           <>
                                                <Button variant="secondary" onClick={handleClear} disabled={isSubmitting} className="me-2">
                                                    Clear
                                                </Button>
                                                <Button variant="primary" onClick={handleSubmit} disabled={isSubmitting}>
                                                    {isSubmitting ? <Spinner as="span" animation="border" size="sm" role="status" aria-hidden="true" /> : 'Submit'}
                                                </Button>
                                           </>
                                       ) : (
                                           <Button variant="success" onClick={fetchLetter}>
                                                Next Letter <i className="bi bi-arrow-right-circle-fill"></i>
                                           </Button>
                                       )}
                                    </div>
                                </Col>
                            </Row>
                        </div>
                    )}

                    {feedback && (
                        <Alert variant={feedback.score >= 75 ? "success" : feedback.score >=50 ? "warning" : "info"} className="mt-4 text-center">
                           {feedback.message} {/*(Score: {feedback.score?.toFixed(1)}%)*/}
                        </Alert>
                    )}
                </Card.Body>
            </Card>
        </div>
    );
};

export default GujaratiTracingActivity; 