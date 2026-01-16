import React from 'react';
import GradePredictor from '../components/GradePredictor';

const Simulator = ({ studentId }) => {
    return (
        <div className="container animate-fade-in" style={{ paddingBottom: '80px' }}>
            <h2 style={{ marginBottom: '1.5rem', textAlign: 'center' }}>Noten-Simulator 🔮</h2>
            <GradePredictor studentId={studentId} />
        </div>
    );
};

export default Simulator;
