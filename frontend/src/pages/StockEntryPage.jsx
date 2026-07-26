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
                <th>Qty</th>
                <th>Unit Type</th>
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
                    <select className={styles.inputField} value={item.unit_type || 'strip'} onChange={e => handleItemChange(idx, 'unit_type', e.target.value)}>
                      <option value="strip">Strip</option>
                      <option value="tablet">Tablet</option>
                      <option value="bottle">Bottle</option>
                      <option value="piece">Piece</option>
                    </select>
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
  const { isRecording, audioBlob, recordingTime, toggleRecording, reset } = useVoiceRecorder();
  const [parsing, setParsing] = useState(false);
  const [item, setItem] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [manualText, setManualText] = useState('');
  const { toasts, error, success } = useToast();
  const navigate = useNavigate();

  async function handleVoiceParse(blob) {
    if (!blob || blob.size < 2000) {
      error("Voice bohot choti thi. Mic button dabayein, bolne ke baad dobara dabayein!");
      reset();
      return;
    }
    setParsing(true);
    try {
      const data = await parseStockVoice(blob, null);
      if (data.error_message) {
        error(data.error_message);
        reset();
      } else if (!data.medicine_name) {
        error("Voice samajh nahi aayi ya clear nahi thi. Please saaf aawaz mein bolne ki koshish karein!");
        reset();
      } else {
        setItem(data);
      }
    } catch(err) {
      error("Voice parse error: " + err.message);
      reset();
    } finally {
      setParsing(false);
    }
  }

  async function handleTextParse() {
    if (!manualText.trim()) return;
    setParsing(true);
    try {
      const data = await parseStockVoice(null, manualText.trim());
      if (data.error_message) {
        error(data.error_message);
      } else if (!data.medicine_name) {
        error("Text samajh nahi aaya. E.g. 'Dolo 650 10 strip price 25' likhein.");
      } else {
        setItem(data);
      }
    } catch(err) {
      error("Text parse error: " + err.message);
    } finally {
      setParsing(false);
    }
  }

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
        <p>AI Voice/Text analyze kar raha hai... Kripya wait karein.</p>
      </div>
    );
  }

  if (item) {
    return (
      <div className={styles.manualForm} style={{ maxWidth: '600px', margin: '0 auto' }}>
        <ToastContainer toasts={toasts} />
        <h3 style={{ marginBottom: 8 }}>Confirm Voice / Text Entry</h3>
        {item.transcribed_text && (
          <p style={{ background: '#edf2f7', padding: '8px 12px', borderRadius: '6px', fontSize: '0.9rem', color: '#2d3748', marginBottom: 16 }}>
            🎤 <strong>AI ne suna:</strong> <em>"{item.transcribed_text}"</em>
          </p>
        )}
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
            <label className={styles.formLabel}>Unit Type</label>
            <select className={styles.inputField} value={item.unit_type || 'strip'} onChange={e => setItem({...item, unit_type: e.target.value})}>
              <option value="strip">Strip (पत्ता)</option>
              <option value="tablet">Tablet (गोली)</option>
              <option value="bottle">Bottle (शीशी)</option>
              <option value="piece">Piece (पीस)</option>
            </select>
          </div>
          <div className={styles.formGroup} style={{ flex: 1 }}>
            <label className={styles.formLabel}>Unit Price (₹)</label>
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
            {submitting ? 'Saving...' : '✅ Confirm & Save'}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.voiceSection} style={{ textAlign: 'center', padding: '24px 16px' }}>
      <ToastContainer toasts={toasts} />
      
      <button
        className={`${styles.micBtn} ${isRecording ? styles.recording : ''}`}
        onClick={toggleRecording}
        title={isRecording ? "Click to Stop" : "Click to Start Recording"}
      >
        <svg width="40" height="40" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 1a4 4 0 014 4v7a4 4 0 01-8 0V5a4 4 0 014-4z"/>
          <path d="M19 10v2a7 7 0 01-14 0v-2H3v2a9 9 0 008 8.94V23h2v-2.06A9 9 0 0021 12v-2h-2z"/>
        </svg>
      </button>

      <p className={styles.voiceHint} style={{ fontSize: '1.1rem', marginTop: 12 }}>
        {isRecording ? (
          <strong style={{ color: '#e53e3e' }}>🔴 Recording in progress... ({recordingTime}s)<br/><span style={{ fontSize: '0.9rem', color: '#666' }}>Stop karne ke liye button par dobara click karein</span></strong>
        ) : (
          <span>Mic button <strong>ek baar dabayein</strong> aur bolo: <em>"Azithromycin 50 strip, price 120"</em></span>
        )}
      </p>

      <div style={{ marginTop: 32, paddingTop: 24, borderTop: '1px solid #e2e8f0', maxWidth: '500px', margin: '32px auto 0' }}>
        <p style={{ fontSize: '0.95rem', color: '#4a5568', marginBottom: 8 }}>Ya fir yahan type / Keyboard Voice type karein:</p>
        <div style={{ display: 'flex', gap: 8 }}>
          <input
            type="text"
            className={styles.inputField}
            placeholder="e.g. Dolo 650 10 strip rate 25"
            value={manualText}
            onChange={e => setManualText(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleTextParse()}
          />
          <button className={styles.btnPrimary} onClick={handleTextParse} style={{ whiteSpace: 'nowrap' }}>
            ⚡ Process
          </button>
        </div>
      </div>
    </div>
  );
}

