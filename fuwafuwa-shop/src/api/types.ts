// 對應 docs/DEVELOPMENT_PLAN.md §5 的 API 契約
export type Role = 'customer' | 'staff' | 'admin';
export type OrderStatus = 'received' | 'processing' | 'shipping' | 'closed' | 'cancelled' | 'returned';
export type ReturnStatus = 'pending' | 'approved' | 'rejected';
export type DiscountType = 'shipping' | 'seasonal' | 'special_event';

export interface User {
  user_id: number;
  loginid: string;
  name: string;
  email: string;
  address: string | null;
  phone: string | null;
  is_active: boolean;
  roles: Role[];
  /** 工作人員隸屬的商店；null 表示總部工作人員（或不是工作人員） */
  store_id?: number | null;
  store_name?: string | null;
  created_at: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface EventDiscount {
  discount_code: string;
  description: string;
  rate: number | null;
  buy_qty: number | null;
  free_qty: number | null;
  start_date: string;
  end_date: string;
}

export interface Product {
  product_id: number;
  store_id: number;
  store_name: string;
  name: string;
  description: string | null;
  category: string | null;
  image_url: string | null;
  price: number;
  stock: number;
  is_listed: boolean;
  created_at: string;
  updated_at: string;
  event_discount: EventDiscount | null;
  also_bought?: Product[];
}

export interface ProductInput {
  store_id: number;
  name: string;
  description: string;
  category: string;
  image_url: string;
  price: number;
  stock: number;
  is_listed: boolean;
}

export interface Review {
  order_id: number;
  store_id: number;
  rating: number;
  comment: string | null;
  reviewed_at: string;
  customer_name: string;
}

export interface Store {
  store_id: number;
  name: string;
  address: string;
  email: string;
  phone: string;
  product_count: number;
  avg_rating: number | null;
  review_count: number;
  products?: Product[];
  reviews?: Review[];
}

export interface AppliedDiscount {
  discount_code: string;
  discount_type: DiscountType;
  description: string;
  amount: number;
}

export interface QuoteLine {
  product_id: number;
  product_name: string;
  store_id: number;
  unit_price: number;
  quantity: number;
  line_subtotal: number;
  event_discount: number;
  event_code: string | null;
  event_description: string | null;
  net_amount: number;
}

export interface Quote {
  lines: QuoteLine[];
  subtotal: number;
  event_discount: number;
  seasonal_discount: number;
  tax_base: number;
  tax_rate: number;
  tax: number;
  shipping_fee: number;
  shipping_discount: number;
  discount_total: number;
  total: number;
  applied_discounts: AppliedDiscount[];
}

export interface CartLine {
  product: Product;
  quantity: number;
  added_at: string;
  line_subtotal: number;
}

export interface CartResponse {
  items: CartLine[];
  quote: Quote;
}

export interface CheckoutPreview {
  quote: Quote;
  recipient: { name: string; phone: string; address: string };
}

export interface CustomerRef {
  user_id: number;
  loginid: string;
  name: string;
}

export interface OrderSummary {
  order_id: number;
  order_time: string;
  status: OrderStatus;
  total: number;
  item_count: number;
  customer: CustomerRef;
  has_return: boolean;
  return_status: ReturnStatus | null;
}

export interface OrderItem {
  item_no: number;
  product_id: number;
  product_name: string;
  image_url: string | null;
  store_name: string;
  unit_price: number;
  quantity: number;
  line_subtotal: number;
  event_discount: number;
}

export interface ReturnItem {
  item_no: number;
  product_name: string;
  unit_price: number;
  quantity: number;
  return_qty: number;
  refund_amount: number | null;
}

export interface ReturnRequest {
  return_id: number;
  order_id: number;
  requested_at: string;
  reason: string;
  status: ReturnStatus;
  processed_by_name: string | null;
  processed_at: string | null;
  reject_reason: string | null;
  refund_total: number | null;
  customer: CustomerRef;
  order_status: OrderStatus;
  order_total: number;
  items: ReturnItem[];
}

export interface Order extends OrderSummary {
  recipient_name: string;
  recipient_phone: string;
  recipient_address: string;
  subtotal: number;
  discount_total: number;
  tax: number;
  shipping_fee: number;
  shipping_discount: number;
  paid_at: string;
  items: OrderItem[];
  discounts: AppliedDiscount[];
  history: { seq_no: number; status: OrderStatus; changed_at: string; changed_by_name: string }[];
  return_request: ReturnRequest | null;
  next_status: OrderStatus | null;
  can_cancel: boolean;
  can_return: boolean;
}

export interface Discount {
  discount_code: string;
  discount_type: DiscountType;
  description: string;
  start_date: string;
  end_date: string;
  rate: number | null;
  min_amount: number | null;
  buy_qty: number | null;
  free_qty: number | null;
  is_active: boolean;
  products: { product_id: number; name: string }[];
  used_count: number;
  is_current: boolean;
}

export interface DiscountInput {
  discount_type: DiscountType;
  description: string;
  start_date: string;
  end_date: string;
  rate?: number | null;
  min_amount?: number | null;
  buy_qty?: number | null;
  free_qty?: number | null;
  is_active?: boolean;
  product_ids?: number[];
}

export interface SalesRow {
  period_start: string;
  period_label: string;
  store_id: number;
  store_name: string;
  order_count: number;
  sales_total: number;
}

export interface TopProductRow {
  store_id: number;
  store_name: string;
  product_id: number;
  product_name: string;
  quantity: number;
  revenue: number;
}

export interface ReportSummary {
  order_count: number;
  sales_total: number;
  customer_count: number;
  pending_returns: number;
  orders_by_status: Record<string, number>;
}

export interface AdminStats {
  users: number;
  customers: number;
  staff: number;
  admins: number;
  inactive: number;
}
