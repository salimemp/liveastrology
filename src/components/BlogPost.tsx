import { useState } from 'react';
import { ArrowLeft, Calendar, Clock, Share2, Heart, MessageCircle, Twitter, Facebook, Link as LinkIcon } from 'lucide-react';

export interface BlogPost {
  id: string;
  title: string;
  excerpt: string;
  content: string;
  author: string;
  date: string;
  readTime: string;
  category: string;
  imageUrl?: string;
  tags: string[];
}

interface BlogPostViewProps {
  post: BlogPost;
  onBack: () => void;
}

export function BlogPostView({ post, onBack }: BlogPostViewProps) {
  const [liked, setLiked] = useState(false);

  const shareOnTwitter = () => {
    const text = encodeURIComponent(`${post.title} - Next Astrology Blog`);
    window.open(`https://twitter.com/intent/tweet?text=${text}&url=${encodeURIComponent(window.location.href)}`, '_blank');
  };

  const shareOnFacebook = () => {
    window.open(`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(window.location.href)}`, '_blank');
  };

  const copyLink = () => {
    navigator.clipboard.writeText(window.location.href);
    alert('Link copied to clipboard!');
  };

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      {/* Back Button */}
      <button
        onClick={onBack}
        className="flex items-center gap-2 text-secondary hover:text-primary transition-colors mb-6"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Blog
      </button>

      {/* Article Header */}
      <article>
        <header className="mb-8">
          <span className="inline-block px-3 py-1 rounded-full text-xs font-medium mb-4" style={{ backgroundColor: '#e8f4fc', color: '#4a6fa5' }}>
            {post.category}
          </span>
          <h1 className="font-cinzel text-3xl md:text-4xl font-bold mb-4 leading-tight" style={{ color: '#1a1a3a' }}>
            {post.title}
          </h1>
          <div className="flex flex-wrap items-center gap-4 text-sm text-secondary">
            <span className="flex items-center gap-1">
              <Calendar className="w-4 h-4" />
              {post.date}
            </span>
            <span className="flex items-center gap-1">
              <Clock className="w-4 h-4" />
              {post.readTime}
            </span>
            <span>By {post.author}</span>
          </div>
        </header>

        {/* Featured Image Placeholder */}
        <div className="w-full h-64 md:h-80 rounded-xl mb-8 overflow-hidden" style={{ background: 'linear-gradient(135deg, #4a6fa5 0%, #302b63 100%)' }}>
          <div className="w-full h-full flex items-center justify-center">
            <span className="text-white text-opacity-50 text-lg">Featured Image</span>
          </div>
        </div>

        {/* Article Content */}
        <div className="prose prose-lg max-w-none">
          <div className="text-secondary leading-relaxed whitespace-pre-line">
            {post.content.split('\n\n').map((paragraph, index) => {
              if (paragraph.startsWith('## ')) {
                return <h2 key={index} className="font-cinzel text-xl font-bold mt-8 mb-4" style={{ color: '#1a1a3a' }}>{paragraph.replace('## ', '')}</h2>;
              }
              if (paragraph.startsWith('- ')) {
                const items = paragraph.split('\n').map(item => item.replace('- ', ''));
                return (
                  <ul key={index} className="list-disc pl-6 space-y-2 my-4">
                    {items.map((item, i) => <li key={i}>{item}</li>)}
                  </ul>
                );
              }
              return <p key={index} className="mb-4">{paragraph}</p>;
            })}
          </div>
        </div>

        {/* Tags */}
        <div className="flex flex-wrap gap-2 mt-8 pt-6 border-t" style={{ borderColor: 'rgba(0,0,0,0.1)' }}>
          {post.tags.map((tag) => (
            <span key={tag} className="px-3 py-1 rounded-full text-xs" style={{ backgroundColor: '#f3f4f6', color: '#6a6a8a' }}>
              #{tag}
            </span>
          ))}
        </div>

        {/* Engagement */}
        <div className="flex items-center justify-between mt-8 pt-6 border-t" style={{ borderColor: 'rgba(0,0,0,0.1)' }}>
          <button
            onClick={() => setLiked(!liked)}
            className={`flex items-center gap-2 px-4 py-2 rounded-full transition-all ${liked ? 'text-pink-500' : 'text-secondary hover:text-pink-500'}`}
            style={{ backgroundColor: liked ? '#fef2f5' : '#f3f4f6' }}
          >
            <Heart className={`w-5 h-5 ${liked ? 'fill-current' : ''}`} />
            {liked ? 'Liked' : 'Like'}
          </button>

          <div className="flex items-center gap-2">
            <span className="text-sm text-secondary">Share:</span>
            <button onClick={shareOnTwitter} className="p-2 rounded-full hover:bg-blue-50 transition-colors" aria-label="Share on Twitter">
              <Twitter className="w-5 h-5 text-blue-400" />
            </button>
            <button onClick={shareOnFacebook} className="p-2 rounded-full hover:bg-blue-50 transition-colors" aria-label="Share on Facebook">
              <Facebook className="w-5 h-5 text-blue-600" />
            </button>
            <button onClick={copyLink} className="p-2 rounded-full hover:bg-gray-100 transition-colors" aria-label="Copy link">
              <LinkIcon className="w-5 h-5 text-gray-500" />
            </button>
          </div>
        </div>

        {/* Comments Section Placeholder */}
        <div className="mt-8 p-6 rounded-xl" style={{ backgroundColor: '#f8f9fa' }}>
          <h3 className="font-cinzel font-semibold mb-4 flex items-center gap-2" style={{ color: '#1a1a3a' }}>
            <MessageCircle className="w-5 h-5" />
            Comments
          </h3>
          <p className="text-sm text-muted">
            Comments feature coming soon! Join the conversation and share your thoughts on this article.
          </p>
        </div>
      </article>
    </div>
  );
}

