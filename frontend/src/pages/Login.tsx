import React, { useState } from 'react';
import './Login.css';
import { FaEnvelope, FaLock, FaBolt, FaChartLine } from 'react-icons/fa';
import { useNavigate } from 'react-router-dom';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [role, setRole] = useState('admin');
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (!email || !password) {
      setError('Please enter both email and password.');
      return;
    }
    setLoading(true);
    // Simulate login API
    setTimeout(() => {
      setLoading(false);
      if (role === 'admin') {
        navigate('/dashboard');
      } else {
        navigate('/user-dashboard');
      }
    }, 1000);
  };

  const Logo = () => (
    <div className="login-logo">
      <FaChartLine size={48} color="#1DA1F2" />
    </div>
  );

  const WelcomeMessage = () => (
    <>
      <h2 className="login-title">Welcome back to BirdAI</h2>
      <p className="login-subtext">Sign in to manage your conversations, models, and dashboards.</p>
    </>
  );

  const Benefits = () => (
    <ul className="login-benefits">
      <li><FaBolt /> Fast and intelligent AI support</li>
      <li><FaLock /> Secure, encrypted user access</li>
      <li><FaChartLine /> Real-time analytics dashboard</li>
    </ul>
  );

  return (
    <div className="login-cover">
      <div className="login-left-panel">
        <Logo />
        <h1 className="brand-name">BirdAI</h1>
        <p className="brand-tagline">Powering smart conversations with AI.</p>
        <Benefits />
      </div>

      <div className="login-right-panel">
        <div className="login-card">
          <Logo />
          <WelcomeMessage />
          {error && <div className="login-error">{error}</div>}
          <form onSubmit={handleLogin} className="login-form">
            <div className="login-form-group">
              <label>Email</label>
              <div className="input-icon-wrapper">
                <FaEnvelope className="icon" />
                <input
                  type="email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="Enter your email"
                />
              </div>
            </div>

            <div className="login-form-group">
              <label>Password</label>
              <div className="input-icon-wrapper">
                <FaLock className="icon" />
                <input
                  type="password"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="Enter your password"
                />
              </div>
            </div>

            <div style={{ margin: '16px 0' }}>
              <label>
                <input
                  type="radio"
                  name="role"
                  value="admin"
                  checked={role === 'admin'}
                  onChange={() => setRole('admin')}
                /> Admin
              </label>
              <label style={{ marginLeft: 16 }}>
                <input
                  type="radio"
                  name="role"
                  value="user"
                  checked={role === 'user'}
                  onChange={() => setRole('user')}
                /> User
              </label>
            </div>

            <button className="login-btn" type="submit" disabled={loading}>
              {loading ? 'Signing in...' : 'Login'}
            </button>
          </form>
          <div className="login-footer">
            <a href="/register">Don't have an account? Register</a>
          </div>
        </div>
      </div>
    </div>
  );
}
