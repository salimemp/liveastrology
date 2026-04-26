import { ArrowLeft, RotateCcw, CreditCard } from 'lucide-react';

type PageType = 'home' | 'birth-chart' | 'synastry' | 'love' | 'blog' | 'terms' | 'privacy' | 'about' | 'contact' | 'refund';

interface RefundPolicyProps {
  onNavigate?: (page: PageType) => void;
}

export default function RefundPolicy({ onNavigate }: RefundPolicyProps) {
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
          Refund Policy
        </h1>

        <p className="text-sm text-gray-500 dark:text-gray-400 mb-8">
          Last updated: April 25, 2025
        </p>

        <div className="mb-8 p-6 bg-teal-50 dark:bg-teal-900/20 rounded-xl border border-teal-200 dark:border-teal-800">
          <div className="flex items-start gap-4">
            <div className="flex-shrink-0 mt-1">
              <div className="w-10 h-10 rounded-full flex items-center justify-center" style={{ backgroundColor: 'rgba(64, 224, 208, 0.2)' }}>
                <CreditCard className="w-5 h-5 text-teal-600 dark:text-teal-400" />
              </div>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-1">All Services Are Free</h3>
              <p className="text-gray-600 dark:text-gray-400 text-sm">
                Live Astrology provides all astrology calculators and birth chart analysis services completely free of charge.
                There are no paid products or services that require a refund.
              </p>
            </div>
          </div>
        </div>

        <div className="prose prose-gray dark:prose-invert max-w-none space-y-6 text-gray-700 dark:text-gray-300">
          <section>
            <h2 className="font-cinzel text-xl font-semibold text-gray-900 dark:text-white mb-3">1. Free Services</h2>
            <p>
              All calculators and tools available on Live Astrology are provided free of charge. This includes:
            </p>
            <ul className="list-disc pl-6 space-y-2">
              <li>Birth Chart Calculator</li>
              <li>Synastry Chart Calculator</li>
              <li>Love Compatibility Calculator</li>
              <li>Daily Horoscopes</li>
              <li>All Sign Calculators (Sun, Moon, Rising, etc.)</li>
            </ul>
          </section>

          <section>
            <h2 className="font-cinzel text-xl font-semibold text-gray-900 dark:text-white mb-3">2. Subscription Cancellations</h2>
            <p>
              While our services are free, if you have subscribed to our newsletter or email updates, you can unsubscribe
              at any time by clicking the "Unsubscribe" link in any email you receive from us, or by contacting us at
              support@liveastrology.app.
            </p>
          </section>

          <section>
            <h2 className="font-cinzel text-xl font-semibold text-gray-900 dark:text-white mb-3">3. Future Paid Services</h2>
            <p>
              In the event that Live Astrology introduces paid products or premium services in the future, this refund policy
              will be updated accordingly. Any such changes will be clearly communicated to users before the launch of paid
              services.
            </p>
          </section>

          <section>
            <h2 className="font-cinzel text-xl font-semibold text-gray-900 dark:text-white mb-3">4. Contact Us</h2>
            <p>
              If you have any questions about this Refund Policy or need assistance with any aspect of our service,
              please don't hesitate to contact us:
            </p>
            <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <p className="font-medium text-gray-900 dark:text-white">Live Astrology Support</p>
              <p className="text-gray-600 dark:text-gray-400">Email: support@liveastrology.app</p>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
