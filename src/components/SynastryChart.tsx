import { useState } from 'react';
import { Heart, Users, Star, Sparkles } from 'lucide-react';
import { ZODIAC_SIGNS } from '../lib/astrology';

interface SynastryResult {
  compatibility: number;
  overview: string;
  strengths: string[];
  challenges: string[];
  romantic: string;
  communication: string;
}

// Convert ZODIAC_SIGNS object to array
const ZODIAC_ARRAY = Object.values(ZODIAC_SIGNS);

function calculateSynastry(sign1: string, sign2: string): SynastryResult {
  // Get sign indices
  const index1 = ZODIAC_ARRAY.findIndex(s => s.name === sign1);
  const index2 = ZODIAC_ARRAY.findIndex(s => s.name === sign2);

  // Element compatibility matrix
  const elements: { [key: string]: string } = {};
  ZODIAC_ARRAY.forEach(sign => {
    const element = sign.element;
    if (!elements[element]) elements[element] = sign.name;
  });

  const sign1Element = ZODIAC_ARRAY[index1]?.element || '';
  const sign2Element = ZODIAC_ARRAY[index2]?.element || '';

  // Calculate base compatibility
  let compatibility = 50;

  // Element harmony
  if (sign1Element === sign2Element) {
    compatibility += 20; // Same element - very compatible
  } else if (
    (sign1Element === 'fire' && sign2Element === 'air') ||
    (sign1Element === 'air' && sign2Element === 'fire') ||
    (sign1Element === 'earth' && sign2Element === 'water') ||
    (sign1Element === 'water' && sign2Element === 'earth')
  ) {
    compatibility += 15; // Complementary elements
  }

  // Modality compatibility
  const sign1Modality = ZODIAC_ARRAY[index1]?.modality || '';
  const sign2Modality = ZODIAC_ARRAY[index2]?.modality || '';

  if (sign1Modality === sign2Modality) {
    compatibility += 10;
  }

  // Calculate distance in zodiac wheel
  const distance = Math.abs(index1 - index2);
  const opposite = distance === 6; // Opposite signs
  const square = distance === 3; // Square signs
  const trine = distance === 4 || distance === 8; // Trine signs

  if (opposite) compatibility += 10; // Opposite signs have magnetic attraction
  else if (trine) compatibility += 8; // Trine signs flow well
  else if (square) compatibility -= 5; // Square signs create tension

  // Ensure compatibility is between 0 and 100
  compatibility = Math.max(0, Math.min(100, compatibility));

  // Generate overview
  let overview = '';
  if (compatibility >= 75) {
    overview = `${sign1} and ${sign2} create a wonderfully harmonious connection! Your elements and energies naturally complement each other, making communication effortless and mutual understanding easy to achieve.`;
  } else if (compatibility >= 50) {
    overview = `${sign1} and ${sign2} have good potential for a meaningful relationship. While you may face some challenges, your differences can actually help you grow together if you're willing to put in the effort.`;
  } else {
    overview = `${sign1} and ${sign2} face some unique challenges in their connection. However, with patience and understanding, these differences can create opportunities for personal growth and a stronger bond.`;
  }

  // Generate specific insights
  const strengths = [
    `${sign1}'s ${ZODIAC_SIGNS[index1]?.element} nature blends well with ${sign2}'s ${ZODIAC_SIGNS[index2]?.element} energy`,
    opposite ? `${sign1} and ${sign2} have a magnetic attraction that can be both exciting and intense` : '',
    trine ? `Your signs flow naturally together, creating a sense of ease in your interactions` : '',
    sign1Element === sign2Element ? `Sharing the same element means you understand each other's core motivations` : '',
  ].filter(Boolean);

  const challenges = [
    square ? `The square aspect between your signs may create occasional friction that requires compromise` : '',
    sign1Modality !== sign2Modality ? `Different approaches to life may require adjustment and patience` : '',
    compatibility < 60 ? `Building trust may take longer than in more naturally compatible pairings` : '',
  ].filter(Boolean);

  return {
    compatibility,
    overview,
    strengths,
    challenges,
    romantic: getRomanticInsight(sign1Element, sign2Element),
    communication: getCommunicationInsight(sign1Modality, sign2Modality),
  };
}

