export interface UserPublic {
  id: string
  username: string
  created_at: string
}

export interface AccessTokenResponse {
  access_token: string
  token_type: string
}

export interface RegisterRequest {
  username: string
  password: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface OrderPublic {
  id: string
  user_id: string
  patient_first_name: string
  patient_last_name: string
  patient_dob: string
  provider_name: string
  provider_npi: string
  created_at: string
  updated_at: string
}

export interface OrderCreateRequest {
  patient_first_name: string
  patient_last_name: string
  patient_dob: string
  provider_name: string
  provider_npi: string
}

export type OrderUpdateRequest = Partial<OrderCreateRequest>

export interface ExtractedFields {
  patient_first_name: string | null
  patient_last_name: string | null
  patient_dob: string | null
  provider_name: string | null
  provider_npi: string | null
}

export interface OrderUploadResponse {
  status: 'created' | 'needs_review'
  saved: boolean
  order_id: string | null
  order: OrderPublic | null
  extracted: ExtractedFields
  errors: Record<string, string>
  review_token: string | null
}

export interface FastApiValidationIssue {
  type?: string
  loc?: Array<string | number>
  msg: string
}

export interface ApiErrorBody {
  detail?: string | FastApiValidationIssue[]
  error_type?: string
}

export class ApiError extends Error {
  readonly status: number
  readonly body: ApiErrorBody
  readonly fieldErrors: Record<string, string>

  constructor(status: number, body: ApiErrorBody) {
    super(formatApiErrorMessage(body, status))
    this.name = 'ApiError'
    this.status = status
    this.body = body
    this.fieldErrors = extractFieldErrors(body)
  }
}

export function extractFieldErrors(body: ApiErrorBody): Record<string, string> {
  const detail = body.detail
  if (!Array.isArray(detail)) {
    return {}
  }

  const errors: Record<string, string> = {}
  for (const issue of detail) {
    const loc = issue.loc ?? []
    const field = loc.filter((part) => part !== 'body').at(-1)
    if (typeof field === 'string' && field.length > 0) {
      errors[field] = issue.msg
    }
  }
  return errors
}

function formatApiErrorMessage(body: ApiErrorBody, status: number): string {
  if (typeof body.detail === 'string' && body.detail.trim()) {
    return body.detail
  }
  if (Array.isArray(body.detail) && body.detail.length > 0) {
    return 'Please correct the highlighted fields and try again.'
  }
  if (status === 401) {
    return 'Your session has expired. Please sign in again.'
  }
  if (status >= 500) {
    return 'The server could not complete this request. Please try again.'
  }
  return 'Request failed. Please try again.'
}

export const EMPTY_ORDER_FORM: OrderCreateRequest = {
  patient_first_name: '',
  patient_last_name: '',
  patient_dob: '',
  provider_name: '',
  provider_npi: '',
}
