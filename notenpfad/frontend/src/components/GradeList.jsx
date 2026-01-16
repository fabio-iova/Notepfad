import React from 'react';

const GradeList = ({ grades, subjects, onDelete }) => {
    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {grades.map(g => {
                const params = subjects.find(s => s.id === g.subject_id);
                return (
                    <div key={g.id} style={{
                        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                        padding: '0.75rem', background: '#f8fafc', borderRadius: '8px'
                    }}>
                        <div>
                            <div style={{ fontWeight: '600' }}>{params ? params.name : 'Fach'}</div>
                            <div style={{ fontSize: '0.85rem', color: '#64748b' }}>
                                {g.type} • {new Date(g.date).toLocaleDateString()}
                            </div>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                            <span style={{ fontWeight: 'bold', fontSize: '1.1rem' }}>{g.value}</span>
                            <button
                                onClick={() => onDelete(g.id)}
                                style={{
                                    background: 'none', border: 'none', cursor: 'pointer',
                                    fontSize: '1.2rem', padding: '4px'
                                }}
                                title="Löschen"
                            >
                                🗑️
                            </button>
                        </div>
                    </div>
                );
            })}
        </div>
    );
};

export default GradeList;
