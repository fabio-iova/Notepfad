import React, { useState } from 'react';

const API_URL = 'http://127.0.0.1:8000';

const Profile = ({ user, onReset, onLogout }) => {
    const [parentMode, setParentMode] = useState(false);



    const handleCreateStudent = async (e) => {


        e.preventDefault();
        setStudentMessage('');
        try {
            const response = await fetch(`${API_URL}/users/student`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: studentUsername, password: studentPassword })
            });

            if (response.ok) {
                setStudentMessage('Schüler-Account erfolgreich erstellt!');
                setStudentUsername('');
                setStudentPassword('');
            } else {
                const data = await response.json();
                setStudentMessage(`Fehler: ${data.detail || 'Erstellung fehlgeschlagen'}`);
            }
        } catch (error) {
            setStudentMessage('Verbindungsfehler');
        }
    };


    const handleReset = async () => {
        if (!confirm("Möchtest du wirklich alle Daten zurücksetzen?")) return;

        await fetch(`${API_URL}/reset`, { method: 'POST' });
        alert("App wurde zurückgesetzt!");
        if (onReset) onReset();
    };

    return (
        <div className="container animate-fade-in" style={{ paddingBottom: '90px' }}>
            <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
                <div style={{
                    width: '60px', height: '60px',
                    borderRadius: '50%', background: '#e2e8f0',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: '2rem'
                }}>
                    👤
                </div>
                <div>
                    <h2 style={{ margin: 0 }}>{user?.username || 'User'}</h2>
                    <p style={{ margin: 0, color: '#64748b' }}>{user?.role === 'student' ? 'Schüler' : 'Elternteil'}</p>
                </div>
            </div>

            <h3>Einstellungen</h3>
            <div className="card">
                <div className="flex-between" style={{ padding: '10px 0', borderBottom: '1px solid #f1f5f9' }}>
                    <span>Dunkelmodus</span>
                    <span style={{ color: '#94a3b8' }}>(Bald verfügbar)</span>
                </div>
                <div className="flex-between" style={{ padding: '10px 0' }}>
                    <span>Benachrichtigungen</span>
                    <input type="checkbox" checked readOnly />
                </div>
            </div>

            <h3>Demo Zone</h3>
            <div className="card">
                <button
                    className="btn"
                    style={{ background: '#ef4444', color: 'white', fontWeight: 'bold' }}
                    onClick={handleReset}
                >
                    App zurücksetzen (Alle Daten löschen)
                </button>
                <p style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '10px' }}>
                    Setzt alle Noten und Checklisten zurück.
                </p>
            </div>

            {user?.role !== 'student' && (
                <>
                    <h3>Eltern-Bereich</h3>
                    <div className="card">
                        <p>Hier können Eltern Einsicht nehmen.</p>
                        <div className="flex-between" style={{ marginTop: '10px', padding: '10px', background: '#f8fafc', borderRadius: '8px' }}>
                            <span>Eltern-Modus aktivieren</span>
                            <input
                                type="checkbox"
                                checked={parentMode}
                                onChange={(e) => setParentMode(e.target.checked)}
                                style={{ width: '20px', height: '20px', accentColor: 'var(--color-primary)' }}
                            />
                        </div>
                        {parentMode && (
                            <div style={{ marginTop: '1rem', borderTop: '1px solid #e2e8f0', paddingTop: '1rem' }}>
                                <h4 style={{ margin: '0 0 10px 0' }}>📄 Wochenbericht</h4>
                                <p style={{ fontSize: '0.9rem' }}>Status: <strong>Kritisch</strong> (Schnitt unter 4.0)</p>
                                <button className="btn btn-primary" style={{ marginTop: '10px', fontSize: '0.9rem' }}>
                                    Bericht unterschreiben ✍️
                                </button>
                            </div>
                        )}
                    </div>
                </>
            )}

            <button
                className="btn"
                style={{ width: '100%', marginTop: '20px', background: '#ef4444', color: 'white' }}
                onClick={onLogout}
            >
                Ausloggen
            </button>
        </div>
    );
};

export default Profile;
