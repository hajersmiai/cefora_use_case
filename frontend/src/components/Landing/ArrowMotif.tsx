// Decorative arrow motif (Cefora brand identity)
// Positioned in the background to add visual interest
const ArrowMotif = () => {
  return (
    <div className="absolute left-0 top-1/4 opacity-10 pointer-events-none hidden lg:block">
      {/* Large arrow SVG shape */}
      <svg width="300" height="500" viewBox="0 0 300 500" fill="none" xmlns="http://www.w3.org/2000/svg">
        {/* Main arrow polygon */}
        <path
          d="M 50 150 L 250 250 L 50 350 L 100 350 L 300 250 L 100 150 Z"
          fill="white"
          opacity="1"
        />
      </svg>
    </div>
  )
}

export default ArrowMotif