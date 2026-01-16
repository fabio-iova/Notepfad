import React from 'react';
import Header from './Header';
import BottomNav from './BottomNav';

const Layout = ({ children, currentView, setView, user }) => {
    return (
        <div className="layout">
            <Header user={user} />
            <main className="main-content">
                {children}
            </main>
            <BottomNav activeView={currentView} setView={setView} user={user} />
        </div>
    );
};

export default Layout;
