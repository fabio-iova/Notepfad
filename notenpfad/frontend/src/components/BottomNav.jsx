import React from 'react';
// We'll replace these with Lucide icons later
const BottomNav = ({ activeView, setView, user }) => {
    return (
        <nav className="bottom-nav">
            <div
                className={`nav-item ${activeView === 'dashboard' ? 'active' : ''}`}
                onClick={() => setView('dashboard')}
            >
                <span>🏠</span>
                <small>Home</small>
            </div>
            <div
                className={`nav-item ${activeView === 'simulator' ? 'active' : ''}`}
                onClick={() => setView('simulator')}
            >
                <span>🔮</span>
                <small>Simu</small>
            </div>
            <div className="nav-item" onClick={() => setView('scan')} style={{
                transform: 'translateY(-20px)',
                background: 'var(--color-primary)',
                borderRadius: '50%',
                padding: '12px',
                boxShadow: 'var(--shadow-md)',
                color: 'white',
                border: '4px solid #f8fafc'
            }}>
                📷
            </div>
            <div className="nav-item" onClick={() => setView('chat')}>
                <div className="icon">🤖</div>
                <span>AI</span>
            </div>
            <div
                className={`nav-item ${activeView === 'certificate' ? 'active' : ''}`}
                onClick={() => setView('certificate')}
            >
                <span>📜</span>
                <small>Zeugnis</small>
            </div>
            {user?.role === 'parent' && (
                <div
                    className={`nav-item ${activeView === 'kids' ? 'active' : ''}`}
                    onClick={() => setView('kids')}
                >
                    <span>👶</span>
                    <small>Kids</small>
                </div>
            )}
            <div className={`nav-item ${activeView === 'profile' ? 'active' : ''}`} onClick={() => setView('profile')}>
                <span>⚙️</span>
                <small>Profile</small>
            </div>
        </nav>
    );
};

export default BottomNav;
