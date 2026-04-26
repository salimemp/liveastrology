import React, { useState, useCallback } from 'react';
import { Sun, Moon, User, ShoppingBag, Star, Heart, Users } from 'lucide-react';
import StarfieldBackground from './components/StarfieldBackground';
import InputForm from './components/InputForm';
import ResultsDisplay from './components/ResultsDisplay';
import SynastryChart from './components/SynastryChart';
import LoveCalculator from './components/LoveCalculator';
import BlogList from './components/BlogPost';
import Footer from './components/Footer';
import TermsOfService from './components/TermsOfService';
import PrivacyPolicy from './components/PrivacyPolicy';
import AboutUs from './components/AboutUs';
import ContactPage from './components/ContactPage';
import RefundPolicy from './components/RefundPolicy';
import SignCalculatorsPage from './components/SignCalculatorsPage';
import { ThemeProvider, useTheme } from './context/ThemeContext';
import { calculateAstrology, BirthData, AstrologyResult } from './lib/astrology';

type PageType = 'home' | 'birth-chart' | 'synastry' | 'love' | 'blog' | 'terms' | 'privacy' | 'about' | 'contact' | 'refund' | 'sign-calculators';

interface NavigationProps {
  activePage: PageType;
  onNavigate: (page: PageType) => void;
}

function Navigation({ activePage, onNavigate }: NavigationProps) {
  const { theme } = useTheme();
  const navLinks: { name: string; page: PageType }[] = [
    { name: 'Home', page: 'home' },
    { name: 'Birth Chart Calculator', page: 'birth-chart' },
    { name: 'Synastry Chart Calculator', page: 'synastry' },
    { name: 'Love Calculator', page: 'love' },
    { name: 'Blog', page: 'blog' },
  ];

  const handleLogoClick = () => {
    onNavigate('home');
  };

  const navBgColor = theme === 'dark' ? 'rgba(13, 27, 42, 0.98)' : 'rgba(255, 255, 255, 0.97)';
  const navBorderColor = theme === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.08)';
  const linkColor = theme === 'dark' ? '#e0e6ed' : '#1a2332';
  const logoColor = theme === 'dark' ? '#ffffff' : '#1a2332';

  return (
    <nav className="w-full py-4 px-4 md:px-6 sticky top-0 z-40" style={{
      backgroundColor: navBgColor,
      backdropFilter: 'blur(10px)',
      borderBottom: `1px solid ${navBorderColor}`
    }}>
      <div className="nav-container flex items-center justify-between">
        {/* Logo */}
        <button
          onClick={handleLogoClick}
          className="flex items-center gap-2 hover:opacity-80 transition-opacity cursor-pointer bg-transparent border-none"
        >
          <svg className="w-10 h-10" viewBox="0 0 40 40" fill="none">
            <circle cx="20" cy="20" r="18" stroke="#40e0d0" strokeWidth="2" />
            <circle cx="20" cy="20" r="12" stroke="#40e0d0" strokeWidth="1.5" />
            <circle cx="20" cy="20" r="6" fill="#40e0d0" />
            <circle cx="20" cy="8" r="2" fill="#ffbf40" />
            <circle cx="30" cy="28" r="1.5" fill="#ffbf40" />
            <circle cx="10" cy="32" r="1.5" fill="#ffbf40" />
          </svg>
          <div className="hidden sm:block">
            <span className="font-cinzel font-bold text-lg" style={{ color: '#40e0d0' }}>LIVE</span>
            <span className="font-cinzel font-bold text-lg" style={{ color: logoColor }}> ASTROLOGY</span>
          </div>
        </button>

        {/* Nav Links - Hidden on mobile */}
        <div className="hidden lg:flex items-center gap-1">
          {navLinks.map((link) => (
            <button
              key={link.page}
              onClick={() => onNavigate(link.page)}
              style={{
                background: 'none',
                border: 'none',
                padding: '0.5rem 1rem',
                borderRadius: '0.5rem',
                cursor: 'pointer',
                fontWeight: activePage === link.page ? 700 : 600,
                color: linkColor,
                transition: 'all 0.2s ease'
              }}
            >
              {link.name}
            </button>
          ))}
        </div>

        {/* User Icons */}
        <div className="flex items-center gap-3">
          <button className="p-2 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors" aria-label="User account">
            <User className="w-5 h-5" style={{ color: linkColor }} />
          </button>
          <button className="p-2 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors relative" aria-label="Shopping cart">
            <ShoppingBag className="w-5 h-5" style={{ color: linkColor }} />
            <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">0</span>
          </button>
        </div>
      </div>
    </nav>
  );
}

