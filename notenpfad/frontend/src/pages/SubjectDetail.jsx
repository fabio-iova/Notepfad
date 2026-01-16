import React, { useState, useEffect } from 'react';

const API_URL = 'http://localhost:8000';

const SubjectDetail = ({ studentId, subject, onBack }) => {
    const [topics, setTopics] = useState([]);
    const [newTopic, setNewTopic] = useState('');
    const [subjectGrades, setSubjectGrades] = useState([]);

    useEffect(() => {
        fetchTopics();
        fetchGrades();
    }, [subject.id, studentId]);

    const fetchTopics = async () => {
        const res = await fetch(`${API_URL}/subjects/${subject.id}/topics`);
        const data = await res.json();
        setTopics(data);
    };

    const fetchGrades = async () => {
        // Fetch all grades and filter (inefficient but simple for demo)
        // Or adding a specific endpoint would be better, but sticking to existing pattern
        const res = await fetch(`${API_URL}/grades/?student_id=${studentId}`);
        const data = await res.json();
        setSubjectGrades(data.filter(g => g.subject_id === subject.id));
    };

    const handleAddTopic = async () => {
        if (!newTopic.trim()) return;
        await fetch(`${API_URL}/topics/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: newTopic, subject_id: subject.id, is_completed: false })
        });
        setNewTopic('');
        fetchTopics();
    };

    const handleToggleTopic = async (topic) => {
        await fetch(`${API_URL}/topics/${topic.id}/toggle`, {
            method: 'PUT'
        });
        fetchTopics();
    };

    return (
        <div className="container animate-fade-in" style={{ paddingBottom: '80px' }}>
            <div style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', cursor: 'pointer', color: 'var(--color-primary)' }} onClick={onBack}>
                <span>← Zurück</span>
            </div>

            <div className="card">
                <h2>{subject.name} <span style={{ fontSize: '0.6em', color: 'var(--color-text-muted)', fontWeight: 'normal' }}>(x{subject.weighting})</span></h2>
            </div>

            <h3>✅ Lern-Checkliste</h3>
            <div className="card">
                {topics.length === 0 && <p>Keine Themen eingetragen.</p>}

                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '1rem' }}>
                    {topics.map(topic => (
                        <div key={topic.id} style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                            <input
                                type="checkbox"
                                checked={topic.is_completed}
                                onChange={() => handleToggleTopic(topic)}
                                style={{ width: '20px', height: '20px', accentColor: 'var(--color-primary)' }}
                            />
                            <span style={{
                                textDecoration: topic.is_completed ? 'line-through' : 'none',
                                color: topic.is_completed ? 'var(--color-text-muted)' : 'inherit'
                            }}>
                                {topic.name}
                            </span>
                        </div>
                    ))}
                </div>

                <div style={{ display: 'flex', gap: '8px' }}>
                    <input
                        type="text"
                        value={newTopic}
                        onChange={(e) => setNewTopic(e.target.value)}
                        placeholder="Neues Thema (z.B. Bruchrechnen)"
                        style={{
                            flex: 1, padding: '8px 12px', borderRadius: '8px', border: '1px solid var(--color-border)', fontSize: '1rem'
                        }}
                    />
                    <button className="btn btn-primary" style={{ width: 'auto' }} onClick={handleAddTopic}>+</button>
                </div>
            </div>

            <h3>📊 Noten in diesem Fach</h3>
            <div className="card">
                {subjectGrades.length === 0 ? <p>Keine Noten.</p> : (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
                        {subjectGrades.map(g => (
                            <div key={g.id} style={{
                                background: '#f1f5f9',
                                padding: '8px 16px',
                                borderRadius: '12px',
                                fontWeight: 'bold',
                                color: g.value >= 4 ? 'var(--color-secondary)' : 'var(--color-danger)'
                            }}>
                                {g.value}
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default SubjectDetail;
