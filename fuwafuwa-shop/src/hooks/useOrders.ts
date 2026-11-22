import { useCallback, useEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { errorMessage } from '../api/client';
import { getMyOrders } from '../services/orderService';
import type { OrderSummary } from '../api/types';

/** 顧客自己的訂單列表（GET /api/orders/mine） */
export const useOrders = () => {
  const { user } = useAuth();
  const [orders, setOrders] = useState<OrderSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    if (!user) {
      setOrders([]);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      setOrders(await getMyOrders());
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    reload();
  }, [reload]);

  const active = orders.filter((o) => ['received', 'processing', 'shipping'].includes(o.status));
  const stats = {
    total: orders.length,
    active: active.length,
    closed: orders.filter((o) => o.status === 'closed').length,
    totalSpent: orders
      .filter((o) => o.status !== 'cancelled' && o.status !== 'returned')
      .reduce((sum, o) => sum + o.total, 0),
  };

  return { orders, stats, loading, error, reload };
};
