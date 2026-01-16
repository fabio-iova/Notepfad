import React, { useState, useEffect } from 'react';

const API_URL = 'http://127.0.0.1:8000';

const Kids = ({ user, onViewChild }) => {
    const [children, setChildren] = useState([]);
    const [showAddForm, setShowAddForm] = useState(false);
    const [newChildName, setNewChildName] = useState('');
    const [newChildUsername, setNewChildUsername] = useState('');
    const [newChildPassword, setNewChildPassword] = useState('');
    const [showPasswordModal, setShowPasswordModal] = useState(false);
    const [selectedChild, setSelectedChild] = useState(null);
    const [childToDelete, setChildToDelete] = useState(null);
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
    const [newPasswordUpdate, setNewPasswordUpdate] = useState('');
    const [error, setError] = useState('');

    useEffect(() => {
        fetchChildren();
    }, [user]);

    const fetchChildren = async () => {
        try {
            const userId = user.id || user.user_id;
            const response = await fetch(`${API_URL}/users/${userId}/children`);
            if (response.ok) {
                const data = await response.json();
                setChildren(data);
            }
        } catch (err) {
            console.error("Failed to fetch children", err);
        }
    };

    const handleAddChild = async (e) => {
        e.preventDefault();
        setError('');
        const userId = user.id || user.user_id;
        try {
            const response = await fetch(`${API_URL}/users/children`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    username: newChildUsername,
                    password: newChildPassword,
                    name: newChildName,
                    parent_id: userId
                })
            });

            if (response.ok) {
                setShowAddForm(false);
                setNewChildName('');
                setNewChildUsername('');
                setNewChildPassword('');
                fetchChildren();
            } else {
                const data = await response.json();
                setError(data.detail || 'Fehler beim Erstellen');
            }
        } catch (err) {
            setError('Verbindungsfehler');
        }
    };

    const openPasswordModal = (child, e) => {
        e.stopPropagation();
        setSelectedChild(child);
        setNewPasswordUpdate('');
        setShowPasswordModal(true);
        setError('');
    };

    const handleUpdatePassword = async (e) => {
        e.preventDefault();
        if (!selectedChild) return;

        try {
            const response = await fetch(`${API_URL}/users/${selectedChild.id}/password`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    password: newPasswordUpdate
                })
            });

            if (response.ok) {
                setShowPasswordModal(false);
                setNewPasswordUpdate('');
                setSelectedChild(null);
                alert("Passwort erfolgreich geändert!");
            } else {
                const data = await response.json();
                setError(data.detail || 'Fehler beim Ändern');
            }
        } catch (err) {
            setError('Verbindungsfehler');
        }
    };

    const confirmDeleteChild = (child, e) => {
        e.stopPropagation();
        setChildToDelete(child);
        setShowDeleteConfirm(true);
    };

    const handleDeleteChild = async () => {
        if (!childToDelete) return;
        try {
            const response = await fetch(`${API_URL}/users/children/${childToDelete.id}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                setShowDeleteConfirm(false);
                setChildToDelete(null);
                fetchChildren(); // Refund list
            } else {
                setError('Fehler beim Löschen');
            }
        } catch (err) {
            setError('Verbindungsfehler beim Löschen');
        }
    };

    return (
        <div className="container animate-fade-in" style={{ paddingBottom: '90px' }}>
            <div className="header-section">
                <h2>Meine Kinder 👨‍👩‍👧‍👦</h2>
                <button
                    className="btn btn-primary"
                    onClick={() => setShowAddForm(!showAddForm)}
                    style={{ fontSize: '0.9rem', padding: '8px 12px' }}
                >
                    {showAddForm ? 'Abbrechen' : '+ Kind hinzufügen'}
                </button>
            </div>

            {showAddForm && (
                <div className="card animate-fade-in">
                    <h3 style={{ marginTop: 0 }}>Neues Kind erfassen</h3>
                    <form onSubmit={handleAddChild}>
                        <div className="form-group">
                            <label>Name (Anzeigename)</label>
                            <input
                                type="text"
                                value={newChildName}
                                onChange={(e) => setNewChildName(e.target.value)}
                                required
                                placeholder="z.B. Hans"
                            />
                        </div>
                        <div className="form-group">
                            <label>Benutzername (Login)</label>
                            <input
                                type="text"
                                value={newChildUsername}
                                onChange={(e) => setNewChildUsername(e.target.value)}
                                required
                                placeholder="z.B. hans123"
                            />
                        </div>
                        <div className="form-group">
                            <label>Passwort</label>
                            <input
                                type="password"
                                value={newChildPassword}
                                onChange={(e) => setNewChildPassword(e.target.value)}
                                required
                            />
                        </div>
                        {error && <p style={{ color: 'red' }}>{error}</p>}
                        <button type="submit" className="btn" style={{ width: '100%', background: 'var(--color-primary)', color: 'white' }}>
                            Speichern
                        </button>
                    </form>
                </div>
            )}

            {showPasswordModal && (
                <div className="modal-overlay">
                    <div className="card animate-fade-in" style={{ maxWidth: '400px', margin: '0 auto' }}>
                        <h3 style={{ marginTop: 0 }}>Passwort ändern für {selectedChild?.username}</h3>
                        <form onSubmit={handleUpdatePassword}>
                            <div className="form-group">
                                <label>Neues Passwort</label>
                                <input
                                    type="password"
                                    value={newPasswordUpdate}
                                    onChange={(e) => setNewPasswordUpdate(e.target.value)}
                                    required
                                    placeholder="Neues Passwort"
                                />
                            </div>
                            {error && <p style={{ color: 'red' }}>{error}</p>}
                            <div style={{ display: 'flex', gap: '10px' }}>
                                <button
                                    type="button"
                                    className="btn"
                                    onClick={() => setShowPasswordModal(false)}
                                    style={{ flex: 1, background: '#ccc' }}
                                >
                                    Abbrechen
                                </button>
                                <button type="submit" className="btn btn-primary" style={{ flex: 1 }}>
                                    Ändern
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {showDeleteConfirm && (
                <div className="modal-overlay">
                    <div className="card animate-fade-in" style={{ maxWidth: '400px', margin: '0 auto', textAlign: 'center' }}>
                        <h3 style={{ marginTop: 0, color: 'var(--color-danger, #ef4444)' }}>Kind löschen?</h3>
                        <p>Bist du sicher, dass du <strong>{childToDelete?.username}</strong> löschen möchtest? Alle Noten gehen verloren.</p>
                        <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
                            <button
                                className="btn"
                                onClick={() => setShowDeleteConfirm(false)}
                                style={{ flex: 1, background: '#ccc' }}
                            >
                                Abbrechen
                            </button>
                            <button
                                className="btn"
                                onClick={handleDeleteChild}
                                style={{ flex: 1, background: 'var(--color-danger, #ef4444)', color: 'white' }}
                            >
                                Ja, löschen
                            </button>
                        </div>
                    </div>
                </div>
            )}

            <div className="children-list">
                {children.length === 0 && !showAddForm && (
                    <p style={{ textAlign: 'center', color: '#64748b', marginTop: '2rem' }}>
                        Noch keine Kinder erfasst.
                    </p>
                )}

                {children.map(child => (
                    <div key={child.id} className="card child-card" onClick={() => onViewChild(child)}>
                        <div className="child-avatar">
                            👤
                        </div>
                        <div className="child-info">
                            <h3>{child.student_profile?.name || child.username}</h3>
                            <p>Klicke um Noten anzusehen</p>
                        </div>
                        <button
                            className="btn-icon"
                            onClick={(e) => openPasswordModal(child, e)}
                            style={{
                                background: 'none',
                                border: 'none',
                                fontSize: '1.2rem',
                                cursor: 'pointer',
                                marginRight: '5px',
                                padding: '5px'
                            }}
                            title="Passwort ändern"
                        >
                            🔑
                        </button>
                        <button
                            className="btn-icon"
                            onClick={(e) => confirmDeleteChild(child, e)}
                            style={{
                                background: 'none',
                                border: 'none',
                                fontSize: '1.2rem',
                                cursor: 'pointer',
                                padding: '5px'
                            }}
                            title="Löschen"
                        >
                            🗑️
                        </button>
                        <div className="child-action" style={{ marginLeft: '10px' }}>
                            👉
                        </div>
                    </div>
                ))}
            </div>

            <style>{`
                .header-section {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 20px;
                }
                .child-card {
                    display: flex;
                    align-items: center;
                    gap: 15px;
                    cursor: pointer;
                    transition: transform 0.2s;
                }
                .child-card:active {
                    transform: scale(0.98);
                }
                .child-avatar {
                    width: 50px;
                    height: 50px;
                    background: #e0f2fe;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 1.5rem;
                }
                .child-info h3 {
                    margin: 0;
                    font-size: 1.1rem;
                }
                .child-info p {
                    margin: 2px 0 0 0;
                    font-size: 0.85rem;
                    color: #64748b;
                }
                .child-action {
                    margin-left: auto;
                    font-size: 1.2rem;
                }
                .modal-overlay {
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(0,0,0,0.5);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 1000;
                    padding: 20px;
                }
            `}</style>
        </div>
    );
};

export default Kids;
