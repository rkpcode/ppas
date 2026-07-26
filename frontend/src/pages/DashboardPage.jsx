import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getSalesHistory } from '../api/sales';
import { getInventory } from '../api/inventory';
import styles from './DashboardPage.module.css';

function StatCard({ icon, label, value, color }) {
  return (
    <div className={styles.statCard}>
      <span className={styles.statIcon}>{icon}</span>
      <span className={styles.statValue} style={{ color }}>{value}</span>
      <span className={styles.statLabel}>{label}</span>
    </div>
  );
}

function SaleRow({ sale }) {
  const time = new Date(sale.created_at).toLocaleTimeString('en-IN', {
    hour: '2-digit', minute: '2-digit', hour12: true,
  });
  return (
    <div className={styles.saleRow}>
      <div className={styles.saleInfo}>
        <span className={styles.saleMed}>{sale.medicine_name}</span>
        <span className={styles.saleMeta}>× {sale.quantity} {sale.unit || ''} · {time}</span>
      </div>
      <span className={styles.saleAmt}>₹{sale.total_price}</span>
    </div>
  );
}

export function DashboardPage() {
  const navigate = useNavigate();
  const [sales, setSales] = useState([]);
  const [lowStock, setLowStock] = useState([]);
  const [loading, setLoading] = useState(true);

  const today = new Date().toLocaleDateString('en-IN', {
    weekday: 'long', day: 'numeric', month: 'short',
  });

  useEffect(() => {
    async function load() {
      try {
        const [salesData, invData] = await Promise.all([
          getSalesHistory(20),
          getInventory(),
        ]);
        // Filter today's sales
        const todayStr = new Date().toDateString();
        const todaySales = (salesData.sales || salesData || []).filter(s =>
          new Date(s.created_at).toDateString() === todayStr
        );
        setSales(todaySales);

        const items = Array.isArray(invData) ? invData : (invData.items || []);
        setLowStock(items.filter(i => {
          const s = i.total_stock ?? i.quantity_strips;
          return s != null && s <= 5;
        }));
      } catch (err) {
        console.error('Dashboard load error:', err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const totalRevenue = sales.reduce((sum, s) => sum + (s.total_price || 0), 0);
  const totalItems   = sales.reduce((sum, s) => sum + (s.quantity || 0), 0);

  return (
    <div className={styles.page}>
      <div className={styles.pageHeader}>
        <div>
          <h1 className={styles.heading}>Dashboard</h1>
          <p className={styles.date}>{today}</p>
        </div>
      </div>

      {/* Stats */}
      <div className={styles.stats}>
        <StatCard icon="🧾" label="Today's Sales" value={sales.length} color="var(--primary-glow)" />
        <StatCard icon="💊" label="Items Sold" value={totalItems} color="var(--success)" />
        <StatCard icon="₹" label="Revenue" value={`₹${totalRevenue}`} color="var(--rupee)" />
      </div>

      {/* New Sale CTA */}
      <button className={styles.newSaleBtn} onClick={() => navigate('/sale')}>
        <span className={styles.newSaleIcon}>🎤</span>
        <div>
          <span className={styles.newSaleTitle}>New Sale Entry</span>
          <span className={styles.newSaleSub}>Voice ya manually entry karein</span>
        </div>
        <span className={styles.arrow}>→</span>
      </button>

      {/* Low Stock Alerts */}
      {lowStock.length > 0 && (
        <div className={styles.section}>
          <h2 className={styles.sectionTitle}>⚠️ Low Stock Alerts</h2>
          <div className={styles.alertList}>
            {lowStock.map(item => (
              <div key={item.id} className={styles.alertRow}>
                <span className={styles.alertName}>{item.name}</span>
                <span className={styles.alertQty}>{item.total_stock ?? item.quantity_strips ?? 0} strips bacha</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Sales */}
      <div className={styles.section}>
        <h2 className={styles.sectionTitle}>Recent Sales</h2>
        {loading ? (
          <div className={styles.loadingList}>
            {[1,2,3].map(i => <div key={i} className={styles.skeleton} />)}
          </div>
        ) : sales.length === 0 ? (
          <p className={styles.empty}>Aaj koi sale nahi hua abhi tak</p>
        ) : (
          <div className={styles.saleList}>
            {sales.map((s, i) => <SaleRow key={s.id || i} sale={s} />)}
          </div>
        )}
      </div>
    </div>
  );
}
