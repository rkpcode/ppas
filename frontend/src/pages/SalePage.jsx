import { useState, useEffect } from 'react';
import { useVoiceRecorder } from '../hooks/useVoiceRecorder';
import { useToast } from '../hooks/useToast';
import { parseVoice, parseVoiceText, confirmSale } from '../api/sales';
import { ToastContainer } from '../components/ui/Toast';
import styles from './SalePage.module.css';

// ── Step 1: Voice Input ───────────────────────────────────
function VoiceStep({ onDraft, onManual }) {
  const { isRecording, audioBlob, startRecording, stopRecording, reset } = useVoiceRecorder();
  const { toasts, error, info } = useToast();
  const [parsing, setParsing] = useState(false);
  const [manualText, setManualText] = useState('');

  useEffect(() => {
    if (audioBlob && !parsing) {
      handleParseAudio(audioBlob);
    }
  }, [audioBlob]);

  async function handleParseAudio(blob) {
    setParsing(true);
    try {
      const draft = await parseVoice(blob);
      onDraft(draft);
    } catch (err) {
      error('AI parse fail hua. Dobara try karein.');
      reset();
    } finally {
      setParsing(false);
    }
  }

  async function handleManualSubmit(e) {
    e.preventDefault();
    if (!manualText.trim()) return;
    setParsing(true);
    try {
      const draft = await parseVoiceText(manualText.trim());
      onDraft(draft);
    } catch (err) {
      error('Medicine nahi mili. Naam check karein.');
    } finally {
      setParsing(false);
    }
  }

  const handleMicPress = async () => {
    if (isRecording) {
      stopRecording();
    } else {
      try {
        await startRecording();
      } catch (err) {
        error(err.message);
      }
    }
  };

  return (
    <div className={styles.step}>
      <ToastContainer toasts={toasts} />

      <div className={styles.voiceSection}>
        {parsing ? (
          <div className={styles.parsingState}>
            <div className={styles.parsingSpinner} />
            <p>AI samajh raha hai...</p>
          </div>
        ) : (
          <>
            <div className={styles.waveform} aria-hidden>
              {Array.from({ length: 9 }).map((_, i) => (
                <div
                  key={i}
                  className={`${styles.bar} ${isRecording ? styles.barActive : ''}`}
                  style={{ animationDelay: `${i * 0.08}s` }}
                />
              ))}
            </div>

            {isRecording && (
              <p className={styles.listeningText}>🔴 Sun raha hoon...</p>
            )}

            <button
              className={`${styles.micBtn} ${isRecording ? styles.recording : ''}`}
              onPointerDown={handleMicPress}
              onPointerUp={isRecording ? stopRecording : undefined}
              aria-label={isRecording ? 'Recording... release to stop' : 'Press to speak'}
            >
              <svg width="40" height="40" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 1a4 4 0 014 4v7a4 4 0 01-8 0V5a4 4 0 014-4z"/>
                <path d="M19 10v2a7 7 0 01-14 0v-2H3v2a9 9 0 008 8.94V23h2v-2.06A9 9 0 0021 12v-2h-2z"/>
              </svg>
              <span>{isRecording ? 'Bol rahe ho...' : 'DABAO AUR BOLO'}</span>
            </button>

            <p className={styles.voiceHint}>
              Bolein: <em>"Dolo 650 do strip saath rupaye"</em>
            </p>
          </>
        )}
      </div>

      <div className={styles.divider}>
        <span>ya manually likhein</span>
      </div>

      <form onSubmit={handleManualSubmit} className={styles.manualForm}>
        <input
          className={styles.manualInput}
          type="text"
          placeholder="Medicine ka naam likhein..."
          value={manualText}
          onChange={e => setManualText(e.target.value)}
          disabled={parsing}
        />
        <button
          type="submit"
          className={styles.searchBtn}
          disabled={parsing || !manualText.trim()}
        >
          Dhundho
        </button>
      </form>
    </div>
  );
}

