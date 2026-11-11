import { describe, expect, it } from 'vitest'
import { ApiError, extractFieldErrors } from './api'

describe('extractFieldErrors', () => {
  it('maps FastAPI validation issues to field messages', () => {
    const errors = extractFieldErrors({
      detail: [
        { loc: ['body', 'provider_npi'], msg: 'provider_npi must be a valid 10-digit NPI' },
        { loc: ['body', 'patient_dob'], msg: 'patient_dob cannot be in the future' },
      ],
    })
    expect(errors.provider_npi).toContain('NPI')
    expect(errors.patient_dob).toContain('future')
  })

  it('creates actionable ApiError messages', () => {
    const error = new ApiError(401, { detail: 'Not authenticated' })
    expect(error.message).toBe('Not authenticated')
    expect(error.status).toBe(401)
  })
})
