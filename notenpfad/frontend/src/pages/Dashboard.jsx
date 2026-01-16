import React, { useState, useEffect } from 'react';
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer
} from 'recharts';

import AddGradeModal from '../components/AddGradeModal';
import GradeList from '../components/GradeList';

const API_URL = 'http://localhost:8000';

const Dashboard = ({ studentId, onSelectSubject, onViewHistory }) => {
    const [stats, setStats] = useState(null); // Changed from average number to stats object
    const [subjects, setSubjects] = useState([]);
    const [grades, setGrades] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isModalOpen, setIsModalOpen] = useState(false);

    useEffect(() => {
        fetchData();
    }, [studentId]);

    const fetchData = async () => {
        try {
            const avgRes = await fetch(`${API_URL}/average/?student_id=${studentId}`);
            const avgData = await avgRes.json();
            setStats(avgData); // Expecting { average, details, passed }

            const subjRes = await fetch(`${API_URL}/subjects/`);
            const subjData = await subjRes.json();
            setSubjects(subjData);

            const gradesRes = await fetch(`${API_URL}/grades/?student_id=${studentId}`);
            const gradesData = await gradesRes.json();
            const sortedGrades = gradesData.sort((a, b) => new Date(b.date) - new Date(a.date));
            setGrades(sortedGrades);

        } catch (error) {
            console.error("Error fetching data:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleCreateSubject = async () => {
        const name = prompt("Fachname (z.B. Mathematik, Deutsch):");
        if (!name) return;
        const weighting = prompt("Gewichtung (z.B. 1.0):", "1.0");

        await fetch(`${API_URL}/subjects/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, weighting: parseFloat(weighting) })
        });
        fetchData();
    };

    const handleSaveGrade = async (gradeData) => {
        await fetch(`${API_URL}/grades/?student_id=${studentId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                ...gradeData,
                date: new Date().toISOString().split('T')[0]
            })
        });
        fetchData();
    };


    const handleDeleteGrade = async (gradeId) => {
        if (!confirm("Note wirklich löschen?")) return;

        await fetch(`${API_URL}/grades/${gradeId}`, {
            method: 'DELETE'
        });
        fetchData();
    };

    const handleDeleteSubject = async (subjectId) => {
        if (!confirm("Fach wirklich löschen? Alle zugehörigen Noten werden ebenfalls gelöscht!")) return;

        await fetch(`${API_URL}/subjects/${subjectId}`, {
            method: 'DELETE'
        });
        fetchData();
    };


    const overallAverage = stats?.average || 0;
    const passed = stats?.passed || false;
    const details = stats?.details;

    return (
        <div className="container animate-fade-in" style={{ paddingBottom: '80px' }}>
            <AddGradeModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                onSave={handleSaveGrade}
                subjects={subjects}
            />

            <div className="card">
                <h2>Gymiprüfung Status 🎓</h2>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <p>Gesamtnote</p>
                        <div style={{
                            fontSize: '3.5rem',
                            fontWeight: '700',
                            color: passed ? 'var(--color-secondary)' : (overallAverage >= 4.0 ? 'var(--color-warning)' : 'var(--color-danger)'),
                            margin: '0'
                        }}>
                            {loading ? '...' : (overallAverage ? overallAverage.toFixed(2) : '--')}
                        </div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                        <span style={{ fontSize: '2.5rem' }}>
                            {passed ? '🎉' : (overallAverage >= 4.5 ? '⚠️' : '🛑')}
                        </span>
                        <div style={{ fontWeight: '600' }}>
                            {passed ? 'BESTANDEN' : 'Noch nicht erreicht'}
                        </div>
                        <small style={{ color: 'var(--color-text-muted)' }}>Ziel: 4.75</small>
                    </div>
                </div>

                {/* Breakdown */}
                {details && (
                    <div style={{ marginTop: '2rem', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                        <div style={{ background: '#f8fafc', padding: '1rem', borderRadius: '8px' }}>
                            <h4 style={{ marginBottom: '0.5rem' }}>Vornote (50%)</h4>
                            <div style={{ fontSize: '1.8rem', fontWeight: 'bold', color: 'var(--color-primary)' }}>
                                {details.vornote.value ? details.vornote.value.toFixed(2) : '-'}
                            </div>
                            <div style={{ marginTop: '0.5rem', fontSize: '0.9rem' }}>
                                <div>Math: <b>{details.vornote.math || '-'}</b></div>
                                <div>Deutsch: <b>{details.vornote.deutsch || '-'}</b></div>
                            </div>
                        </div>
                        <div style={{ background: '#f8fafc', padding: '1rem', borderRadius: '8px' }}>
                            <h4 style={{ marginBottom: '0.5rem' }}>Prüfungsnote (50%)</h4>
                            <div style={{ fontSize: '1.8rem', fontWeight: 'bold', color: 'var(--color-primary)' }}>
                                {details.exam.value ? details.exam.value.toFixed(2) : '-'}
                            </div>

                            {/* Simplified Prediction / Status */}
                            <div style={{ marginTop: '0.5rem', fontSize: '0.9rem', display: 'flex', justifyContent: 'space-between' }}>
                                <div>
                                    Math<br />
                                    <b style={{ fontSize: '1.1rem' }}>{details.exam.math || '?'}</b>
                                </div>
                                <div style={{ textAlign: 'right' }}>
                                    Deutsch<br />
                                    <b style={{ fontSize: '1.1rem' }}>{details.exam.deutsch.value || '?'}</b>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem' }}>
                    <button className="btn btn-primary" onClick={() => setIsModalOpen(true)}>
                        Note eintragen
                    </button>
                    <button className="btn" style={{ background: '#e2e8f0' }} onClick={handleCreateSubject}>
                        + Fach
                    </button>
                </div>
            </div>

            {grades.length > 0 && (
                <div className="card">
                    <h3>📈 Verlauf</h3>
                    <div style={{ width: '100%', height: 200, marginTop: '1rem' }}>
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={grades}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                                <XAxis dataKey="date" hide />
                                <YAxis domain={[1, 6]} hide />
                                <Tooltip
                                    contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                                />
                                <Line
                                    type="monotone"
                                    dataKey="value"
                                    stroke="var(--color-primary)"
                                    strokeWidth={3}
                                    dot={{ fill: 'var(--color-primary)', r: 4 }}
                                    activeDot={{ r: 6 }}
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>

                    <h4 style={{ marginTop: '2rem' }}>Notenliste (letzte 5)</h4>
                    <GradeList
                        grades={grades.slice(0, 5)}
                        subjects={subjects}
                        onDelete={handleDeleteGrade}
                    />

                    {grades.length > 5 && (
                        <button
                            className="btn"
                            style={{ width: '100%', marginTop: '1rem', background: '#f1f5f9' }}
                            onClick={onViewHistory}
                        >
                            Alle anzeigen ({grades.length})
                        </button>
                    )}
                </div>
            )}



            <h3>Deine Fächer</h3>
            {subjects.length === 0 ? (
                <div className="card">
                    <p>Noch keine Fächer erfasst.</p>
                </div>
            ) : (
                <div>
                    {subjects.map(sub => {
                        const subGrades = grades.filter(g => g.subject_id === sub.id);
                        const subAvg = subGrades.length > 0
                            ? (subGrades.reduce((acc, curr) => acc + curr.value, 0) / subGrades.length).toFixed(2)
                            : '-';

                        return (
                            <div
                                key={sub.id}
                                className="card flex-between"
                                style={{ padding: '0.5rem 1rem', display: 'flex', alignItems: 'center' }}
                            >
                                <div
                                    style={{ flex: 1, cursor: 'pointer', padding: '0.5rem 0' }}
                                    onClick={() => onSelectSubject && onSelectSubject(sub)}
                                >
                                    <span style={{ fontWeight: '600', display: 'block' }}>{sub.name}</span>
                                    {subGrades.length > 0 && (
                                        <span style={{ fontSize: '0.9rem', color: '#64748b' }}>
                                            Ø {subAvg}
                                        </span>
                                    )}
                                </div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                                    <span className="badge" style={{
                                        background: '#f1f5f9', padding: '4px 8px', borderRadius: '4px', fontSize: '0.8rem'
                                    }}>x{sub.weighting}</span>
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            handleDeleteSubject(sub.id);
                                        }}
                                        style={{
                                            background: 'none', border: 'none', cursor: 'pointer',
                                            fontSize: '1.2rem', padding: '4px', opacity: 0.6
                                        }}
                                        title="Fach löschen"
                                        onMouseOver={(e) => e.target.style.opacity = 1}
                                        onMouseOut={(e) => e.target.style.opacity = 0.6}
                                    >
                                        🗑️
                                    </button>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
};

export default Dashboard;
