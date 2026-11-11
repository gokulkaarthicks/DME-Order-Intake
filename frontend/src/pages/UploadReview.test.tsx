import { render, screen, waitFor, cleanup } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { uploadOrderPdf } from '../api/orders'
import { UploadPage } from './UploadPage'
import { OrderEditorPage } from './OrderEditorPage'

vi.mock('../api/orders', () => ({
  uploadOrderPdf: vi.fn(),
  getOrder: vi.fn(),
  updateOrder: vi.fn(),
}))

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

describe('upload review', () => {
  it('retains the original PDF and resubmits corrected fields with the review token', async () => {
    const user = userEvent.setup()
    const file = new File(['pdf'], 'order.pdf', { type: 'application/pdf' })
    const review = vi.fn()
    vi.mocked(uploadOrderPdf).mockResolvedValueOnce({
      status: 'needs_review', saved: false, order_id: null, order: null,
      extracted: { patient_first_name: 'Jane', patient_last_name: null, patient_dob: '1988-04-12', provider_name: 'Dr Example', provider_npi: '1234567893' },
      errors: { patient_last_name: 'missing or unreadable' }, review_token: 'review-proof',
    })
    const view = render(<UploadPage onBack={vi.fn()} onCreated={vi.fn()} onNeedsReview={review} />)
    await user.upload(screen.getByLabelText('PDF file'), file)
    await user.click(screen.getByRole('button', { name: 'Upload and extract' }))
    await waitFor(() => expect(review).toHaveBeenCalledOnce())
    const payload = review.mock.calls[0][0]
    expect(payload.file).toBe(file)
    expect(payload.reviewToken).toBe('review-proof')
    view.unmount()

    const saved = vi.fn()
    vi.mocked(uploadOrderPdf).mockResolvedValueOnce({
      status: 'created', saved: true, order_id: 'id', order: null,
      extracted: payload.values, errors: {}, review_token: null,
    })
    render(<OrderEditorPage mode="review" file={payload.file} reviewToken={payload.reviewToken}
      initialValues={payload.values} initialFieldErrors={payload.fieldErrors} onBack={vi.fn()} onSaved={saved} />)
    await user.type(screen.getByLabelText(/Patient last name/), 'Doe')
    await user.click(screen.getByRole('button', { name: 'Save order' }))
    await waitFor(() => expect(saved).toHaveBeenCalledOnce())
    expect(uploadOrderPdf).toHaveBeenLastCalledWith(file, expect.objectContaining({ patient_last_name: 'Doe' }), 'review-proof')
  })
})
