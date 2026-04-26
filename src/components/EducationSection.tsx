import { useState } from 'react';
import { ChevronDown, ChevronUp, HelpCircle, BookOpen, Sparkles } from 'lucide-react';

interface FAQItem {
  question: string;
  answer: string;
}

interface EducationSectionProps {
  title: string;
  content: string;
  icon?: React.ReactNode;
}

export const EducationSection = ({ title, content, icon }: EducationSectionProps) => {
  return (
    <div className="glass-card p-6 mb-6 opacity-0 animate-fade-in-up" style={{ animationDelay: '800ms', animationFillMode: 'forwards' }}>
      <div className="flex items-start gap-3 mb-4">
        {icon && <div className="text-cosmic-gold mt-1">{icon}</div>}
        <h3 className="font-cinzel text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>
          {title}
        </h3>
      </div>
      <p className="text-secondary leading-relaxed text-sm" dangerouslySetInnerHTML={{ __html: content }} />
    </div>
  );
};

export const WhatIsBirthChart = () => {
  return (
    <EducationSection
      title="What Is a Birth Chart?"
      icon={<BookOpen className="w-5 h-5" />}
      content={`
        A <strong>birth chart</strong> (also known as a <strong>natal chart</strong>) is a snapshot of the sky at the exact moment you were born.
        It serves as a personal roadmap showing how the planets and houses align to shape your <strong>personality</strong>,
        <strong>emotions</strong>, and <strong>life direction</strong>.
        <br/><br/>
        Your <strong>Sun, Moon, and Rising signs</strong> lay the foundation, while the rest of your chart reveals
        how you love, think, connect, and grow.
        <br/><br/>
        <em>Why Your Birth Chart Matters:</em>
        <ul className="list-disc pl-5 mt-2 space-y-1">
          <li>Acts as a personal guide written in the stars</li>
          <li>Shows how planets and zodiac signs were aligned at birth</li>
          <li>Provides clarity and direction for personality, relationships, career, and more</li>
          <li>Helps make more aligned choices and grow with confidence</li>
        </ul>
      `}
    />
  );
};

export const PlanetMeanings = () => {
  const planets = [
    { symbol: '☉', name: 'Sun', meaning: 'Core identity and life purpose' },
    { symbol: '☽', name: 'Moon', meaning: 'Emotions and inner world' },
    { symbol: '☿', name: 'Mercury', meaning: 'How you think and communicate' },
    { symbol: '♀', name: 'Venus', meaning: 'Love and values' },
    { symbol: '♂', name: 'Mars', meaning: 'Motivation and passion' },
    { symbol: '♃', name: 'Jupiter', meaning: 'Growth and expansion' },
    { symbol: '♄', name: 'Saturn', meaning: 'Structure and life lessons' },
    { symbol: '♅', name: 'Uranus', meaning: 'Transformation and change' },
    { symbol: '♆', name: 'Neptune', meaning: 'Spiritual energy' },
    { symbol: '♇', name: 'Pluto', meaning: 'Power and rebirth' }
  ];

  return (
    <div className="glass-card p-6 mb-6 opacity-0 animate-fade-in-up" style={{ animationDelay: '900ms', animationFillMode: 'forwards' }}>
      <div className="flex items-center gap-2 mb-4">
        <Sparkles className="w-5 h-5 text-cosmic-gold" />
        <h3 className="font-cinzel text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>
          Planet Meanings in Your Chart
        </h3>
      </div>
      <p className="text-secondary text-sm mb-4">
        Understanding what each planet represents helps you decode your birth chart's language:
      </p>
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {planets.map((planet) => (
          <div
            key={planet.name}
            className="text-center p-3 rounded-xl"
            style={{ backgroundColor: 'var(--bg-tertiary)' }}
          >
            <div className="text-2xl mb-1" style={{ color: '#f4c542' }}>{planet.symbol}</div>
            <div className="font-semibold text-sm" style={{ color: 'var(--text-primary)' }}>{planet.name}</div>
            <div className="text-xs" style={{ color: 'var(--text-muted)' }}>{planet.meaning}</div>
          </div>
        ))}
      </div>
    </div>
  );
};

export const FAQSection = () => {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  const faqs: FAQItem[] = [
    {
      question: 'How Accurate Is the Birth Chart Calculator?',
      answer: 'Highly accurate when exact birth date, time, and location are provided. Creates a precise snapshot of the sky at birth. Reveals Moon and Rising signs, house placements, and planetary positions with great accuracy.'
    },
    {
      question: 'What Can I Learn from My Birth Chart?',
      answer: 'You can discover how your unique energy shows up in love, career, emotions, communication, and personal growth. Learn your natural strengths, challenges, and life lessons. Find answers to why you\'re drawn to certain people or patterns. Get a life path map with purpose and potential insights.'
    },
    {
      question: 'What\'s the Difference Between Birth Chart and Horoscope?',
      answer: '<strong>Horoscope:</strong> Looks at your Sun sign only and gives broad daily/weekly predictions. <br/><strong>Birth Chart:</strong> A complete snapshot including your Sun, Moon, Rising signs, all planetary positions, houses, and aspects - providing deep personalized insight.'
    },
    {
      question: 'Can a Birth Chart Predict My Future?',
      answer: 'Not in a fixed way. Your birth chart shows energies, patterns, and potentials you\'re working with. It acts as a cosmic blueprint highlighting your strengths, challenges, and key life themes. Astrology offers guidance and insight—not predetermined fate.'
    },
    {
      question: 'Why Is Birth Time Required for Accurate Results?',
      answer: 'Your birth time is crucial because the Moon changes signs every 2.5 days and the Rising sign (Ascendant) changes every 2 hours. Without your exact birth time, your Moon and Rising sign calculations may be less accurate.'
    },
    {
      question: 'What\'s the Difference Between Sun, Moon, and Rising Signs?',
      answer: '<strong>Sun Sign:</strong> Your core identity and life purpose - who you are at your essence.<br/><strong>Moon Sign:</strong> Your emotional nature and inner world - how you feel and process emotions.<br/><strong>Rising Sign:</strong> Your outer presentation and how others perceive you - your social mask.'
    }
  ];

  return (
    <div className="glass-card p-6 mb-6 opacity-0 animate-fade-in-up" style={{ animationDelay: '1000ms', animationFillMode: 'forwards' }}>
      <div className="flex items-center gap-2 mb-4">
        <HelpCircle className="w-5 h-5 text-cosmic-rose" />
        <h3 className="font-cinzel text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>
          Frequently Asked Questions
        </h3>
      </div>
      <div className="space-y-3">
        {faqs.map((faq, index) => (
          <div
            key={index}
            className="rounded-xl overflow-hidden"
            style={{ backgroundColor: 'var(--bg-tertiary)' }}
          >
            <button
              onClick={() => setOpenIndex(openIndex === index ? null : index)}
              className="w-full px-4 py-3 flex items-center justify-between text-left transition-colors"
            >
              <span className="font-medium text-sm" style={{ color: 'var(--text-primary)' }}>
                {faq.question}
              </span>
              {openIndex === index ? (
                <ChevronUp className="w-4 h-4 flex-shrink-0" style={{ color: 'var(--text-muted)' }} />
              ) : (
                <ChevronDown className="w-4 h-4 flex-shrink-0" style={{ color: 'var(--text-muted)' }} />
              )}
            </button>
            {openIndex === index && (
              <div className="px-4 pb-4">
                <p className="text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }} dangerouslySetInnerHTML={{ __html: faq.answer }} />
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default { EducationSection, WhatIsBirthChart, PlanetMeanings, FAQSection };