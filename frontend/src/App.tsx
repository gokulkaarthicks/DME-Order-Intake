import { useState } from 'react'
import { AuthProvider, useAuth } from './auth/AuthContext'
import { DashboardPage } from './pages/DashboardPage'
import { LoginPage } from './pages/LoginPage'
import { OrderEditorPage } from './pages/OrderEditorPage'
import { RegisterPage } from './pages/RegisterPage'
import { UploadPage } from './pages/UploadPage'
import type { ExtractedFields, OrderCreateRequest, PendingReview } from './types/api'

type AppView =
  | { name: 'login' }
  | { name: 'register' }
  | { name: 'dashboard' }
  | { name: 'upload' }
  | { name: 'edit'; orderId: string }
  | { name: 'pending'; review: PendingReview }
  | {
      name: 'review'
      extracted: ExtractedFields
      file: File
      reviewToken: string
      values: OrderCreateRequest
      fieldErrors: Record<string, string>
      notice: string
    }

function AuthenticatedApp() {
  const { isAuthenticated, logout } = useAuth()
  const [view, setView] = useState<AppView>({ name: 'login' })
  const [refreshKey, setRefreshKey] = useState(0)
  const [dashboardNotice, setDashboardNotice] = useState<string | null>(null)

  function goDashboard(refresh = false) {
    if (refresh) {
      setRefreshKey((value) => value + 1)
    }
    setView({ name: 'dashboard' })
  }

  if (!isAuthenticated) {
    if (view.name === 'register') {
      return (
        <RegisterPage
          onLogin={() => setView({ name: 'login' })}
          onSuccess={() => setView({ name: 'login' })}
        />
      )
    }
    return (
      <LoginPage
        onRegister={() => setView({ name: 'register' })}
        onSuccess={() => goDashboard(true)}
      />
    )
  }

  if (view.name === 'upload') {
    return (
      <UploadPage
        onBack={() => goDashboard()}
        onCreated={() => goDashboard(true)}
        onNeedsReview={({ file, extracted, reviewToken, values, fieldErrors, notice }) =>
          setView({ name: 'review', file, extracted, reviewToken, values, fieldErrors, notice })
        }
      />
    )
  }

  if (view.name === 'edit') {
    return (
      <OrderEditorPage
        mode="edit"
        orderId={view.orderId}
        onBack={() => goDashboard()}
        onSaved={() => goDashboard(true)}
      />
    )
  }

  if (view.name === 'review') {
    return (
      <OrderEditorPage
        mode="review"
        file={view.file}
        reviewToken={view.reviewToken}
        extracted={view.extracted}
        onReviewSaved={() => { setDashboardNotice('Saved for human review.'); goDashboard(true) }}
        initialValues={view.values}
        initialFieldErrors={view.fieldErrors}
        notice={view.notice}
        onBack={() => goDashboard()}
        onSaved={() => goDashboard(true)}
      />
    )
  }

  if (view.name === 'pending') {
    const fields = view.review.extracted
    return <OrderEditorPage mode="pending" reviewId={view.review.id}
      initialValues={{ patient_first_name: fields.patient_first_name ?? '', patient_last_name: fields.patient_last_name ?? '',
        patient_dob: fields.patient_dob ?? '', provider_name: fields.provider_name ?? '', provider_npi: fields.provider_npi ?? '' }}
      initialFieldErrors={view.review.errors} onBack={() => goDashboard()} onSaved={() => goDashboard(true)} />
  }

  return (
    <DashboardPage
      refreshKey={refreshKey}
      notice={dashboardNotice}
      onReview={(review) => { setDashboardNotice(null); setView({ name: 'pending', review }) }}
      onLogout={() => {
        logout()
        setView({ name: 'login' })
      }}
      onUpload={() => { setDashboardNotice(null); setView({ name: 'upload' }) }}
      onEdit={(orderId) => setView({ name: 'edit', orderId })}
    />
  )
}

export default function App() {
  return (
    <AuthProvider>
      <AuthenticatedApp />
    </AuthProvider>
  )
}