function getRomanticInsight(element1: string, element2: string): string {
  if (element1 === element2) {
    return "You share similar approaches to love and romance, which creates deep understanding. You'll likely enjoy doing romantic things together and appreciate similar gestures of affection.";
  }
  if ((element1 === 'fire' && element2 === 'water') || (element1 === 'water' && element2 === 'fire')) {
    return "Your romantic styles are quite different - one of you may be more passionate while the other is more emotional. This can create beautiful balance if embraced.";
  }
  if ((element1 === 'earth' && element2 === 'air') || (element1 === 'air' && element2 === 'earth')) {
    return "One of you may be more practical while the other is more idealistic about romance. Together, you can balance dreams with reality.";
  }
  return "Your romantic connection has potential for growth as you learn to appreciate different expressions of love and affection.";
}

function getCommunicationInsight(modality1: string, modality2: string): string {
  if (modality1 === modality2) {
    return "You communicate in similar ways, which makes conversations smooth and understanding natural. You're likely on the same page about goals and priorities.";
  }
  return "Your communication styles may differ, but this diversity can enrich your exchanges. Learning to adapt to each other's pace will strengthen your bond.";
}

interface SynastryChartProps {
  onReset?: () => void;
}

export default function SynastryChart({ onReset }: SynastryChartProps) {
  const [step, setStep] = useState<'input' | 'result'>('input');
  const [person1, setPerson1] = useState({ name: '', day: '', month: '', year: '', sign: '' });
  const [person2, setPerson2] = useState({ name: '', day: '', month: '', year: '', sign: '' });
  const [result, setResult] = useState<SynastryResult | null>(null);

  const handlePerson1Submit = () => {
    if (person1.day && person1.month && person1.year) {
      const sign = calculateSimpleSign(parseInt(person1.month), parseInt(person1.day));
      setPerson1({ ...person1, sign });
    }
  };

  const handlePerson2Submit = () => {
    if (person2.day && person2.month && person2.year) {
      const sign = calculateSimpleSign(parseInt(person2.month), parseInt(person2.day));
      setPerson2({ ...person2, sign });
      if (person1.sign) {
        const synastryResult = calculateSynastry(person1.sign, person2.sign);
        setResult(synastryResult);
        setStep('result');
      }
    }
  };

  const getCompatibilityColor = (score: number) => {
    if (score >= 75) return '#22c55e';
    if (score >= 50) return '#f4c542';
    return '#e84a7f';
  };

  const getCompatibilityEmoji = (score: number) => {
    if (score >= 75) return '💕';
    if (score >= 50) return '✨';
    return '💫';
  };

  if (step === 'result' && result) {
    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="text-center">
          <div className="inline-flex items-center gap-2 mb-2">
            <Users className="w-6 h-6" style={{ color: '#4a6fa5' }} />
            <span className="font-cormorant text-sm uppercase tracking-widest" style={{ color: '#4a6fa5' }}>
              Synastry Chart Analysis
            </span>
          </div>
          <h2 className="font-cinzel text-2xl font-bold mb-2" style={{ color: '#1a1a3a' }}>
            {person1.name} & {person2.name}
          </h2>
          <div className="flex items-center justify-center gap-4 text-lg">
            <span className="font-semibold" style={{ color: '#4a6fa5' }}>{person1.sign}</span>
            <Heart className="w-5 h-5 text-pink-500" />
            <span className="font-semibold" style={{ color: '#4a6fa5' }}>{person2.sign}</span>
          </div>
        </div>

        {/* Compatibility Score */}
        <div className="glass-card p-6 text-center">
          <div className="relative w-40 h-40 mx-auto mb-4">
            <svg className="w-full h-full transform -rotate-90">
              <circle
                cx="80"
                cy="80"
                r="70"
                stroke="#e5e7eb"
                strokeWidth="12"
                fill="none"
              />
              <circle
                cx="80"
                cy="80"
                r="70"
                stroke={getCompatibilityColor(result.compatibility)}
                strokeWidth="12"
                fill="none"
                strokeDasharray={`${result.compatibility * 4.4} 440`}
                strokeLinecap="round"
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <span className="text-4xl">{getCompatibilityEmoji(result.compatibility)}</span>
                <p className="text-3xl font-bold" style={{ color: getCompatibilityColor(result.compatibility) }}>
                  {result.compatibility}%
                </p>
              </div>
            </div>
          </div>
          <p className="text-secondary">Overall Compatibility Score</p>
        </div>

        {/* Overview */}
        <div className="glass-card p-6">
          <h3 className="font-cinzel text-lg font-semibold mb-4" style={{ color: '#1a1a3a' }}>
            Relationship Overview
          </h3>
          <p className="text-secondary leading-relaxed">{result.overview}</p>
        </div>

        {/* Strengths & Challenges */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="glass-card p-5">
            <h4 className="font-cinzel font-semibold mb-3 flex items-center gap-2" style={{ color: '#22c55e' }}>
              <Star className="w-5 h-5" />
              Strengths
            </h4>
            <ul className="space-y-2">
              {result.strengths.map((strength, i) => (
                <li key={i} className="text-secondary text-sm flex items-start gap-2">
                  <span className="text-green-500 mt-1">•</span>
                  {strength}
                </li>
              ))}
            </ul>
          </div>
          <div className="glass-card p-5">
            <h4 className="font-cinzel font-semibold mb-3 flex items-center gap-2" style={{ color: '#e84a7f' }}>
              <Sparkles className="w-5 h-5" />
              Growth Areas
            </h4>
            <ul className="space-y-2">
              {result.challenges.map((challenge, i) => (
                <li key={i} className="text-secondary text-sm flex items-start gap-2">
                  <span className="text-pink-500 mt-1">•</span>
                  {challenge}
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Detailed Insights */}
        <div className="glass-card p-6">
          <h3 className="font-cinzel text-lg font-semibold mb-4" style={{ color: '#1a1a3a' }}>
            Detailed Compatibility Analysis
          </h3>
          <div className="space-y-4">
            <div className="border-l-4 border-pink-400 pl-4">
              <h4 className="font-semibold text-secondary mb-1">Romantic Chemistry</h4>
              <p className="text-sm text-muted">{result.romantic}</p>
            </div>
            <div className="border-l-4 border-blue-400 pl-4">
              <h4 className="font-semibold text-secondary mb-1">Communication Style</h4>
              <p className="text-sm text-muted">{result.communication}</p>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="text-center pt-4">
          <button
            onClick={() => {
              setStep('input');
              setResult(null);
              setPerson1({ name: '', day: '', month: '', year: '', sign: '' });
              setPerson2({ name: '', day: '', month: '', year: '', sign: '' });
            }}
            className="cta-button"
          >
            Calculate Another Pairing
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* What is Synastry */}
      <div className="glass-card p-5 mb-6">
        <h3 className="font-cinzel text-lg font-semibold mb-3" style={{ color: '#1a1a3a' }}>
          What is a Synastry Chart?
        </h3>
        <p className="text-secondary text-sm leading-relaxed">
          A synastry chart compares two people's birth charts to analyze their relationship dynamics.
          By examining how the planets in one chart interact with the other, we can understand
          compatibility, communication styles, romantic potential, and areas for growth together.
        </p>
      </div>

      {/* Person 1 */}
      <div className="glass-card p-5">
        <h3 className="font-cinzel text-lg font-semibold mb-4 text-center" style={{ color: '#1a1a3a' }}>
          First Person
        </h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: '#4a5568' }}>Name</label>
            <input
              type="text"
              value={person1.name}
              onChange={(e) => setPerson1({ ...person1, name: e.target.value })}
              placeholder="Enter name"
              className="form-input w-full px-4 py-3 rounded-lg"
            />
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: '#4a5568' }}>Month</label>
              <select
                value={person1.month}
                onChange={(e) => setPerson1({ ...person1, month: e.target.value })}
                className="form-input w-full px-4 py-3 rounded-lg"
              >
                <option value="">Month</option>
                {Array.from({ length: 12 }, (_, i) => (
                  <option key={i} value={i + 1}>{i + 1}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: '#4a5568' }}>Day</label>
              <select
                value={person1.day}
                onChange={(e) => setPerson1({ ...person1, day: e.target.value })}
                className="form-input w-full px-4 py-3 rounded-lg"
              >
                <option value="">Day</option>
                {Array.from({ length: 31 }, (_, i) => (
                  <option key={i} value={i + 1}>{i + 1}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: '#4a5568' }}>Year</label>
              <input
                type="number"
                value={person1.year}
                onChange={(e) => setPerson1({ ...person1, year: e.target.value })}
                placeholder="1990"
                className="form-input w-full px-4 py-3 rounded-lg"
              />
            </div>
          </div>
          <button
            onClick={handlePerson1Submit}
            disabled={!person1.name || !person1.month || !person1.day || !person1.year}
            className="cta-button w-full disabled:opacity-50"
          >
            {person1.sign ? `Sign: ${person1.sign}` : 'Calculate Sign'}
          </button>
        </div>
      </div>

      {/* Person 2 */}
      <div className="glass-card p-5">
        <h3 className="font-cinzel text-lg font-semibold mb-4 text-center" style={{ color: '#1a1a3a' }}>
          Second Person
        </h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: '#4a5568' }}>Name</label>
            <input
              type="text"
              value={person2.name}
              onChange={(e) => setPerson2({ ...person2, name: e.target.value })}
              placeholder="Enter name"
              className="form-input w-full px-4 py-3 rounded-lg"
            />
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: '#4a5568' }}>Month</label>
              <select
                value={person2.month}
                onChange={(e) => setPerson2({ ...person2, month: e.target.value })}
                className="form-input w-full px-4 py-3 rounded-lg"
              >
                <option value="">Month</option>
                {Array.from({ length: 12 }, (_, i) => (
                  <option key={i} value={i + 1}>{i + 1}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: '#4a5568' }}>Day</label>
              <select
                value={person2.day}
                onChange={(e) => setPerson2({ ...person2, day: e.target.value })}
                className="form-input w-full px-4 py-3 rounded-lg"
              >
                <option value="">Day</option>
                {Array.from({ length: 31 }, (_, i) => (
                  <option key={i} value={i + 1}>{i + 1}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: '#4a5568' }}>Year</label>
              <input
                type="number"
                value={person2.year}
                onChange={(e) => setPerson2({ ...person2, year: e.target.value })}
                placeholder="1990"
                className="form-input w-full px-4 py-3 rounded-lg"
              />
            </div>
          </div>
          <button
            onClick={handlePerson2Submit}
            disabled={!person2.name || !person2.month || !person2.day || !person2.year || !person1.sign}
            className="cta-button w-full disabled:opacity-50"
          >
            {person2.sign ? `Sign: ${person2.sign}` : 'Calculate Sign & Compatibility'}
          </button>
        </div>
      </div>

      <p className="text-xs text-center text-muted">
        Note: This calculator provides entertainment insights based on simplified calculations.
        For detailed relationship analysis, consult a professional astrologer.
      </p>
    </div>
  );
}

// Simplified sun sign calculation
function calculateSimpleSign(month: number, day: number): string {
  const signs = [
    { name: 'Capricorn', end: [1, 19] },
    { name: 'Aquarius', end: [2, 18] },
    { name: 'Pisces', end: [3, 20] },
    { name: 'Aries', end: [4, 19] },
    { name: 'Taurus', end: [5, 20] },
    { name: 'Gemini', end: [6, 20] },
    { name: 'Cancer', end: [7, 22] },
    { name: 'Leo', end: [8, 22] },
    { name: 'Virgo', end: [9, 22] },
    { name: 'Libra', end: [10, 22] },
    { name: 'Scorpio', end: [11, 21] },
    { name: 'Sagittarius', end: [12, 21] },
    { name: 'Capricorn', end: [12, 31] },
  ];

  for (const sign of signs) {
    if (month === sign.end[0] && day <= sign.end[1]) {
      return sign.name;
    }
    if (month < sign.end[0] && day <= sign.end[1]) {
      const prevSign = signs[signs.indexOf(sign) - 1];
      return prevSign ? prevSign.name : 'Capricorn';
    }
  }
  return 'Capricorn';
}

export { calculateSimpleSign };
