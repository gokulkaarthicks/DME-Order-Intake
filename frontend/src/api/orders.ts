import { apiRequest } from './client'
import type {
  OrderCreateRequest,
  OrderPublic,
  OrderUpdateRequest,
  OrderUploadResponse,
} from '../types/api'

export async function listOrders(): Promise<OrderPublic[]> {
  return apiRequest<OrderPublic[]>('/api/orders')
}

export async function getOrder(orderId: string): Promise<OrderPublic> {
  return apiRequest<OrderPublic>(`/api/orders/${orderId}`)
}

export async function createOrder(payload: OrderCreateRequest): Promise<OrderPublic> {
  return apiRequest<OrderPublic>('/api/orders', {
    method: 'POST',
    json: payload,
  })
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

export async function uploadOrderPdf(file: File): Promise<OrderUploadResponse> {
  const formData = new FormData()
  formData.append('file', file)
  return apiRequest<OrderUploadResponse>('/api/orders/upload', {
    method: 'POST',
    body: formData,
  })
}
