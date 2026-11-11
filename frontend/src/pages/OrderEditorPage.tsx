import { useEffect, useState } from 'react'
import { getOrder, updateOrder, uploadOrderPdf } from '../api/orders'
import { AppShell } from '../components/AppShell'
import { OrderForm } from '../components/OrderForm'
import { StatusBanner } from '../components/StatusBanner'
import { ApiError, EMPTY_ORDER_FORM, type OrderCreateRequest } from '../types/api'

interface OrderEditorPageProps {
  mode: 'edit' | 'review'
  file?: File
  reviewToken?: string
  orderId?: string
  initialValues?: Partial<OrderCreateRequest>
  initialFieldErrors?: Record<string, string>
  notice?: string | null
  onBack: () => void
  onSaved: () => void
}

export function OrderEditorPage({
  mode,
  orderId,
  file,
  reviewToken,
  initialValues,
  initialFieldErrors,
  notice,
  onBack,
  onSaved,
}: OrderEditorPageProps) {
  const [values, setValues] = useState<OrderCreateRequest>({
    ...EMPTY_ORDER_FORM,
    ...initialValues,
  })
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>(
    initialFieldErrors ?? {},
  )
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(mode === 'edit')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (mode !== 'edit' || !orderId) {
      return
    }
    const editOrderId = orderId
    let cancelled = false
    async function load() {
      setLoading(true)
      setError(null)
      try {
        const order = await getOrder(editOrderId)
        if (!cancelled) {
          setValues({
            patient_first_name: order.patient_first_name,
            patient_last_name: order.patient_last_name,
            patient_dob: order.patient_dob,
            provider_name: order.provider_name,
            provider_npi: order.provider_npi,
          })
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Unable to load the order.')
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }
    void load()
    return () => {
      cancelled = true
    }
  }, [mode, orderId])

  async function handleSubmit(nextValues: OrderCreateRequest) {
    setBusy(true)
    setError(null)
    setFieldErrors({})
    try {
      if (mode === 'edit' && orderId) {
        await updateOrder(orderId, nextValues)
      } else if (mode === 'review' && file && reviewToken) {
        const result = await uploadOrderPdf(file, nextValues, reviewToken)
        if (!result.saved) {
          setFieldErrors(result.errors)
          throw new Error('Please correct the highlighted fields.')
        }
      } else {
        throw new Error('The original PDF is required. Please upload it again.')
      }
      onSaved()
    } catch (err) {
      if (err instanceof ApiError) {
        setFieldErrors(err.fieldErrors)
        setError(err.message)
      } else {
        setError(err instanceof Error ? err.message : 'Unable to save the order.')
      }
      throw err
    } finally {
      setBusy(false)
    }
  }

  const title = mode === 'edit' ? 'Edit order' : 'Review extracted order'

  return (
    <AppShell
      title={title}
      actions={
        <button type="button" className="button button-secondary" onClick={onBack}>
          Back to orders
        </button>
      }
    >
      <section className="panel narrow-panel">
        {notice ? <StatusBanner tone="info">{notice}</StatusBanner> : null}
        {loading ? <StatusBanner>Loading order…</StatusBanner> : null}
        {error ? <StatusBanner tone="error">{error}</StatusBanner> : null}
        {!loading ? (
          <OrderForm
            key={`${mode}-${orderId ?? 'new'}-${values.provider_npi}-${values.patient_dob}`}
            initialValues={values}
            fieldErrors={fieldErrors}
            submitLabel={mode === 'edit' ? 'Save changes' : 'Save order'}
            busy={busy}
            onSubmit={handleSubmit}
          />
        ) : null}
      </section>
    </AppShell>
  )
}
