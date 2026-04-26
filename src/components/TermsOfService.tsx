import { ArrowLeft } from 'lucide-react';

type PageType = 'home' | 'birth-chart' | 'synastry' | 'love' | 'blog' | 'terms' | 'privacy' | 'about' | 'contact' | 'refund';

interface TermsOfServiceProps {
  onNavigate?: (page: PageType) => void;
}

export default function TermsOfService({ onNavigate }: TermsOfServiceProps) {
  const handleBack = () => {
    if (onNavigate) {
      onNavigate('home');
    }
  };

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
        <h1 className="font-cinzel text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-6">
          Terms of Service
        </h1>

        <p className="text-sm text-gray-500 dark:text-gray-400 mb-8">
          Last updated: April 25, 2025
        </p>

        <div className="prose prose-gray dark:prose-invert max-w-none space-y-6 text-gray-700 dark:text-gray-300">
          <section>
            <h2 className="font-cinzel text-xl font-semibold text-gray-900 dark:text-white mb-3">1. Acceptance of Terms</h2>
            <p>
              By accessing and using Live Astrology's website and services, you accept and agree to be bound by the terms
              and provision of this agreement. If you do not agree to abide by these terms, please do not use this service.
            </p>
          </section>

          <section>
            <h2 className="font-cinzel text-xl font-semibold text-gray-900 dark:text-white mb-3">2. Description of Service</h2>
            <p>
              Live Astrology provides free astrology calculators and birth chart analysis tools. Our services include,
              but are not limited to: Birth Chart Calculator, Synastry Chart Calculator, Love Calculator, and Daily Horoscopes.
            </p>
            <p>
              All content provided on this website is for informational and entertainment purposes only. Astrology readings
              should not be used as a substitute for professional advice in any area including but not limited to legal,
              financial, medical, or psychological matters.
            </p>
          </section>

          <section>
            <h2 className="font-cinzel text-xl font-semibold text-gray-900 dark:text-white mb-3">3. User Responsibilities</h2>
            <p>As a user of Live Astrology, you agree to:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li>Use the service only for lawful purposes</li>
              <li>Not attempt to gain unauthorized access to our systems</li>
              <li>Not use automated tools to scrape or extract data from our website</li>
              <li>Provide accurate information when using our calculators</li>
              <li>Respect other users and maintain civil discourse</li>
            </ul>
          </section>

          <section>
            <h2 className="font-cinzel text-xl font-semibold text-gray-900 dark:text-white mb-3">4. Intellectual Property</h2>
            <p>
              All content on this website, including but not limited to text, graphics, logos, button icons, images,
              audio clips, digital downloads, data compilations, and software, is the property of Live Astrology or its
              content suppliers and is protected by international copyright laws.
            </p>
          </section>

          <section>
            <h2 className="font-cinzel text-xl font-semibold text-gray-900 dark:text-white mb-3">5. Disclaimer of Warranties</h2>
            <p>
              THE SERVICE IS PROVIDED "AS IS" AND "AS AVAILABLE" WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
              INCLUDING BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE,
              AND NON-INFRINGEMENT.
            </p>
            <p>
              Live Astrology does not warrant that the service will be uninterrupted, timely, secure, or error-free.
              Astrology predictions and readings are based on traditional astrological principles and should be regarded
              as entertainment rather than factual predictions.
            </p>
          </section>

          <section>
            <h2 className="font-cinzel text-xl font-semibold text-gray-900 dark:text-white mb-3">6. Limitation of Liability</h2>
            <p>
              In no event shall Live Astrology be liable for any indirect, incidental, special, consequential, or punitive
              damages, including without limitation, loss of profits, data, use, goodwill, or other intangible losses, resulting
              from (i) your access to or use of or inability to access or use the service.
            </p>
          </section>

          <section>
            <h2 className="font-cinzel text-xl font-semibold text-gray-900 dark:text-white mb-3">7. Privacy Policy</h2>
            <p>
              Your privacy is important to us. Please review our Privacy Policy, which also governs your use of the service,
              to understand how we collect, use, and safeguard the information you provide to us.
            </p>
          </section>

          <section>
            <h2 className="font-cinzel text-xl font-semibold text-gray-900 dark:text-white mb-3">8. Modifications to Service</h2>
            <p>
              Live Astrology reserves the right to modify or discontinue, temporarily or permanently, the service (or any part
              thereof) with or without notice. We shall not be liable to you or to any third party for any modification,
              suspension, or discontinuance of the service.
            </p>
          </section>

          <section>
            <h2 className="font-cinzel text-xl font-semibold text-gray-900 dark:text-white mb-3">9. Governing Law</h2>
            <p>
              These Terms of Service shall be governed by and construed in accordance with the laws of the United States,
              without regard to its conflict of law provisions. You agree to submit to the personal and exclusive jurisdiction
              of the courts located within the United States for the resolution of any disputes.
            </p>
          </section>

          <section>
            <h2 className="font-cinzel text-xl font-semibold text-gray-900 dark:text-white mb-3">10. Contact Information</h2>
            <p>
              If you have any questions about these Terms of Service, please contact us at:
            </p>
            <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <p className="font-medium text-gray-900 dark:text-white">Live Astrology</p>
              <p className="text-gray-600 dark:text-gray-400">Email: legal@liveastrology.app</p>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
