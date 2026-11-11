import { apiRequest } from './client'
import type {
  OrderCreateRequest,
  OrderPublic,
  OrderUpdateRequest,
  OrderUploadResponse,
  ExtractedFields,
  PendingReview,
} from '../types/api'

export async function listOrders(): Promise<OrderPublic[]> {
  return apiRequest<OrderPublic[]>('/api/orders')
}

export async function getOrder(orderId: string): Promise<OrderPublic> {
  return apiRequest<OrderPublic>(`/api/orders/${orderId}`)
}

export async function updateOrder(
  orderId: string,
  payload: OrderUpdateRequest,
): Promise<OrderPublic> {
  return apiRequest<OrderPublic>(`/api/orders/${orderId}`, {
    method: 'PATCH',
    json: payload,
  })
}

export async function deleteOrder(orderId: string): Promise<void> {
  await apiRequest<void>(`/api/orders/${orderId}`, {
    method: 'DELETE',
  })
}

export async function uploadOrderPdf(file: File, corrections?: OrderCreateRequest, reviewToken?: string): Promise<OrderUploadResponse> {
  const formData = new FormData()
  formData.append('file', file)
  if (corrections && reviewToken) {
    formData.append('corrections', JSON.stringify(corrections))
    formData.append('review_token', reviewToken)
  }
  return apiRequest<OrderUploadResponse>('/api/orders/upload', {
    method: 'POST',
    body: formData,
  })
}


export async function saveReview(extracted: ExtractedFields, reviewToken: string): Promise<PendingReview> {
  return apiRequest<PendingReview>('/api/reviews', { method: 'POST', json: { extracted, review_token: reviewToken } })
}

export async function listReviews(): Promise<PendingReview[]> {
  return apiRequest<PendingReview[]>('/api/reviews')
}

export async function resolveReview(id: string, payload: OrderCreateRequest): Promise<OrderPublic> {
  return apiRequest<OrderPublic>(`/api/reviews/${id}/resolve`, { method: 'POST', json: payload })
}
