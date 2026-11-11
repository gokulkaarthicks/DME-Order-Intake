import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { OrderForm } from './OrderForm'

describe('OrderForm', () => {
  it('shows backend field errors and preserves extracted NPI values', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()

    render(
      <OrderForm
        initialValues={{
          patient_first_name: 'Marie',
          patient_last_name: 'Curie',
          patient_dob: '1900-12-05',
          provider_name: 'Arjun Raj D.P.M.',
          provider_npi: '9182734556',
        }}
        fieldErrors={{
          provider_npi: 'provider_npi must be a valid 10-digit NPI',
        }}
        submitLabel="Save order"
        onSubmit={onSubmit}
      />,
    )

    expect(screen.getByDisplayValue('9182734556')).toBeInTheDocument()
    expect(screen.getByText(/valid 10-digit NPI/i)).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Save order' }))
    expect(onSubmit).toHaveBeenCalled()
  })

  it('blocks submit when required fields are blank', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(<OrderForm submitLabel="Save order" onSubmit={onSubmit} />)
    await user.click(screen.getByRole('button', { name: 'Save order' }))
    expect(screen.getByText(/First name is required/i)).toBeInTheDocument()
    expect(onSubmit).not.toHaveBeenCalled()
  })
})
