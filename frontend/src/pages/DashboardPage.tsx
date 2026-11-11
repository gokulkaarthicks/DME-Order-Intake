import { useCallback, useEffect, useState } from 'react'
import { deleteOrder, listOrders, listReviews } from '../api/orders'
import { AppShell } from '../components/AppShell'
import { OrderTable } from '../components/OrderTable'
import { StatusBanner } from '../components/StatusBanner'
import type { OrderPublic, PendingReview } from '../types/api'

interface DashboardPageProps {
  onLogout: () => void
  onUpload: () => void
  onEdit: (orderId: string) => void
  onReview: (review: PendingReview) => void
  notice: string | null
  refreshKey: number
}

export function DashboardPage({
  onLogout,
  onUpload,
  onEdit,
  onReview,
  notice,
  refreshKey,
}: DashboardPageProps) {
  const [reviews, setReviews] = useState<PendingReview[]>([])
  const [orders, setOrders] = useState<OrderPublic[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [busyOrderId, setBusyOrderId] = useState<string | null>(null)

  const loadOrders = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [data, pending] = await Promise.all([listOrders(), listReviews()])
      setOrders(data)
      setReviews(pending)
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
          <button type="button" className="button button-secondary" onClick={onLogout}>
            Sign out
          </button>
        </>
      }
    >
      <section className="panel">
        {notice ? <StatusBanner tone="success">{notice}</StatusBanner> : null}
        {loading ? <StatusBanner>Loading orders…</StatusBanner> : null}
        {error ? <StatusBanner tone="error">{error}</StatusBanner> : null}
        {!loading && !error ? (
          <>
          {reviews.map((review) => (
            <div className="result-card" key={review.id}>
              <strong>Needs Review</strong>
              <p>{[review.extracted.patient_first_name, review.extracted.patient_last_name].filter(Boolean).join(' ') || 'Patient name unavailable'}</p>
              <button type="button" className="button button-secondary" onClick={() => onReview(review)}>Review</button>
            </div>
          ))}
          <OrderTable
            orders={orders}
            onEdit={onEdit}
            onDelete={handleDelete}
            busyOrderId={busyOrderId}
          />
          </>
        ) : null}
      </section>
    </AppShell>
  )
}
