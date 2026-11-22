// 呼叫 FastAPI 後端的共用函式：自動帶 JWT、把錯誤轉成 ApiError（訊息取自後端的 detail）
const TOKEN_KEY = 'fuwa_token';

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export const tokenStore = {
  get: (): string | null => {
    try { return localStorage.getItem(TOKEN_KEY); } catch { return null; }
  },
  set: (t: string | null) => {
    try {
      if (t) localStorage.setItem(TOKEN_KEY, t);
      else localStorage.removeItem(TOKEN_KEY);
    } catch { /* ignore */ }
  },
};

type Query = Record<string, string | number | boolean | null | undefined>;

function buildUrl(path: string, query?: Query): string {
  const url = `/api${path}`;
  if (!query) return url;
  const params = new URLSearchParams();
  Object.entries(query).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') params.append(k, String(v));
  });
  const qs = params.toString();
  return qs ? `${url}?${qs}` : url;
}

function detailToMessage(detail: unknown): string {
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    // FastAPI 422 驗證錯誤
    return detail
      .map((d: { loc?: unknown[]; msg?: string }) => `${(d.loc || []).slice(1).join('.')}：${d.msg}`)
      .join('；');
  }
  return '發生錯誤，請稍後再試';
}

export async function api<T = unknown>(
  method: string,
  path: string,
  options: { body?: unknown; query?: Query } = {},
): Promise<T> {
  const headers: Record<string, string> = {};
  const token = tokenStore.get();
  if (token) headers.Authorization = `Bearer ${token}`;
  if (options.body !== undefined) headers['Content-Type'] = 'application/json';
  const res = await fetch(buildUrl(path, options.query), {
    method,
    headers,
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
  });
  if (res.status === 204) return undefined as T;
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    if (res.status === 401 && token) {
      tokenStore.set(null);
      window.dispatchEvent(new Event('fuwa:unauthorized'));
    }
    throw new ApiError(res.status, detailToMessage(data?.detail));
  }
  return data as T;
}

export const get = <T>(path: string, query?: Query) => api<T>('GET', path, { query });
export const post = <T>(path: string, body?: unknown) => api<T>('POST', path, { body: body ?? {} });
export const put = <T>(path: string, body?: unknown) => api<T>('PUT', path, { body: body ?? {} });
export const patch = <T>(path: string, body?: unknown) => api<T>('PATCH', path, { body: body ?? {} });
export const del = <T>(path: string) => api<T>('DELETE', path);

export const errorMessage = (e: unknown): string =>
  e instanceof Error ? e.message : '發生錯誤，請稍後再試';

export const formatMoney = (n: number | null | undefined): string =>
  `NT$ ${Number(n ?? 0).toLocaleString('zh-TW')}`;

export const formatDateTime = (s: string | null | undefined): string =>
  s ? new Date(s).toLocaleString('zh-TW', { hour12: false }) : '—';

export const ORDER_STATUS_LABEL: Record<string, string> = {
  received: '已接單',
  processing: '處理中',
  shipping: '配送中',
  closed: '已完成',
  cancelled: '已取消',
  returned: '已退貨',
};

export const RETURN_STATUS_LABEL: Record<string, string> = {
  pending: '待審核',
  approved: '已核准',
  rejected: '已拒絕',
};

export const ROLE_LABEL: Record<string, string> = {
  customer: '顧客',
  staff: '工作人員',
  admin: '平台管理員',
};

export const DISCOUNT_TYPE_LABEL: Record<string, string> = {
  shipping: '運費折扣',
  seasonal: '季節性折扣',
  special_event: '特殊活動折扣',
};
