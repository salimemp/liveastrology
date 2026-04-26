import { ArrowLeft, Star, Heart, Users, Sparkles } from 'lucide-react';

type PageType = 'home' | 'birth-chart' | 'synastry' | 'love' | 'blog' | 'terms' | 'privacy' | 'about' | 'contact' | 'refund';

interface AboutUsProps {
  onNavigate?: (page: PageType) => void;
}

export default function AboutUs({ onNavigate }: AboutUsProps) {
  const handleBack = () => {
    if (onNavigate) {
      onNavigate('home');
    }
  };

  const values = [
    {
      icon: <Star className="w-8 h-8" />,
      title: 'Accurate Astrology',
      description: 'Our calculations are based on traditional astrological principles combined with modern astronomical data for precise readings.'
    },
    {
      icon: <Heart className="w-8 h-8" />,
      title: 'Accessibility',
      description: 'We believe everyone deserves access to astrological insights. Our tools are free and easy to use for beginners and experts alike.'
    },
    {
      icon: <Users className="w-8 h-8" />,
      title: 'Community',
      description: 'We serve a growing community of astrology enthusiasts from around the world, united by curiosity about the cosmos.'
    },
    {
      icon: <Sparkles className="w-8 h-8" />,
      title: 'Continuous Improvement',
      description: 'We are always enhancing our calculators and adding new features to provide the best astrological experience possible.'
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

      <div className="glass-card p-8 md:p-12">
        <h1 className="font-cinzel text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-6 text-center">
          About Live Astrology
        </h1>

        <div className="prose prose-gray dark:prose-invert max-w-none space-y-6 text-gray-700 dark:text-gray-300">
          <section className="text-center mb-12">
            <div className="inline-flex items-center justify-center w-20 h-20 rounded-full mb-6" style={{ backgroundColor: '#40e0d0' }}>
              <svg className="w-12 h-12 text-white" viewBox="0 0 40 40" fill="none">
                <circle cx="20" cy="20" r="18" stroke="currentColor" strokeWidth="2" />
                <circle cx="20" cy="20" r="12" stroke="currentColor" strokeWidth="1.5" />
                <circle cx="20" cy="20" r="6" fill="currentColor" />
                <circle cx="20" cy="8" r="2" fill="#ffbf40" />
                <circle cx="30" cy="28" r="1.5" fill="#ffbf40" />
                <circle cx="10" cy="32" r="1.5" fill="#ffbf40" />
              </svg>
            </div>
            <p className="text-lg leading-relaxed">
              Live Astrology is a free online platform dedicated to making astrological knowledge accessible to everyone.
              Founded in 2024, we provide a suite of powerful astrology calculators that help people discover their
              cosmic identity through birth chart analysis.
            </p>
          </section>

          <section>
            <h2 className="font-cinzel text-xl font-semibold text-gray-900 dark:text-white mb-4 text-center">Our Mission</h2>
            <p>
              Our mission is to democratize astrology by providing free, accurate, and easy-to-understand astrological
              tools. We believe that understanding the positions of celestial bodies at the moment of your birth can provide
              valuable insights into your personality, relationships, and life path.
            </p>
          </section>

          <section>
            <h2 className="font-cinzel text-xl font-semibold text-gray-900 dark:text-white mb-4 text-center">What We Offer</h2>
            <div className="grid md:grid-cols-2 gap-4">
              <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Birth Chart Calculator</h3>
                <p className="text-sm">Complete analysis of your Sun, Moon, and Rising signs with detailed personality insights.</p>
              </div>
              <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Synastry Charts</h3>
                <p className="text-sm">Discover how your birth chart connects with your partner's chart for relationship insights.</p>
              </div>
              <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Love Compatibility</h3>
                <p className="text-sm">Find zodiac compatibility scores and personalized relationship guidance.</p>
              </div>
              <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Daily Horoscopes</h3>
                <p className="text-sm">Free daily astrology forecasts for all zodiac signs.</p>
              </div>
            </div>
          </section>

          <section>
            <h2 className="font-cinzel text-xl font-semibold text-gray-900 dark:text-white mb-4 text-center">Our Values</h2>
            <div className="grid md:grid-cols-2 gap-6">
              {values.map((value, index) => (
                <div key={index} className="flex gap-4">
                  <div className="flex-shrink-0 w-14 h-14 rounded-full flex items-center justify-center" style={{ backgroundColor: 'rgba(64, 224, 208, 0.15)' }}>
                    <div className="text-teal-600 dark:text-teal-400">{value.icon}</div>
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-white mb-1">{value.title}</h3>
                    <p className="text-sm">{value.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section>
            <h2 className="font-cinzel text-xl font-semibold text-gray-900 dark:text-white mb-4 text-center">Our Team</h2>
            <p>
              We are a passionate team of astrology enthusiasts, software developers, and designers united by our fascination
              with the cosmos. Our diverse backgrounds in technology, psychology, and ancient wisdom traditions allow us to
              create tools that bridge the gap between millennia-old astrological knowledge and modern digital experiences.
            </p>
          </section>

          <section>
            <h2 className="font-cinzel text-xl font-semibold text-gray-900 dark:text-white mb-4 text-center">Get In Touch</h2>
            <p>
              We love hearing from our community! Whether you have questions, suggestions, or just want to say hello,
              please feel free to reach out to us.
            </p>
            <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg text-center">
              <p className="font-medium text-gray-900 dark:text-white">Email</p>
              <p className="text-teal-600 dark:text-teal-400">hello@liveastrology.app</p>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
