import { useState } from 'react';
import { Heart, Star, Flame, MessageCircle, Target } from 'lucide-react';
import { ZODIAC_SIGNS } from '../lib/astrology';

interface LoveResult {
  compatibilityScore: number;
  loveLanguage: {
    name: string;
    description: string;
  }[];
  strengths: string[];
  challenges: string[];
  loveAdvice: string;
  longTermPotential: string;
}

// Convert ZODIAC_SIGNS object to array
const ZODIAC_ARRAY = Object.values(ZODIAC_SIGNS);

function calculateLoveCompatibility(sign1: string, sign2: string): LoveResult {
  // Calculate base compatibility
  const index1 = ZODIAC_ARRAY.findIndex(s => s.name === sign1);
  const index2 = ZODIAC_ARRAY.findIndex(s => s.name === sign2);

  const sign1Data = ZODIAC_ARRAY[index1] || ZODIAC_ARRAY[0];
  const sign2Data = ZODIAC_ARRAY[index2] || ZODIAC_ARRAY[0];

  let score = 50;

  // Element harmony
  const elements = {
    fire: ['Aries', 'Leo', 'Sagittarius'],
    earth: ['Taurus', 'Virgo', 'Capricorn'],
    air: ['Gemini', 'Libra', 'Aquarius'],
    water: ['Cancer', 'Scorpio', 'Pisces'],
  };

  const sign1Element = Object.entries(elements).find(([_, signs]) => signs.includes(sign1))?.[0] || '';
  const sign2Element = Object.entries(elements).find(([_, signs]) => signs.includes(sign2))?.[0] || '';

  if (sign1Element === sign2Element) score += 15;
  else if ((sign1Element === 'fire' && sign2Element === 'air') || (sign1Element === 'earth' && sign2Element === 'water')) score += 10;
  else if ((sign1Element === 'fire' && sign2Element === 'water') || (sign1Element === 'earth' && sign2Element === 'air')) score -= 5;

  // Ruling planets compatibility
  const rulingPlanets: { [key: string]: string } = {
    Aries: 'Mars', Taurus: 'Venus', Gemini: 'Mercury', Cancer: 'Moon',
    Leo: 'Sun', Virgo: 'Mercury', Libra: 'Venus', Scorpio: 'Pluto',
    Sagittarius: 'Jupiter', Capricorn: 'Saturn', Aquarius: 'Uranus', Pisces: 'Neptune'
  };

  const r1 = rulingPlanets[sign1] || '';
  const r2 = rulingPlanets[sign2] || '';

  if (r1 === r2) score += 5;
  else if ((r1 === 'Venus' && r2 === 'Mars') || (r1 === 'Mars' && r2 === 'Venus')) score += 10;
  else if ((r1 === 'Sun' && r2 === 'Moon') || (r1 === 'Moon' && r2 === 'Sun')) score += 8;

  // Zodiac position
  const distance = Math.abs(index1 - index2);
  if (distance === 0) score += 5; // Same sign
  else if (distance === 6) score += 8; // Opposite signs - magnetic attraction
  else if (distance === 4 || distance === 8) score += 5; // Trine - easy flow
  else if (distance === 3 || distance === 9) score -= 3; // Square - challenging

  score = Math.max(20, Math.min(98, score));

  // Love languages based on elements
  const loveLanguagesByElement: { [key: string]: { name: string; description: string }[] } = {
    fire: [
      { name: 'Passionate Touch', description: 'Physical affection and passionate expressions of love' },
      { name: 'Exciting Dates', description: 'Adventure and new experiences together' },
    ],
    earth: [
      { name: 'Quality Time', description: 'Present, attentive companionship' },
      { name: 'Acts of Service', description: 'Practical support and reliability' },
    ],
    air: [
      { name: 'Words of Affirmation', description: 'Deep conversations and intellectual connection' },
      { name: 'Freedom & Space', description: 'Independence within the relationship' },
    ],
    water: [
      { name: 'Emotional Intimacy', description: 'Deep emotional sharing and understanding' },
      { name: 'Thoughtful Gestures', description: 'Sentimental and caring acts of love' },
    ],
  };

  const loveLanguage = [
    ...(loveLanguagesByElement[sign1Element] || loveLanguagesByElement.air),
    ...(loveLanguagesByElement[sign2Element] || loveLanguagesByElement.air),
  ].slice(0, 3);

  // Generate strengths
  const strengths = [
    `${sign1} brings ${sign1Data.element} energy to the relationship`,
    `${sign2} contributes ${sign2Data.element} stability`,
    sign1Data.modality === sign2Data.modality ? 'Similar approaches to life create harmony' : 'Different perspectives enrich the partnership',
    score >= 70 ? 'Strong natural chemistry and mutual understanding' : 'Opportunities for growth through understanding differences',
  ];

  // Generate challenges
  const challenges = [
    sign1Element !== sign2Element ? 'Different emotional expression styles may need adjustment' : '',
    score < 60 ? 'Building trust may require conscious effort from both parties' : '',
    sign1Data.rulingPlanet !== sign2Data.rulingPlanet ? 'Different priorities may occasionally clash' : '',
  ].filter(Boolean);

  return {
    compatibilityScore: score,
    loveLanguage,
    strengths,
    challenges,
    loveAdvice: getLoveAdvice(sign1, sign2, score),
    longTermPotential: getLongTermPotential(sign1Element, sign2Element, score),
  };
}

