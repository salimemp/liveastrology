import { useState } from 'react';
import { Heart, Send, Mail } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';

type PageType = 'home' | 'birth-chart' | 'synastry' | 'love' | 'blog' | 'terms' | 'privacy' | 'about' | 'contact' | 'refund' | 'sign-calculators';

interface FooterProps {
  onNavigate?: (page: PageType) => void;
}

export default function Footer({ onNavigate }: FooterProps) {
  const { theme } = useTheme();
  const [email, setEmail] = useState('');
  const [subscribed, setSubscribed] = useState(false);

  const handleSubscribe = (e: React.FormEvent) => {
    e.preventDefault();
    if (email) {
      setSubscribed(true);
      setEmail('');
      setTimeout(() => setSubscribed(false), 3000);
    }
  };

  const handleLinkClick = (page: PageType) => {
    if (onNavigate) {
      onNavigate(page);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  // Internal navigation links (within the app)
  const internalLinks = [
    { name: 'Birth Chart Calculator', page: 'birth-chart' as PageType },
    { name: 'Synastry Chart Calculator', page: 'synastry' as PageType },
    { name: 'Love Compatibility Calculator', page: 'love' as PageType },
    { name: 'Sign Calculators', page: 'sign-calculators' as PageType },
  ];

  const signCalculators = [
    { name: 'Sun Sign Calculator', page: 'sign-calculators' as PageType },
    { name: 'Moon Sign Calculator', page: 'sign-calculators' as PageType },
    { name: 'Rising Sign Calculator', page: 'sign-calculators' as PageType },
    { name: 'Venus Sign Calculator', page: 'sign-calculators' as PageType },
    { name: 'Mars Sign Calculator', page: 'sign-calculators' as PageType },
    { name: 'Mercury Sign Calculator', page: 'sign-calculators' as PageType },
  ];

  // Solid dark background colors to ensure text visibility
  const newsletterBg = '#1b263b';
  const mainFooterBg = '#0d1b2a';
  const textWhite = '#ffffff';
  const textLight = '#e5e7eb';
  const textMuted = '#9ca3af';
  const borderColor = 'rgba(64, 224, 208, 0.3)';

  return (
    <footer style={{ backgroundColor: mainFooterBg }}>
      {/* Newsletter Section - Solid Background */}
      <div style={{ backgroundColor: newsletterBg, borderTop: '2px solid #40e0d0' }}>
        <div className="max-w-2xl mx-auto text-center py-12 px-4">
          <h3 style={{ fontFamily: 'Cinzel, serif', fontSize: '1.25rem', fontWeight: 700, letterSpacing: '0.05em', color: textWhite, marginBottom: '0.5rem' }}>
            FREE DAILY HOROSCOPES & ASTROLOGY UPDATES
          </h3>
          <p style={{ fontSize: '0.875rem', color: 'rgba(255,255,255,0.9)', marginBottom: '1.5rem' }}>
            Subscribe for free astrology insights, daily horoscopes, and cosmic guidance delivered to your inbox.
          </p>
          <form onSubmit={handleSubscribe} className="flex flex-col sm:flex-row gap-3 max-w-md mx-auto">
            <div className="flex-1 relative">
              <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5" style={{ color: '#6b7280' }} />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your email"
                style={{
                  backgroundColor: '#ffffff',
                  border: '2px solid #d1d5db',
                  color: '#1f2937',
                  borderRadius: '9999px',
                  paddingLeft: '3rem',
                  paddingRight: '1rem',
                  paddingTop: '0.75rem',
                  paddingBottom: '0.75rem',
                  fontSize: '0.875rem',
                  width: '100%'
                }}
              />
            </div>
            <button
              type="submit"
              style={{
                backgroundColor: '#40e0d0',
                color: '#0a1520',
                padding: '0.75rem 1.5rem',
                borderRadius: '9999px',
                fontWeight: 600,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.5rem',
                border: 'none',
                cursor: 'pointer'
              }}
            >
              <Send className="w-4 h-4" />
              Subscribe Free
            </button>
          </form>
          {subscribed && (
            <p style={{ fontSize: '0.875rem', marginTop: '0.75rem', color: textWhite }}>
              <span style={{ color: '#86efac' }}>✓</span>
              Thanks for subscribing! You'll receive free daily horoscopes.
            </p>
          )}
          <p style={{ fontSize: '0.75rem', marginTop: '0.75rem', color: 'rgba(255,255,255,0.7)' }}>
            By subscribing, you agree to our{' '}
            <button onClick={() => handleLinkClick('terms')} style={{ textDecoration: 'underline', color: textWhite, fontWeight: 600, background: 'none', border: 'none', cursor: 'pointer' }}>Terms</button> &{' '}
            <button onClick={() => handleLinkClick('privacy')} style={{ textDecoration: 'underline', color: textWhite, fontWeight: 600, background: 'none', border: 'none', cursor: 'pointer' }}>Privacy Policy</button>
          </p>
        </div>
      </div>

      {/* Main Footer Content - Solid Background */}
      <div style={{ backgroundColor: mainFooterBg }}>
        <div className="max-w-7xl mx-auto px-4 py-12">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {/* Resources Column */}
            <div>
              <h4 style={{ fontFamily: 'Cinzel, serif', fontSize: '0.875rem', fontWeight: 700, letterSpacing: '0.05em', color: textWhite, marginBottom: '1rem' }}>RESOURCES</h4>
              <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                {internalLinks.map((item) => (
                  <li key={item.name} style={{ marginBottom: '0.5rem' }}>
                    <button
                      onClick={() => handleLinkClick(item.page)}
                      style={{
                        background: 'none',
                        border: 'none',
                        padding: 0,
                        textAlign: 'left',
                        cursor: 'pointer',
                        color: textLight,
                        fontSize: '0.875rem',
                        fontWeight: 500,
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.375rem',
                        width: '100%'
                      }}
                    >
                      {item.name}
                    </button>
                  </li>
                ))}
              </ul>
            </div>

            {/* Sign Calculators Column */}
            <div>
              <h4 style={{ fontFamily: 'Cinzel, serif', fontSize: '0.875rem', fontWeight: 700, letterSpacing: '0.05em', color: textWhite, marginBottom: '1rem' }}>SIGN CALCULATORS</h4>
              <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                {signCalculators.map((item) => (
                  <li key={item.name} style={{ marginBottom: '0.5rem' }}>
                    <button
                      onClick={() => handleLinkClick(item.page)}
                      style={{
                        background: 'none',
                        border: 'none',
                        padding: 0,
                        textAlign: 'left',
                        cursor: 'pointer',
                        color: textLight,
                        fontSize: '0.875rem',
                        fontWeight: 500,
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.375rem',
                        width: '100%'
                      }}
                    >
                      {item.name}
                    </button>
                  </li>
                ))}
              </ul>
            </div>

            {/* About Column */}
            <div>
              <h4 style={{ fontFamily: 'Cinzel, serif', fontSize: '0.875rem', fontWeight: 700, letterSpacing: '0.05em', color: textWhite, marginBottom: '1rem' }}>COMPANY</h4>
              <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                <li style={{ marginBottom: '0.5rem' }}>
                  <button
                    onClick={() => handleLinkClick('about')}
                    style={{
                      background: 'none',
                      border: 'none',
                      padding: 0,
                      textAlign: 'left',
                      cursor: 'pointer',
                      color: textLight,
                      fontSize: '0.875rem',
                      fontWeight: 500,
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.375rem',
                      width: '100%'
                    }}
                  >
                    About Us
                  </button>
                </li>
                <li style={{ marginBottom: '0.5rem' }}>
                  <button
                    onClick={() => handleLinkClick('contact')}
                    style={{
                      background: 'none',
                      border: 'none',
                      padding: 0,
                      textAlign: 'left',
                      cursor: 'pointer',
                      color: textLight,
                      fontSize: '0.875rem',
                      fontWeight: 500,
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.375rem',
                      width: '100%'
                    }}
                  >
                    Contact Us
                  </button>
                </li>
                <li style={{ marginBottom: '0.5rem' }}>
                  <button
                    onClick={() => handleLinkClick('privacy')}
                    style={{
                      background: 'none',
                      border: 'none',
                      padding: 0,
                      textAlign: 'left',
                      cursor: 'pointer',
                      color: textLight,
                      fontSize: '0.875rem',
                      fontWeight: 500,
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.375rem',
                      width: '100%'
                    }}
                  >
                    Privacy Policy
                  </button>
                </li>
                <li style={{ marginBottom: '0.5rem' }}>
                  <button
                    onClick={() => handleLinkClick('terms')}
                    style={{
                      background: 'none',
                      border: 'none',
                      padding: 0,
                      textAlign: 'left',
                      cursor: 'pointer',
                      color: textLight,
                      fontSize: '0.875rem',
                      fontWeight: 500,
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.375rem',
                      width: '100%'
                    }}
                  >
                    Terms and Conditions
                  </button>
                </li>
                <li style={{ marginBottom: '0.5rem' }}>
                  <button
                    onClick={() => handleLinkClick('refund')}
                    style={{
                      background: 'none',
                      border: 'none',
                      padding: 0,
                      textAlign: 'left',
                      cursor: 'pointer',
                      color: textLight,
                      fontSize: '0.875rem',
                      fontWeight: 500,
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.375rem',
                      width: '100%'
                    }}
                  >
                    Refund Policy
                  </button>
                </li>
              </ul>
            </div>

            {/* Logo & Description Column */}
            <div>
              <button
                onClick={() => handleLinkClick('home')}
                style={{
                  background: 'none',
                  border: 'none',
                  padding: 0,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  marginBottom: '1rem',
                  opacity: 0.8
                }}
              >
                <svg className="w-10 h-10" viewBox="0 0 40 40" fill="none">
                  <circle cx="20" cy="20" r="18" stroke="#40e0d0" strokeWidth="2" />
                  <circle cx="20" cy="20" r="12" stroke="#40e0d0" strokeWidth="1.5" />
                  <circle cx="20" cy="20" r="6" fill="#40e0d0" />
                  <circle cx="20" cy="8" r="2" fill="#ffbf40" />
                  <circle cx="30" cy="28" r="1.5" fill="#ffbf40" />
                  <circle cx="10" cy="32" r="1.5" fill="#ffbf40" />
                </svg>
                <div>
                  <span style={{ fontFamily: 'Cinzel, serif', fontWeight: 700, fontSize: '1.125rem', color: '#40e0d0' }}>LIVE</span>
                  <span style={{ fontFamily: 'Cinzel, serif', fontWeight: 700, fontSize: '1.125rem', color: textWhite }}> ASTROLOGY</span>
                </div>
              </button>
              <p style={{ fontSize: '0.875rem', color: textLight, marginBottom: '1rem', lineHeight: 1.6 }}>
                Discover your cosmic identity through our free astrology calculators and detailed birth chart analysis.
              </p>
              <div style={{ display: 'flex', gap: '0.75rem' }}>
                <a href="https://twitter.com/liveastrology" target="_blank" rel="noopener noreferrer" style={{ width: '2.5rem', height: '2.5rem', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(64, 224, 208, 0.15)', transition: 'background-color 0.2s' }} aria-label="Twitter">
                  <svg style={{ width: '1.25rem', height: '1.25rem', color: textWhite }} fill="currentColor" viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
                </a>
                <a href="https://facebook.com/liveastrology" target="_blank" rel="noopener noreferrer" style={{ width: '2.5rem', height: '2.5rem', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(64, 224, 208, 0.15)', transition: 'background-color 0.2s' }} aria-label="Facebook">
                  <svg style={{ width: '1.25rem', height: '1.25rem', color: textWhite }} fill="currentColor" viewBox="0 0 24 24"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>
                </a>
                <a href="https://instagram.com/liveastrology" target="_blank" rel="noopener noreferrer" style={{ width: '2.5rem', height: '2.5rem', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(64, 224, 208, 0.15)', transition: 'background-color 0.2s' }} aria-label="Instagram">
                  <svg style={{ width: '1.25rem', height: '1.25rem', color: textWhite }} fill="currentColor" viewBox="0 0 24 24"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/></svg>
                </a>
                <a href="https://youtube.com/@liveastrology" target="_blank" rel="noopener noreferrer" style={{ width: '2.5rem', height: '2.5rem', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(64, 224, 208, 0.15)', transition: 'background-color 0.2s' }} aria-label="YouTube">
                  <svg style={{ width: '1.25rem', height: '1.25rem', color: textWhite }} fill="currentColor" viewBox="0 0 24 24"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>
                </a>
                <a href="https://tiktok.com/@liveastrology" target="_blank" rel="noopener noreferrer" style={{ width: '2.5rem', height: '2.5rem', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(64, 224, 208, 0.15)', transition: 'background-color 0.2s' }} aria-label="TikTok">
                  <svg style={{ width: '1.25rem', height: '1.25rem', color: textWhite }} fill="currentColor" viewBox="0 0 24 24"><path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5 20.1a6.34 6.34 0 0 0 10.86-4.43v-7a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1-.1z"/></svg>
                </a>
              </div>
            </div>
          </div>

          {/* Bottom Bar */}
          <div style={{ marginTop: '3rem', paddingTop: '2rem', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem' }}>
              <p style={{ fontSize: '0.875rem', color: textLight }}>
                Copyright © 2025 Live Astrology. All rights reserved.
              </p>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.875rem', color: textLight }}>
                <span>Made with</span>
                <Heart className="w-4 h-4" style={{ color: '#ec4899', fill: '#ec4899' }} />
                <span>for astrology lovers</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
