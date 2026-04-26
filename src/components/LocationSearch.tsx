// Major world cities with coordinates and timezones
export interface CityData {
  name: string;
  country: string;
  latitude: number;
  longitude: number;
  timezone: string;
}

export const MAJOR_CITIES: CityData[] = [
  // North America
  { name: 'New York', country: 'USA', latitude: 40.7128, longitude: -74.006, timezone: 'America/New_York' },
  { name: 'Los Angeles', country: 'USA', latitude: 34.0522, longitude: -118.2437, timezone: 'America/Los_Angeles' },
  { name: 'Chicago', country: 'USA', latitude: 41.8781, longitude: -87.6298, timezone: 'America/Chicago' },
  { name: 'Houston', country: 'USA', latitude: 29.7604, longitude: -95.3698, timezone: 'America/Chicago' },
  { name: 'Phoenix', country: 'USA', latitude: 33.4484, longitude: -112.074, timezone: 'America/Phoenix' },
  { name: 'Philadelphia', country: 'USA', latitude: 39.9526, longitude: -75.1652, timezone: 'America/New_York' },
  { name: 'San Antonio', country: 'USA', latitude: 29.4241, longitude: -98.4936, timezone: 'America/Chicago' },
  { name: 'San Diego', country: 'USA', latitude: 32.7157, longitude: -117.1611, timezone: 'America/Los_Angeles' },
  { name: 'Dallas', country: 'USA', latitude: 32.7767, longitude: -96.797, timezone: 'America/Chicago' },
  { name: 'San Jose', country: 'USA', latitude: 37.3382, longitude: -121.8863, timezone: 'America/Los_Angeles' },
  { name: 'Austin', country: 'USA', latitude: 30.2672, longitude: -97.7431, timezone: 'America/Chicago' },
  { name: 'Seattle', country: 'USA', latitude: 47.6062, longitude: -122.3321, timezone: 'America/Los_Angeles' },
  { name: 'Denver', country: 'USA', latitude: 39.7392, longitude: -104.9903, timezone: 'America/Denver' },
  { name: 'Boston', country: 'USA', latitude: 42.3601, longitude: -71.0589, timezone: 'America/New_York' },
  { name: 'Miami', country: 'USA', latitude: 25.7617, longitude: -80.1918, timezone: 'America/New_York' },
  { name: 'Atlanta', country: 'USA', latitude: 33.749, longitude: -84.388, timezone: 'America/New_York' },
  { name: 'San Francisco', country: 'USA', latitude: 37.7749, longitude: -122.4194, timezone: 'America/Los_Angeles' },
  { name: 'Toronto', country: 'Canada', latitude: 43.6532, longitude: -79.3832, timezone: 'America/Toronto' },
  { name: 'Vancouver', country: 'Canada', latitude: 49.2827, longitude: -123.1207, timezone: 'America/Vancouver' },
  { name: 'Montreal', country: 'Canada', latitude: 45.5017, longitude: -73.5673, timezone: 'America/Montreal' },
  { name: 'Mexico City', country: 'Mexico', latitude: 19.4326, longitude: -99.1332, timezone: 'America/Mexico_City' },

  // Europe
  { name: 'London', country: 'UK', latitude: 51.5074, longitude: -0.1278, timezone: 'Europe/London' },
  { name: 'Paris', country: 'France', latitude: 48.8566, longitude: 2.3522, timezone: 'Europe/Paris' },
  { name: 'Berlin', country: 'Germany', latitude: 52.52, longitude: 13.405, timezone: 'Europe/Berlin' },
  { name: 'Madrid', country: 'Spain', latitude: 40.4168, longitude: -3.7038, timezone: 'Europe/Madrid' },
  { name: 'Rome', country: 'Italy', latitude: 41.9028, longitude: 12.4964, timezone: 'Europe/Rome' },
  { name: 'Amsterdam', country: 'Netherlands', latitude: 52.3676, longitude: 4.9041, timezone: 'Europe/Amsterdam' },
  { name: 'Vienna', country: 'Austria', latitude: 48.2082, longitude: 16.3738, timezone: 'Europe/Vienna' },
  { name: 'Brussels', country: 'Belgium', latitude: 50.8503, longitude: 4.3517, timezone: 'Europe/Brussels' },
  { name: 'Stockholm', country: 'Sweden', latitude: 59.3293, longitude: 18.0686, timezone: 'Europe/Stockholm' },
  { name: 'Oslo', country: 'Norway', latitude: 59.9139, longitude: 10.7522, timezone: 'Europe/Oslo' },
  { name: 'Copenhagen', country: 'Denmark', latitude: 55.6761, longitude: 12.5683, timezone: 'Europe/Copenhagen' },
  { name: 'Helsinki', country: 'Finland', latitude: 60.1699, longitude: 24.9384, timezone: 'Europe/Helsinki' },
  { name: 'Dublin', country: 'Ireland', latitude: 53.3498, longitude: -6.2603, timezone: 'Europe/Dublin' },
  { name: 'Lisbon', country: 'Portugal', latitude: 38.7223, longitude: -9.1393, timezone: 'Europe/Lisbon' },
  { name: 'Barcelona', country: 'Spain', latitude: 41.3851, longitude: 2.1734, timezone: 'Europe/Madrid' },
  { name: 'Munich', country: 'Germany', latitude: 48.1351, longitude: 11.582, timezone: 'Europe/Berlin' },
  { name: 'Milan', country: 'Italy', latitude: 45.4642, longitude: 9.19, timezone: 'Europe/Rome' },
  { name: 'Prague', country: 'Czech Republic', latitude: 50.0755, longitude: 14.4378, timezone: 'Europe/Prague' },
  { name: 'Warsaw', country: 'Poland', latitude: 52.2297, longitude: 21.0122, timezone: 'Europe/Warsaw' },
  { name: 'Budapest', country: 'Hungary', latitude: 47.4979, longitude: 19.0402, timezone: 'Europe/Budapest' },
  { name: 'Athens', country: 'Greece', latitude: 37.9838, longitude: 23.7275, timezone: 'Europe/Athens' },
  { name: 'Istanbul', country: 'Turkey', latitude: 41.0082, longitude: 28.9784, timezone: 'Europe/Istanbul' },
  { name: 'Moscow', country: 'Russia', latitude: 55.7558, longitude: 37.6173, timezone: 'Europe/Moscow' },
  { name: 'Zurich', country: 'Switzerland', latitude: 47.3769, longitude: 8.5417, timezone: 'Europe/Zurich' },
  { name: 'Geneva', country: 'Switzerland', latitude: 46.2044, longitude: 6.1432, timezone: 'Europe/Zurich' },

  // Asia
  { name: 'Tokyo', country: 'Japan', latitude: 35.6762, longitude: 139.6503, timezone: 'Asia/Tokyo' },
  { name: 'Shanghai', country: 'China', latitude: 31.2304, longitude: 121.4737, timezone: 'Asia/Shanghai' },
  { name: 'Beijing', country: 'China', latitude: 39.9042, longitude: 116.4074, timezone: 'Asia/Shanghai' },
  { name: 'Hong Kong', country: 'Hong Kong', latitude: 22.3193, longitude: 114.1694, timezone: 'Asia/Hong_Kong' },
  { name: 'Singapore', country: 'Singapore', latitude: 1.3521, longitude: 103.8198, timezone: 'Asia/Singapore' },
  { name: 'Seoul', country: 'South Korea', latitude: 37.5665, longitude: 126.978, timezone: 'Asia/Seoul' },
  { name: 'Mumbai', country: 'India', latitude: 19.076, longitude: 72.8777, timezone: 'Asia/Kolkata' },
  { name: 'Delhi', country: 'India', latitude: 28.7041, longitude: 77.1025, timezone: 'Asia/Kolkata' },
  { name: 'Bangkok', country: 'Thailand', latitude: 13.7563, longitude: 100.5018, timezone: 'Asia/Bangkok' },
  { name: 'Dubai', country: 'UAE', latitude: 25.2048, longitude: 55.2708, timezone: 'Asia/Dubai' },
  { name: 'Taipei', country: 'Taiwan', latitude: 25.033, longitude: 121.5654, timezone: 'Asia/Taipei' },
  { name: 'Osaka', country: 'Japan', latitude: 34.6937, longitude: 135.5023, timezone: 'Asia/Tokyo' },
  { name: 'Kuala Lumpur', country: 'Malaysia', latitude: 3.139, longitude: 101.6869, timezone: 'Asia/Kuala_Lumpur' },
  { name: 'Jakarta', country: 'Indonesia', latitude: -6.2088, longitude: 106.8456, timezone: 'Asia/Jakarta' },
  { name: 'Manila', country: 'Philippines', latitude: 14.5995, longitude: 120.9842, timezone: 'Asia/Manila' },
  { name: 'Ho Chi Minh City', country: 'Vietnam', latitude: 10.8231, longitude: 106.6297, timezone: 'Asia/Ho_Chi_Minh' },
  { name: 'Tel Aviv', country: 'Israel', latitude: 32.0853, longitude: 34.7818, timezone: 'Asia/Jerusalem' },
  { name: 'Riyadh', country: 'Saudi Arabia', latitude: 24.7136, longitude: 46.6753, timezone: 'Asia/Riyadh' },
  { name: 'Karachi', country: 'Pakistan', latitude: 24.8607, longitude: 67.0011, timezone: 'Asia/Karachi' },
  { name: 'Hanoi', country: 'Vietnam', latitude: 21.0278, longitude: 105.8342, timezone: 'Asia/Ho_Chi_Minh' },

  // Oceania
  { name: 'Sydney', country: 'Australia', latitude: -33.8688, longitude: 151.2093, timezone: 'Australia/Sydney' },
  { name: 'Melbourne', country: 'Australia', latitude: -37.8136, longitude: 144.9631, timezone: 'Australia/Melbourne' },
  { name: 'Brisbane', country: 'Australia', latitude: -27.4698, longitude: 153.0251, timezone: 'Australia/Brisbane' },
  { name: 'Perth', country: 'Australia', latitude: -31.9505, longitude: 115.8605, timezone: 'Australia/Perth' },
  { name: 'Auckland', country: 'New Zealand', latitude: -36.8485, longitude: 174.7633, timezone: 'Pacific/Auckland' },
  { name: 'Wellington', country: 'New Zealand', latitude: -41.2865, longitude: 174.7762, timezone: 'Pacific/Auckland' },

  // South America
  { name: 'Sao Paulo', country: 'Brazil', latitude: -23.5505, longitude: -46.6333, timezone: 'America/Sao_Paulo' },
  { name: 'Rio de Janeiro', country: 'Brazil', latitude: -22.9068, longitude: -43.1729, timezone: 'America/Sao_Paulo' },
  { name: 'Buenos Aires', country: 'Argentina', latitude: -34.6037, longitude: -58.3816, timezone: 'America/Argentina/Buenos_Aires' },
  { name: 'Lima', country: 'Peru', latitude: -12.0464, longitude: -77.0428, timezone: 'America/Lima' },
  { name: 'Bogota', country: 'Colombia', latitude: 4.711, longitude: -74.0721, timezone: 'America/Bogota' },
  { name: 'Santiago', country: 'Chile', latitude: -33.4489, longitude: -70.6693, timezone: 'America/Santiago' },

  // Africa
  { name: 'Cairo', country: 'Egypt', latitude: 30.0444, longitude: 31.2357, timezone: 'Africa/Cairo' },
  { name: 'Lagos', country: 'Nigeria', latitude: 6.5244, longitude: 3.3792, timezone: 'Africa/Lagos' },
  { name: 'Johannesburg', country: 'South Africa', latitude: -26.2041, longitude: 28.0473, timezone: 'Africa/Johannesburg' },
  { name: 'Cape Town', country: 'South Africa', latitude: -33.9249, longitude: 18.4241, timezone: 'Africa/Johannesburg' },
  { name: 'Nairobi', country: 'Kenya', latitude: -1.2921, longitude: 36.8219, timezone: 'Africa/Nairobi' },
  { name: 'Casablanca', country: 'Morocco', latitude: 33.5731, longitude: -7.5898, timezone: 'Africa/Casablanca' }
];

// Search cities by name
export function searchCities(query: string): CityData[] {
  if (!query || query.length < 2) return [];

  const normalizedQuery = query.toLowerCase().trim();
  return MAJOR_CITIES.filter(city =>
    city.name.toLowerCase().includes(normalizedQuery) ||
    city.country.toLowerCase().includes(normalizedQuery)
  ).slice(0, 8);
}

// Get timezone offset in hours
export function getTimezoneOffset(timezone: string): number {
  try {
    const now = new Date();
    const utcDate = new Date(now.toLocaleString('en-US', { timeZone: 'UTC' }));
    const tzDate = new Date(now.toLocaleString('en-US', { timeZone: timezone }));
    return (tzDate.getTime() - utcDate.getTime()) / (1000 * 60 * 60);
  } catch {
    return 0;
  }
}