function HeroSection() {
  return (
    <div className="text-center px-4 py-16 md:py-24">
      <h1 className="hero-title text-white dark:text-white" style={{ color: 'white' }}>
        Explore Free Astrology Charts
      </h1>
      <p className="hero-subtitle mb-12 text-white dark:text-white" style={{ color: 'rgba(255, 255, 255, 0.9)' }}>
        Discover your unique personality traits, understand how the planets influence your relationships,
        and gain valuable insights into your life path.
      </p>
    </div>
  );
}

interface FeatureCardsProps {
  onFeatureClick: (page: PageType) => void;
}

function FeatureCards({ onFeatureClick }: FeatureCardsProps) {
  const { theme } = useTheme();
  const features: { icon: React.ReactNode; title: string; description: string; page: PageType }[] = [
    {
      icon: <Star className="w-6 h-6 text-white" />,
      title: 'Birth Chart Calculator',
      description: 'Enter your birth details to get an accurate reading of your Sun, Moon, and Rising signs along with comprehensive analysis.',
      page: 'birth-chart',
    },
    {
      icon: <Users className="w-6 h-6 text-white" />,
      title: 'Synastry Chart Calculator',
      description: 'Discover how your birth chart connects with your partner. Uncover strengths, challenges, and compatibility insights.',
      page: 'synastry',
    },
    {
      icon: <Heart className="w-6 h-6 text-white" />,
      title: 'Love Calculator',
      description: 'Find out if you and your partner are destined for long-term harmony. Get personalized zodiac compatibility insights.',
      page: 'love',
    },
  ];

  return (
    <div className="px-4 pb-16">
      <div className="features-grid">
        {features.map((feature, index) => (
          <div key={index} className="feature-card text-center" style={{
            backgroundColor: theme === 'dark' ? 'rgba(27, 38, 59, 0.98)' : 'rgba(255, 255, 255, 0.95)',
            border: theme === 'dark' ? '1px solid rgba(255,255,255,0.15)' : '1px solid rgba(0,0,0,0.08)'
          }}>
            <div className="feature-icon mx-auto">
              {feature.icon}
            </div>
            <h3 className="feature-title" style={{ color: theme === 'dark' ? '#ffffff' : '#1a1a3a' }}>{feature.title}</h3>
            <p className="feature-description" style={{ color: theme === 'dark' ? '#b8c5d6' : '#3a4558' }}>{feature.description}</p>
            <button onClick={() => onFeatureClick(feature.page)} className="cta-button" style={{ color: '#0a1520', fontWeight: 700 }}>Get Free Report</button>
          </div>
        ))}
      </div>
    </div>
  );
}

