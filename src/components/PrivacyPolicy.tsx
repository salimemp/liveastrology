import { ArrowLeft } from 'lucide-react';

type PageType = 'home' | 'birth-chart' | 'synastry' | 'love' | 'blog' | 'terms' | 'privacy' | 'about' | 'contact' | 'refund';

interface PrivacyPolicyProps {
  onNavigate?: (page: PageType) => void;
}

export default function PrivacyPolicy({ onNavigate }: PrivacyPolicyProps) {
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
          Privacy Policy
        </h1>

        <p className="text-sm text-gray-500 dark:text-gray-400 mb-8">
          Last updated: April 25, 2025
        </p>

        <div className="prose prose-gray dark:prose-invert max-w-none space-y-6 text-gray-700 dark:text-gray-300">
          <section>
            <h2 className="font-cinzel text-xl font-semibold text-gray-900 dark:text-white mb-3">1. Introduction</h2>
            <p>
              Live Astrology ("we," "our," or "us") is committed to protecting your privacy. This Privacy Policy explains how
              we collect, use, disclose, and safeguard your information when you visit our website liveastrology.app and use
              our astrology services.
            </p>
            <p>
              Please read this privacy policy carefully. If you do not agree with the terms of this privacy policy, please
              do not access the site.
            </p>
          </section>

          <section>
            <h2 className="font-cinzel text-xl font-semibold text-gray-900 dark:text-white mb-3">2. Information We Collect</h2>
            <p>We collect information that you provide directly to us, including:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li><strong>Personal Information:</strong> Name, email address, and birth information (date, time, location) when you use our calculators</li>
              <li><strong>Usage Data:</strong> Information about how you access and use our website, including your IP address, browser type, and pages visited</li>
              <li><strong>Cookies:</strong> Small data files stored on your device to remember your preferences and settings</li>
            </ul>
          </section>

          <section>
            <h2 className="font-cinzel text-xl font-semibold text-gray-900 dark:text-white mb-3">3. How We Use Your Information</h2>
            <p>We use the information we collect to:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li>Provide and maintain our astrology calculator services</li>
              <li>Generate accurate birth chart calculations and readings</li>
              <li>Send you newsletters and updates if you subscribe to our mailing list</li>
              <li>Improve, personalize, and expand our services</li>
              <li>Understand and analyze how you use our website</li>
              <li>Develop new products, services, features, and functionality</li>
            </ul>
          </section>

          <section>
            <h2 className="font-cinzel text-xl font-semibold text-gray-900 dark:text-white mb-3">4. Information Sharing and Disclosure</h2>
            <p>We do not sell, trade, or otherwise transfer your personal information to third parties except in the following circumstances:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li><strong>Service Providers:</strong> We may share your information with trusted third-party service providers who assist us in operating our website</li>
              <li><strong>Legal Requirements:</strong> We may disclose your information if required to do so by law or in response to valid requests by public authorities</li>
              <li><strong>Business Transfers:</strong> In the event of a merger, acquisition, or sale of assets, your information may be transferred</li>
            </ul>
          </section>

          <section>
            <h2 className="font-cinzel text-xl font-semibold text-gray-900 dark:text-white mb-3">5. Data Security</h2>
            <p>
              The security of your data is important to us. We implement appropriate technical and organizational security
              measures to protect your personal information against unauthorized access, alteration, disclosure, or destruction.
              However, no method of transmission over the Internet or electronic storage is 100% secure.
            </p>
          </section>

          <section>
            <h2 className="font-cinzel text-xl font-semibold text-gray-900 dark:text-white mb-3">6. Cookies and Tracking Technologies</h2>
            <p>
              We use cookies and similar tracking technologies to track activity on our website and hold certain information.
              You can instruct your browser to refuse all cookies or to indicate when a cookie is being sent.
            </p>
            <p>Types of cookies we use:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li><strong>Essential Cookies:</strong> Required for the website to function properly</li>
              <li><strong>Analytics Cookies:</strong> Help us understand how visitors interact with our website</li>
              <li><strong>Preference Cookies:</strong> Remember your settings and preferences</li>
            </ul>
          </section>

          <section>
            <h2 className="font-cinzel text-xl font-semibold text-gray-900 dark:text-white mb-3">7. Your Rights</h2>
            <p>Depending on your location, you may have certain rights regarding your personal information, including:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li>The right to access the personal information we hold about you</li>
              <li>The right to request correction of inaccurate information</li>
              <li>The right to request deletion of your personal information</li>
              <li>The right to opt out of marketing communications</li>
            </ul>
            <p>To exercise these rights, please contact us at privacy@liveastrology.app</p>
          </section>

          <section>
            <h2 className="font-cinzel text-xl font-semibold text-gray-900 dark:text-white mb-3">8. Third-Party Links</h2>
            <p>
              Our website may contain links to third-party websites and services. We are not responsible for the privacy
              practices of these third parties. We encourage you to read the privacy statements of any third-party sites
              you visit.
            </p>
          </section>

          <section>
            <h2 className="font-cinzel text-xl font-semibold text-gray-900 dark:text-white mb-3">9. Children's Privacy</h2>
            <p>
              Our service is not intended for use by children under the age of 13. We do not knowingly collect personal
              information from children under 13. If you are a parent or guardian and believe your child has provided us
              with personal information, please contact us immediately.
            </p>
          </section>

          <section>
            <h2 className="font-cinzel text-xl font-semibold text-gray-900 dark:text-white mb-3">10. Changes to This Privacy Policy</h2>
            <p>
              We may update our Privacy Policy from time to time. We will notify you of any changes by posting the new
              Privacy Policy on this page and updating the "Last updated" date at the top. You are advised to review this
              Privacy Policy periodically for any changes.
            </p>
          </section>

          <section>
            <h2 className="font-cinzel text-xl font-semibold text-gray-900 dark:text-white mb-3">11. Contact Us</h2>
            <p>
              If you have any questions about this Privacy Policy, please contact us:
            </p>
            <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <p className="font-medium text-gray-900 dark:text-white">Live Astrology</p>
              <p className="text-gray-600 dark:text-gray-400">Email: privacy@liveastrology.app</p>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
