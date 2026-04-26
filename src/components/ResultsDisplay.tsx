import { useState } from 'react';
import { ArrowLeft, Share2, Copy, Check, RefreshCw, MapPin, Calendar, Clock, Sparkles } from 'lucide-react';
import { AstrologyResult, BirthData } from '../lib/astrology';
import SignCard from './SignCard';
import { ElementBalanceChart, ModalityChart } from './Charts';
import CompatibilitySection from './CompatibilitySection';
import { WhatIsBirthChart, PlanetMeanings, FAQSection } from './EducationSection';

interface ResultsDisplayProps {
  result: AstrologyResult;
  birthData: BirthData;
  userName: string;
  onReset: () => void;
}

const ResultsDisplay = ({ result, birthData, userName, onReset }: ResultsDisplayProps) => {
  const [copied, setCopied] = useState(false);

  const handleCopyShare = async () => {
    const shareText = generateShareText();
    try {
      await navigator.clipboard.writeText(shareText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      const textarea = document.createElement('textarea');
      textarea.value = shareText;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleNativeShare = async () => {
    const shareText = generateShareText();
    if (navigator.share) {
      try {
        await navigator.share({
          title: `${userName}'s Astrology Chart`,
          text: shareText
        });
      } catch {
        // User cancelled or error
      }
    } else {
      handleCopyShare();
    }
  };

  const generateShareText = (): string => {
    return `
✨ ${userName}'s Astrology Chart ✨

☀️ Sun Sign: ${result.sun.name}
🌙 Moon Sign: ${result.moon.name}
⬆️ Rising Sign: ${result.rising.name}

📍 Born: ${result.birthChart.location}
📅 Date: ${result.birthChart.date}
🕐 Time: ${result.birthChart.time}

🌟 Element Balance: ${result.elementBalance.fire}% Fire, ${result.elementBalance.earth}% Earth, ${result.elementBalance.air}% Air, ${result.elementBalance.water}% Water

Calculate your chart at [Sun Moon Rising Calculator]
`.trim();
  };

  return (
    <div className="space-y-6">
      {/* Header with actions */}
      <div className="flex items-center justify-between gap-4">
        <button
          onClick={onReset}
          className="btn-secondary flex items-center gap-2"
        >
          <ArrowLeft className="w-4 h-4" />
          <span className="hidden sm:inline">New Calculation</span>
        </button>

        <div className="flex items-center gap-2">
          <button
            onClick={handleCopyShare}
            className="btn-secondary flex items-center gap-2"
          >
            {copied ? (
              <>
                <Check className="w-4 h-4" style={{ color: '#1abc9c' }} />
                <span className="hidden sm:inline">Copied!</span>
              </>
            ) : (
              <>
                <Copy className="w-4 h-4" />
                <span className="hidden sm:inline">Copy</span>
              </>
            )}
          </button>

          <button
            onClick={handleNativeShare}
            className="btn-secondary flex items-center gap-2"
          >
            <Share2 className="w-4 h-4" />
            <span className="hidden sm:inline">Share</span>
          </button>
        </div>
      </div>

      {/* Personalized Greeting */}
      <div className="text-center opacity-0 animate-fade-in-up" style={{ animationDelay: '0ms', animationFillMode: 'forwards' }}>
        <h2 className="font-cinzel text-2xl md:text-3xl mb-2" style={{ color: 'var(--text-primary)' }}>
          Hello, {userName}! ✨
        </h2>
        <p className="text-secondary">
          Your celestial identity has been revealed
        </p>
      </div>

      {/* Birth Info Summary */}
      <div className="glass-card p-4 opacity-0 animate-fade-in-up" style={{ animationDelay: '50ms', animationFillMode: 'forwards' }}>
        <div className="flex flex-wrap items-center justify-center gap-4 text-sm text-secondary">
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4" style={{ color: '#f4c542' }} />
            <span>{result.birthChart.date}</span>
          </div>
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4" style={{ color: '#c0c0e0' }} />
            <span>{result.birthChart.time}</span>
          </div>
          <div className="flex items-center gap-2">
            <MapPin className="w-4 h-4" style={{ color: '#e84a7f' }} />
            <span>{result.birthChart.location}</span>
          </div>
        </div>
      </div>

      {/* Main Title */}
      <div className="text-center opacity-0 animate-fade-in-up" style={{ animationDelay: '100ms', animationFillMode: 'forwards' }}>
        <div className="inline-flex items-center gap-2 mb-2">
          <Sparkles className="w-5 h-5" style={{ color: '#f4c542' }} />
          <span className="font-cormorant text-sm uppercase tracking-widest" style={{ color: '#f4c542' }}>
            Your Complete Astrological Profile
          </span>
          <Sparkles className="w-5 h-5" style={{ color: '#f4c542' }} />
        </div>
        <h3 className="font-cinzel text-xl md:text-2xl" style={{ color: 'var(--text-primary)' }}>
          The Trinity of Your Soul
        </h3>
      </div>

      {/* Sign Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-6">
        <SignCard sign={result.sun} type="sun" delay={200} />
        <SignCard sign={result.moon} type="moon" delay={300} />
        <SignCard sign={result.rising} type="rising" delay={400} />
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6">
        <ElementBalanceChart balance={result.elementBalance} />
        <ModalityChart balance={result.modalityBalance} />
      </div>

      {/* Compatibility Section */}
      <CompatibilitySection compatibility={result.compatibility} sunSign={result.sun.name} />

      {/* Educational Sections */}
      <WhatIsBirthChart />
      <PlanetMeanings />
      <FAQSection />

      {/* Detailed Summary */}
      <div className="glass-card p-5 md:p-6 opacity-0 animate-fade-in-up" style={{ animationDelay: '900ms', animationFillMode: 'forwards' }}>
        <h3 className="font-cinzel text-lg font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>
          {userName}'s Cosmic Identity
        </h3>

        <div className="space-y-4">
          <p className="text-secondary leading-relaxed">
            As a <span style={{ color: '#f4c542', fontWeight: 600 }}>{result.sun.name}</span> with
            <span style={{ color: '#c0c0e0', fontWeight: 600 }}> {result.moon.name}</span> Moon and
            <span style={{ color: '#e84a7f', fontWeight: 600 }}> {result.rising.name}</span> Rising,
            you possess a unique blend of celestial influences, {userName}.
          </p>

          <p className="text-secondary leading-relaxed">
            Your <strong className="text-primary">Sun</strong> represents your core essence and main life purpose.
            Your <strong className="text-primary">Moon</strong> governs your emotional world and inner self.
            Your <strong className="text-primary">Rising sign</strong> shapes how others perceive you and your first impressions.
          </p>

          <p className="text-muted leading-relaxed text-sm">
            This powerful combination creates your unique personality tapestry, {userName}. Understanding these three pillars
            of your astrological identity can help you navigate relationships, career choices, and personal growth
            with greater self-awareness and cosmic alignment.
          </p>
        </div>
      </div>

      {/* Footer Actions */}
      <div className="text-center pt-4">
        <button
          onClick={onReset}
          className="btn-primary inline-flex items-center gap-2"
        >
          <RefreshCw className="w-4 h-4" />
          Calculate for Another Birth
        </button>
      </div>

      {/* Disclaimer */}
      <div className="text-center">
        <p className="text-xs text-subtle max-w-md mx-auto">
          This calculator provides entertainment and general guidance based on simplified astrological calculations.
          For precise birth chart analysis, consult a professional astrologer with access to ephemeris data and
          detailed calculation methods.
        </p>
      </div>
    </div>
  );
};

export default ResultsDisplay;