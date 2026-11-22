import React from 'react';
import { ReactionType } from '../../types';
import { useLanguage } from '../../i18n';
import './ReactionPreview.css';

interface ReactionPreviewProps {
  reactionType: ReactionType;
}

export const ReactionPreview: React.FC<ReactionPreviewProps> = ({ reactionType }) => {
  const { t } = useLanguage();
  
  const reactionConfig = {
    hungry: {
      image: '/images/dog_heart_press_1.webp',
      emoji: '🤤',
      text: t.reactions.hungry,
    },
    excited: {
      image: '/images/dog_heart_press_2.webp',
      emoji: '✨',
      text: t.reactions.excited,
    },
    happy: {
      image: '/images/dog.webp',
      emoji: '💖',
      text: t.reactions.happy,
    },
    curious: {
      image: '/images/dog.webp',
      emoji: '👀',
      text: t.reactions.curious,
    },
    neutral: {
      image: '/images/dog.webp',
      emoji: '😊',
      text: t.reactions.neutral,
    },
  };

  const reaction = reactionConfig[reactionType];

  return (
    <div className="reaction-preview">
      <div className="reaction-preview__bubble">
        <span className="reaction-preview__emoji">{reaction.emoji}</span>
        <p className="reaction-preview__text">{reaction.text}</p>
      </div>
      <div className="reaction-preview__pet">
        <img src={reaction.image} alt="Pet Reaction" />
      </div>
    </div>
  );
};
