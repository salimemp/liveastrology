import { ZodiacSignName } from '../lib/astrology';

interface ZodiacSymbolProps {
  sign: ZodiacSignName;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  animated?: boolean;
  className?: string;
}

const ELEMENT_COLORS = {
  aries: '#e74c3c',
  taurus: '#27ae60',
  gemini: '#3498db',
  cancer: '#9b59b6',
  leo: '#f39c12',
  virgo: '#27ae60',
  libra: '#3498db',
  scorpio: '#9b59b6',
  sagittarius: '#e74c3c',
  capricorn: '#27ae60',
  aquarius: '#3498db',
  pisces: '#9b59b6'
};

const SIZE_CLASSES = {
  sm: 'w-8 h-8 text-lg',
  md: 'w-12 h-12 text-2xl',
  lg: 'w-16 h-16 text-4xl',
  xl: 'w-24 h-24 text-6xl'
};

const ZodiacSymbol = ({ sign, size = 'md', animated = false, className = '' }: ZodiacSymbolProps) => {
  const color = ELEMENT_COLORS[sign];

  return (
    <div
      className={`
        relative flex items-center justify-center
        ${SIZE_CLASSES[size]}
        ${animated ? 'animate-spin-slow' : ''}
        zodiac-symbol ${className}
      `}
      style={{ color }}
    >
      {/* Glow effect */}
      <div
        className="absolute inset-0 rounded-full opacity-30 blur-xl"
        style={{ backgroundColor: color }}
      />

      {/* Symbol */}
      <span className="relative z-10">{getSignSymbol(sign)}</span>

      {/* Decorative ring */}
      {size !== 'sm' && (
        <svg
          className="absolute inset-0 w-full h-full"
          viewBox="0 0 100 100"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <circle
            cx="50"
            cy="50"
            r="45"
            stroke={color}
            strokeWidth="1"
            strokeDasharray="4 4"
            opacity="0.3"
            className={animated ? 'animate-spin-slow' : ''}
            style={{ transformOrigin: 'center', animationDuration: '30s' }}
          />
        </svg>
      )}
    </div>
  );
};

function getSignSymbol(sign: ZodiacSignName): string {
  const symbols: Record<ZodiacSignName, string> = {
    aries: '♈',
    taurus: '♉',
    gemini: '♊',
    cancer: '♋',
    leo: '♌',
    virgo: '♍',
    libra: '♎',
    scorpio: '♏',
    sagittarius: '♐',
    capricorn: '♑',
    aquarius: '♒',
    pisces: '♓'
  };
  return symbols[sign];
}

// Export the color getter for use in other components
export const getSignColor = (sign: ZodiacSignName): string => ELEMENT_COLORS[sign];

export const getElementGradient = (element: 'fire' | 'earth' | 'air' | 'water'): string => {
  const gradients: Record<string, string> = {
    fire: 'from-element-fire/30 to-cosmic-gold/20',
    earth: 'from-element-earth/30 to-cosmic-gold/20',
    air: 'from-element-air/30 to-cosmic-silver/20',
    water: 'from-element-water/30 to-cosmic-purple/20'
  };
  return gradients[element];
};

export const getElementBorderColor = (element: 'fire' | 'earth' | 'air' | 'water'): string => {
  const colors: Record<string, string> = {
    fire: 'border-element-fire/40',
    earth: 'border-element-earth/40',
    air: 'border-element-air/40',
    water: 'border-element-water/40'
  };
  return colors[element];
};

export const getElementTextColor = (element: 'fire' | 'earth' | 'air' | 'water'): string => {
  const colors: Record<string, string> = {
    fire: 'text-element-fire',
    earth: 'text-element-earth',
    air: 'text-element-air',
    water: 'text-element-water'
  };
  return colors[element];
};

export default ZodiacSymbol;
