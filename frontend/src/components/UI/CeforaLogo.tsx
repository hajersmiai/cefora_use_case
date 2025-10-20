// Cefora official logo component
const CeforaLogo = () => {
  return (
    <div className="flex items-center gap-2">
      {/* CEFORA text */}
      <span className="text-2xl font-black tracking-tight text-white">
        CEFORA
      </span>
      
      {/* Double chevron arrows (brand mark) */}
      <div className="flex gap-0.5">
        <svg width="16" height="20" viewBox="0 0 16 20" fill="none">
          <path d="M2 10L10 2L10 6L14 6L14 14L10 14L10 18L2 10Z" fill="white"/>
        </svg>
        <svg width="16" height="20" viewBox="0 0 16 20" fill="none">
          <path d="M2 10L10 2L10 6L14 6L14 14L10 14L10 18L2 10Z" fill="white"/>
        </svg>
      </div>
    </div>
  )
}

export default CeforaLogo