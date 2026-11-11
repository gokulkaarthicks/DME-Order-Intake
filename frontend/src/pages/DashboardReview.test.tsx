import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { DashboardPage } from './DashboardPage'

vi.mock('../api/orders', () => ({
  listOrders: vi.fn().mockResolvedValue([{ id: 'order', user_id: 'user', patient_first_name: 'Ada', patient_last_name: 'Lovelace', patient_dob: '1815-12-10', provider_name: 'Doctor', provider_npi: '1234567893', created_at: '', updated_at: '' }]),
  listReviews: vi.fn().mockResolvedValue([{ id: 'review', extracted: { patient_first_name: 'Jane', patient_last_name: null, patient_dob: null, provider_name: null, provider_npi: null }, errors: { patient_last_name: 'missing' }, status: 'pending', created_at: '', updated_at: '' }]),
  deleteOrder: vi.fn(),
}))

describe('dashboard reviews', () => {
  it('shows validated orders and pending reviews with a review action', async () => {
    const onReview = vi.fn()
    render(<DashboardPage refreshKey={0} notice={null} onReview={onReview} onLogout={vi.fn()} onUpload={vi.fn()} onEdit={vi.fn()} />)
    expect(await screen.findByText('Needs Review')).toBeInTheDocument()
    expect(screen.getByText('Validated')).toBeInTheDocument()
    await userEvent.setup().click(screen.getByRole('button', { name: 'Review' }))
    expect(onReview).toHaveBeenCalledWith(expect.objectContaining({ id: 'review', errors: { patient_last_name: 'missing' } }))
  })
})