const blogPosts: BlogPost[] = [
  {
    id: '1',
    title: 'Understanding Your Sun Sign: The Core of Your Astrological Identity',
    excerpt: 'Learn what your Sun sign reveals about your core personality, life purpose, and the essential self that drives you forward.',
    content: `Your Sun sign is the most well-known aspect of astrology, but its depth goes far beyond the daily horoscope predictions you might read in the newspaper.

## What Exactly Is a Sun Sign?

Your Sun sign represents the position of the Sun in the zodiac at the moment of your birth. This is determined by when you were born and corresponds to one of the twelve zodiac constellations.

## Why Is the Sun Sign So Important?

The Sun represents your core essence - who you are at your most fundamental level. Think of it as the glow that others see when they look at you, the quality of energy you radiate naturally.

## The Four Elements and Your Sun Sign

Each Sun sign belongs to one of four elements:

- **Fire Signs (Aries, Leo, Sagittarius):** Passionate, dynamic, and confident
- **Earth Signs (Taurus, Virgo, Capricorn):** Practical, reliable, and grounded
- **Air Signs (Gemini, Libra, Aquarius):** Intellectual, social, and communicative
- **Water Signs (Cancer, Scorpio, Pisces):** Emotional, intuitive, and nurturing

## How to Work With Your Sun Sign

Understanding your Sun sign is just the beginning of your astrological journey. Use this knowledge to:

- Recognize your natural strengths and work on your weaknesses
- Understand why certain life paths feel more aligned than others
- Find compatible relationships and career paths
- Embrace your authentic self without comparison to others

Remember, your Sun sign is the foundation, but your full astrological profile includes your Moon sign, Rising sign, and the positions of other planets for a complete picture.`,
    author: 'Celestial Insights',
    date: 'December 15, 2024',
    readTime: '5 min read',
    category: 'Astrology Basics',
    tags: ['sun sign', 'zodiac', 'astrology basics', 'self discovery'],
  },
  {
    id: '2',
    title: 'Moon Sign vs Rising Sign: What\'s the Difference?',
    excerpt: 'Discover the unique influences of your Moon and Rising signs and how they work together with your Sun sign to create your complete astrological profile.',
    content: `While your Sun sign captures your essential self, your Moon and Rising signs add crucial layers to your astrological identity. Understanding all three gives you a much richer picture.

## Your Moon Sign: The Inner You

The Moon represents your emotional nature, your instinctual reactions, and what you need to feel secure. It's the part of you that operates below conscious awareness.

**Your Moon sign reveals:**
- How you process and express emotions
- What makes you feel safe and nurtured
- Your intuitive and subconscious patterns
- How you respond to stress and crisis

## Your Rising Sign (Ascendant): Your Outer Shell

The Rising sign is the zodiac sign that was rising on the eastern horizon at your birth moment. It represents how others perceive you and how you engage with the world.

**Your Rising sign influences:**
- First impressions you make on others
- Your approach to new situations
- Your physical appearance and mannerisms
- The "mask" you wear in public

## How the Three Signs Work Together

The Sun, Moon, and Rising signs work as a trinity in astrology:

- **Sun:** What you want to be (conscious will)
- **Moon:** What you need (emotional needs)
- **Rising:** How you appear to others (external presentation)

When these three signs harmonize, you might feel a sense of alignment. When they conflict, you may experience internal tension that prompts personal growth.

## Finding Balance

Understanding your complete Sun-Moon-Rising profile helps you:
- Navigate relationships more effectively
- Understand why you act differently in various situations
- Make career choices that honor all aspects of yourself
- Develop self-compassion for your apparent contradictions

Take our free Birth Chart Calculator to discover your complete astrological profile!`,
    author: 'Stellar Guide',
    date: 'December 10, 2024',
    readTime: '7 min read',
    category: 'Astrology Basics',
    tags: ['moon sign', 'rising sign', 'ascendant', 'birth chart'],
  },
  {
    id: '3',
    title: 'How Venus and Mars Influence Your Love Life',
    excerpt: 'Explore how the planets of love and desire shape your romantic relationships, attraction patterns, and what you seek in a partner.',
    content: `When it comes to love and romance, Venus and Mars play starring roles in your astrological chart. These two planets reveal how you give and receive love.

## Venus: The Planet of Love and Beauty

Venus represents your values in relationships, what you're attracted to aesthetically, and how you express affection.

**Your Venus sign shows:**
- What qualities you find attractive in a partner
- How you express love and appreciation
- Your aesthetic preferences and sense of style
- What brings you pleasure and harmony

## Mars: The Planet of Desire and Action

Mars represents your drive, passion, and how you pursue what you want - especially in relationships.

**Your Mars sign reveals:**
- How you pursue romantic interests
- Your sexual desires and expression
- What makes you angry or frustrated
- Your competitive nature

## Venus-Mars Interactions in Relationships

When two people connect, their Venus and Mars signs create attraction patterns:

- **Venus trine Mars:** Natural harmony in romance
- **Mars opposite Venus:** Intense attraction with potential tension
- **Venus square Mars:** Learning curve in relationships

## Love Styles by Element

Your Venus sign's element influences your love language:

- **Fire Venus:** Passionate, direct, enthusiastic
- **Earth Venus:** Sensual, loyal, practical expressions of love
- **Air Venus:** Communicative, intellectual, social
- **Water Venus:** Emotional, devoted, romantic at heart

## Using This Knowledge

Understanding Venus and Mars in your chart helps you:
- Recognize why certain types attract you
- Communicate your needs more effectively
- Understand partner dynamics better
- Navigate the dating world with more clarity

Remember, while these planets are important, they work within the context of your entire birth chart for a complete understanding.`,
    author: 'Cosmic Love',
    date: 'December 5, 2024',
    readTime: '6 min read',
    category: 'Love & Relationships',
    tags: ['venus', 'mars', 'romance', 'compatibility', 'love'],
  },
];

