import { useEffect, useState, useRef } from 'react';
import { getInventory } from '../api/inventory';
import { createMedicine, updateMedicine, addBatch } from '../api/stock';
import { useToast } from '../hooks/useToast';
import { ToastContainer } from '../components/ui/Toast';
import styles from './InventoryPage.module.css';

function StockBadge({ qty }) {
  if (qty == null) return null;
  if (qty <= 0) return <span className={`${styles.badge} ${styles.badgeOut}`}>OUT</span>;
  if (qty <= 5) return <span className={`${styles.badge} ${styles.badgeLow}`}>LOW ⚠️</span>;
  return <span className={`${styles.badge} ${styles.badgeOk}`}>IN STOCK</span>;
}

function MedicineCard({ item, onEdit, onAddStock }) {
  const stock = item.total_stock ?? item.quantity_strips ?? 0;
  const price = item.unit_price ?? item.price_per_strip;
  const isOut = stock <= 0;
  return (
    <div className={`${styles.card} ${isOut ? styles.cardOut : ''}`}>
      <div className={styles.cardMain}>
        <div>
          <p className={styles.medName}>{item.name}</p>
          {item.generic_name && <p className={styles.medGeneric}>{item.generic_name}</p>}
        </div>
        <StockBadge qty={stock} />
      </div>
      <div className={styles.cardMeta}>
        <span>📦 {stock} strips</span>
        {item.expiry_date && (
          <span>📅 Exp: {new Date(item.expiry_date).toLocaleDateString('en-IN', { month: 'short', year: 'numeric' })}</span>
        )}
        {price != null && (
          <span style={{ color: 'var(--rupee)' }}>₹{price}/strip</span>
        )}
      </div>
      <div className={styles.cardActions}>
        <button className={styles.actionBtn} onClick={() => onAddStock(item)}>📦 +Stock</button>
        <button className={styles.actionBtn} onClick={() => onEdit(item)}>✏️ Edit</button>
      </div>
    </div>
  );
}

