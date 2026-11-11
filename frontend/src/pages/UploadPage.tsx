import { useState, type FormEvent } from 'react'
import { uploadOrderPdf } from '../api/orders'
import { AppShell } from '../components/AppShell'
import { StatusBanner } from '../components/StatusBanner'
import type { OrderCreateRequest, OrderUploadResponse } from '../types/api'

interface UploadPageProps {
  onBack: () => void
  onCreated: () => void
  onNeedsReview: (payload: {
    file: File
    reviewToken: string
    values: OrderCreateRequest
    fieldErrors: Record<string, string>
    notice: string
  }) => void
}

export function UploadPage({ onBack, onCreated, onNeedsReview }: UploadPageProps) {
  const [file, setFile] = useState<File | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [lastResult, setLastResult] = useState<OrderUploadResponse | null>(null)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setSuccess(null)
    setLastResult(null)

    if (!file) {
      setError('Choose a PDF file to upload.')
      return
    }
    if (file.type && file.type !== 'application/pdf') {
      setError('Only PDF files are supported.')
      return
    }

    setBusy(true)
    try {
      const result = await uploadOrderPdf(file)
      setLastResult(result)

      if (result.status === 'created' && result.saved) {
        setSuccess('Extraction succeeded and the order was saved.')
        onCreated()
        return
      }

      if (!result.review_token) {
        throw new Error('Review is unavailable. Please upload the PDF again.')
      }
      onNeedsReview({
        file,
        reviewToken: result.review_token,
        values: {
          patient_first_name: result.extracted.patient_first_name ?? '',
          patient_last_name: result.extracted.patient_last_name ?? '',
          patient_dob: result.extracted.patient_dob ?? '',
          provider_name: result.extracted.provider_name ?? '',
          provider_npi: result.extracted.provider_npi ?? '',
        },
        fieldErrors: result.errors,
        notice:
          'Extraction needs review. Correct the highlighted fields, then save. Extracted values were not changed automatically.',
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <AppShell
      title="Upload order PDF"
      actions={
        <button type="button" className="button button-secondary" onClick={onBack} disabled={busy}>
          Back to orders
        </button>
      }
    >
      <section className="panel narrow-panel">
        <p className="muted">
          Upload a medical order PDF. The backend extracts the five required fields and saves the
          order only when validation passes.
        </p>
        {error ? <StatusBanner tone="error">{error}</StatusBanner> : null}
        {success ? <StatusBanner tone="success">{success}</StatusBanner> : null}
        {busy ? <StatusBanner>Processing PDF with AI extraction…</StatusBanner> : null}

        <form className="stack-form" onSubmit={handleSubmit}>
          <label className="field">
            <span>PDF file</span>
            <input
              type="file"
              accept="application/pdf,.pdf"
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
              disabled={busy}
            />
          </label>
          <button type="submit" className="button button-primary" disabled={busy}>
            {busy ? 'Uploading…' : 'Upload and extract'}
          </button>
        </form>

        {lastResult?.status === 'created' && lastResult.order ? (
          <div className="result-card">
            <h2>Saved order</h2>
            <p>
              {lastResult.order.patient_first_name} {lastResult.order.patient_last_name}
            </p>
            <p>DOB: {lastResult.order.patient_dob}</p>
            <p>
              Provider: {lastResult.order.provider_name} ({lastResult.order.provider_npi})
            </p>
          </div>
        ) : null}
      </section>
    </AppShell>
  )
}
