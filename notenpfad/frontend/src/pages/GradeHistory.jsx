import React, { useState, useEffect } from 'react';
import GradeList from '../components/GradeList';

import { API_BASE_URL as API_URL } from '../config';

const GradeHistory = ({ studentId, onBack }) => {
    const [grades, setGrades] = useState([]);
    const [subjects, setSubjects] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchData();
    }, [studentId]);

    const fetchData = async () => {
        try {
            const token = localStorage.getItem('access_token');
            const headers = { 'Authorization': `Bearer ${token}` };

            const [gradesRes, subjRes] = await Promise.all([
                fetch(`${API_URL}/grades/?student_id=${studentId}`, { headers }),
                fetch(`${API_URL}/subjects/`, { headers })
            ]);

            const gradesData = await gradesRes.json();
            const subjData = await subjRes.json();

            // Sort by date descending (newest first)
            const sortedGrades = gradesData.sort((a, b) => new Date(b.date) - new Date(a.date));

            setGrades(sortedGrades);
            setSubjects(subjData);
        } catch (error) {
            console.error("Error fetching history:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteGrade = async (gradeId) => {
        if (!confirm("Note wirklich löschen?")) return;

        await fetch(`${API_URL}/grades/${gradeId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
        });
        fetchData();
    };

    return (
        <div className="container animate-fade-in" style={{ paddingBottom: '80px' }}>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '1.5rem', gap: '1rem' }}>
                <button
                    onClick={onBack}
                    className="btn"
                    style={{ padding: '0.5rem 1rem', background: '#f1f5f9' }}
                >
                    ← Zurück
                </button>
                <h2 style={{ margin: 0 }}>Notenverlauf</h2>
            </div>

            <div className="card">
                {loading ? (
                    <p>Laden...</p>
                ) : grades.length === 0 ? (
                    <p>Keine Noten vorhanden.</p>
                ) : (
                    <GradeList
                        grades={grades}
                        subjects={subjects}
                        onDelete={handleDeleteGrade}
                    />
                )}
            </div>
        </div>
    );
};

export default GradeHistory;
