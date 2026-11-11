import { useState } from 'react'
import { AuthProvider, useAuth } from './auth/AuthContext'
import { DashboardPage } from './pages/DashboardPage'
import { LoginPage } from './pages/LoginPage'
import { OrderEditorPage } from './pages/OrderEditorPage'
import { RegisterPage } from './pages/RegisterPage'
import { UploadPage } from './pages/UploadPage'
import type { OrderCreateRequest } from './types/api'

type AppView =
  | { name: 'login' }
  | { name: 'register' }
  | { name: 'dashboard' }
  | { name: 'upload' }
  | { name: 'edit'; orderId: string }
  | {
      name: 'review'
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
        onNeedsReview={({ file, reviewToken, values, fieldErrors, notice }) =>
          setView({ name: 'review', file, reviewToken, values, fieldErrors, notice })
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
        initialValues={view.values}
        initialFieldErrors={view.fieldErrors}
        notice={view.notice}
        onBack={() => goDashboard()}
        onSaved={() => goDashboard(true)}
      />
    )
  }

  return (
    <DashboardPage
      refreshKey={refreshKey}
      onLogout={() => {
        logout()
        setView({ name: 'login' })
      }}
      onUpload={() => setView({ name: 'upload' })}
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
