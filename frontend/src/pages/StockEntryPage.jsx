import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { parseReceipt, parseStockVoice, confirmBulkStock } from '../api/stock';
import { useVoiceRecorder } from '../hooks/useVoiceRecorder';
import { useToast } from '../hooks/useToast';
import { ToastContainer } from '../components/ui/Toast';
import styles from './StockEntryPage.module.css';

function ReceiptTab() {
  const [parsing, setParsing] = useState(false);
  const [items, setItems] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const fileInputRef = useRef(null);
  const { toasts, error, success } = useToast();
  const navigate = useNavigate();

  async function handleFileChange(e) {
    const file = e.target.files[0];
    if (!file) return;

    setParsing(true);
    try {
      const data = await parseReceipt(file);
      if (!data.items || data.items.length === 0) {
        error("Receipt se kuch nahi mila. Clear photo daalein.");
      } else {
        setItems(data.items);
      }
    } catch (err) {
      error("Image read karne mein error aayi: " + err.message);
    } finally {
      setParsing(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  }

  function handleItemChange(index, field, value) {
    const newItems = [...items];
    newItems[index][field] = value;
    setItems(newItems);
  }

  function handleRemoveItem(index) {
    const newItems = [...items];
    newItems.splice(index, 1);
    setItems(newItems);
  }

  async function handleConfirm() {
    if (!items || items.length === 0) return;
    setSubmitting(true);
    try {
      await confirmBulkStock(items);
      success("Stock successfully save ho gaya!");
      setTimeout(() => navigate('/inventory'), 1500);
    } catch (err) {
      error("Save fail hua: " + err.message);
      setSubmitting(false);
    }
  }

  if (parsing) {
    return (
      <div className={styles.parsingState}>
        <div className={styles.parsingSpinner} />
        <p>AI Receipt padh raha hai... kripya wait karein.</p>
      </div>
    );
  }

  if (items) {
    return (
      <div className={styles.reviewSection}>
        <ToastContainer toasts={toasts} />
        <div className={styles.reviewHeader}>
          <span className={styles.reviewTitle}>Review & Confirm Stock</span>
          <span className={styles.textMuted}>{items.length} items found</span>
        </div>
        <div className={styles.tableWrapper}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Medicine Name</th>
                <th>Batch No</th>
                <th>Qty (Strips)</th>
                <th>Unit Price (₹)</th>
                <th>Expiry (YYYY-MM-DD)</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {items.map((item, idx) => (
                <tr key={idx}>
                  <td>
                    <input className={styles.inputField} value={item.medicine_name || ''} onChange={e => handleItemChange(idx, 'medicine_name', e.target.value)} />
                  </td>
                  <td>
                    <input className={`${styles.inputField} ${styles.inputMed}`} value={item.batch_number || ''} onChange={e => handleItemChange(idx, 'batch_number', e.target.value)} placeholder="Optional" />
                  </td>
                  <td>
                    <input type="number" className={`${styles.inputField} ${styles.inputSmall}`} value={item.quantity || 1} onChange={e => handleItemChange(idx, 'quantity', Number(e.target.value))} />
                  </td>
                  <td>
                    <input type="number" className={`${styles.inputField} ${styles.inputSmall}`} value={item.unit_price || ''} onChange={e => handleItemChange(idx, 'unit_price', Number(e.target.value))} placeholder="₹" />
                  </td>
                  <td>
                    <input type="text" className={`${styles.inputField} ${styles.inputMed}`} value={item.expiry_date || ''} onChange={e => handleItemChange(idx, 'expiry_date', e.target.value)} placeholder="YYYY-MM-DD" />
                  </td>
                  <td>
                    <button className={styles.actionBtn} onClick={() => handleRemoveItem(idx)} title="Remove row">✕</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className={styles.reviewFooter}>
          <button className={styles.btnSecondary} onClick={() => setItems(null)} disabled={submitting}>Cancel</button>
          <button className={styles.btnPrimary} onClick={handleConfirm} disabled={submitting || items.length === 0}>
            {submitting ? 'Saving...' : '✅ Confirm & Save All'}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div>
      <ToastContainer toasts={toasts} />
      <div className={styles.uploadArea} onClick={() => fileInputRef.current?.click()}>
        <span className={styles.uploadIcon}>📸</span>
        <span className={styles.uploadText}>Click to upload Receipt / Invoice</span>
        <span className={styles.uploadSubtext}>Supports JPG, PNG, WEBP</span>
        <input 
          type="file" 
          accept="image/*" 
          className={styles.hiddenInput} 
          ref={fileInputRef}
          onChange={handleFileChange}
        />
      </div>
    </div>
  );
}

function VoiceTab() {
  const { isRecording, audioBlob, startRecording, stopRecording, reset } = useVoiceRecorder();
  const [parsing, setParsing] = useState(false);
  const [item, setItem] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const { toasts, error, success } = useToast();
  const navigate = useNavigate();

  // Similar parsing logic as Receipt, but for single item from voice
  async function handleVoiceParse(blob) {
    setParsing(true);
    try {
      const data = await parseStockVoice(blob, null);
      setItem(data);
    } catch(err) {
      error("Voice samajh nahi aayi: " + err.message);
      reset();
    } finally {
      setParsing(false);
    }
  }

  // Effect to trigger parse when audioBlob is ready

  useEffect(() => {
    if (audioBlob && !parsing && !item) {
      handleVoiceParse(audioBlob);
    }
  }, [audioBlob]);

  async function handleConfirm() {
    setSubmitting(true);
    try {
      await confirmBulkStock([item]);
      success("Stock save ho gaya!");
      setTimeout(() => navigate('/inventory'), 1500);
    } catch (err) {
      error("Save fail hua: " + err.message);
      setSubmitting(false);
    }
  }

  if (parsing) {
    return (
      <div className={styles.parsingState}>
        <div className={styles.parsingSpinner} />
        <p>AI Voice analyze kar raha hai...</p>
      </div>
    );
  }

  if (item) {
    return (
      <div className={styles.manualForm} style={{ maxWidth: '600px', margin: '0 auto' }}>
        <ToastContainer toasts={toasts} />
        <h3 style={{ marginBottom: 16 }}>Confirm Voice Entry</h3>
        <div className={styles.formGroup}>
          <label className={styles.formLabel}>Medicine Name</label>
          <input className={styles.inputField} value={item.medicine_name || ''} onChange={e => setItem({...item, medicine_name: e.target.value})} />
        </div>
        <div style={{ display: 'flex', gap: 16 }}>
          <div className={styles.formGroup} style={{ flex: 1 }}>
            <label className={styles.formLabel}>Quantity</label>
            <input type="number" className={styles.inputField} value={item.quantity || 1} onChange={e => setItem({...item, quantity: Number(e.target.value)})} />
          </div>
          <div className={styles.formGroup} style={{ flex: 1 }}>
            <label className={styles.formLabel}>Unit Price</label>
            <input type="number" className={styles.inputField} value={item.unit_price || ''} onChange={e => setItem({...item, unit_price: Number(e.target.value)})} />
          </div>
        </div>
        <div style={{ display: 'flex', gap: 16 }}>
          <div className={styles.formGroup} style={{ flex: 1 }}>
            <label className={styles.formLabel}>Batch No (Optional)</label>
            <input className={styles.inputField} value={item.batch_number || ''} onChange={e => setItem({...item, batch_number: e.target.value})} />
          </div>
          <div className={styles.formGroup} style={{ flex: 1 }}>
            <label className={styles.formLabel}>Expiry (YYYY-MM-DD)</label>
            <input className={styles.inputField} value={item.expiry_date || ''} onChange={e => setItem({...item, expiry_date: e.target.value})} />
          </div>
        </div>
        <div className={styles.reviewFooter} style={{ marginTop: 16 }}>
          <button className={styles.btnSecondary} onClick={() => { setItem(null); reset(); }} disabled={submitting}>Cancel</button>
          <button className={styles.btnPrimary} onClick={handleConfirm} disabled={submitting}>
            {submitting ? 'Saving...' : '✅ Confirm'}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.voiceSection}>
      <ToastContainer toasts={toasts} />
      <button
        className={`${styles.micBtn} ${isRecording ? styles.recording : ''}`}
        onPointerDown={startRecording}
        onPointerUp={stopRecording}
      >
        <svg width="40" height="40" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 1a4 4 0 014 4v7a4 4 0 01-8 0V5a4 4 0 014-4z"/>
          <path d="M19 10v2a7 7 0 01-14 0v-2H3v2a9 9 0 008 8.94V23h2v-2.06A9 9 0 0021 12v-2h-2z"/>
        </svg>
      </button>
      <p className={styles.voiceHint}>
        Dabao aur bolo: <em>"Azithromycin 50 strip, price 120"</em>
      </p>
    </div>
  );
}

export function StockEntryPage() {
  const [tab, setTab] = useState('receipt'); // receipt, voice

  return (
    <div className={styles.page}>
      <div className={styles.pageHeader}>
        <h1 className={styles.heading}>📦 Add Stock</h1>
        <div className={styles.tabs}>
          <button className={`${styles.tab} ${tab === 'receipt' ? styles.tabActive : ''}`} onClick={() => setTab('receipt')}>
            📸 Receipt Scan
          </button>
          <button className={`${styles.tab} ${tab === 'voice' ? styles.tabActive : ''}`} onClick={() => setTab('voice')}>
            🎤 Voice Entry
          </button>
          <button className={`${styles.tab} ${tab === 'manual' ? styles.tabActive : ''}`} onClick={() => setTab('manual')}>
            ✍️ Manual / Forms
          </button>
        </div>
      </div>

      <div className={styles.tabContent}>
        {tab === 'receipt' && <ReceiptTab />}
        {tab === 'voice' && <VoiceTab />}
        {tab === 'manual' && (
          <div className={styles.uploadArea}>
            <span className={styles.uploadText}>Please use Inventory Page to Add/Edit manually.</span>
            <span className={styles.uploadSubtext}>Inventory page me ab naye Edit aur +Stock buttons add kar diye gaye hain.</span>
          </div>
        )}
      </div>
    </div>
  );
}
