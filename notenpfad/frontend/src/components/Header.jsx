import React from 'react';

const Header = ({ user }) => {
    return (
        <header className="app-header">
            <div className="container flex-between" style={{ height: 'var(--header-height)' }}>
                <h1 style={{ fontSize: '1.5rem', color: 'var(--color-primary)' }}>Notenpfad</h1>
                <div className="user-avatar" style={{
                    width: '32px', height: '32px', borderRadius: '50%', backgroundColor: '#e2e8f0', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.2rem'
                }}>
                    {user?.role === 'student' ? '👦' : '👤'}
                </div>
            </div>
        </header>
    );
};

export default Header;
