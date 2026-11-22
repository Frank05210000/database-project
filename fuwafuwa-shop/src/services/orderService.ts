// OMS：結帳、訂單查詢、取消與退貨
import { get, post } from '../api/client';
import type { CheckoutPreview, Order, OrderSummary, ReturnRequest } from '../api/types';

export interface CreateOrderData {
  recipient_name: string;
  recipient_phone: string;
  recipient_address: string;
}

export const getCheckoutPreview = () => get<CheckoutPreview>('/orders/checkout-preview');

export const createOrder = (data: CreateOrderData) => post<Order>('/orders/', data);

export const getMyOrders = () => get<OrderSummary[]>('/orders/mine');

export const getOrder = (id: number) => get<Order>(`/orders/${id}`);

export const cancelOrder = (id: number) => post<Order>(`/orders/${id}/cancel`);

export interface CreateReturnData {
  order_id: number;
  reason: string;
  items: { item_no: number; return_qty: number }[];
}

export const createReturn = (data: CreateReturnData) => post<ReturnRequest>('/returns/', data);

export const getMyReturns = () => get<ReturnRequest[]>('/returns/mine');
