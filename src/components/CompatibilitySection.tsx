import { Heart, Users, Zap } from 'lucide-react';
import { CompatibilityInfo } from '../lib/astrology';

interface CompatibilitySectionProps {
  compatibility: CompatibilityInfo;
  sunSign: string;
}

export const CompatibilitySection = ({ compatibility, sunSign }: CompatibilitySectionProps) => {
  return (
    <div className="glass-card p-5 md:p-6 opacity-0 animate-fade-in-up" style={{ animationDelay: '800ms', animationFillMode: 'forwards' }}>
      <h3 className="font-cinzel text-lg font-semibold text-white mb-2 flex items-center gap-2">
        <Heart className="w-5 h-5 text-cosmic-rose" />
        Compatible Signs
      </h3>

      <p className="text-xs text-[#a0a0c0] mb-4">
        Based on your {sunSign} element — signs that resonate with your energy
      </p>

      <div className="space-y-4">
        {/* Best Matches */}
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Heart className="w-4 h-4 text-cosmic-rose" />
            <span className="text-xs font-semibold text-cosmic-rose uppercase tracking-wider">
              Soul Matches
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            {compatibility.bestMatches.map((sign) => (
              <span
                key={sign}
                className="px-3 py-1.5 bg-gradient-to-r from-cosmic-rose/20 to-cosmic-purple/20 border border-cosmic-rose/30 rounded-full text-xs text-white"
              >
                {sign}
              </span>
            ))}
          </div>
          <p className="text-xs text-[#606080] mt-1">
            Deep connection, shared values, mutual understanding
          </p>
        </div>

        {/* Friendship Matches */}
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Users className="w-4 h-4 text-cosmic-blue" />
            <span className="text-xs font-semibold text-cosmic-blue uppercase tracking-wider">
              Harmony Partners
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            {compatibility.friendshipMatches.map((sign) => (
              <span
                key={sign}
                className="px-3 py-1.5 bg-gradient-to-r from-cosmic-blue/20 to-cosmic-teal/20 border border-cosmic-blue/30 rounded-full text-xs text-white"
              >
                {sign}
              </span>
            ))}
          </div>
          <p className="text-xs text-[#606080] mt-1">
            Intellectual stimulation, lively exchanges, balanced perspective
          </p>
        </div>

        {/* Growth Opportunities */}
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Zap className="w-4 h-4 text-cosmic-gold" />
            <span className="text-xs font-semibold text-cosmic-gold uppercase tracking-wider">
              Growth Opportunities
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            {compatibility.challengingMatches.map((sign) => (
              <span
                key={sign}
                className="px-3 py-1.5 bg-gradient-to-r from-cosmic-gold/20 to-element-fire/20 border border-cosmic-gold/30 rounded-full text-xs text-white"
              >
                {sign}
              </span>
            ))}
          </div>
          <p className="text-xs text-[#606080] mt-1">
            Lessons in balance, complementary opposites, mutual growth
          </p>
        </div>
      </div>

      <div className="mt-4 pt-4 border-t border-space-600/30">
        <p className="text-xs text-[#a0a0c0] italic">
          Remember: Astrology is a guide, not a rule. Any sign can find harmony with any other sign through understanding and effort.
        </p>
      </div>
    </div>
  );
};

export default CompatibilitySection;
