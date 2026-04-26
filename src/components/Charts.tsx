import { ElementBalance, ModalityBalance, ELEMENT_COLORS, MODALITY_COLORS } from '../lib/astrology';

interface ElementBalanceChartProps {
  balance: ElementBalance;
}

const ELEMENT_INFO = {
  fire: { label: 'Fire', icon: '🔥', traits: 'Passion, Energy, Inspiration' },
  earth: { label: 'Earth', icon: '🌍', traits: 'Stability, Practicality, Dependability' },
  air: { label: 'Air', icon: '💨', traits: 'Intellect, Communication, Social' },
  water: { label: 'Water', icon: '💧', traits: 'Emotion, Intuition, Sensitivity' }
};

export const ElementBalanceChart = ({ balance }: ElementBalanceChartProps) => {
  const total = balance.fire + balance.earth + balance.air + balance.water;
  const elements = ['fire', 'earth', 'air', 'water'] as const;

  return (
    <div className="glass-card p-5 md:p-6 opacity-0 animate-fade-in-up" style={{ animationDelay: '600ms', animationFillMode: 'forwards' }}>
      <h3 className="font-cinzel text-lg font-semibold text-white mb-4 flex items-center gap-2">
        <span className="text-cosmic-gold">◆</span>
        Element Balance
      </h3>

      <p className="text-xs text-[#a0a0c0] mb-4">
        The distribution of elements in your Sun, Moon, and Rising signs reveals your fundamental nature
      </p>

      {/* Donut Chart */}
      <div className="relative w-40 h-40 mx-auto mb-6">
        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
          {/* Background circle */}
          <circle
            cx="50"
            cy="50"
            r="40"
            fill="none"
            stroke="#1a1a3a"
            strokeWidth="12"
          />

          {/* Element segments */}
          {elements.reduce((acc, element, index) => {
            const percentage = (balance[element] / total) * 100;
            if (percentage === 0) return acc;

            const circumference = 2 * Math.PI * 40;
            const segmentLength = (percentage / 100) * circumference;
            const offset = acc.offset;

            acc.elements.push(
              <circle
                key={element}
                cx="50"
                cy="50"
                r="40"
                fill="none"
                stroke={ELEMENT_COLORS[element]}
                strokeWidth="12"
                strokeDasharray={`${segmentLength} ${circumference - segmentLength}`}
                strokeDashoffset={-offset}
                className="transition-all duration-1000 ease-out"
                style={{
                  filter: `drop-shadow(0 0 4px ${ELEMENT_COLORS[element]})`
                }}
              />
            );

            acc.offset += segmentLength;
            return acc;
          }, { elements: [] as JSX.Element[], offset: 0 }).elements}

          {/* Center circle */}
          <circle
            cx="50"
            cy="50"
            r="30"
            fill="#12122a"
          />

          {/* Center text */}
          <text
            x="50"
            y="47"
            textAnchor="middle"
            className="fill-white text-xs font-semibold"
          >
            YOUR
          </text>
          <text
            x="50"
            y="60"
            textAnchor="middle"
            className="fill-cosmic-gold text-sm font-bold"
          >
            CHART
          </text>
        </svg>
      </div>

      {/* Legend */}
      <div className="grid grid-cols-2 gap-3">
        {elements.map((element) => {
          const info = ELEMENT_INFO[element];
          const percentage = Math.round((balance[element] / total) * 100);

          return (
            <div
              key={element}
              className="flex items-center gap-2 p-2 rounded-lg bg-space-700/30"
            >
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: ELEMENT_COLORS[element] }}
              />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1">
                  <span className="text-sm">{info.icon}</span>
                  <span className="text-xs text-white font-medium truncate">
                    {info.label}
                  </span>
                </div>
                <div className="text-xs text-[#606080]">
                  {percentage}%
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Interpretation */}
      <div className="mt-4 pt-4 border-t border-space-600/30">
        <p className="text-xs text-[#a0a0c0]">
          {getElementInterpretation(balance)}
        </p>
      </div>
    </div>
  );
};

function getElementInterpretation(balance: ElementBalance): string {
  const { fire, earth, air, water } = balance;
  const max = Math.max(fire, earth, air, water);

  if (fire === max) {
    return "You're dominated by Fire energy — passionate, dynamic, and driven by inspiration. Channel this energy into creative pursuits and leadership.";
  }
  if (earth === max) {
    return "You're grounded by Earth energy — practical, reliable, and focused on building tangible results. Use this stability to achieve your goals.";
  }
  if (air === max) {
    return "You're guided by Air energy — intellectual, communicative, and socially oriented. Cultivate connections and share your ideas.";
  }
  if (water === max) {
    return "You're deeply influenced by Water energy — intuitive, emotional, and spiritually aware. Trust your feelings and nurture your inner world.";
  }

  return "Your elements are balanced, giving you versatility and adaptability.";
}

interface ModalityChartProps {
  balance: ModalityBalance;
}

const MODALITY_INFO = {
  cardinal: { label: 'Cardinal', icon: '🌱', traits: 'Initiative, Leadership, Achievement' },
  fixed: { label: 'Fixed', icon: '💎', traits: 'Stability, Persistence, Determination' },
  mutable: { label: 'Mutable', icon: '🦋', traits: 'Adaptability, Flexibility, Change' }
};

export const ModalityChart = ({ balance }: ModalityChartProps) => {
  const modalities = ['cardinal', 'fixed', 'mutable'] as const;

  return (
    <div className="glass-card p-5 md:p-6 opacity-0 animate-fade-in-up" style={{ animationDelay: '700ms', animationFillMode: 'forwards' }}>
      <h3 className="font-cinzel text-lg font-semibold text-white mb-4 flex items-center gap-2">
        <span className="text-cosmic-rose">◆</span>
        Modality Balance
      </h3>

      <p className="text-xs text-[#a0a0c0] mb-4">
        How you initiate, sustain, and adapt in life
      </p>

      {/* Horizontal Bar Chart */}
      <div className="space-y-4">
        {modalities.map((modality) => {
          const info = MODALITY_INFO[modality];
          const percentage = Math.round((balance[modality] / 3) * 100);

          return (
            <div key={modality} className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-lg">{info.icon}</span>
                  <span className="text-sm text-white font-medium">{info.label}</span>
                </div>
                <span className="text-sm text-[#a0a0c0]">{percentage}%</span>
              </div>

              <div className="h-2 bg-space-700/50 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-1000 ease-out"
                  style={{
                    width: `${percentage}%`,
                    backgroundColor: MODALITY_COLORS[modality],
                    boxShadow: `0 0 10px ${MODALITY_COLORS[modality]}50`
                  }}
                />
              </div>

              <p className="text-xs text-[#606080] pl-8">
                {info.traits}
              </p>
            </div>
          );
        })}
      </div>

      {/* Interpretation */}
      <div className="mt-4 pt-4 border-t border-space-600/30">
        <p className="text-xs text-[#a0a0c0]">
          {getModalityInterpretation(balance)}
        </p>
      </div>
    </div>
  );
};

function getModalityInterpretation(balance: ModalityBalance): string {
  const { cardinal, fixed, mutable } = balance;

  if (cardinal === 2) {
    return "You have strong Cardinal energy — you're a natural initiator who leads with vision and drive. Focus on starting projects you can see through.";
  }
  if (fixed === 2) {
    return "You're dominated by Fixed energy — you commit deeply and see things through. Your determination is an asset, but remember to stay open to change.";
  }
  if (mutable === 2) {
    return "You're strongly influenced by Mutable energy — you're adaptable and versatile. Embrace your flexibility while building consistency in key areas.";
  }
  if (cardinal === 1 && fixed === 1 && mutable === 1) {
    return "Perfect balance! You can initiate, sustain, and adapt as needed. This versatility makes you well-equipped for any challenge.";
  }

  if (cardinal === 1) {
    return "You have some Cardinal energy — capable of taking initiative when needed.";
  }
  if (fixed === 1) {
    return "You show Fixed qualities — able to focus and persist when committed.";
  }
  if (mutable === 1) {
    return "You express Mutable traits — comfortable with change and adaptation.";
  }

  return "Your modality balance shapes how you approach life's challenges.";
}
