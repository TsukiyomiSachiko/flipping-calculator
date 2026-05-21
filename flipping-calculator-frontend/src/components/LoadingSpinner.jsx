export default function LoadingSpinner({ size = 'md', message }) {
  const sizeClasses = {
    sm: 'w-6 h-6 border-2',
    md: 'w-12 h-12 border-4',
    lg: 'w-20 h-20 border-4',
  };

  return (
    <div className="flex flex-col items-center justify-center p-8 space-y-4">
      <div className="relative flex items-center justify-center">
        {/* Glowing aura background */}
        <div className="absolute w-24 h-24 rounded-full bg-luxury-purple/10 blur-xl pointer-events-none" />
        
        {/* Outer Ring - Gold and Purple */}
        <div className={`rounded-full border-luxury-border border-t-luxury-gold border-b-luxury-purple animate-spin ${sizeClasses[size]}`} />
        
        {/* Inner Ring - Lavender (reverse spin) */}
        <div className={`absolute rounded-full border-transparent border-l-luxury-purpleLight border-r-luxury-purpleLight animate-spin [animation-direction:reverse] [animation-duration:1.2s] ${
          size === 'sm' ? 'w-4 h-4 border-2' : size === 'md' ? 'w-8 h-8 border-2' : 'w-14 h-14 border-2'
        }`} />
      </div>
      {message && (
        <p className="text-xs md:text-sm font-semibold tracking-wider text-luxury-purpleLight/80 animate-pulse-subtle font-outfit uppercase">
          {message}
        </p>
      )}
    </div>
  );
}