function getLoveAdvice(sign1: string, sign2: string, score: number): string {
  if (score >= 80) {
    return `Your ${sign1}-${sign2} connection has wonderful potential! Trust your natural chemistry and focus on maintaining the spark through intentional quality time together.`;
  } else if (score >= 60) {
    return `As a ${sign1}-${sign2} pairing, you have solid foundations. Celebrate your differences as opportunities for growth. Open communication will be your greatest asset.`;
  } else {
    return `The ${sign1}-${sign2} dynamic may require more patience, but love can absolutely flourish. Focus on understanding each other's core needs and don't be afraid to seek compromise.`;
  }
}

function getLongTermPotential(element1: string, element2: string, score: number): string {
  const sameElement = element1 === element2;
  const complementary = (element1 === 'fire' && element2 === 'air') || (element1 === 'earth' && element2 === 'water');

  if (sameElement && score >= 70) {
    return 'Excellent long-term potential. You naturally understand each other\'s needs and motivations, creating a stable foundation for lasting love.';
  } else if (complementary) {
    return 'Strong long-term compatibility. Your different strengths balance each other, creating a harmonious partnership that can withstand life\'s challenges.';
  } else if (score >= 60) {
    return 'Good potential for a lasting relationship with conscious effort. Learning to appreciate your differences will only strengthen your bond over time.';
  } else {
    return 'Long-term success requires dedication from both partners. Focus on communication and be willing to grow together through challenges.';
  }
}

