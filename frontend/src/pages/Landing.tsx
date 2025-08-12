
import React, { useState, useEffect } from 'react';
import './landing.css';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';


export default function Landing() {
  const [modal, setModal] = useState(null); // 'login' | 'register' | null
  const [input, setInput] = useState('');
  const [role, setRole] = useState('user');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [error, setError] = useState('');
  const location = useLocation();
  const navigate = useNavigate();
  const { login, user, isAuthenticated } = useAuth();

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated && user) {
      let redirectPath = '/user-dashboard'; // default for user role
      
      if (user.role === 'admin') {
        redirectPath = '/dashboard';
      } else if (user.role === 'widget-admin') {
        redirectPath = '/admin-dashboard';
      }
      
      navigate(redirectPath);
    }
  }, [isAuthenticated, user, navigate]);




  const openModal = (type) => {
    setError('');
    setRole('user');
    setEmail('');
    setPassword('');
    setName('');
    setModal(type);
  };


  const closeModal = () => {
    setModal(null);
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (!email || !password || (modal === 'register' && !name)) {
      setError('Please fill all fields.');
      return;
    }
    // Always send a valid role (default to 'user' if empty or invalid)
    let safeRole = role && typeof role === 'string' && role.trim() !== '' ? role : 'user';
    try {
      if (modal === 'login') {
        const success = await login(email, password, safeRole);
        if (success) {
          setError('');
          closeModal();
          // Navigation will be handled by useEffect above
        } else {
          setError('Login failed. Please check your credentials.');
        }
      } else if (modal === 'register') {
        const res = await fetch('http://localhost:8004/api/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, email, password, role: safeRole })
        });
        if (!res.ok) {
          const data = await res.json().catch(() => ({}));
          setError(data.detail || 'Registration failed.');
          return;
        }
        const data = await res.json();
        setError('Registration successful! Please login.');
        // Switch to login modal
        setModal('login');
        setPassword(''); // Clear password for security
      }
    } catch (err) {
      setError('Network error. Please try again.');
    }
  };

  return (
    <div className="landing-container">
      {/* Nav */}
      <header className="nav-bar">
        <div className="nav-logo">DevLaunch</div>
        <div className="nav-actions">
          <button className="main-btn" onClick={() => openModal('login')}>Login / Register</button>
        </div>
      </header>

      {/* Hero */}
      <main className="hero">
        <div className="badge">🚀 AI-Powered Platform</div>
        <h1 className="hero-title">
          The Future of <span className="gradient-text">Development</span>
        </h1>
        <p className="hero-subtitle">
          Experience zero-touch automation with AI that understands your intent.<br />
          Navigate, create, and manage with natural language commands.
        </p>

        {/* Input Box */}
        <form className="input-form" onSubmit={handleSubmit}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="e.g. Open settings, deploy project..."
            className="landing-input"
          />
          <button type="submit" className="input-submit">Go</button>
        </form>

        {/* CTA Buttons */}
        <div className="hero-buttons">
          <button className="main-btn">Start Building</button>
          <button className="secondary-btn">View Documentation</button>
        </div>

        {/* Features */}
        <section className="features">
          <div className="feature-card">
            <h3>Zero-Touch Navigation</h3>
            <p>AI understands your commands and navigates instantly.</p>
          </div>
          <div className="feature-card">
            <h3>Intelligent Interface</h3>
            <p>Modern development environment with smart automation.</p>
          </div>
          <div className="feature-card">
            <h3>Enterprise Ready</h3>
            <p>Built for scale with enterprise-grade security.</p>
          </div>
          <div className="feature-card">
            <h3>Secure by Design</h3>
            <p>Advanced security features and compliance standards.</p>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="footer">
        &copy; 2025 DevLaunch. Built with modern tech and AI.
      </footer>

      {/* Modern Modal */}
      {modal && (
        <div className="modal-backdrop smart-modal">
          <div className="modal-box modern-modal">
            <button className="close-btn" onClick={closeModal}>&times;</button>
            <h2 className="modal-title">{modal === 'login' ? 'Welcome Back' : 'Create Your Account'}</h2>
            <form className="modal-form" onSubmit={handleSubmit}>
              {modal === 'register' && (
                <input
                  type="text"
                  placeholder="Full Name"
                  value={name}
                  onChange={e => setName(e.target.value)}
                  className="modal-input"
                  required
                  autoFocus
                />
              )}
              <input
                type="email"
                placeholder="Email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                className="modal-input"
                required
                autoFocus={modal === 'login'}
              />
              <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                className="modal-input"
                required
              />
              <div className="role-select-row">
                <label htmlFor="role-select">Role:</label>
                <select
                  id="role-select"
                  value={role}
                  onChange={e => setRole(e.target.value)}
                  className="role-select"
                >
                  <option value="user">User</option>
                  <option value="admin">Admin</option>
                  <option value="widget-admin">Widget Admin</option>
                </select>
              </div>
              {error && <div className="modal-error">{error}</div>}
              <button type="submit" className="main-btn modal-action-btn">{modal === 'login' ? 'Login' : 'Register'}</button>
            </form>
            <div className="modal-footer">
              {modal === 'login' ? (
                <span>New here? <button className="modal-link" onClick={() => openModal('register')}>Register</button></span>
              ) : (
                <span>Already have an account? <button className="modal-link" onClick={() => openModal('login')}>Login</button></span>
              )}
            </div>
          </div>
        </div>
      )}
      {/* Modern Modal Styles */}
      <style>{`
        .smart-modal {
          backdrop-filter: blur(6px) brightness(0.7);
          background: rgba(30, 30, 40, 0.45);
        }
        .modern-modal {
          border-radius: 22px;
          box-shadow: 0 8px 40px 0 rgba(80, 0, 180, 0.18), 0 1.5px 8px 0 rgba(0,0,0,0.12);
          background: linear-gradient(135deg, #23233b 80%, #3a1c5d 100%);
          border: 1.5px solid #a18aff33;
          padding: 2.5rem 2.5rem 1.5rem 2.5rem;
          min-width: 350px;
          max-width: 95vw;
          color: #fff;
          position: relative;
          animation: modalPop 0.25s cubic-bezier(.4,2,.6,1) 1;
        }
        @keyframes modalPop {
          0% { transform: scale(0.92) translateY(30px); opacity: 0; }
          100% { transform: scale(1) translateY(0); opacity: 1; }
        }
        .modal-title {
          font-size: 2rem;
          font-weight: 700;
          margin-bottom: 1.2rem;
          text-align: center;
        }
        .modal-form {
          display: flex;
          flex-direction: column;
          gap: 1.1rem;
        }
        .modal-input {
          border-radius: 8px;
          border: 1.5px solid #a18aff44;
          background: #23233b;
          color: #fff;
          padding: 0.85rem 1.1rem;
          font-size: 1.08rem;
          outline: none;
          transition: border 0.2s;
        }
        .modal-input:focus {
          border: 1.5px solid #a18aff;
        }
        .role-select-row {
          display: flex;
          align-items: center;
          gap: 0.7rem;
          margin-bottom: 0.2rem;
        }
        .role-select {
          border-radius: 6px;
          border: 1.5px solid #a18aff44;
          background: #23233b;
          color: #fff;
          padding: 0.5rem 1rem;
          font-size: 1rem;
        }
        .modal-error {
          background: #ff4d4f22;
          color: #ff4d4f;
          border-radius: 6px;
          padding: 0.5rem 1rem;
          margin-bottom: 0.5rem;
          text-align: center;
          font-size: 1rem;
        }
        .modal-action-btn {
          margin-top: 0.5rem;
          font-size: 1.1rem;
          font-weight: 600;
          background: linear-gradient(90deg, #a18aff 0%, #7f5fff 100%);
          color: #fff;
          border: none;
          border-radius: 8px;
          box-shadow: 0 2px 8px 0 #a18aff33;
        }
        .modal-footer {
          margin-top: 1.2rem;
          text-align: center;
          color: #bbb;
        }
        .modal-link {
          background: none;
          border: none;
          color: #a18aff;
          font-weight: 600;
          cursor: pointer;
          text-decoration: underline;
          font-size: 1rem;
        }
        .close-btn {
          position: absolute;
          top: 1.1rem;
          right: 1.1rem;
          background: none;
          border: none;
          color: #fff;
          font-size: 1.7rem;
          cursor: pointer;
          opacity: 0.7;
          transition: opacity 0.2s;
        }
        .close-btn:hover {
          opacity: 1;
        }
      `}</style>
    </div>
  );
}
