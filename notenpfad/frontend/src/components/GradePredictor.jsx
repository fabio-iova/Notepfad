import React, { useState, useEffect } from 'react';

const GradePredictor = ({ studentId }) => {
    // Inputs
    const [mathV, setMathV] = useState('');
    const [deutV, setDeutV] = useState('');
    const [mathExam, setMathExam] = useState('');
    const [deutAufsatz, setDeutAufsatz] = useState('');
    const [deutSprach, setDeutSprach] = useState('');

    const [result, setResult] = useState(null);

    // Live calculation
    useEffect(() => {
        calculate();
    }, [mathV, deutV, mathExam, deutAufsatz, deutSprach]);

    const calculate = () => {
        // Parse floats or use null
        const mv = mathV ? parseFloat(mathV) : null;
        const dv = deutV ? parseFloat(deutV) : null;
        const me = mathExam ? parseFloat(mathExam) : null;
        const da = deutAufsatz ? parseFloat(deutAufsatz) : null;
        const ds = deutSprach ? parseFloat(deutSprach) : null;

        // Vornote (50%)
        let vornote = null;
        if (mv !== null && dv !== null) vornote = (mv + dv) / 2;
        else if (mv !== null) vornote = mv;
        else if (dv !== null) vornote = dv;

        // Deutsch Exam
        let deutExam = null;
        if (da !== null && ds !== null) deutExam = (da + ds) / 2;
        else if (da !== null) deutExam = da;
        else if (ds !== null) deutExam = ds;

        // Exam (50%)
        let exam = null;
        if (me !== null && deutExam !== null) exam = (me + deutExam) / 2;
        else if (me !== null) exam = me;
        else if (deutExam !== null) exam = deutExam;

        // Total
        let total = null;
        if (vornote !== null && exam !== null) total = (vornote + exam) / 2;
        else if (vornote !== null) total = vornote; // optimistic? No, just showing what we have
        else if (exam !== null) total = exam;

        // Only show result if we have at least ONE value? 
        // Or specific rule: Show if we have at least partial data.

        if (total !== null) {
            setResult({
                total: total.toFixed(2),
                passed: total >= 4.75,
                vornote: vornote ? vornote.toFixed(2) : '-',
                exam: exam ? exam.toFixed(2) : '-'
            });
        } else {
            setResult(null);
        }
    };

    const inputStyle = {
        width: '100%',
        padding: '8px',
        borderRadius: '6px',
        border: '1px solid #ccc',
        marginTop: '4px'
    };

    const groupStyle = {
        background: 'white',
        padding: '1rem',
        borderRadius: '8px',
        marginBottom: '1rem'
    };

    return (
        <div className="card" style={{ border: '2px solid var(--color-primary)', background: '#eef2ff' }}>
            <h3>🔮 Noten-Simulator</h3>
            <p style={{ fontSize: '0.9rem', marginBottom: '1rem' }}>
                Simuliere deine Gymi-Note. Gib deine erwarteten Noten ein:
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>

                {/* Vornote Inputs */}
                <div style={groupStyle}>
                    <h5 style={{ margin: '0 0 0.5rem 0' }}>Vornoten</h5>
                    <div style={{ marginBottom: '0.5rem' }}>
                        <label style={{ fontSize: '0.8rem' }}>Mathematik</label>
                        <input type="number" step="0.5" style={inputStyle} value={mathV} onChange={e => setMathV(e.target.value)} placeholder="5.0" />
                    </div>
                    <div>
                        <label style={{ fontSize: '0.8rem' }}>Deutsch</label>
                        <input type="number" step="0.5" style={inputStyle} value={deutV} onChange={e => setDeutV(e.target.value)} placeholder="5.0" />
                    </div>
                </div>

                {/* Exam Inputs */}
                <div style={groupStyle}>
                    <h5 style={{ margin: '0 0 0.5rem 0' }}>Prüfung</h5>
                    <div style={{ marginBottom: '0.5rem' }}>
                        <label style={{ fontSize: '0.8rem' }}>Mathe Prüfung</label>
                        <input type="number" step="0.5" style={inputStyle} value={mathExam} onChange={e => setMathExam(e.target.value)} placeholder="4.0" />
                    </div>
                    <div style={{ marginBottom: '0.5rem' }}>
                        <label style={{ fontSize: '0.8rem' }}>Deutsch Aufsatz</label>
                        <input type="number" step="0.5" style={inputStyle} value={deutAufsatz} onChange={e => setDeutAufsatz(e.target.value)} placeholder="4.0" />
                    </div>
                    <div>
                        <label style={{ fontSize: '0.8rem' }}>D. Sprachbetrachtung</label>
                        <input type="number" step="0.5" style={inputStyle} value={deutSprach} onChange={e => setDeutSprach(e.target.value)} placeholder="6.0" />
                    </div>
                </div>
            </div>

            {/* Result Area */}
            {result ? (
                <div style={{
                    textAlign: 'center',
                    background: 'white',
                    padding: '1.5rem',
                    borderRadius: '8px',
                    border: result.passed ? '2px solid var(--color-secondary)' : '2px solid var(--color-danger)'
                }}>
                    <p style={{ margin: 0, fontWeight: '600' }}>Simulierte Gesamtnote</p>
                    <div style={{
                        fontSize: '3rem',
                        fontWeight: '700',
                        color: result.passed ? 'var(--color-secondary)' : 'var(--color-danger)',
                        lineHeight: '1.2'
                    }}>
                        {result.total}
                    </div>
                    <div style={{
                        margin: '0.5rem 0',
                        fontSize: '1.2rem',
                        fontWeight: 'bold',
                        color: result.passed ? 'var(--color-secondary)' : 'var(--color-danger)'
                    }}>
                        {result.passed ? '🎉 BESTANDEN' : '🛑 NICHT BESTANDEN'}
                    </div>
                    <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.5rem' }}>
                        Vornote: {result.vornote} &bull; Prüfung: {result.exam}
                    </div>
                </div>
            ) : (
                <div style={{ textAlign: 'center', padding: '1rem', color: '#94a3b8' }}>
                    Gib Noten ein, um das Ergebnis zu sehen.
                </div>
            )}
        </div>
    );
};

export default GradePredictor;
