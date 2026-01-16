import React, { useState } from 'react';

const Login = ({ onLogin }) => {
    const [isRegistering, setIsRegistering] = useState(false);
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [accessCode, setAccessCode] = useState('');
    const [error, setError] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');

        if (isRegistering && accessCode !== '9999') {
            setError('Invalid access code. Account creation restricted.');
            return;
        }

        const endpoint = isRegistering ? '/register' : '/login';

        try {
            const response = await fetch(`http://127.0.0.1:8000${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username, password }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Authentication failed');
            }

            // If registering, we might auto-login or ask to login.
            // For simplicity/UX, let's treat registration as immediate login if backend returns user details,
            // but the backend /register endpoint returns UserOut, while /login returns { message, user_id, username }.
            // Let's adjust based on what we get.

            if (isRegistering) {
                // After registration, we can either auto-login or switch to login mode.
                // Let's switch to login mode with a success message or just auto login if we want to be fancy.
                // For now: Switch to login mode and pre-fill (already filled).
                // Actually, let's just create a new login request or say "Registration successful, please login".
                // Let's go with "Registration successful, please login" for clarity.
                setIsRegistering(false);
                setError('Account created! You can now log in.'); // Using error state for info message temporarily or add success state.
                return;
            }

            // Login success
            onLogin(data);

        } catch (err) {
            setError(err.message);
        }
    };

    return (
        <div className="login-container">
            <div className="login-card">
                <h1>Notenpfad</h1>
                <h2>{isRegistering ? 'Create Account' : 'Welcome Back'}</h2>

                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label>Username</label>
                        <input
                            type="text"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            required
                        />
                    </div>

                    <div className="form-group">
                        <label>Password</label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                        />
                    </div>

                    {isRegistering && (
                        <div className="form-group">
                            <label>Access Code</label>
                            <input
                                type="text"
                                value={accessCode}
                                onChange={(e) => setAccessCode(e.target.value)}
                                placeholder="Code"
                                required
                            />
                        </div>
                    )}

                    {error && <p className="error-message">{error}</p>}

                    <button type="submit" className="primary-btn">
                        {isRegistering ? 'Sign Up' : 'Login'}
                    </button>
                </form>

                <p className="toggle-auth">
                    {isRegistering ? 'Already have an account?' : 'Need an account?'}
                    <button
                        type="button"
                        className="link-btn"
                        onClick={() => {
                            setIsRegistering(!isRegistering);
                            setError('');
                        }}
                    >
                        {isRegistering ? 'Login' : 'Create Account'}
                    </button>
                </p>
            </div>
        </div>
    );
};

export default Login;
