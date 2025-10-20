import React from "react";

export type MobileViewProps = {
  className?: string;
  onMenu?: () => void;
  onBell?: () => void;
  onSearch?: () => void;
  onNavHome?: () => void;
  onNavDashboard?: () => void;
  onNavChat?: () => void;
  onNavSettings?: () => void;
};

/**
 * MobileView renders your mobile mock as a responsive, accessible React/TSX component.
 * The header menu, bell, search bar, and bottom nav icons are clickable.
 */
export default function MobileView({
  className,
  onMenu,
  onBell,
  onSearch,
  onNavHome,
  onNavDashboard,
  onNavChat,
  onNavSettings,
}: MobileViewProps) {
  const onKeyActivate: React.KeyboardEventHandler<SVGGElement> = (e) => {
    if (e.key === "Enter" || e.key === " ") {
      (e.currentTarget as any).click?.();
    }
  };

  return (
    <div className={className ?? ""}>
      <svg
        viewBox="0 0 400 800"
        xmlns="http://www.w3.org/2000/svg"
        role="img"
        aria-labelledby="mobileTitle mobileDesc"
        className="w-full h-auto"
      >
        <title id="mobileTitle">VacaViz Mobile</title>
        <desc id="mobileDesc">Mobile layout with header, search, quick stats, trending list, chart preview, and bottom navigation.</desc>

        <defs>
          <linearGradient id="mobileGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#39037E" stopOpacity={1} />
            <stop offset="100%" stopColor="#B49BFF" stopOpacity={1} />
          </linearGradient>
        </defs>

        {/* Phone Frame */}
        <rect x={20} y={20} width={360} height={760} rx={30} fill="#1A1A1A" />
        <rect x={35} y={35} width={330} height={730} rx={20} fill="#FFFFFF" />

        {/* Status Bar */}
        <rect x={35} y={35} width={330} height={25} rx={20} fill="#000000" opacity={0.9} />
        <text x={60} y={52} fontFamily="Arial, sans-serif" fontSize={12} fill="#FFFFFF">9:41</text>
        <circle cx={340} cy={47} r={3} fill="#FFFFFF" />
        <rect x={315} y={43} width={20} height={9} rx={2} fill="none" stroke="#FFFFFF" strokeWidth={1} />
        <rect x={317} y={45} width={14} height={5} fill="#FFFFFF" />

        {/* App Header */}
        <rect x={35} y={60} width={330} height={60} fill="url(#mobileGrad)" />

        {/* Menu button */}
        <g
          role="button"
          aria-label="Open menu"
          tabIndex={0}
          onKeyDown={onKeyActivate}
          onClick={onMenu}
          style={{ cursor: onMenu ? "pointer" : "default" }}
        >
          <rect x={50} y={75} width={35} height={35} rx={8} fill="#FFFFFF" opacity={0.3} />
          <text x={67} y={98} fontFamily="Arial, sans-serif" fontSize={18} fill="#FFFFFF" textAnchor="middle">☰</text>
        </g>

        <text x={200} y={98} fontFamily="Arial, sans-serif" fontSize={18} fontWeight="bold" fill="#FFFFFF" textAnchor="middle">VacaViz</text>

        {/* Bell button */}
        <g
          role="button"
          aria-label="Notifications"
          tabIndex={0}
          onKeyDown={onKeyActivate}
          onClick={onBell}
          style={{ cursor: onBell ? "pointer" : "default" }}
        >
          <circle cx={330} cy={92} r={15} fill="#FFFFFF" opacity={0.3} />
          <text x={330} y={98} fontFamily="Arial, sans-serif" fontSize={14} fill="#FFFFFF" textAnchor="middle">🔔</text>
        </g>

        {/* Search Bar */}
        <g
          role="button"
          aria-label="Search"
          tabIndex={0}
          onKeyDown={onKeyActivate}
          onClick={onSearch}
          style={{ cursor: onSearch ? "pointer" : "default" }}
        >
          <rect x={50} y={135} width={300} height={45} rx={22} fill="#F5F5F5" />
          <circle cx={75} cy={157} r={8} fill="#B49BFF" />
          <text x={75} y={162} fontFamily="Arial, sans-serif" fontSize={12} fill="#FFFFFF" textAnchor="middle">🔍</text>
          <text x={95} y={162} fontFamily="Arial, sans-serif" fontSize={14} fill="#999">Search jobs, skills...</text>
        </g>

        {/* Quick Stats Cards */}
        <text x={50} y={210} fontFamily="Arial, sans-serif" fontSize={16} fontWeight="bold" fill="#39037E">Quick Stats</text>

        <rect x={50} y={225} width={140} height={90} rx={12} fill="#BAE0DE" opacity={0.3} />
        <text x={120} y={255} fontFamily="Arial, sans-serif" fontSize={24} fontWeight="bold" fill="#39037E" textAnchor="middle">8,542</text>
        <text x={120} y={280} fontFamily="Arial, sans-serif" fontSize={12} fill="#666" textAnchor="middle">Active Jobs</text>
        <circle cx={170} cy={240} r={6} fill="#39037E" />

        <rect x={210} y={225} width={140} height={90} rx={12} fill="#FFBAE8" opacity={0.3} />
        <text x={280} y={255} fontFamily="Arial, sans-serif" fontSize={24} fontWeight="bold" fill="#39037E" textAnchor="middle">234</text>
        <text x={280} y={280} fontFamily="Arial, sans-serif" fontSize={12} fill="#666" textAnchor="middle">Companies</text>
        <circle cx={330} cy={240} r={6} fill="#FA6B12" />

        {/* Trending Section */}
        <text x={50} y={345} fontFamily="Arial, sans-serif" fontSize={16} fontWeight="bold" fill="#39037E">Trending Now 🔥</text>

        <rect x={50} y={360} width={300} height={60} rx={10} fill="#FFFFFF" stroke="#B49BFF" strokeWidth={2} />
        <text x={70} y={385} fontFamily="Arial, sans-serif" fontSize={14} fontWeight="bold" fill="#39037E">Python Developer</text>
        <text x={70} y={405} fontFamily="Arial, sans-serif" fontSize={12} fill="#666">+23% demand | Brussels</text>
        <path d="M 320 385 L 330 390 L 320 395" fill="#FA6B12" />

        <rect x={50} y={435} width={300} height={60} rx={10} fill="#FFFFFF" stroke="#B49BFF" strokeWidth={2} />
        <text x={70} y={460} fontFamily="Arial, sans-serif" fontSize={14} fontWeight="bold" fill="#39037E">Data Analyst</text>
        <text x={70} y={480} fontFamily="Arial, sans-serif" fontSize={12} fill="#666">+18% demand | Antwerp</text>
        <path d="M 320 460 L 330 465 L 320 470" fill="#FA6B12" />

        {/* Chart Preview */}
        <text x={50} y={530} fontFamily="Arial, sans-serif" fontSize={16} fontWeight="bold" fill="#39037E">Monthly Trends</text>

        <rect x={50} y={545} width={300} height={120} rx={10} fill="#FCFAC7" opacity={0.3} />
        <polyline
          points="70,635 110,625 150,615 190,605 230,600 270,595 310,585 330,580"
          fill="none"
          stroke="#39037E"
          strokeWidth={3}
        />
        <circle cx={70} cy={635} r={5} fill="#FA6B12" />
        <circle cx={150} cy={615} r={5} fill="#FA6B12" />
        <circle cx={230} cy={600} r={5} fill="#FA6B12" />
        <circle cx={330} cy={580} r={5} fill="#FA6B12" />

        <text x={70} y={655} fontFamily="Arial, sans-serif" fontSize={10} fill="#666">Jul</text>
        <text x={190} y={655} fontFamily="Arial, sans-serif" fontSize={10} fill="#666">Sep</text>
        <text x={310} y={655} fontFamily="Arial, sans-serif" fontSize={10} fill="#666">Oct</text>

        {/* Bottom Navigation */}
        <rect x={35} y={700} width={330} height={65} fill="#FFFFFF" style={{ filter: "drop-shadow(0 -2px 8px rgba(0,0,0,0.1))" }} />

        {/* Home */}
        <g
          role="button"
          aria-label="Home"
          tabIndex={0}
          onKeyDown={onKeyActivate}
          onClick={onNavHome}
          style={{ cursor: onNavHome ? "pointer" : "default" }}
        >
          <circle cx={90} cy={730} r={20} fill="#39037E" />
          <text x={90} y={738} fontFamily="Arial, sans-serif" fontSize={18} fill="#FFFFFF" textAnchor="middle">🏠</text>
        </g>

        {/* Dashboard */}
        <g
          role="button"
          aria-label="Dashboard"
          tabIndex={0}
          onKeyDown={onKeyActivate}
          onClick={onNavDashboard}
          style={{ cursor: onNavDashboard ? "pointer" : "default" }}
        >
          <circle cx={165} cy={730} r={20} fill="#E0E0E0" />
          <text x={165} y={738} fontFamily="Arial, sans-serif" fontSize={18} fill="#666" textAnchor="middle">📊</text>
        </g>

        {/* Chat */}
        <g
          role="button"
          aria-label="Chat"
          tabIndex={0}
          onKeyDown={onKeyActivate}
          onClick={onNavChat}
          style={{ cursor: onNavChat ? "pointer" : "default" }}
        >
          <circle cx={240} cy={730} r={20} fill="#E0E0E0" />
          <text x={240} y={738} fontFamily="Arial, sans-serif" fontSize={18} fill="#666" textAnchor="middle">💬</text>
        </g>

        {/* Settings */}
        <g
          role="button"
          aria-label="Settings"
          tabIndex={0}
          onKeyDown={onKeyActivate}
          onClick={onNavSettings}
          style={{ cursor: onNavSettings ? "pointer" : "default" }}
        >
          <circle cx={315} cy={730} r={20} fill="#E0E0E0" />
          <text x={315} y={738} fontFamily="Arial, sans-serif" fontSize={18} fill="#666" textAnchor="middle">⚙️</text>
        </g>
      </svg>
    </div>
  );
}
