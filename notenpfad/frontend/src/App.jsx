import React, { useState, useEffect } from 'react';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import ScanExam from './pages/ScanExam';
import Simulator from './pages/Simulator';
import SubjectDetail from './pages/SubjectDetail';
import ChatBot from './pages/ChatBot';
import Certificate from './pages/Certificate';
import Profile from './pages/Profile';
import GradeHistory from './pages/GradeHistory';
import Login from './pages/Login';

import Kids from './pages/Kids';

function App() {
  const [user, setUser] = useState(null);
  const [view, setView] = useState('dashboard');
  const [selectedSubject, setSelectedSubject] = useState(null);
  const [viewingChild, setViewingChild] = useState(null);

  useEffect(() => {
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
  }, []);

  const handleLogin = (userData) => {
    setUser(userData);
    localStorage.setItem('user', JSON.stringify(userData));
    setView('dashboard');
  };

  const handleLogout = () => {
    setUser(null);
    setViewingChild(null);
    localStorage.removeItem('user');
    setView('dashboard');
  };

  const handleSelectSubject = (subject) => {
    setSelectedSubject(subject);
    setView('subjectDetail');
  };

  const handleViewChild = (child) => {
    setViewingChild(child);
    setView('dashboard');
  };

  const handleExitChildView = () => {
    setViewingChild(null);
    setView('kids');
  };

  // Determine current student ID (either my own linked student profile, or the child's)
  // If I am a student, I am my own student. If I am parent viewing child, use child's student_id.
  const currentStudentId = viewingChild?.student_profile?.id || user?.student_id || 1;

  const renderView = () => {
    switch (view) {
      case 'dashboard': return <Dashboard studentId={currentStudentId} onSelectSubject={handleSelectSubject} onViewHistory={() => setView('history')} />;
      case 'history': return <GradeHistory studentId={currentStudentId} onBack={() => setView('dashboard')} />;
      case 'simulator': return <Simulator studentId={currentStudentId} />;
      case 'scan': return <ScanExam />;
      case 'chat': return <ChatBot />;
      case 'certificate': return <Certificate studentId={currentStudentId} />;
      case 'profile': return <Profile user={user} onReset={() => setView('dashboard')} onLogout={handleLogout} />;
      case 'kids': return <Kids user={user} onViewChild={handleViewChild} />;
      case 'subjectDetail':
        return <SubjectDetail studentId={currentStudentId} subject={selectedSubject} onBack={() => setView('dashboard')} />;
      default: return <Dashboard studentId={currentStudentId} onSelectSubject={handleSelectSubject} />;
    }
  };

  if (!user) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <Layout currentView={view} setView={setView} user={user}>
      {viewingChild && (
        <div style={{
          background: 'var(--color-secondary)',
          color: 'white',
          padding: '8px',
          textAlign: 'center',
          fontSize: '0.9rem',
          position: 'sticky',
          top: '60px',
          zIndex: 99
        }}>
          👁️ Viewing as <strong>{viewingChild.student_profile?.name || viewingChild.username}</strong>
          <button
            onClick={handleExitChildView}
            style={{ marginLeft: '10px', background: 'rgba(255,255,255,0.2)', border: 'none', color: 'white', borderRadius: '4px', padding: '2px 6px', cursor: 'pointer' }}
          >
            Exit
          </button>
        </div>
      )}
      {renderView()}
    </Layout>
  );
}

export default App;
