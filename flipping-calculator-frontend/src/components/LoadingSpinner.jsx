export default function LoadingSpinner({ size = 'md', message }) {
  const spinnerClass = size === 'sm' ? 'tsuki-spinner-sm' : size === 'lg' ? 'tsuki-spinner-lg' : '';

  return (
    <div className="flex flex-col items-center justify-center p-8 space-y-4">
      <div className="relative flex items-center justify-center">
        {/* Glowing aura background */}
        <div className="absolute w-24 h-24 rounded-full bg-luxury-purple/10 blur-xl pointer-events-none" />
        <div className={`tsuki-spinner ${spinnerClass}`} />
      </div>
      {message && (
        <p className="text-xs md:text-sm font-semibold tracking-wider text-luxury-purpleLight/80 animate-pulse-subtle font-outfit uppercase">
          {message}
        </p>
      )}
    </div>
  );
}
