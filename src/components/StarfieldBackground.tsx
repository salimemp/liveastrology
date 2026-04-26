import { useEffect, useRef } from 'react';

const StarfieldBackground = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationId: number;

    const resizeCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };

    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Create stars
    const stars: { x: number; y: number; size: number; opacity: number; twinkleSpeed: number; twinklePhase: number }[] = [];
    const numStars = Math.min(200, Math.floor((canvas.width * canvas.height) / 8000));

    for (let i = 0; i < numStars; i++) {
      stars.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        size: Math.random() * 2 + 0.5,
        opacity: Math.random() * 0.8 + 0.2,
        twinkleSpeed: Math.random() * 0.02 + 0.005,
        twinklePhase: Math.random() * Math.PI * 2
      });
    }

    // Shooting stars
    const shootingStars: { x: number; y: number; length: number; speed: number; angle: number; opacity: number; active: boolean }[] = [];

    const createShootingStar = () => {
      if (shootingStars.length < 2) {
        shootingStars.push({
          x: Math.random() * canvas.width,
          y: Math.random() * canvas.height * 0.5,
          length: Math.random() * 80 + 40,
          speed: Math.random() * 8 + 6,
          angle: Math.PI / 4 + (Math.random() - 0.5) * 0.3,
          opacity: 1,
          active: true
        });
      }
    };

    // Create shooting star periodically
    const shootingStarInterval = setInterval(() => {
      if (Math.random() > 0.7) {
        createShootingStar();
      }
    }, 2000);

    // Nebula effect
    const nebulaColors = [
      { x: 0.2, y: 0.3, color: 'rgba(155, 89, 182, 0.03)', radius: 300 },
      { x: 0.8, y: 0.7, color: 'rgba(52, 152, 219, 0.03)', radius: 350 },
      { x: 0.5, y: 0.5, color: 'rgba(232, 74, 127, 0.02)', radius: 400 }
    ];

    const drawNebula = () => {
      nebulaColors.forEach(nebula => {
        const gradient = ctx.createRadialGradient(
          nebula.x * canvas.width,
          nebula.y * canvas.height,
          0,
          nebula.x * canvas.width,
          nebula.y * canvas.height,
          nebula.radius
        );
        gradient.addColorStop(0, nebula.color);
        gradient.addColorStop(1, 'transparent');
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, canvas.width, canvas.height);
      });
    };

    // Constellation lines (subtle)
    const constellations = [
      { stars: [{ x: 0.15, y: 0.1 }, { x: 0.2, y: 0.15 }, { x: 0.25, y: 0.12 }, { x: 0.28, y: 0.18 }] },
      { stars: [{ x: 0.7, y: 0.2 }, { x: 0.75, y: 0.25 }, { x: 0.8, y: 0.22 }] },
      { stars: [{ x: 0.85, y: 0.6 }, { x: 0.9, y: 0.65 }, { x: 0.88, y: 0.72 }, { x: 0.92, y: 0.68 }] }
    ];

    const drawConstellations = () => {
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.03)';
      ctx.lineWidth = 1;
      constellations.forEach(constellation => {
        for (let i = 0; i < constellation.stars.length - 1; i++) {
          const start = constellation.stars[i];
          const end = constellation.stars[i + 1];
          ctx.beginPath();
          ctx.moveTo(start.x * canvas.width, start.y * canvas.height);
          ctx.lineTo(end.x * canvas.width, end.y * canvas.height);
          ctx.stroke();
        }
      });
    };

    let time = 0;

    const animate = () => {
      ctx.fillStyle = '#0a0a1a';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Draw nebula background
      drawNebula();

      // Draw constellations
      drawConstellations();

      // Update and draw stars
      time += 0.016; // ~60fps
      stars.forEach(star => {
        const twinkle = Math.sin(time * star.twinkleSpeed * 60 + star.twinklePhase);
        const currentOpacity = star.opacity * (0.5 + twinkle * 0.5);

        ctx.beginPath();
        ctx.arc(star.x, star.y, star.size, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(255, 255, 255, ${currentOpacity})`;
        ctx.fill();

        // Add glow for larger stars
        if (star.size > 1.5) {
          ctx.beginPath();
          ctx.arc(star.x, star.y, star.size * 2, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(255, 255, 255, ${currentOpacity * 0.1})`;
          ctx.fill();
        }
      });

      // Update and draw shooting stars
      for (let i = shootingStars.length - 1; i >= 0; i--) {
        const ss = shootingStars[i];
        if (!ss.active) continue;

        ss.x += Math.cos(ss.angle) * ss.speed;
        ss.y += Math.sin(ss.angle) * ss.speed;
        ss.opacity -= 0.015;

        if (ss.opacity <= 0 || ss.x > canvas.width || ss.y > canvas.height) {
          shootingStars.splice(i, 1);
          continue;
        }

        const gradient = ctx.createLinearGradient(
          ss.x - Math.cos(ss.angle) * ss.length,
          ss.y - Math.sin(ss.angle) * ss.length,
          ss.x,
          ss.y
        );
        gradient.addColorStop(0, 'transparent');
        gradient.addColorStop(1, `rgba(255, 255, 255, ${ss.opacity})`);

        ctx.beginPath();
        ctx.moveTo(ss.x - Math.cos(ss.angle) * ss.length, ss.y - Math.sin(ss.angle) * ss.length);
        ctx.lineTo(ss.x, ss.y);
        ctx.strokeStyle = gradient;
        ctx.lineWidth = 2;
        ctx.stroke();
      }

      animationId = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      window.removeEventListener('resize', resizeCanvas);
      clearInterval(shootingStarInterval);
      cancelAnimationFrame(animationId);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 w-full h-full pointer-events-none"
      style={{ zIndex: 0 }}
    />
  );
};

export default StarfieldBackground;
