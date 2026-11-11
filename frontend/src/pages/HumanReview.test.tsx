import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { saveReview } from '../api/orders'
import { OrderEditorPage } from './OrderEditorPage'

vi.mock('../api/orders', () => ({
  saveReview: vi.fn(), resolveReview: vi.fn(), getOrder: vi.fn(), updateOrder: vi.fn(), uploadOrderPdf: vi.fn(),
}))

describe('human review', () => {
  it('saves an incomplete extraction without requiring correction', async () => {
    const user = userEvent.setup()
    const saved = vi.fn()
    const extracted = { patient_first_name: 'Jane', patient_last_name: null, patient_dob: '1988-04-12', provider_name: 'Dr Example', provider_npi: '1234567893' }
    vi.mocked(saveReview).mockResolvedValue({ id: 'one', extracted, errors: { patient_last_name: 'missing or unreadable' }, status: 'pending', created_at: '', updated_at: '' })
    render(<OrderEditorPage mode="review" file={new File(['pdf'], 'order.pdf')} reviewToken="proof"
      extracted={extracted} initialValues={{ ...extracted, patient_last_name: '' }}
      initialFieldErrors={{ patient_last_name: 'missing or unreadable' }} onReviewSaved={saved} onBack={vi.fn()} onSaved={vi.fn()} />)
    expect(screen.getByText('missing or unreadable')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Save for Human Review' }))
    await waitFor(() => expect(saved).toHaveBeenCalledOnce())
    expect(saveReview).toHaveBeenCalledWith(extracted, 'proof')
  })
})
