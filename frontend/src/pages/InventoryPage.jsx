import { useEffect, useState, useRef } from 'react';
import { getInventory } from '../api/inventory';
import styles from './InventoryPage.module.css';

function StockBadge({ qty }) {
  if (qty == null) return null;
  if (qty <= 0) return <span className={`${styles.badge} ${styles.badgeOut}`}>OUT</span>;
  if (qty <= 5) return <span className={`${styles.badge} ${styles.badgeLow}`}>LOW ⚠️</span>;
  return <span className={`${styles.badge} ${styles.badgeOk}`}>IN STOCK</span>;
}

function MedicineCard({ item }) {
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
    </div>
  );
}

export function InventoryPage() {
  const [items, setItems] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const searchRef = useRef(null);

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

  const getStock = i => i.total_stock ?? i.quantity_strips ?? 0;
  const outOfStock  = items.filter(i => getStock(i) <= 0);
  const lowStock    = items.filter(i => getStock(i) > 0 && getStock(i) <= 5);
  const inStock     = items.filter(i => getStock(i) > 5);

  return (
    <div className={styles.page}>
      <div className={styles.pageHeader}>
        <h1 className={styles.heading}>📦 Inventory</h1>
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
              {outOfStock.map(item => <MedicineCard key={item.id} item={item} />)}
            </>
          )}
          {lowStock.length > 0 && (
            <>
              <p className={styles.groupLabel}>⚠️ Low Stock</p>
              {lowStock.map(item => <MedicineCard key={item.id} item={item} />)}
            </>
          )}
          {inStock.length > 0 && (
            <>
              {(outOfStock.length > 0 || lowStock.length > 0) && (
                <p className={styles.groupLabel}>✅ In Stock</p>
              )}
              {inStock.map(item => <MedicineCard key={item.id} item={item} />)}
            </>
          )}
        </div>
      )}
    </div>
  );
}
