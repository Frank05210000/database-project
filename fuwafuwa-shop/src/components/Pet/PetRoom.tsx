import React, { useEffect, useRef, useState } from 'react';
import { usePet } from '../../hooks/usePet';
import { useLanguage } from '../../i18n';
import './PetRoom.css';

/** 首頁上方的裝飾小房間：點按鈕和寵物互動，狀態只存在瀏覽器，不影響購物。 */
type Action = 'brush' | 'play' | 'feed';

const BUTTONS: { action: Action; icon: string; emoji: string; zh: string; en: string; say: [string, string] }[] = [
  { action: 'brush', icon: 'brush.webp', emoji: '💖', zh: '梳毛', en: 'Brush', say: ['好舒服～', 'So comfy~'] },
  { action: 'play', icon: 'ball.webp', emoji: '✨', zh: '玩球', en: 'Play', say: ['好好玩！', 'So fun!'] },
  { action: 'feed', icon: 'can.webp', emoji: '😋', zh: '餵食', en: 'Feed', say: ['好好吃！', 'Yummy!'] },
];

export const PetRoom: React.FC = () => {
  const pet = usePet();
  const { language } = useLanguage();
  const en = language === 'en';
  const [reaction, setReaction] = useState<{ n: number; emoji: string; text: string } | null>(null);
  const timer = useRef<number | undefined>(undefined);

  useEffect(() => () => window.clearTimeout(timer.current), []);

  const interact = (b: (typeof BUTTONS)[number]) => {
    pet[b.action]();
    window.clearTimeout(timer.current);
    // n 每次都不同，讓連續點擊也會重新播放動畫
    setReaction((r) => ({ n: (r?.n ?? 0) + 1, emoji: b.emoji, text: b.say[en ? 1 : 0] }));
    timer.current = window.setTimeout(() => setReaction(null), 1600);
  };

  return (
    <section className="pet-room" aria-label={en ? 'Pet room' : '寵物小房間'}>
      <img className="pet-room__bg" src="/images/electric_chicken_background.webp" alt="" />
      <div className="pet-room__controls">
        {BUTTONS.map((b) => (
          <button key={b.action} type="button" className="pet-room__control-btn" onClick={() => interact(b)}
            aria-label={en ? b.en : b.zh} title={en ? b.en : b.zh}>
            <img src={`/images/${b.icon}`} alt="" />
            <span>{en ? b.en : b.zh}</span>
          </button>
        ))}
      </div>
      <div className="pet-room__mood" aria-live="polite">💖 {pet.pet.happiness}</div>
      <div key={reaction?.n ?? 0} className={`pet-room__pet${reaction ? ' is-reacting' : ''}`}>
        {reaction && <div className="pet-room__bubble">{reaction.emoji} {reaction.text}</div>}
        <img src={reaction ? '/images/dog_heart_press_1.webp' : '/images/dog.webp'} alt={en ? 'Pet' : '寵物'} />
      </div>
    </section>
  );
};