interface BlogListProps {
  onSelectPost?: (post: BlogPost) => void;
}

export function BlogList({ onSelectPost }: BlogListProps) {
  const [selectedPost, setSelectedPost] = useState<BlogPost | null>(null);

  if (selectedPost && onSelectPost) {
    return <BlogPostView post={selectedPost} onBack={() => setSelectedPost(null)} />;
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-12">
      <h2 className="font-cinzel text-3xl font-bold text-center mb-4" style={{ color: '#1a1a3a' }}>
        Astrology Blog
      </h2>
      <p className="text-center text-secondary mb-12 max-w-2xl mx-auto">
        Explore the cosmos through our articles on astrology, relationships, and self-discovery.
        Deepen your understanding of the celestial influences in your life.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {blogPosts.map((post) => (
          <article
            key={post.id}
            onClick={() => {
              setSelectedPost(post);
              onSelectPost?.(post);
            }}
            className="feature-card cursor-pointer"
          >
            {/* Image Placeholder */}
            <div className="w-full h-40 -mx-6 -mt-6 mb-4 rounded-t-xl overflow-hidden" style={{ background: 'linear-gradient(135deg, #4a6fa5 0%, #302b63 100%)' }}>
              <div className="w-full h-full flex items-center justify-center">
                <span className="text-white text-opacity-40 text-sm">Article Image</span>
              </div>
            </div>

            <span className="inline-block px-2 py-1 rounded text-xs font-medium mb-3" style={{ backgroundColor: '#e8f4fc', color: '#4a6fa5' }}>
              {post.category}
            </span>

            <h3 className="feature-title mb-2 line-clamp-2">{post.title}</h3>

            <p className="feature-description line-clamp-3 mb-4">{post.excerpt}</p>

            <div className="flex items-center justify-between text-xs text-muted pt-4 border-t" style={{ borderColor: 'rgba(0,0,0,0.05)' }}>
              <span>{post.date}</span>
              <span>{post.readTime}</span>
            </div>
          </article>
        ))}
      </div>

      {/* Newsletter Section */}
      <div className="mt-16 p-8 rounded-2xl text-center" style={{ background: 'linear-gradient(135deg, #4a6fa5 0%, #302b63 100%)' }}>
        <h3 className="font-cinzel text-xl font-bold text-white mb-2">
          Join Our Newsletter
        </h3>
        <p className="text-white text-opacity-80 text-sm mb-4 max-w-md mx-auto">
          Get weekly astrology insights, horoscopes, and cosmic guidance delivered to your inbox.
        </p>
        <div className="flex flex-col sm:flex-row gap-3 max-w-md mx-auto">
          <input
            type="email"
            placeholder="Enter your email"
            className="flex-1 px-4 py-3 rounded-full text-sm"
          />
          <button className="px-6 py-3 rounded-full bg-white text-blue-600 font-semibold hover:bg-gray-100 transition-colors">
            Subscribe
          </button>
        </div>
        <p className="text-white text-opacity-50 text-xs mt-3">
          By subscribing, you agree to our Terms & Privacy Policy
        </p>
      </div>
    </div>
  );
}

export default BlogList;
