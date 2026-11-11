import { useEffect, useState, type FormEvent } from 'react'
import type { OrderCreateRequest } from '../types/api'
import { EMPTY_ORDER_FORM } from '../types/api'

const NO_FIELD_ERRORS: Record<string, string> = {}

interface OrderFormProps {
  initialValues?: Partial<OrderCreateRequest>
  fieldErrors?: Record<string, string>
  submitLabel: string
  busy?: boolean
  onSubmit: (values: OrderCreateRequest) => Promise<void>
}

function validateClient(values: OrderCreateRequest): Record<string, string> {
  const errors: Record<string, string> = {}
  if (!values.patient_first_name.trim()) {
    errors.patient_first_name = 'First name is required.'
  }
  if (!values.patient_last_name.trim()) {
    errors.patient_last_name = 'Last name is required.'
  }
  if (!values.patient_dob.trim()) {
    errors.patient_dob = 'Date of birth is required.'
  }
  if (!values.provider_name.trim()) {
    errors.provider_name = 'Provider name is required.'
  }
  if (!/^\d{10}$/.test(values.provider_npi.trim())) {
    errors.provider_npi = 'NPI must be exactly 10 digits.'
  }
  return errors
}

export function OrderForm({
  initialValues,
  fieldErrors = NO_FIELD_ERRORS,
  submitLabel,
  busy = false,
  onSubmit,
}: OrderFormProps) {
  const [values, setValues] = useState<OrderCreateRequest>({
    ...EMPTY_ORDER_FORM,
    ...initialValues,
  })
  const [clientErrors, setClientErrors] = useState<Record<string, string>>({})
  const [serverErrors, setServerErrors] = useState<Record<string, string>>(fieldErrors)
  const [formError, setFormError] = useState<string | null>(null)

  useEffect(() => {
    setServerErrors(fieldErrors)
  }, [fieldErrors])

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setFormError(null)
    const nextValues: OrderCreateRequest = {
      patient_first_name: values.patient_first_name.trim(),
      patient_last_name: values.patient_last_name.trim(),
      patient_dob: values.patient_dob.trim(),
      provider_name: values.provider_name.trim(),
      provider_npi: values.provider_npi.trim(),
    }
    const localErrors = validateClient(nextValues)
    setClientErrors(localErrors)
    if (Object.keys(localErrors).length > 0) {
      return
    }

    try {
      await onSubmit(nextValues)
    } catch (error) {
      setFormError(error instanceof Error ? error.message : 'Unable to save the order.')
    }
  }

  function updateField(name: keyof OrderCreateRequest, value: string) {
    setValues((current) => ({ ...current, [name]: value }))
    setServerErrors((current) => {
      if (!(name in current)) {
        return current
      }
      const next = { ...current }
      delete next[name]
      return next
    })
    setClientErrors((current) => {
      if (!(name in current)) {
        return current
      }
      const next = { ...current }
      delete next[name]
      return next
    })
  }

  function fieldError(name: keyof OrderCreateRequest): string | undefined {
    return serverErrors[name] ?? clientErrors[name]
  }

  return (
    <form className="stack-form" onSubmit={handleSubmit} noValidate>
      {formError ? (
        <p className="field-error" role="alert">
          {formError}
        </p>
      ) : null}

      <label className="field">
        <span>Patient first name</span>
        <input
          name="patient_first_name"
          value={values.patient_first_name}
          onChange={(event) => updateField('patient_first_name', event.target.value)}
          disabled={busy}
          aria-invalid={Boolean(fieldError('patient_first_name'))}
        />
        {fieldError('patient_first_name') ? (
          <span className="field-error">{fieldError('patient_first_name')}</span>
        ) : null}
      </label>

      <label className="field">
        <span>Patient last name</span>
        <input
          name="patient_last_name"
          value={values.patient_last_name}
          onChange={(event) => updateField('patient_last_name', event.target.value)}
          disabled={busy}
          aria-invalid={Boolean(fieldError('patient_last_name'))}
        />
        {fieldError('patient_last_name') ? (
          <span className="field-error">{fieldError('patient_last_name')}</span>
        ) : null}
      </label>

      <label className="field">
        <span>Patient date of birth</span>
        <input
          type="date"
          name="patient_dob"
          value={values.patient_dob}
          onChange={(event) => updateField('patient_dob', event.target.value)}
          disabled={busy}
          aria-invalid={Boolean(fieldError('patient_dob'))}
        />
        {fieldError('patient_dob') ? (
          <span className="field-error">{fieldError('patient_dob')}</span>
        ) : null}
      </label>

      <label className="field">
        <span>Ordering provider</span>
        <input
          name="provider_name"
          value={values.provider_name}
          onChange={(event) => updateField('provider_name', event.target.value)}
          disabled={busy}
          aria-invalid={Boolean(fieldError('provider_name'))}
        />
        {fieldError('provider_name') ? (
          <span className="field-error">{fieldError('provider_name')}</span>
        ) : null}
      </label>

      <label className="field">
        <span>Provider NPI</span>
        <input
          name="provider_npi"
          inputMode="numeric"
          maxLength={10}
          value={values.provider_npi}
          onChange={(event) => updateField('provider_npi', event.target.value)}
          disabled={busy}
          aria-invalid={Boolean(fieldError('provider_npi'))}
        />
        {fieldError('provider_npi') ? (
          <span className="field-error">{fieldError('provider_npi')}</span>
        ) : null}
      </label>

      <button type="submit" className="button button-primary" disabled={busy}>
        {busy ? 'Saving…' : submitLabel}
      </button>
    </form>
  )
}
