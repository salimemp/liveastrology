import { useState, useRef, useEffect } from 'react';
import { Search, Calendar, Clock, MapPin, Navigation, Loader2, Sparkles, User } from 'lucide-react';
import { BirthData } from '../lib/astrology';
import { searchCities, CityData } from './LocationSearch';
import { useTheme } from '../context/ThemeContext';

interface InputFormProps {
  onCalculate: (data: BirthData, name: string) => void;
  isCalculating: boolean;
}

const InputForm = ({ onCalculate, isCalculating }: InputFormProps) => {
  const { theme } = useTheme();
  const [name, setName] = useState('');
  const [birthDate, setBirthDate] = useState('');
  const [birthTime, setBirthTime] = useState('');
  const [locationQuery, setLocationQuery] = useState('');
  const [selectedLocation, setSelectedLocation] = useState<CityData | null>(null);
  const [searchResults, setSearchResults] = useState<CityData[]>([]);
  const [showResults, setShowResults] = useState(false);
  const [errors, setErrors] = useState<{ name?: string; date?: string; time?: string; location?: string }>({});

  const searchRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Close search results when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setShowResults(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Search cities when query changes
  useEffect(() => {
    if (locationQuery.length >= 2) {
      const results = searchCities(locationQuery);
      setSearchResults(results);
      setShowResults(true);
    } else {
      setSearchResults([]);
      setShowResults(false);
    }
  }, [locationQuery]);

  const handleLocationSelect = (city: CityData) => {
    setSelectedLocation(city);
    setLocationQuery(`${city.name}, ${city.country}`);
    setShowResults(false);
    setErrors(prev => ({ ...prev, location: undefined }));
  };

  const handleUseMyLocation = () => {
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude } = position.coords;
          const closestCity = {
            name: 'Current Location',
            country: '',
            latitude,
            longitude,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
          };
          setSelectedLocation(closestCity);
          setLocationQuery('Current Location (Detected)');
          setShowResults(false);
          setErrors(prev => ({ ...prev, location: undefined }));
        },
        () => {
          setErrors(prev => ({ ...prev, location: 'Unable to detect location' }));
        }
      );
    } else {
      setErrors(prev => ({ ...prev, location: 'Geolocation not supported' }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: typeof errors = {};

    if (!name.trim()) {
      newErrors.name = 'Please enter your name';
    } else if (name.trim().length < 2) {
      newErrors.name = 'Name must be at least 2 characters';
    }

    if (!birthDate) {
      newErrors.date = 'Please enter your birth date';
    } else {
      const date = new Date(birthDate);
      const today = new Date();
      if (date > today) {
        newErrors.date = 'Birth date cannot be in the future';
      }
      if (date < new Date('1900-01-01')) {
        newErrors.date = 'Please enter a valid birth date';
      }
    }

    if (!birthTime) {
      newErrors.time = 'Please enter your birth time';
    }

    if (!selectedLocation) {
      newErrors.location = 'Please select your birth location';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validateForm() && selectedLocation) {
      onCalculate({
        date: new Date(birthDate),
        time: birthTime,
        location: {
          name: selectedLocation.name + (selectedLocation.country ? `, ${selectedLocation.country}` : ''),
          latitude: selectedLocation.latitude,
          longitude: selectedLocation.longitude,
          timezone: selectedLocation.timezone
        }
      }, name.trim());
    }
  };

  return (
    <div className="max-w-lg mx-auto">
      {/* Form Header - Consistent with hero section */}
      <div className="text-center mb-8">
        <div className="inline-flex items-center gap-3 mb-3">
          <Sparkles className="w-5 h-5" style={{ color: '#ffbf40' }} />
          <h2 className="font-cinzel text-xl font-bold tracking-wide" style={{ color: theme === 'dark' ? '#ffffff' : '#1a2332' }}>
            ENTER YOUR DETAILS
          </h2>
          <Sparkles className="w-5 h-5" style={{ color: '#ffbf40' }} />
        </div>
        <p className="text-sm font-medium" style={{ color: theme === 'dark' ? '#b8c5d6' : '#3a4558' }}>
          Your birth information is used to calculate your unique astrological profile
        </p>
      </div>

      {/* Form Card */}
      <form onSubmit={handleSubmit} className="p-6 md:p-8 space-y-6 rounded-2xl" style={{
        backgroundColor: theme === 'dark' ? 'rgba(27, 38, 59, 0.98)' : 'rgba(255, 255, 255, 0.98)',
        border: theme === 'dark' ? '1px solid rgba(255, 255, 255, 0.15)' : '1px solid rgba(0, 0, 0, 0.08)',
        backdropFilter: 'blur(12px)'
      }}>
        {/* Name Field */}
        <div className="space-y-2">
          <label className="flex items-center gap-2 text-sm font-semibold" style={{ color: theme === 'dark' ? '#e0e6ed' : '#3a4558' }}>
            <User className="w-4 h-4" style={{ color: '#e84a7f' }} />
            Your Name
          </label>
          <div className="relative">
            <input
              type="text"
              value={name}
              onChange={(e) => {
                setName(e.target.value);
                setErrors(prev => ({ ...prev, name: undefined }));
              }}
              placeholder="Enter your name"
              className={`w-full form-input rounded-xl px-4 py-3
                focus:outline-none focus:ring-2 focus:ring-cosmic-gold/50
                transition-all duration-200`}
            />
          </div>
          {errors.name && (
            <p className="text-cosmic-rose text-xs mt-1">{errors.name}</p>
          )}
        </div>

        {/* Date of Birth */}
        <div className="space-y-2">
          <label className="flex items-center gap-2 text-sm font-semibold" style={{ color: theme === 'dark' ? '#e0e6ed' : '#3a4558' }}>
            <Calendar className="w-4 h-4" style={{ color: '#f4c542' }} />
            Date of Birth
          </label>
          <div className="relative">
            <input
              type="date"
              value={birthDate}
              onChange={(e) => {
                setBirthDate(e.target.value);
                setErrors(prev => ({ ...prev, date: undefined }));
              }}
              max={new Date().toISOString().split('T')[0]}
              min="1900-01-01"
              className={`w-full form-input rounded-xl px-4 py-3
                focus:outline-none focus:ring-2 focus:ring-cosmic-gold/50
                transition-all duration-200 appearance-none cursor-pointer
                [&::-webkit-calendar-picker-indicator]:invert [&::-webkit-calendar-picker-indicator]:cursor-pointer`}
            />
          </div>
          {errors.date && (
            <p className="text-cosmic-rose text-xs mt-1">{errors.date}</p>
          )}
        </div>

        {/* Time of Birth */}
        <div className="space-y-2">
          <label className="flex items-center gap-2 text-sm font-semibold" style={{ color: theme === 'dark' ? '#e0e6ed' : '#3a4558' }}>
            <Clock className="w-4 h-4" style={{ color: '#c0c0e0' }} />
            Time of Birth
            <span className="text-xs font-normal" style={{ color: theme === 'dark' ? '#8899aa' : '#5a6578' }}>(for accurate Rising sign)</span>
          </label>
          <div className="relative">
            <input
              type="time"
              value={birthTime}
              onChange={(e) => {
                setBirthTime(e.target.value);
                setErrors(prev => ({ ...prev, time: undefined }));
              }}
              className={`w-full form-input rounded-xl px-4 py-3
                focus:outline-none focus:ring-2 focus:ring-cosmic-gold/50
                transition-all duration-200 appearance-none cursor-pointer
                [&::-webkit-calendar-picker-indicator]:invert [&::-webkit-calendar-picker-indicator]:cursor-pointer`}
            />
          </div>
          {errors.time && (
            <p className="text-cosmic-rose text-xs mt-1">{errors.time}</p>
          )}
          <p className="text-xs mt-1" style={{ color: theme === 'dark' ? '#8899aa' : '#5a6578' }}>
            If unknown, leave as 12:00 - Rising sign will be approximate
          </p>
        </div>

        {/* Location of Birth */}
        <div className="space-y-2" ref={searchRef}>
          <label className="flex items-center gap-2 text-sm font-semibold" style={{ color: theme === 'dark' ? '#e0e6ed' : '#3a4558' }}>
            <MapPin className="w-4 h-4" style={{ color: '#e84a7f' }} />
            Place of Birth
          </label>

          <div className="relative">
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-subtle">
              <Search className="w-5 h-5" />
            </div>
            <input
              ref={inputRef}
              type="text"
              value={locationQuery}
              onChange={(e) => {
                setLocationQuery(e.target.value);
                setSelectedLocation(null);
                setErrors(prev => ({ ...prev, location: undefined }));
              }}
              onFocus={() => {
                if (locationQuery.length >= 2) {
                  setShowResults(true);
                }
              }}
              placeholder="Search city..."
              className={`w-full form-input rounded-xl
                pl-10 pr-4 py-3
                focus:outline-none focus:ring-2 focus:ring-cosmic-gold/50
                transition-all duration-200`}
            />

            {/* Search Results Dropdown */}
            {showResults && searchResults.length > 0 && (
              <div className="absolute z-50 w-full mt-2 overflow-hidden shadow-xl max-h-64 overflow-y-auto" style={{
                backgroundColor: theme === 'dark' ? 'rgba(27, 38, 59, 0.98)' : 'rgba(255, 255, 255, 0.98)',
                border: theme === 'dark' ? '1px solid rgba(255, 255, 255, 0.15)' : '1px solid rgba(0, 0, 0, 0.08)',
                borderRadius: '0.75rem'
              }}>
                {searchResults.map((city, index) => (
                  <button
                    key={`${city.name}-${index}`}
                    type="button"
                    onClick={() => handleLocationSelect(city)}
                    className="w-full px-4 py-3 text-left transition-colors duration-150 border-b last:border-b-0"
                    style={{
                      backgroundColor: 'transparent',
                      borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.08)'
                    }}
                  >
                    <span style={{ color: theme === 'dark' ? '#ffffff' : '#1a2332' }}>{city.name}</span>
                    <span className="text-sm ml-2" style={{ color: theme === 'dark' ? '#8899aa' : '#5a6578' }}>{city.country}</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Use My Location Button */}
          <button
            type="button"
            onClick={handleUseMyLocation}
            className="flex items-center gap-2 text-sm transition-colors mt-1 font-medium"
            style={{ color: '#3498db' }}
          >
            <Navigation className="w-4 h-4" />
            Use my current location
          </button>

          {errors.location && (
            <p className="text-cosmic-rose text-xs mt-1">{errors.location}</p>
          )}

          {/* Selected Location Indicator */}
          {selectedLocation && (
            <div className="flex items-center gap-2 mt-2 text-sm" style={{ color: '#1abc9c' }}>
              <div className="w-2 h-2 rounded-full animate-pulse" style={{ backgroundColor: '#1abc9c' }} />
              <span>Selected: {selectedLocation.name}, {selectedLocation.country || 'Detected'}</span>
            </div>
          )}
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isCalculating}
          className="btn-primary w-full flex items-center justify-center gap-2 text-lg py-4"
        >
          {isCalculating ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Calculating Your Stars...
            </>
          ) : (
            <>
              <Sparkles className="w-5 h-5" />
              Discover My Signs
            </>
          )}
        </button>

        {/* Privacy Note */}
        <p className="text-center text-xs mt-4" style={{ color: theme === 'dark' ? '#8899aa' : '#5a6578' }}>
          Your data is processed locally and never stored or shared
        </p>
      </form>

      {/* Features Preview */}
      <div className="mt-8 grid grid-cols-3 gap-4 text-center">
        <div className="glass-card p-4" style={theme === 'dark' ? { background: 'rgba(27, 38, 59, 0.98)', border: '1px solid rgba(255, 255, 255, 0.15)' } : {}}>
          <div className="text-2xl mb-1">☀️</div>
          <div className="text-xs font-semibold" style={{ color: theme === 'dark' ? '#e0e6ed' : '#3a4558' }}>Sun Sign</div>
          <div className="text-[10px]" style={{ color: theme === 'dark' ? '#8899aa' : '#5a6578' }}>Your Core Self</div>
        </div>
        <div className="glass-card p-4" style={theme === 'dark' ? { background: 'rgba(27, 38, 59, 0.98)', border: '1px solid rgba(255, 255, 255, 0.15)' } : {}}>
          <div className="text-2xl mb-1">🌙</div>
          <div className="text-xs font-semibold" style={{ color: theme === 'dark' ? '#e0e6ed' : '#3a4558' }}>Moon Sign</div>
          <div className="text-[10px]" style={{ color: theme === 'dark' ? '#8899aa' : '#5a6578' }}>Your Emotions</div>
        </div>
        <div className="glass-card p-4" style={theme === 'dark' ? { background: 'rgba(27, 38, 59, 0.98)', border: '1px solid rgba(255, 255, 255, 0.15)' } : {}}>
          <div className="text-2xl mb-1">⬆️</div>
          <div className="text-xs font-semibold" style={{ color: theme === 'dark' ? '#e0e6ed' : '#3a4558' }}>Rising Sign</div>
          <div className="text-[10px]" style={{ color: theme === 'dark' ? '#8899aa' : '#5a6578' }}>Your Mask</div>
        </div>
      </div>
    </div>
  );
};

export default InputForm;