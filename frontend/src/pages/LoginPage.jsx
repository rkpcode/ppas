import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { register as apiRegister } from '../api/auth';
import styles from './LoginPage.module.css';

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [isRegister, setIsRegister] = useState(false);
  const [name, setName] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('Pharmacist');
  const [showPass, setShowPass] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [shake, setShake] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');
    try {
      if (isRegister) {
        try {
          await apiRegister({ name, username, password, role });
          setSuccess('Account created successfully! Logging in...');
        } catch (regErr) {
          if (regErr.message && regErr.message.toLowerCase().includes('already registered')) {
            setSuccess('Username exists, logging in...');
          } else {
            throw regErr;
          }
        }
        await login(username, password);
        navigate('/dashboard');
      } else {
        await login(username, password);
        navigate('/dashboard');
      }
    } catch (err) {
      setError(err.message || (isRegister ? 'Registration failed' : 'Login failed'));
      setShake(true);
      setTimeout(() => setShake(false), 500);
    } finally {
      setLoading(false);
    }
  }


  function toggleMode() {
    setIsRegister(prev => !prev);
    setError('');
    setSuccess('');
  }

  return (
    <div className={styles.page}>
      <div className={styles.bg}>
        <div className={styles.blob1} />
        <div className={styles.blob2} />
      </div>

      <div className={`${styles.card} ${shake ? styles.shake : ''}`}>
        <div className={styles.logoSection}>
          <div className={styles.logoIcon}>💊</div>
          <h1 className={styles.title}>Pradhan Drug House</h1>
          <p className={styles.subtitle}>
            Odisha · {isRegister ? 'Create New Account' : 'Staff Login'}
          </p>
        </div>

        <form onSubmit={handleSubmit} className={styles.form}>
          {isRegister && (
            <div className={styles.field}>
              <label className={styles.label}>Full Name</label>
              <input
                className={styles.input}
                type="text"
                placeholder="Enter full name"
                value={name}
                onChange={e => setName(e.target.value)}
                required
              />
            </div>
          )}

          <div className={styles.field}>
            <label className={styles.label}>Username</label>
            <input
              className={styles.input}
              type="text"
              placeholder="Enter username"
              value={username}
              onChange={e => setUsername(e.target.value)}
              required
              autoComplete="username"
            />
          </div>

          <div className={styles.field}>
            <label className={styles.label}>Password</label>
            <div className={styles.inputWrap}>
              <input
                className={styles.input}
                type={showPass ? 'text' : 'password'}
                placeholder="Enter password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
                autoComplete={isRegister ? 'new-password' : 'current-password'}
              />
              <button
                type="button"
                className={styles.eyeBtn}
                onClick={() => setShowPass(p => !p)}
              >
                {showPass ? '🙈' : '👁'}
              </button>
            </div>
          </div>

          {isRegister && (
            <div className={styles.field}>
              <label className={styles.label}>Role</label>
              <select
                className={styles.input}
                value={role}
                onChange={e => setRole(e.target.value)}
              >
                <option value="Pharmacist">Pharmacist</option>
                <option value="Admin">Admin</option>
                <option value="Staff">Staff</option>
              </select>
            </div>
          )}

          {error && <p className={styles.error}>{error}</p>}
          {success && <p className={styles.success} style={{ color: '#10b981', fontSize: '13px', textAlign: 'center' }}>{success}</p>}

          <button
            type="submit"
            className={styles.loginBtn}
            disabled={loading}
          >
            {loading ? (
              <span className={styles.spinner} />
            ) : isRegister ? (
              'Create Account & Login →'
            ) : (
              'Login to Dashboard →'
            )}
          </button>
        </form>

        <div style={{ textAlign: 'center', marginTop: '16px' }}>
          <button
            type="button"
            onClick={toggleMode}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--primary-glow)',
              cursor: 'pointer',
              fontSize: '13px',
              textDecoration: 'underline',
            }}
          >
            {isRegister
              ? 'Already have an account? Login'
              : 'New staff? Create a new username / account'}
          </button>
        </div>

        <p className={styles.powered}>Powered by NVIDIA AI</p>
      </div>
    </div>
  );
}

