import React, { useState } from 'react';
import './Register.css';
import { FaEnvelope, FaLock } from 'react-icons/fa';
import { useNavigate } from 'react-router-dom';

export default function Register() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!name || !email || !password || !confirm) {
      setError('Please fill all fields.');
      return;
    }

    if (password !== confirm) {
      setError('Passwords do not match.');
      return;
    }

    try {
      const res = await fetch('http://localhost:8000/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, password }),
      });

      const data = await res.json();

      if (res.ok) {
        alert('✅ Registered! Now login.');
        navigate('/login');
      } else {
        setError(data.detail || 'Registration failed.');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    }
  };

  const Logo = () => (
    <div className="login-logo">
      <i className="bx bx-user-circle" style={{ fontSize: 36, color: '#1DA1F2' }}></i>
    </div>
  );

  const WelcomeMessage = () => (
    <>
      <h2 className="login-title">Create your BirdAI account</h2>
      <p className="login-subtext">Register to access your dashboard and tools.</p>
    </>
  );

  const Benefits = () => (
    <ul className="login-benefits">
      <li><FaLock /> Secure, encrypted user access</li>
      <li><FaEnvelope /> Email-based account verification</li>
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
          <form onSubmit={handleRegister} className="login-form">
            <div className="login-form-group">
              <label>Name</label>
              <div className="input-icon-wrapper">
                <i className="bx bx-user icon" style={{ fontSize: 18 }}></i>
                <input
                  type="text"
                  value={name}
                  onChange={e => setName(e.target.value)}
                  placeholder="Enter your name"
                />
              </div>
            </div>

            <div className="login-form-group">
              <label>Email</label>
              <div className="input-icon-wrapper">
                <i className="bx bx-envelope icon" style={{ fontSize: 18 }}></i>
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
                <i className="bx bx-lock icon" style={{ fontSize: 18 }}></i>
                <input
                  type="password"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="Enter your password"
                />
              </div>
            </div>

            <div className="login-form-group">
              <label>Confirm Password</label>
              <div className="input-icon-wrapper">
                <i className="bx bx-lock icon" style={{ fontSize: 18 }}></i>
                <input
                  type="password"
                  value={confirm}
                  onChange={e => setConfirm(e.target.value)}
                  placeholder="Confirm your password"
                />
              </div>
            </div>

            <button className="login-btn" type="submit">Register</button>
          </form>

          <div className="login-footer">
            <a href="/login">Already have an account? Login</a>
          </div>
        </div>
      </div>
    </div>
  );
}
