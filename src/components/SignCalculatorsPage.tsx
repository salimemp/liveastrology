import { ArrowLeft, Star, Moon, Sun, Heart, Compass, TrendingUp } from 'lucide-react';

type PageType = 'home' | 'birth-chart' | 'synastry' | 'love' | 'blog' | 'terms' | 'privacy' | 'about' | 'contact' | 'refund' | 'sign-calculators';

interface SignCalculatorsPageProps {
  onNavigate?: (page: PageType) => void;
}

interface CalculatorItem {
  name: string;
  description: string;
  icon: React.ReactNode;
  page: PageType;
}

export default function SignCalculatorsPage({ onNavigate }: SignCalculatorsPageProps) {
  const handleBack = () => {
    if (onNavigate) {
      onNavigate('home');
    }
  };

  const calculators: CalculatorItem[] = [
    {
      name: 'Sun Sign Calculator',
      description: 'Discover your Sun sign - the core of your personality and the "you" that you present to the world.',
      icon: <Sun className="w-6 h-6" />,
      page: 'home'
    },
    {
      name: 'Moon Sign Calculator',
      description: 'Find your Moon sign - representing your emotions, intuition, and inner self.',
      icon: <Moon className="w-6 h-6" />,
      page: 'home'
    },
    {
      name: 'Rising Sign Calculator',
      description: 'Calculate your Ascendant (Rising sign) - the mask you wear and how others perceive you.',
      icon: <Star className="w-6 h-6" />,
      page: 'home'
    },
    {
      name: 'Venus Sign Calculator',
      description: 'Discover your Venus sign - governing love, beauty, values, and what you attract.',
      icon: <Heart className="w-6 h-6" />,
      page: 'home'
    },
    {
      name: 'Mars Sign Calculator',
      description: 'Find your Mars sign - representing your drive, energy, passion, and how you take action.',
      icon: <Compass className="w-6 h-6" />,
      page: 'home'
    },
    {
      name: 'Mercury Sign Calculator',
      description: 'Discover your Mercury sign - governing communication, intellect, and how you think.',
      icon: <TrendingUp className="w-6 h-6" />,
      page: 'home'
    }
  ];

  return (
    <div className="max-w-4xl mx-auto px-4 py-12">
      <button
        onClick={handleBack}
        className="flex items-center gap-2 mb-8 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Back to Home</span>
      </button>

      <div className="text-center mb-12">
        <h1 className="font-cinzel text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-4">
          Sign Calculators
        </h1>
        <p className="text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
          Explore your cosmic identity through our comprehensive suite of astrology calculators.
          Each calculator reveals a different aspect of your astrological chart.
        </p>
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        {calculators.map((calc, index) => (
          <div
            key={index}
            className="feature-card hover:shadow-xl transition-all duration-300 cursor-pointer group"
            onClick={() => onNavigate && onNavigate(calc.page)}
          >
            <div className="feature-icon group-hover:scale-110 transition-transform">
              {calc.icon}
            </div>
            <h3 className="feature-title text-center">{calc.name}</h3>
            <p className="feature-description text-center text-sm">{calc.description}</p>
            <button className="cta-button w-full mt-4 text-sm py-2">
              Calculate Now
            </button>
          </div>
        ))}
      </div>

      <div className="mt-12 text-center">
        <div className="glass-card p-8 max-w-2xl mx-auto">
          <h2 className="font-cinzel text-xl font-semibold text-gray-900 dark:text-white mb-3">
            Want a Complete Analysis?
          </h2>
          <p className="text-gray-600 dark:text-gray-300 mb-4">
            Our comprehensive Birth Chart Calculator provides all your signs in one complete report,
            along with detailed interpretations for each planet's placement.
          </p>
          <button
            onClick={() => onNavigate && onNavigate('birth-chart')}
            className="cta-button"
          >
            Get Your Full Birth Chart
          </button>
        </div>
      </div>
    </div>
  );
}
