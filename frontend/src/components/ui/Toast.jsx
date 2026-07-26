import styles from './Toast.module.css';

export function ToastContainer({ toasts }) {
  return (
    <div className={styles.container}>
      {toasts.map(t => (
        <div key={t.id} className={`${styles.toast} ${styles[t.type]}`}>
          <span className={styles.icon}>
            {t.type === 'success' ? '✓' : t.type === 'error' ? '✕' : 'ℹ'}
          </span>
          {t.message}
        </div>
      ))}
    </div>
  );
}
