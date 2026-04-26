# Sun Moon Rising Sign Calculator - Specification

## Concept & Vision

A mystical, celestial-themed astrology calculator that calculates and displays Sun, Moon, and Rising signs with elegant cosmic animations and deep personality insights. The experience should feel like gazing into a personalized astrological chart — immersive, intimate, and enlightening. Mobile-first design ensures smooth, intuitive interactions on any device.

## Design Language

### Aesthetic Direction
Deep space mysticism meets modern elegance — think a premium astrology app with constellation patterns, subtle starfield animations, and celestial gradients. Dark mode by default with luminous accent colors that evoke cosmic energy.

### Color Palette
- **Primary Background**: #0a0a1a (deep space)
- **Secondary Background**: #12122a (card backgrounds)
- **Accent Gold**: #f4c542 (sun energy)
- **Accent Silver**: #c0c0e0 (moon energy)
- **Accent Rose**: #e84a7f (rising/ascendant energy)
- **Text Primary**: #ffffff
- **Text Secondary**: #a0a0c0
- **Border Glow**: rgba(244, 197, 66, 0.3)

### Typography
- **Headings**: "Cinzel", serif — elegant, mystical feel
- **Body**: "Quicksand", sans-serif — modern, readable
- **Accent/Labels**: "Cormorant Garamond", serif — zodiac names

### Spatial System
- Mobile: 16px base padding, 12px gaps
- Desktop: 24px padding, 16px gaps
- Border radius: 16px for cards, 12px for inputs
- Generous whitespace for breathing room

### Motion Philosophy
- Celestial rotations on zodiac symbols (slow, continuous)
- Fade-in with upward drift for result reveals (400ms ease-out)
- Subtle pulse on active elements
- Star twinkle animations in background
- Constellation line drawing animations

### Visual Assets
- Custom SVG zodiac symbols for each sign
- Animated starfield background
- Gradient orbs representing each sign type
- Constellation connection lines

## Layout & Structure

### Mobile-First Architecture
1. **Hero Section**: Cosmic background with title, animated starfield
2. **Input Form**: Birth details in elegant stepped cards
3. **Results Section**: Three sign cards with detailed insights
4. **Footer**: Minimal attribution

### Responsive Strategy
- Single column on mobile (< 640px)
- Two-column grid for results on tablet (640px - 1024px)
- Three-column layout on desktop (> 1024px)
- Touch-friendly inputs with large tap targets (min 44px)

## Features & Interactions

### Core Features

#### 1. Birth Information Input
- **Date of Birth**: Native date picker with custom styling
- **Time of Birth**: Time picker with minute precision
- **Birth Location**: Searchable city/autocomplete with timezone detection
- **Optional**: Birth country selector for disambiguation

#### 2. Sun Sign Calculation
- Standard zodiac calculation based on birth date
- Display with zodiac symbol, element, modality
- Personality traits based on sun position

#### 3. Moon Sign Calculation
- Complex calculation based on birth date, time, and location
- Emotional nature and inner self insights
- Element and modality analysis

#### 4. Rising Sign (Ascendant) Calculation
- Most complex calculation requiring exact birth time and location
- External personality and first impressions
- Chart ruler analysis

#### 5. Extended Features (Enhanced)
- **Element Balance**: Visual chart showing fire/earth/air/water distribution
- **Cardinal/Fixed/Mutable Balance**: Modality distribution
- **Planetary Dignities Overview**: Brief note on sign strengths
- **Compatible Signs**: Suggested matches based on element compatibility
- **Share Results**: Generate shareable image/text summary
- **Daily Horoscope Preview**: Curated based on calculated signs

### Interaction Details

#### Input Form
- Smooth validation with helpful error messages
- Location search with debounced API calls
- "My location" quick option using browser geolocation
- Date pre-validation (no future dates, reasonable past dates)

#### Results Reveal
- Animated calculation "processing" state (1.5s)
- Cards flip/fade in with staggered timing
- Sign symbols rotate into place
- Detailed descriptions expand on tap

#### Error States
- Invalid date: Gentle highlight with explanation
- Missing time: Warning that rising sign may be less accurate
- Location not found: Suggest manual timezone entry

### Edge Cases
- Unknown exact birth time: Allow calculation with "approximately" rising sign
- DST transitions: Auto-detect based on location and date
- Southern hemisphere: Handle reversed seasons correctly
- Leap years: Proper date handling

## Component Inventory

### 1. StarfieldBackground
- Canvas-based or CSS animated stars
- Multiple parallax layers
- Occasional shooting star
- States: Default (ambient), Active (on scroll/interaction)

### 2. ZodiacSymbol
- SVG for each of 12 zodiac signs
- Animated rotation (optional, can be toggled)
- Glow effect on hover
- Size variants: small (24px), medium (48px), large (80px)

### 3. InputCard
- Floating label design
- Focus glow effect (gold)
- Error state with rose highlight
- Success checkmark when valid

### 4. DatePicker / TimePicker
- Custom styled to match theme
- Wheel-style selection on mobile
- Calendar popup on desktop
- States: default, focused, error, disabled

### 5. LocationSearch
- Autocomplete dropdown
- Recent searches memory
- Loading spinner during search
- States: empty, searching, results, selected, error

### 6. SignCard
- Gradient background based on element
- Zodiac symbol with glow
- Sign name in Cinzel font
- Element badge
- Expandable description
- States: loading (skeleton), revealed, expanded

### 7. ElementBalanceChart
- Donut chart with 4 segments
- Animated fill on reveal
- Legend with percentages
- Tooltip with details

### 8. ModalityChart
- Horizontal bar chart
- Three segments: Cardinal/Fixed/Mutable
- Color-coded
- Animated bars

### 9. CompatibilitySection
- List of compatible signs
- Friendship/love/work icons
- Brief compatibility note

### 10. ShareButton
- Generates shareable content
- Copy to clipboard functionality
- Social sharing options
- Loading state during generation

## Technical Approach

### Frontend Stack
- React 18 with TypeScript
- Tailwind CSS for styling
- Framer Motion for animations
- React Hook Form for form handling

### Astrology Calculations
- Custom calculation logic based on Swiss Ephemeris principles
- Sun sign: Simple date range lookup
- Moon sign: Simplified orbital calculation
- Rising sign: Ascendant calculation using birth time, location

### Data Structure
```typescript
interface BirthData {
  date: Date;
  time: string; // HH:MM format
  location: {
    name: string;
    latitude: number;
    longitude: number;
    timezone: string;
  };
}

interface AstrologyResult {
  sun: Sign;
  moon: Sign;
  rising: Sign;
  elementBalance: ElementBalance;
  modalityBalance: ModalityBalance;
  planetaryInfo: PlanetaryInfo;
}

interface Sign {
  name: string;
  symbol: string;
  element: 'fire' | 'earth' | 'air' | 'water';
  modality: 'cardinal' | 'fixed' | 'mutable';
  degree: number;
  traits: string[];
  description: string;
  rulingPlanet: string;
}
```

### Performance Considerations
- Lazy load heavy components
- Optimize zodiac SVG symbols
- Debounce location search
- Cache calculation results

### Accessibility
- ARIA labels on interactive elements
- Keyboard navigation support
- High contrast mode compatibility
- Screen reader friendly results