function ManualTab() {
  const [item, setItem] = useState({
    medicine_name: '',
    quantity: 1,
    unit_type: 'strip',
    unit_price: '',
    batch_number: '',
    expiry_date: ''
  });
  const [submitting, setSubmitting] = useState(false);
  const { toasts, error, success } = useToast();
  const navigate = useNavigate();

  async function handleConfirm(e) {
    e.preventDefault();
    if (!item.medicine_name.trim()) {
      error("Medicine Name is required");
      return;
    }
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

  return (
    <div className={styles.manualForm} style={{ maxWidth: '600px', margin: '0 auto', textAlign: 'left' }}>
      <ToastContainer toasts={toasts} />
      <h3 style={{ marginBottom: 16 }}>✍️ Manual Stock Entry</h3>
      <form onSubmit={handleConfirm}>
        <div className={styles.formGroup}>
          <label className={styles.formLabel}>Medicine Name</label>
          <input className={styles.inputField} value={item.medicine_name} onChange={e => setItem({...item, medicine_name: e.target.value})} required placeholder="e.g. Cerelac" />
        </div>
        <div style={{ display: 'flex', gap: 16 }}>
          <div className={styles.formGroup} style={{ flex: 1 }}>
            <label className={styles.formLabel}>Quantity</label>
            <input type="number" className={styles.inputField} value={item.quantity} onChange={e => setItem({...item, quantity: Number(e.target.value)})} required min="1" />
          </div>
          <div className={styles.formGroup} style={{ flex: 1 }}>
            <label className={styles.formLabel}>Unit Type (इकाई)</label>
            <select className={styles.inputField} value={item.unit_type} onChange={e => setItem({...item, unit_type: e.target.value})}>
              <option value="strip">Strip (पत्ता)</option>
              <option value="tablet">Tablet (गोली)</option>
              <option value="bottle">Bottle (शीशी)</option>
              <option value="piece">Piece (पीस)</option>
            </select>
          </div>
          <div className={styles.formGroup} style={{ flex: 1 }}>
            <label className={styles.formLabel}>Unit Price (₹)</label>
            <input type="number" step="0.01" className={styles.inputField} value={item.unit_price} onChange={e => setItem({...item, unit_price: e.target.value ? Number(e.target.value) : ''})} placeholder="Optional" />
          </div>
        </div>
        <div style={{ display: 'flex', gap: 16 }}>
          <div className={styles.formGroup} style={{ flex: 1 }}>
            <label className={styles.formLabel}>Batch No (Optional)</label>
            <input className={styles.inputField} value={item.batch_number} onChange={e => setItem({...item, batch_number: e.target.value})} placeholder="e.g. BATCH123" />
          </div>
          <div className={styles.formGroup} style={{ flex: 1 }}>
            <label className={styles.formLabel}>Expiry (YYYY-MM-DD)</label>
            <input type="date" className={styles.inputField} value={item.expiry_date} onChange={e => setItem({...item, expiry_date: e.target.value})} />
          </div>
        </div>
        <div className={styles.reviewFooter} style={{ marginTop: 16 }}>
          <button type="submit" className={styles.btnPrimary} disabled={submitting}>
            {submitting ? 'Saving...' : '✅ Save Stock'}
          </button>
        </div>
      </form>
    </div>
  );
}

export function StockEntryPage() {
  const [tab, setTab] = useState('receipt'); // receipt, voice, manual

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
        {tab === 'manual' && <ManualTab />}
      </div>
    </div>
  );
}