export function InventoryPage() {
  const [items, setItems] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const searchRef = useRef(null);
  const { toasts, success, error } = useToast();

  const [medModal, setMedModal] = useState({ open: false, data: null });
  const [batchModal, setBatchModal] = useState({ open: false, data: null });

  async function load(q = '') {
    setLoading(true);
    try {
      const data = await getInventory(q);
      setItems(data.items || data || []);
    } catch (err) {
      console.error('Inventory load error:', err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  // Debounce search
  useEffect(() => {
    clearTimeout(searchRef.current);
    searchRef.current = setTimeout(() => load(search), 350);
    return () => clearTimeout(searchRef.current);
  }, [search]);

  async function handleSaveMedicine(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = {
      name: formData.get('name'),
      generic_name: formData.get('generic_name'),
      manufacturer: formData.get('manufacturer'),
      unit_price: Number(formData.get('unit_price')),
    };
    try {
      if (medModal.data) {
        await updateMedicine(medModal.data.id, data);
        success("Medicine updated!");
      } else {
        await createMedicine(data);
        success("Medicine added!");
      }
      setMedModal({ open: false, data: null });
      load(search);
    } catch (err) {
      error(err.message);
    }
  }

  async function handleSaveBatch(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = {
      batch_number: formData.get('batch_number'),
      quantity: Number(formData.get('quantity')),
      expiry_date: formData.get('expiry_date'),
    };
    try {
      await addBatch(batchModal.data.id, data);
      success("Stock added!");
      setBatchModal({ open: false, data: null });
      load(search);
    } catch (err) {
      error(err.message);
    }
  }

  const getStock = i => i.total_stock ?? i.quantity_strips ?? 0;
  const outOfStock  = items.filter(i => getStock(i) <= 0);
  const lowStock    = items.filter(i => getStock(i) > 0 && getStock(i) <= 5);
  const inStock     = items.filter(i => getStock(i) > 5);

  return (
    <div className={styles.page}>
      <ToastContainer toasts={toasts} />
      <div className={styles.pageHeader}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h1 className={styles.heading}>📦 Inventory</h1>
          <button className={styles.addBtn} onClick={() => setMedModal({ open: true, data: null })}>
            + Add Medicine
          </button>
        </div>
        <div className={styles.searchBox}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/>
          </svg>
          <input
            className={styles.searchInput}
            type="text"
            placeholder="Medicine dhundho..."
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
          {search && (
            <button className={styles.clearBtn} onClick={() => setSearch('')}>✕</button>
          )}
        </div>
      </div>

      {/* Summary chips */}
      <div className={styles.chips}>
        <span className={`${styles.chip} ${styles.chipOk}`}>{inStock.length} In Stock</span>
        <span className={`${styles.chip} ${styles.chipLow}`}>{lowStock.length} Low</span>
        <span className={`${styles.chip} ${styles.chipOut}`}>{outOfStock.length} Out</span>
      </div>

      {loading ? (
        <div className={styles.loadingList}>
          {[1,2,3,4].map(i => <div key={i} className={styles.skeleton} />)}
        </div>
      ) : items.length === 0 ? (
        <p className={styles.empty}>Koi medicine nahi mili</p>
      ) : (
        <div className={styles.list}>
          {outOfStock.length > 0 && (
            <>
              <p className={styles.groupLabel}>❌ Out of Stock</p>
              {outOfStock.map(item => <MedicineCard key={item.id} item={item} onEdit={d => setMedModal({open: true, data: d})} onAddStock={d => setBatchModal({open: true, data: d})} />)}
            </>
          )}
          {lowStock.length > 0 && (
            <>
              <p className={styles.groupLabel}>⚠️ Low Stock</p>
              {lowStock.map(item => <MedicineCard key={item.id} item={item} onEdit={d => setMedModal({open: true, data: d})} onAddStock={d => setBatchModal({open: true, data: d})} />)}
            </>
          )}
          {inStock.length > 0 && (
            <>
              {(outOfStock.length > 0 || lowStock.length > 0) && (
                <p className={styles.groupLabel}>✅ In Stock</p>
              )}
              {inStock.map(item => <MedicineCard key={item.id} item={item} onEdit={d => setMedModal({open: true, data: d})} onAddStock={d => setBatchModal({open: true, data: d})} />)}
            </>
          )}
        </div>
      )}

      {/* Modals */}
      {medModal.open && (
        <div className={styles.modalOverlay} onClick={() => setMedModal({open:false, data:null})}>
          <div className={styles.modalContent} onClick={e => e.stopPropagation()}>
            <h2 className={styles.modalTitle}>{medModal.data ? 'Edit Medicine' : 'Add New Medicine'}</h2>
            <form onSubmit={handleSaveMedicine} className={styles.form}>
              <div className={styles.formGroup}>
                <label>Name</label>
                <input name="name" required defaultValue={medModal.data?.name} />
              </div>
              <div className={styles.formGroup}>
                <label>Generic Name</label>
                <input name="generic_name" defaultValue={medModal.data?.generic_name} />
              </div>
              <div className={styles.formGroup}>
                <label>Manufacturer</label>
                <input name="manufacturer" defaultValue={medModal.data?.manufacturer} />
              </div>
              <div className={styles.formGroup}>
                <label>Unit Price (₹)</label>
                <input name="unit_price" type="number" step="0.01" required defaultValue={medModal.data?.unit_price} />
              </div>
              <div className={styles.modalActions}>
                <button type="button" onClick={() => setMedModal({open:false, data:null})} className={styles.btnSecondary}>Cancel</button>
                <button type="submit" className={styles.btnPrimary}>Save</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {batchModal.open && (
        <div className={styles.modalOverlay} onClick={() => setBatchModal({open:false, data:null})}>
          <div className={styles.modalContent} onClick={e => e.stopPropagation()}>
            <h2 className={styles.modalTitle}>Add Stock for {batchModal.data.name}</h2>
            <form onSubmit={handleSaveBatch} className={styles.form}>
              <div className={styles.formGroup}>
                <label>Batch Number</label>
                <input name="batch_number" required />
              </div>
              <div className={styles.formGroup}>
                <label>Quantity (Strips/Units)</label>
                <input name="quantity" type="number" required />
              </div>
              <div className={styles.formGroup}>
                <label>Expiry Date</label>
                <input name="expiry_date" type="date" required />
              </div>
              <div className={styles.modalActions}>
                <button type="button" onClick={() => setBatchModal({open:false, data:null})} className={styles.btnSecondary}>Cancel</button>
                <button type="submit" className={styles.btnPrimary}>Add Stock</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