export default function LoveCalculator() {
  const [step, setStep] = useState<'input' | 'result'>('input');
  const [user1, setUser1] = useState({ name: '', sign: '' });
  const [user2, setUser2] = useState({ name: '', sign: '' });
  const [result, setResult] = useState<LoveResult | null>(null);

  const handleCalculate = () => {
    if (user1.sign && user2.sign) {
      const loveResult = calculateLoveCompatibility(user1.sign, user2.sign);
      setResult(loveResult);
      setStep('result');
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return '#22c55e';
    if (score >= 60) return '#f4c542';
    if (score >= 40) return '#f97316';
    return '#e84a7f';
  };

  const getScoreLabel = (score: number) => {
    if (score >= 80) return 'Excellent Match';
    if (score >= 60) return 'Good Compatibility';
    if (score >= 40) return 'Moderate Match';
    return 'Challenging Pairing';
  };

  if (step === 'result' && result) {
    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="text-center">
          <div className="inline-flex items-center gap-2 mb-2">
            <Heart className="w-6 h-6 text-pink-500" />
            <span className="font-cormorant text-sm uppercase tracking-widest" style={{ color: '#4a6fa5' }}>
              Love Calculator
            </span>
          </div>
          <h2 className="font-cinzel text-2xl font-bold mb-2" style={{ color: '#1a1a3a' }}>
            {user1.name} & {user2.name}
          </h2>
          <div className="flex items-center justify-center gap-4 text-lg">
            <span className="font-semibold px-3 py-1 rounded-full" style={{ backgroundColor: '#f3f4f6' }}>
              {user1.sign}
            </span>
            <Heart className="w-6 h-6 text-pink-500" />
            <span className="font-semibold px-3 py-1 rounded-full" style={{ backgroundColor: '#f3f4f6' }}>
              {user2.sign}
            </span>
          </div>
        </div>

        {/* Score Card */}
        <div className="glass-card p-6 text-center">
          <div className="w-32 h-32 mx-auto mb-4 relative">
            <svg className="w-full h-full transform -rotate-90">
              <circle cx="64" cy="64" r="56" stroke="#e5e7eb" strokeWidth="10" fill="none" />
              <circle
                cx="64"
                cy="64"
                r="56"
                stroke={getScoreColor(result.compatibilityScore)}
                strokeWidth="10"
                fill="none"
                strokeDasharray={`${result.compatibilityScore * 3.52} 352`}
                strokeLinecap="round"
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <div>
                <p className="text-3xl font-bold" style={{ color: getScoreColor(result.compatibilityScore) }}>
                  {result.compatibilityScore}%
                </p>
              </div>
            </div>
          </div>
          <h3 className="text-xl font-semibold mb-1" style={{ color: getScoreColor(result.compatibilityScore) }}>
            {getScoreLabel(result.compatibilityScore)}
          </h3>
          <p className="text-secondary text-sm">Love Compatibility Score</p>
        </div>

        {/* Love Advice */}
        <div className="glass-card p-5 border-l-4 border-pink-400">
          <h4 className="font-cinzel font-semibold mb-2 flex items-center gap-2" style={{ color: '#1a1a3a' }}>
            <Heart className="w-5 h-5 text-pink-500" />
            Relationship Advice
          </h4>
          <p className="text-secondary leading-relaxed">{result.loveAdvice}</p>
        </div>

        {/* Love Languages */}
        <div className="glass-card p-5">
          <h4 className="font-cinzel font-semibold mb-4 flex items-center gap-2" style={{ color: '#1a1a3a' }}>
            <Heart className="w-5 h-5 text-pink-500" />
            Your Love Languages
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {result.loveLanguage.map((lang, i) => (
              <div key={i} className="p-3 rounded-lg" style={{ backgroundColor: '#f8f5f0' }}>
                <p className="font-semibold text-sm mb-1" style={{ color: '#4a6fa5' }}>{lang.name}</p>
                <p className="text-xs text-muted">{lang.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Strengths & Challenges */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="glass-card p-5">
            <h4 className="font-cinzel font-semibold mb-3 flex items-center gap-2" style={{ color: '#22c55e' }}>
              <Star className="w-5 h-5" />
              Relationship Strengths
            </h4>
            <ul className="space-y-2">
              {result.strengths.map((s, i) => (
                <li key={i} className="text-sm text-secondary flex items-start gap-2">
                  <span className="text-green-500">✓</span>
                  {s}
                </li>
              ))}
            </ul>
          </div>
          <div className="glass-card p-5">
            <h4 className="font-cinzel font-semibold mb-3 flex items-center gap-2" style={{ color: '#e84a7f' }}>
              <Flame className="w-5 h-5" />
              Areas to Work On
            </h4>
            <ul className="space-y-2">
              {result.challenges.length > 0 ? (
                result.challenges.map((c, i) => (
                  <li key={i} className="text-sm text-secondary flex items-start gap-2">
                    <span className="text-pink-500">!</span>
                    {c}
                  </li>
                ))
              ) : (
                <li className="text-sm text-secondary">Your signs naturally complement each other well!</li>
              )}
            </ul>
          </div>
        </div>

        {/* Long Term Potential */}
        <div className="glass-card p-5 border-l-4 border-green-400">
          <h4 className="font-cinzel font-semibold mb-2 flex items-center gap-2" style={{ color: '#1a1a3a' }}>
            <Target className="w-5 h-5 text-green-500" />
            Long-Term Potential
          </h4>
          <p className="text-secondary leading-relaxed">{result.longTermPotential}</p>
        </div>

        {/* Actions */}
        <div className="text-center pt-4">
          <button
            onClick={() => {
              setStep('input');
              setResult(null);
              setUser1({ name: '', sign: '' });
              setUser2({ name: '', sign: '' });
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
      {/* Explanation */}
      <div className="glass-card p-5 mb-6">
        <h3 className="font-cinzel text-lg font-semibold mb-3" style={{ color: '#1a1a3a' }}>
          How Does the Love Calculator Work?
        </h3>
        <p className="text-secondary text-sm leading-relaxed">
          Our Love Calculator analyzes the zodiac compatibility between two people based on their
          Sun signs. It evaluates elemental harmony, planetary rulerships, and zodiac aspects to
          provide insights into romantic chemistry, communication styles, and long-term potential.
        </p>
      </div>

      {/* User 1 */}
      <div className="glass-card p-5">
        <h3 className="font-cinzel text-lg font-semibold mb-4 text-center" style={{ color: '#1a1a3a' }}>
          Your Information
        </h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: '#4a5568' }}>Your Name</label>
            <input
              type="text"
              value={user1.name}
              onChange={(e) => setUser1({ ...user1, name: e.target.value })}
              placeholder="Enter your name"
              className="form-input w-full px-4 py-3 rounded-lg"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: '#4a5568' }}>Your Zodiac Sign</label>
            <select
              value={user1.sign}
              onChange={(e) => setUser1({ ...user1, sign: e.target.value })}
              className="form-input w-full px-4 py-3 rounded-lg"
            >
              <option value="">Select your sign</option>
              {ZODIAC_ARRAY.map((sign) => (
                <option key={sign.name} value={sign.name}>{sign.name}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* User 2 */}
      <div className="glass-card p-5">
        <h3 className="font-cinzel text-lg font-semibold mb-4 text-center" style={{ color: '#1a1a3a' }}>
          Partner Information
        </h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: '#4a5568' }}>Partner's Name</label>
            <input
              type="text"
              value={user2.name}
              onChange={(e) => setUser2({ ...user2, name: e.target.value })}
              placeholder="Enter partner's name"
              className="form-input w-full px-4 py-3 rounded-lg"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: '#4a5568' }}>Partner's Zodiac Sign</label>
            <select
              value={user2.sign}
              onChange={(e) => setUser2({ ...user2, sign: e.target.value })}
              className="form-input w-full px-4 py-3 rounded-lg"
            >
              <option value="">Select their sign</option>
              {ZODIAC_ARRAY.map((sign) => (
                <option key={sign.name} value={sign.name}>{sign.name}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Calculate Button */}
      <button
        onClick={handleCalculate}
        disabled={!user1.name || !user1.sign || !user2.name || !user2.sign}
        className="cta-button w-full py-4 text-lg disabled:opacity-50"
      >
        <Heart className="w-5 h-5 inline mr-2" />
        Calculate Love Compatibility
      </button>

      <p className="text-xs text-center text-muted">
        This calculator provides entertainment insights based on simplified zodiac compatibility.
        Real relationships are complex and unique. For deeper understanding, explore each other's full birth charts.
      </p>
    </div>
  );
}
