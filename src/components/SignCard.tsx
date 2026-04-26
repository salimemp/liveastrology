import { useState } from 'react';
import { ChevronDown, ChevronUp, Star } from 'lucide-react';
import { Sign } from '../lib/astrology';
import ZodiacSymbol, { getElementGradient, getElementBorderColor, getSignColor } from './ZodiacSymbol';

interface SignCardProps {
  sign: Sign;
  type: 'sun' | 'moon' | 'rising';
  delay?: number;
}

const TYPE_CONFIG = {
  sun: {
    title: 'Sun Sign',
    subtitle: 'Your Core Essence',
    icon: '☀️',
    color: '#f4c542',
    bgGradient: 'from-cosmic-gold/20 to-transparent'
  },
  moon: {
    title: 'Moon Sign',
    subtitle: 'Your Inner World',
    icon: '🌙',
    color: '#c0c0e0',
    bgGradient: 'from-cosmic-silver/20 to-transparent'
  },
  rising: {
    title: 'Rising Sign',
    subtitle: 'Your Outer Mask',
    icon: '⬆️',
    color: '#e84a7f',
    bgGradient: 'from-cosmic-rose/20 to-transparent'
  }
};

const ELEMENT_ICONS = {
  fire: '🔥',
  earth: '🌍',
  air: '💨',
  water: '💧'
};

const MODALITY_LABELS = {
  cardinal: 'Cardinal',
  fixed: 'Fixed',
  mutable: 'Mutable'
};

const SignCard = ({ sign, type, delay = 0 }: SignCardProps) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const config = TYPE_CONFIG[type];
  const signColor = getSignColor(sign.signName);

  return (
    <div
      className={`
        relative overflow-hidden rounded-2xl
        ${getElementGradient(sign.element)} ${getElementBorderColor(sign.element)}
        border backdrop-blur-sm
        opacity-0 animate-fade-in-up
      `}
      style={{ animationDelay: `${delay}ms`, animationFillMode: 'forwards' }}
    >
      {/* Glowing accent line */}
      <div
        className="absolute top-0 left-0 right-0 h-1"
        style={{ background: `linear-gradient(90deg, transparent, ${config.color}, transparent)` }}
      />

      <div className="p-5 md:p-6">
        {/* Header */}
        <div className="flex items-start gap-4 mb-4">
          {/* Zodiac Symbol */}
          <div className="relative">
            <ZodiacSymbol sign={sign.signName} size="lg" animated />
            <div
              className="absolute -inset-2 rounded-full opacity-20 blur-md"
              style={{ backgroundColor: signColor }}
            />
          </div>

          {/* Sign Info */}
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-lg" style={{ color: config.color }}>
                {config.icon}
              </span>
              <span className="text-xs uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
                {config.title}
              </span>
            </div>
            <h3 className="font-cinzel text-2xl md:text-3xl font-bold mb-1" style={{ color: 'var(--text-primary)' }}>
              {sign.name}
            </h3>
            <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
              {config.subtitle}
            </p>
          </div>

          {/* Degree */}
          <div className="text-right">
            <div className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>{sign.degree}°</div>
            <div className="text-xs" style={{ color: 'var(--text-subtle)' }}>
              {MODALITY_LABELS[sign.modality]}
            </div>
          </div>
        </div>

        {/* Quick Info Badges */}
        <div className="flex flex-wrap gap-2 mb-4">
          {/* Element Badge */}
          <span className={`
            inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium
            ${sign.element === 'fire' ? 'bg-element-fire/20 text-element-fire' : ''}
            ${sign.element === 'earth' ? 'bg-element-earth/20 text-element-earth' : ''}
            ${sign.element === 'air' ? 'bg-element-air/20 text-element-air' : ''}
            ${sign.element === 'water' ? 'bg-element-water/20 text-element-water' : ''}
          `}>
            {ELEMENT_ICONS[sign.element]} {sign.element.charAt(0).toUpperCase() + sign.element.slice(1)}
          </span>

          {/* Ruling Planet Badge */}
          <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium" style={{ backgroundColor: 'var(--bg-tertiary)', color: 'var(--text-secondary)' }}>
            <Star className="w-3 h-3" /> {sign.rulingPlanet}
          </span>
        </div>

        {/* Quick Traits */}
        <div className="flex flex-wrap gap-1 mb-4">
          {sign.traits.slice(0, 3).map((trait, index) => (
            <span
              key={index}
              className="px-2 py-1 rounded text-xs"
              style={{ backgroundColor: 'var(--bg-tertiary)', color: 'var(--text-muted)' }}
            >
              {trait}
            </span>
          ))}
        </div>

        {/* Expandable Description */}
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full flex items-center justify-between py-2 text-sm transition-colors"
          style={{ color: 'var(--text-muted)' }}
        >
          <span>{isExpanded ? 'Show less' : 'Read full description'}</span>
          {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>

        {/* Expanded Content */}
        <div className={`
          overflow-hidden transition-all duration-300 ease-in-out
          ${isExpanded ? 'max-h-96 opacity-100 mt-4' : 'max-h-0 opacity-0'}
        `}>
          <div className="pt-4 space-y-4" style={{ borderTop: '1px solid var(--border-default)' }}>
            {/* Full Description */}
            <p className="text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
              {sign.description}
            </p>

            {/* All Traits */}
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wider mb-2" style={{ color: 'var(--text-primary)' }}>
                Key Traits
              </h4>
              <div className="flex flex-wrap gap-1">
                {sign.traits.map((trait, index) => (
                  <span
                    key={index}
                    className="px-2 py-1 rounded text-xs"
                    style={{ backgroundColor: 'var(--bg-tertiary)', color: 'var(--text-muted)' }}
                  >
                    {trait}
                  </span>
                ))}
              </div>
            </div>

            {/* Strengths */}
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wider mb-2" style={{ color: '#1abc9c' }}>
                Strengths
              </h4>
              <ul className="space-y-1">
                {sign.strengths.map((strength, index) => (
                  <li key={index} className="flex items-center gap-2 text-xs" style={{ color: 'var(--text-muted)' }}>
                    <span className="w-1 h-1 rounded-full" style={{ backgroundColor: '#1abc9c' }} />
                    {strength}
                  </li>
                ))}
              </ul>
            </div>

            {/* Challenges */}
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wider mb-2" style={{ color: '#e84a7f' }}>
                Growth Areas
              </h4>
              <ul className="space-y-1">
                {sign.challenges.map((challenge, index) => (
                  <li key={index} className="flex items-center gap-2 text-xs" style={{ color: 'var(--text-muted)' }}>
                    <span className="w-1 h-1 rounded-full" style={{ backgroundColor: '#e84a7f' }} />
                    {challenge}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Decorative corner accents */}
      <div
        className="absolute bottom-0 right-0 w-20 h-20 opacity-10 blur-2xl"
        style={{ backgroundColor: signColor }}
      />
    </div>
  );
};

export default SignCard;