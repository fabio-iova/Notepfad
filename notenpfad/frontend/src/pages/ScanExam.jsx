import React, { useState } from 'react';

const API_URL = 'http://localhost:8000';

const ScanExam = () => {
    const [analyzing, setAnalyzing] = useState(false);
    const [result, setResult] = useState(null);

    const handleMockScan = async () => {
        setAnalyzing(true);
        // Simulate network delay
        setTimeout(async () => {
            try {
                const res = await fetch(`${API_URL}/analyze-exam`, {
                    method: 'POST',
                });
                const data = await res.json();
                setResult(data);
            } catch (error) {
                console.error("Scan error", error);
            } finally {
                setAnalyzing(false);
            }
        }, 1500);
    };

    return (
        <div className="container animate-fade-in" style={{ paddingTop: '1rem' }}>
            <h2>Prüfung Scannen 📸</h2>
            <p style={{ marginBottom: '1.5rem' }}>Fotografiere deine Prüfung, um die Note automatisch zu erfassen und Tipps zu erhalten (Demo).</p>

            <div className="card flex-center" style={{
                height: '300px',
                border: '2px dashed var(--color-border)',
                backgroundColor: '#f1f5f9',
                flexDirection: 'column',
                cursor: 'pointer'
            }} onClick={handleMockScan}>
                {analyzing ? (
                    <div style={{ textAlign: 'center' }}>
                        <span style={{ fontSize: '3rem', display: 'block', marginBottom: '1rem' }} className="animate-pulse">🧠</span>
                        <p>Analysiere Prüfung...</p>
                    </div>
                ) : (
                    <>
                        <span style={{ fontSize: '3rem', marginBottom: '1rem' }}>📷</span>
                        <p>Hier tippen um zu scannen</p>
                    </>
                )}
            </div>

            {result && (
                <div className="card animate-fade-in" style={{ border: '2px solid var(--color-primary)' }}>
                    <h3>Ergebnis</h3>
                    <div style={{ margin: '1rem 0' }}>
                        <p>Erkannte Note: <strong style={{ color: 'var(--color-primary)', fontSize: '1.2rem' }}>{result.grade}</strong></p>
                        <p>Fach: <strong>{result.subject}</strong></p>
                    </div>
                    <div style={{ background: '#eff6ff', padding: '1rem', borderRadius: '8px' }}>
                        <p style={{ color: '#1e40af', fontSize: '0.9rem' }}>💡 <strong>AI Tipp:</strong> {result.feedback}</p>
                    </div>
                    <button className="btn btn-primary" style={{ marginTop: '1rem' }} onClick={() => alert('Note gespeichert!')}>
                        Note übernehmen
                    </button>
                </div>
            )}
        </div>
    );
};

export default ScanExam;
