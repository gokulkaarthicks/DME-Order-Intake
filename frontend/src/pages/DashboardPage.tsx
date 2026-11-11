import { useCallback, useEffect, useState } from 'react'
import { deleteOrder, listOrders } from '../api/orders'
import { AppShell } from '../components/AppShell'
import { OrderTable } from '../components/OrderTable'
import { StatusBanner } from '../components/StatusBanner'
import type { OrderPublic } from '../types/api'

interface DashboardPageProps {
  onLogout: () => void
  onUpload: () => void
  onCreate: () => void
  onEdit: (orderId: string) => void
  refreshKey: number
}

export function DashboardPage({
  onLogout,
  onUpload,
  onCreate,
  onEdit,
  refreshKey,
}: DashboardPageProps) {
  const [orders, setOrders] = useState<OrderPublic[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [busyOrderId, setBusyOrderId] = useState<string | null>(null)

  const loadOrders = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await listOrders()
      setOrders(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load orders.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadOrders()
  }, [loadOrders, refreshKey])

  async function handleDelete(orderId: string) {
    const confirmed = window.confirm('Delete this order? This cannot be undone.')
    if (!confirmed) {
      return
    }
    setBusyOrderId(orderId)
    setError(null)
    try {
      await deleteOrder(orderId)
      await loadOrders()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to delete the order.')
    } finally {
      setBusyOrderId(null)
    }
  }

  return (
    <AppShell
      title="Orders"
      actions={
        <>
          <button type="button" className="button button-secondary" onClick={onUpload}>
            Upload PDF
          </button>
          <button type="button" className="button button-primary" onClick={onCreate}>
            New order
          </button>
          <button type="button" className="button button-secondary" onClick={onLogout}>
            Sign out
          </button>
        </>
      }
    >
      <section className="panel">
        {loading ? <StatusBanner>Loading orders…</StatusBanner> : null}
        {error ? <StatusBanner tone="error">{error}</StatusBanner> : null}
        {!loading && !error ? (
          <OrderTable
            orders={orders}
            onEdit={onEdit}
            onDelete={handleDelete}
            busyOrderId={busyOrderId}
          />
        ) : null}
      </section>
    </AppShell>
  )
}
