import { useCallback, useState } from 'react';

/** 寵物小房間的狀態只是裝飾，存在瀏覽器 localStorage，不經過後端。 */
export interface PetState {
  happiness: number;
  hunger: number;
  energy: number;
  totalInteractions: number;
}

const KEY = 'fuwa_pet';
const DEFAULT: PetState = { happiness: 50, hunger: 50, energy: 50, totalInteractions: 0 };
const clamp = (n: number) => Math.max(0, Math.min(100, n));

const load = (): PetState => {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? { ...DEFAULT, ...JSON.parse(raw) } : DEFAULT;
  } catch {
    return DEFAULT;
  }
};

export const usePet = () => {
  const [pet, setPet] = useState<PetState>(load);

  const apply = useCallback((delta: Partial<PetState>) => {
    setPet((prev) => {
      const next: PetState = {
        happiness: clamp(prev.happiness + (delta.happiness ?? 0)),
        hunger: clamp(prev.hunger + (delta.hunger ?? 0)),
        energy: clamp(prev.energy + (delta.energy ?? 0)),
        totalInteractions: prev.totalInteractions + 1,
      };
      try {
        localStorage.setItem(KEY, JSON.stringify(next));
      } catch {
        /* ignore */
      }
      return next;
    });
  }, []);

  return {
    pet,
    feed: () => apply({ hunger: -20, happiness: 5 }),
    play: () => apply({ happiness: 15, energy: -10 }),
    brush: () => apply({ happiness: 10 }),
  };
};