function AppContent() {
  const [birthData, setBirthData] = useState<BirthData | null>(null);
  const [result, setResult] = useState<AstrologyResult | null>(null);
  const [isCalculating, setIsCalculating] = useState(false);
  const [userName, setUserName] = useState('');
  const [activePage, setActivePage] = useState<PageType>('home');
  const { theme, toggleTheme } = useTheme();

  const handleCalculate = useCallback(async (data: BirthData, name: string) => {
    setBirthData(data);
    setUserName(name);
    setIsCalculating(true);

    await new Promise(resolve => setTimeout(resolve, 1500));

    const astrologyResult = calculateAstrology(data);
    setResult(astrologyResult);
    setIsCalculating(false);
  }, []);

  const handleReset = useCallback(() => {
    setBirthData(null);
    setResult(null);
    setIsCalculating(false);
    setUserName('');
  }, []);

  const handleNavigate = (page: PageType) => {
    setActivePage(page);
    if (page !== 'birth-chart' || result) {
      handleReset();
    }
  };

  const handleStartCalculator = () => {
    setActivePage('birth-chart');
  };

  const handleFeatureClick = (page: PageType) => {
    setActivePage(page);
  };

  // Render different pages based on activePage
  const renderPageContent = () => {
    if (result) {
      return (
        <div className="px-4 pb-16 max-w-6xl mx-auto">
          <ResultsDisplay
            result={result}
            birthData={birthData!}
            userName={userName}
            onReset={handleReset}
          />
        </div>
      );
    }

    switch (activePage) {
      case 'birth-chart':
        return (
          <div className="max-w-lg mx-auto px-4 pb-16">
            <div className="glass-card p-6">
              <h2 className="font-cinzel text-2xl font-bold text-center mb-6 text-gray-900 dark:text-white">
                Birth Chart Calculator
              </h2>
              <InputForm onCalculate={handleCalculate} isCalculating={isCalculating} />
            </div>
          </div>
        );
      case 'synastry':
        return (
          <div className="max-w-lg mx-auto px-4 pb-16">
            <SynastryChart />
          </div>
        );
      case 'love':
        return (
          <div className="max-w-lg mx-auto px-4 pb-16">
            <div className="glass-card p-6">
              <LoveCalculator />
            </div>
          </div>
        );
      case 'blog':
        return <BlogList />;
      case 'terms':
        return <TermsOfService onNavigate={handleNavigate} />;
      case 'privacy':
        return <PrivacyPolicy onNavigate={handleNavigate} />;
      case 'about':
        return <AboutUs onNavigate={handleNavigate} />;
      case 'contact':
        return <ContactPage onNavigate={handleNavigate} />;
      case 'refund':
        return <RefundPolicy onNavigate={handleNavigate} />;
      case 'sign-calculators':
        return <SignCalculatorsPage onNavigate={handleNavigate} />;
      case 'home':
      default:
        return (
          <>
            <HeroSection />
            <FeatureCards onFeatureClick={handleFeatureClick} />
            <div className="text-center px-4 pb-16">
              <button
                onClick={handleStartCalculator}
                className="cta-button text-lg px-8 py-3"
              >
                Start Your Free Birth Chart
              </button>
            </div>
            <div className="max-w-lg mx-auto px-4 pb-16">
              <div className="glass-card p-6">
                <InputForm onCalculate={handleCalculate} isCalculating={isCalculating} />
              </div>
            </div>
          </>
        );
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      {theme === 'dark' && <StarfieldBackground />}

      <main className="relative z-10 flex-1">
        {/* Navigation Header */}
        <Navigation activePage={activePage} onNavigate={handleNavigate} />

        {/* Main Content */}
        {renderPageContent()}
      </main>

      {/* Footer */}
      <Footer onNavigate={handleNavigate} />

      {/* Theme Toggle - Fixed position */}
      <button
        onClick={toggleTheme}
        className="fixed bottom-6 right-6 w-14 h-14 rounded-full shadow-lg transition-all duration-300 hover:scale-110 z-50 flex items-center justify-center"
        style={{
          backgroundColor: '#ffffff',
          border: '3px solid #40e0d0',
          boxShadow: '0 4px 20px rgba(64, 224, 208, 0.4)'
        }}
        aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
      >
        {theme === 'dark' ? (
          <Sun className="w-7 h-7" style={{ color: '#ffbf40' }} />
        ) : (
          <Moon className="w-7 h-7" style={{ color: '#0d1b2a' }} />
        )}
      </button>
    </div>
  );
}

function App() {
  return (
    <ThemeProvider>
      <AppContent />
    </ThemeProvider>
  );
}

export default App;
