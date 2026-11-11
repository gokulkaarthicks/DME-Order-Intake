import type { OrderPublic } from '../types/api'

interface OrderTableProps {
  orders: OrderPublic[]
  onEdit: (orderId: string) => void
  onDelete: (orderId: string) => void
  busyOrderId?: string | null
}

function formatDate(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  return date.toLocaleString()
}

export function OrderTable({ orders, onEdit, onDelete, busyOrderId }: OrderTableProps) {
  if (orders.length === 0) {
    return <p className="muted">No orders yet. Upload a PDF to create one.</p>
  }

  return (
    <div className="table-wrap">
      <table className="orders-table">
        <thead>
          <tr>
            <th scope="col">Status</th>
            <th scope="col">Patient</th>
            <th scope="col">Date of birth</th>
            <th scope="col">Ordering provider</th>
            <th scope="col">Provider NPI</th>
            <th scope="col">Created</th>
            <th scope="col">Actions</th>
          </tr>
        </thead>
        <tbody>
          {orders.map((order) => (
            <tr key={order.id}>
              <td>Validated</td>
              <td>
                {order.patient_first_name} {order.patient_last_name}
              </td>
              <td>{order.patient_dob}</td>
              <td>{order.provider_name}</td>
              <td>{order.provider_npi}</td>
              <td>{formatDate(order.created_at)}</td>
              <td className="actions-cell">
                <button
                  type="button"
                  className="button button-secondary"
                  onClick={() => onEdit(order.id)}
                  disabled={busyOrderId === order.id}
                >
                  Edit
                </button>
                <button
                  type="button"
                  className="button button-danger"
                  onClick={() => onDelete(order.id)}
                  disabled={busyOrderId === order.id}
                >
                  {busyOrderId === order.id ? 'Deleting…' : 'Delete'}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