// ── Step 2: Draft Review ──────────────────────────────────
function DraftStep({ draft, onConfirm, onRetry }) {
  const [qty, setQty] = useState(draft.quantity || 1);
  const [price, setPrice] = useState(draft.total_price || 0);
  const [customer, setCustomer] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const { toasts, error } = useToast();

  const stockColor =
    draft.available_stock <= 0 ? 'var(--danger)' :
    draft.available_stock <= 5 ? 'var(--warning)' :
    'var(--success)';

  async function handleConfirm() {
    setSubmitting(true);
    try {
      const result = await confirmSale({
        medicine_name: draft.medicine_name,
        medicine_id: draft.medicine_id,
        quantity: qty,
        total_price: price,
        customer_name: customer || undefined,
      });
      onConfirm(result);
    } catch (err) {
      error(err.message || 'Sale save nahi hua');
      setSubmitting(false);
    }
  }

  return (
    <div className={styles.step}>
      <ToastContainer toasts={toasts} />

      <div className={styles.draftCard}>
        <div className={styles.draftHeader}>
          <div>
            <p className={styles.draftLabel}>Medicine</p>
            <h2 className={styles.draftMedName}>{draft.medicine_name}</h2>
            {draft.generic_name && (
              <p className={styles.draftGeneric}>{draft.generic_name}</p>
            )}
          </div>
          <span className={styles.foundBadge}>✓ Mila</span>
        </div>

        <div className={styles.draftFields}>
          <div className={styles.draftField}>
            <label className={styles.draftFieldLabel}>Quantity</label>
            <div className={styles.qtyControl}>
              <button onClick={() => setQty(q => Math.max(1, q - 1))}>−</button>
              <span>{qty}</span>
              <button onClick={() => setQty(q => q + 1)}>+</button>
            </div>
          </div>

          <div className={styles.draftField}>
            <label className={styles.draftFieldLabel}>Total (₹)</label>
            <input
              className={styles.priceInput}
              type="number"
              value={price}
              onChange={e => setPrice(Number(e.target.value))}
              min={0}
            />
          </div>
        </div>

        <div className={styles.draftField}>
          <label className={styles.draftFieldLabel}>Customer Name (Optional)</label>
          <input
            className={styles.customerInput}
            type="text"
            placeholder="Customer ka naam (optional)"
            value={customer}
            onChange={e => setCustomer(e.target.value)}
          />
        </div>

        <div className={styles.stockInfo}>
          <span>📦 Stock Available:</span>
          <span style={{ color: stockColor, fontWeight: 700 }}>
            {draft.available_stock ?? '—'} strips
          </span>
        </div>
      </div>

      <div className={styles.draftActions}>
        <button
          className={styles.confirmBtn}
          onClick={handleConfirm}
          disabled={submitting}
        >
          {submitting ? <span className={styles.spinner} /> : '✅ Confirm & Submit'}
        </button>
        <button className={styles.retryBtn} onClick={onRetry}>
          🔄 Dobara Bolo
        </button>
      </div>
    </div>
  );
}

// ── Step 3: Success ───────────────────────────────────────
function SuccessStep({ result, onNewSale }) {
  return (
    <div className={styles.successStep}>
      <div className={styles.successIcon}>✅</div>
      <h2 className={styles.successTitle}>Sale Record Ho Gayi!</h2>
      <div className={styles.successCard}>
        <p className={styles.successMed}>{result.medicine_name}</p>
        <p className={styles.successDetails}>
          {result.quantity} strip · <span style={{ color: 'var(--rupee)' }}>₹{result.total_price}</span>
        </p>
        {result.new_stock !== undefined && (
          <p className={styles.successStock}>
            Stock: {result.old_stock ?? '?'} → {result.new_stock}
          </p>
        )}
      </div>
      <button className={styles.newSaleBtnSuccess} onClick={onNewSale}>
        + Naya Sale
      </button>
    </div>
  );
}

// ── Main Sale Page ────────────────────────────────────────
export function SalePage() {
  const [step, setStep] = useState('voice'); // 'voice' | 'draft' | 'success'
  const [draft, setDraft] = useState(null);
  const [result, setResult] = useState(null);

  function handleDraft(d) {
    setDraft(d);
    setStep('draft');
  }

  function handleConfirm(r) {
    setResult(r);
    setStep('success');
  }

  function handleReset() {
    setDraft(null);
    setResult(null);
    setStep('voice');
  }

  return (
    <div className={styles.page}>
      <div className={styles.pageHeader}>
        <h1 className={styles.heading}>
          {step === 'voice' && '🎤 New Sale'}
          {step === 'draft' && '📋 Review Karo'}
          {step === 'success' && ''}
        </h1>
        {/* Step indicator */}
        <div className={styles.steps}>
          {['voice', 'draft', 'success'].map((s, i) => (
            <div
              key={s}
              className={`${styles.stepDot} ${step === s ? styles.stepActive : ''} ${
                ['voice','draft','success'].indexOf(step) > i ? styles.stepDone : ''
              }`}
            />
          ))}
        </div>
      </div>

      {step === 'voice' && <VoiceStep onDraft={handleDraft} />}
      {step === 'draft' && <DraftStep draft={draft} onConfirm={handleConfirm} onRetry={handleReset} />}
      {step === 'success' && <SuccessStep result={result} onNewSale={handleReset} />}
    </div>
  );
}
