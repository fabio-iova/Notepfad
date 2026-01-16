import React, { useState, useEffect } from 'react';

const API_URL = 'http://localhost:8000';

const Certificate = ({ studentId }) => {
    const [stats, setStats] = useState([]);
    const [overallAvg, setOverallAvg] = useState(0);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchData();
    }, [studentId]);

    const fetchData = async () => {
        try {
            const [subjRes, gradesRes] = await Promise.all([
                fetch(`${API_URL}/subjects/`),
                fetch(`${API_URL}/grades/?student_id=${studentId}`)
            ]);

            const subjects = await subjRes.json();
            const grades = await gradesRes.json();

            // Calculate average per subject
            const subjectStats = subjects.map(sub => {
                const subGrades = grades.filter(g => g.subject_id === sub.id);
                const avg = subGrades.length > 0
                    ? subGrades.reduce((acc, curr) => acc + curr.value, 0) / subGrades.length
                    : null;
                return {
                    ...sub,
                    average: avg
                };
            }); // Removed filter here to show all subjects

            setStats(subjectStats);

            // Calculate overall Zeugnis average (average of averages)
            const validAverages = subjectStats.map(s => s.average).filter(a => a !== null);
            const totalAvg = validAverages.length > 0
                ? validAverages.reduce((acc, curr) => acc + curr, 0) / validAverages.length
                : 0;

            setOverallAvg(totalAvg);

        } catch (error) {
            console.error("Error fetching certificate data:", error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="container animate-fade-in" style={{ paddingBottom: '80px' }}>
            <div className="card" style={{ textAlign: 'center', marginBottom: '2rem' }}>
                <div style={{ fontSize: '3rem', marginBottom: '0.5rem' }}>📜</div>
                <h2>Dein Zeugnis</h2>
                <div style={{ margin: '1.5rem 0' }}>
                    <p style={{ margin: 0, color: '#64748b' }}>Zeugnisschnitt</p>
                    <div style={{
                        fontSize: '3.5rem',
                        fontWeight: '700',
                        color: overallAvg >= 4.75 ? 'var(--color-secondary)' : (overallAvg >= 4.0 ? 'var(--color-warning)' : 'var(--color-danger)')
                    }}>
                        {loading ? '...' : overallAvg.toFixed(2)}
                    </div>
                </div>
            </div>

            <div style={{ display: 'grid', gap: '1rem' }}>
                {stats.length === 0 ? (
                    <div className="card">
                        <p>Noch keine Fächer erfasst.</p>
                    </div>
                ) : (
                    stats.map(sub => (
                        <div key={sub.id} className="card flex-between" style={{ padding: '1rem' }}>
                            <span style={{ fontWeight: '600', fontSize: '1.1rem' }}>{sub.name}</span>
                            <div style={{ textAlign: 'right' }}>
                                <div style={{
                                    fontWeight: 'bold',
                                    fontSize: '1.4rem',
                                    color: sub.average === null ? '#94a3b8' : (sub.average >= 4.75 ? 'var(--color-secondary)' : (sub.average >= 4.0 ? 'var(--color-warning)' : 'var(--color-danger)'))
                                }}>
                                    {sub.average ? sub.average.toFixed(2) : '-'}
                                </div>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};

export default Certificate;
