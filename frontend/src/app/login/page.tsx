'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { login } from '../../lib/api';

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');
    setLoading(true);

    try {
      const res = await login(username, password);
      // Store token
      localStorage.setItem('token', res.access_token);
      localStorage.setItem('username', username);
      
      // Redirect to Launchpad
      router.push('/');
    } catch (err: any) {
      setErrorMsg(err.message || 'Usuario o contraseña incorrectos');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px',
      background: 'radial-gradient(circle at center, #0a1118 0%, #020406 100%)'
    }}>
      <div style={{
        width: '100%',
        maxWidth: '420px',
        padding: '32px',
        background: 'rgba(10, 15, 20, 0.95)',
        border: '1px solid #1a2b3c',
        borderRadius: '8px',
        boxShadow: '0 8px 32px rgba(0,0,0,0.5), inset 0 0 0 1px rgba(255,255,255,0.05)',
        position: 'relative',
        overflow: 'hidden'
      }}>
        {/* Accent Top Bar */}
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: '3px',
          background: 'linear-gradient(90deg, transparent, var(--mil-blue), transparent)'
        }}></div>

        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <h1 style={{ 
            color: 'var(--text-primary)', 
            fontSize: '1.5rem', 
            fontWeight: '600',
            letterSpacing: '2px',
            marginBottom: '8px',
            textTransform: 'uppercase'
          }}>
            SYSTEM IDENTIFICATION
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', letterSpacing: '1px' }}>
            RESTRICTED ACCESS AREA
          </p>
        </div>

        <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div>
            <label style={{ 
              display: 'block', 
              fontSize: '0.75rem', 
              color: 'var(--text-muted)', 
              marginBottom: '8px',
              letterSpacing: '1px'
            }}>
              OPERATIVE ID
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              className="mil-input"
              style={{
                width: '100%',
                padding: '12px 16px',
                background: '#04070a',
                border: '1px solid #1a2b3c',
                color: '#fff',
                fontSize: '1rem',
                borderRadius: '4px',
                fontFamily: 'monospace'
              }}
              placeholder="Enter User ID"
            />
          </div>

          <div>
            <label style={{ 
              display: 'block', 
              fontSize: '0.75rem', 
              color: 'var(--text-muted)', 
              marginBottom: '8px',
              letterSpacing: '1px'
            }}>
              AUTHORIZATION KEY
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="mil-input"
              style={{
                width: '100%',
                padding: '12px 16px',
                background: '#04070a',
                border: '1px solid #1a2b3c',
                color: '#fff',
                fontSize: '1rem',
                borderRadius: '4px',
                fontFamily: 'monospace',
                letterSpacing: '3px'
              }}
              placeholder="••••••••"
            />
          </div>

          {errorMsg && (
            <div style={{ 
              color: '#ff4444', 
              background: 'rgba(255, 68, 68, 0.1)',
              border: '1px solid rgba(255, 68, 68, 0.2)',
              padding: '10px',
              borderRadius: '4px',
              fontSize: '0.85rem',
              textAlign: 'center',
              marginTop: '4px'
            }}>
              {errorMsg}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              marginTop: '12px',
              padding: '14px',
              background: loading ? '#1a2b3c' : 'var(--mil-blue)',
              color: '#fff',
              border: 'none',
              borderRadius: '4px',
              fontWeight: '600',
              letterSpacing: '2px',
              cursor: loading ? 'wait' : 'pointer',
              transition: 'background 0.2s',
              fontSize: '0.9rem'
            }}
          >
            {loading ? 'AUTHENTICATING...' : 'ESTABLISH LINK'}
          </button>
        </form>

        <div style={{ 
          marginTop: '32px', 
          textAlign: 'center', 
          fontSize: '0.7rem', 
          color: 'var(--text-muted)',
          opacity: 0.5 
        }}>
          UNAUTHORIZED ACCESS IS PROHIBITED
        </div>
      </div>
    </div>
  );
}
