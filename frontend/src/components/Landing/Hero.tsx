// Hero section with main title and tagline
const Hero = () => {
  return (
    <div className="text-center mb-12">
      {/* Main title - white text on gradient background */}
      <h1 className="text-5xl md:text-6xl font-black text-white mb-4 uppercase tracking-tight">
        Discover Job<br />Market Trends
      </h1>
      
      {/* Tagline - mint accent color */}
      <p className="text-xl md:text-2xl text-accent-mint font-medium">
        Stay Jobtimal
      </p>
    </div>
  )
}

export default Hero