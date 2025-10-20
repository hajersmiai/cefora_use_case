// src/pages/Dashboard.tsx
import React from "react";
import { useNavigate } from "react-router-dom";
import ceforaLogoUrl from "../assets/CEVORA-CEFORA_Logo+baseline_RGB.png?url";
import { useLanguage } from "../i18n/LanguageProvider";
type Lang = "FR" | "NL" | "EN";
export type DashboardProps = {
  className?: string;
  onExport?: () => void;
  onReset?: () => void;
};

export default function Dashboard({ className, onExport, onReset }: DashboardProps) {
  const navigate = useNavigate();
  const { lang } = useLanguage();

  // Mini-i18n pour les libellés visibles de cette page
  const label = {
    FR: {
      filters: "Filtres",
      dateRange: "Période",
      region: "Région",
      sector: "Secteur",
      skills: "Compétences",
      activeFilters: "Filtres actifs :",
      export: "Exporter",
      reset: "Réinitialiser",
      back: "Retour",
      bySector: "Offres par secteur",
      geo: "Répartition géographique",
      trend: "Évolution dans le temps",
      totalOffers: "Offres d’emploi",
      companies: "Entreprises qui recrutent",
      growth: "Croissance vs mois dernier",
      allRegions: "Toutes régions ▼",
      allSectors: "Tous secteurs ▼",
      searchSkills: "Rechercher des compétences...",
    },
    NL: {
      filters: "Filters",
      dateRange: "Periode",
      region: "Regio",
      sector: "Sector",
      skills: "Vaardigheden",
      activeFilters: "Actieve filters:",
      export: "Exporteren",
      reset: "Resetten",
      back: "Terug",
      bySector: "Vacatures per sector",
      geo: "Geografische verdeling",
      trend: "Evolutie in de tijd",
      totalOffers: "Vacatures",
      companies: "Bedrijven die werven",
      growth: "Groei t.o.v. vorige maand",
      allRegions: "Alle regio’s ▼",
      allSectors: "Alle sectoren ▼",
      searchSkills: "Zoek vaardigheden...",
    },
    EN: {
      filters: "Filters",
      dateRange: "Date Range",
      region: "Region",
      sector: "Sector",
      skills: "Skills",
      activeFilters: "Active Filters:",
      export: "Export",
      reset: "Reset",
      back: "Back",
      bySector: "Job Offers by Sector",
      geo: "Geographic Distribution",
      trend: "Trend Over Time",
      totalOffers: "Total Job Offers",
      companies: "Companies Hiring",
      growth: "Growth vs Last Month",
      allRegions: "All Regions ▼",
      allSectors: "All Sectors ▼",
      searchSkills: "Search skills...",
    },
  }[lang];

  const onKeyActivate: React.KeyboardEventHandler<SVGGElement> = (e) => {
    if (e.key === "Enter" || e.key === " ") (e.currentTarget as any).click?.();
  };

  return (
    <div className={"w-full min-h-screen flex flex-col items-center justify-start bg-white " + (className ?? "")}>
      <svg viewBox="0 0 1400 900" xmlns="http://www.w3.org/2000/svg" className="w-full h-auto">
        {/* ====== DEFS ====== */}
        <defs>
          <linearGradient id="chartGradient" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#B49BFF" stopOpacity="0.8" />
            <stop offset="100%" stopColor="#39037E" stopOpacity="0.3" />
          </linearGradient>
        </defs>

        {/* ====== BACKGROUND ====== */}
        <rect width="1400" height="900" fill="#F8F8FF" />

        {/* ====== HEADER ====== */}
        <rect x="0" y="0" width="1400" height="100" fill="#39037E" />

        {/* Plaque claire sous le logo pour contraste */}
        <rect x="28" y="12" width="290" height="75" rx="14" fill="#FFFFFF" opacity="0.75" />
        {/* Logo CEFORA */}
        <image
          href={ceforaLogoUrl}
          x="30"
          y="15"
          width="280"
          height="70"
          preserveAspectRatio="xMidYMid meet"
          aria-label="Cefora logo"
        />

        <text x="350" y="60" fontFamily="Arial, sans-serif" fontSize="40" fontWeight="bold" fill="#FFFFFF">
          VacaViz Dashboard
        </text>

        {/* Profil à droite */}
        <circle cx="1320" cy="35" r="20" fill="#B49BFF" />
        <text x="1320" y="42" fontFamily="Arial, sans-serif" fontSize="16" fill="#FFFFFF" textAnchor="middle">
          👤
        </text>

        {/* ====== SIDEBAR / FILTERS ====== */}
        <rect x="0" y="110" width="280" height="800" fill="#FFFFFF" />
        <text x="20" y="150" fontFamily="Arial, sans-serif" fontSize="18" fontWeight="bold" fill="#39037E">
          {label.filters}
        </text>

        {/* Date Filter */}
        <text x="20" y="170" fontFamily="Arial, sans-serif" fontSize="14" fill="#666">
          {label.dateRange}
        </text>
        <rect x="20" y="180" width="240" height="35" rx="6" fill="#F5F5F5" stroke="#B49BFF" strokeWidth={1} />
        <text x="30" y="202" fontFamily="Arial, sans-serif" fontSize="12" fill="#666">
          Jan 2024 - Oct 2025
        </text>

        {/* Region Filter */}
        <text x="20" y="240" fontFamily="Arial, sans-serif" fontSize="14" fill="#666">
          {label.region}
        </text>
        <rect x="20" y="250" width="240" height="35" rx="6" fill="#F5F5F5" stroke="#B49BFF" strokeWidth={1} />
        <text x="30" y="272" fontFamily="Arial, sans-serif" fontSize="12" fill="#666">
          {label.allRegions}
        </text>

        {/* Sector Filter */}
        <text x="20" y="320" fontFamily="Arial, sans-serif" fontSize="14" fill="#666">
          {label.sector}
        </text>
        <rect x="20" y="330" width="240" height="35" rx="6" fill="#F5F5F5" stroke="#B49BFF" strokeWidth={1} />
        <text x="30" y="352" fontFamily="Arial, sans-serif" fontSize="12" fill="#666">
          {label.allSectors}
        </text>

        {/* Skills Filter */}
        <text x="20" y="390" fontFamily="Arial, sans-serif" fontSize="14" fill="#666">
          {label.skills}
        </text>
        <rect x="20" y="400" width="240" height="35" rx="6" fill="#F5F5F5" stroke="#B49BFF" strokeWidth={1} />
        <text x="30" y="422" fontFamily="Arial, sans-serif" fontSize="12" fill="#666">
          {label.searchSkills}
        </text>

        {/* Selected Filters */}
        <rect x="20" y="450" width="240" height="120" rx="8" fill="#FCFAC7" opacity={0.3} />
        <text x="30" y="475" fontFamily="Arial, sans-serif" fontSize="12" fontWeight="bold" fill="#39037E">
          {label.activeFilters}
        </text>
        <rect x="30" y="490" width="80" height="25" rx="12" fill="#BAE0DE" />
        <text x="70" y="507" fontFamily="Arial, sans-serif" fontSize="11" fill="#39037E" textAnchor="middle">
          IT Sector ✕
        </text>

        {/* Action Buttons */}
        <g
          role="button"
          aria-label="Export dashboard"
          tabIndex={0}
          onKeyDown={onKeyActivate}
          onClick={onExport}
          style={{ cursor: onExport ? "pointer" : "default" }}
        >
          <rect x="20" y="840" width="110" height="40" rx="8" fill="#FA6B12" />
          <text x="75" y="865" fontFamily="Arial, sans-serif" fontSize="14" fontWeight="bold" fill="#FFFFFF" textAnchor="middle">
            {label.export}
          </text>
        </g>

        <g
          role="button"
          aria-label="Reset filters"
          tabIndex={0}
          onKeyDown={onKeyActivate}
          onClick={onReset}
          style={{ cursor: onReset ? "pointer" : "default" }}
        >
          <rect x="150" y="840" width="110" height="40" rx="8" fill="#E0E0E0" />
          <text x="205" y="865" fontFamily="Arial, sans-serif" fontSize="14" fill="#666" textAnchor="middle">
            {label.reset}
          </text>
        </g>

        {/* ====== MAIN CONTENT ====== */}
        {/* KPI Cards */}
        <rect x="310" y="110" width="240" height="100" rx="10" fill="#FFFFFF" style={{ filter: "drop-shadow(0 2px 8px rgba(0,0,0,0.1))" }} />
        <text x="430" y="155" fontFamily="Arial, sans-serif" fontSize="32" fontWeight="bold" fill="#39037E" textAnchor="middle">
          8,542
        </text>
        <text x="430" y="185" fontFamily="Arial, sans-serif" fontSize="14" fill="#666" textAnchor="middle">
          {label.totalOffers}
        </text>
        <circle cx="510" cy="130" r="8" fill="#BAE0DE" />

        <rect x="570" y="110" width="240" height="100" rx="10" fill="#FFFFFF" style={{ filter: "drop-shadow(0 2px 8px rgba(0,0,0,0.1))" }} />
        <text x="690" y="155" fontFamily="Arial, sans-serif" fontSize="32" fontWeight="bold" fill="#39037E" textAnchor="middle">
          234
        </text>
        <text x="690" y="185" fontFamily="Arial, sans-serif" fontSize="14" fill="#666" textAnchor="middle">
          {label.companies}
        </text>
        <circle cx="770" cy="130" r="8" fill="#FFBAE8" />

        <rect x="830" y="110" width="240" height="100" rx="10" fill="#FFFFFF" style={{ filter: "drop-shadow(0 2px 8px rgba(0,0,0,0.1))" }} />
        <text x="950" y="155" fontFamily="Arial, sans-serif" fontSize="32" fontWeight="bold" fill="#39037E" textAnchor="middle">
          +12%
        </text>
        <text x="950" y="185" fontFamily="Arial, sans-serif" fontSize="14" fill="#666" textAnchor="middle">
          {label.growth}
        </text>
        <circle cx="1030" cy="130" r="8" fill="#B49BFF" />

        {/* Chart Area */}
        <rect x="310" y="230" width="520" height="320" rx="10" fill="#FFFFFF" style={{ filter: "drop-shadow(0 2px 8px rgba(0,0,0,0.1))" }} />
        <text x="330" y="260" fontFamily="Arial, sans-serif" fontSize="16" fontWeight="bold" fill="#39037E">
          {label.bySector}
        </text>

        {/* Bar Chart Simulation */}
        <rect x="340" y="310" width="60" height="200" fill="url(#chartGradient)" />
        <text x="370" y="490" fontFamily="Arial, sans-serif" fontSize="11" fill="#666" textAnchor="middle">
          IT
        </text>

        <rect x="420" y="350" width="60" height="160" fill="url(#chartGradient)" />
        <text x="450" y="490" fontFamily="Arial, sans-serif" fontSize="11" fill="#666" textAnchor="middle">
          Finance
        </text>

        <rect x="500" y="380" width="60" height="130" fill="url(#chartGradient)" />
        <text x="530" y="490" fontFamily="Arial, sans-serif" fontSize="11" fill="#666" textAnchor="middle">
          Health
        </text>

        <rect x="580" y="400" width="60" height="110" fill="url(#chartGradient)" />
        <text x="610" y="490" fontFamily="Arial, sans-serif" fontSize="11" fill="#666" textAnchor="middle">
          Retail
        </text>

        <rect x="660" y="420" width="60" height="90" fill="url(#chartGradient)" />
        <text x="690" y="490" fontFamily="Arial, sans-serif" fontSize="11" fill="#666" textAnchor="middle">
          Industry
        </text>

        <rect x="740" y="440" width="60" height="70" fill="url(#chartGradient)" />
        <text x="770" y="490" fontFamily="Arial, sans-serif" fontSize="11" fill="#666" textAnchor="middle">
          Other
        </text>

        {/* Map Area */}
        <rect x="850" y="230" width="520" height="320" rx="10" fill="#FFFFFF" style={{ filter: "drop-shadow(0 2px 8px rgba(0,0,0,0.1))" }} />
        <text x="870" y="260" fontFamily="Arial, sans-serif" fontSize="16" fontWeight="bold" fill="#39037E">
          {label.geo}
        </text>

        {/* Belgium Map Simplified */}
        <path d="M 940 310 L 1040 300 L 1110 330 L 1100 420 L 1020 460 L 950 460 L 920 370 Z" fill="#E8E3F5" stroke="#39037E" strokeWidth={2} />
        <circle cx="1000" cy="370" r="25" fill="#FA6B12" opacity={0.7} />
        <text x="1000" y="375" fontFamily="Arial, sans-serif" fontSize="12" fill="#FFFFFF" textAnchor="middle">
          Brussels
        </text>
        <circle cx="1070" cy="400" r="18" fill="#B49BFF" opacity={0.7} />
        <circle cx="970" cy="430" r="15" fill="#BAE0DE" opacity={0.7} />

        <text x="1200" y="370" fontFamily="Arial, sans-serif" fontSize="12" fill="#666">
          ● Brussels: 2,453
        </text>
        <text x="1200" y="385" fontFamily="Arial, sans-serif" fontSize="12" fill="#666">
          ● Flanders: 4,127
        </text>
        <text x="1200" y="400" fontFamily="Arial, sans-serif" fontSize="12" fill="#666">
          ● Wallonia: 1,962
        </text>

        {/* Timeline Chart */}
        <rect x="310" y="570" width="1060" height="240" rx="10" fill="#FFFFFF" style={{ filter: "drop-shadow(0 2px 8px rgba(0,0,0,0.1))" }} />
        <text x="330" y="600" fontFamily="Arial, sans-serif" fontSize="16" fontWeight="bold" fill="#39037E">
          {label.trend}
        </text>

        {/* Line Chart Simulation */}
        <polyline
          points="340,750 470,730 550,710 630,690 710,700 790,680 870,670 950,660 1030,650 1110,640 1190,640 1270,620 1350,600"
          fill="none"
          stroke="#39037E"
          strokeWidth={3}
        />
        <polyline
          points="340,750 470,730 550,710 630,690 710,700 790,680 870,670 950,660 1030,650 1110,640 1190,640 1270,620 1350,600"
          fill="url(#chartGradient)"
          opacity={0.3}
        />

        {/* X-axis labels */}
        <text x="340" y="780" fontFamily="Arial, sans-serif" fontSize="10" fill="#666" textAnchor="middle">
          Jan
        </text>
        <text x="500" y="780" fontFamily="Arial, sans-serif" fontSize="10" fill="#666" textAnchor="middle">
          Mar
        </text>
        <text x="660" y="780" fontFamily="Arial, sans-serif" fontSize="10" fill="#666" textAnchor="middle">
          May
        </text>
        <text x="820" y="780" fontFamily="Arial, sans-serif" fontSize="10" fill="#666" textAnchor="middle">
          Jul
        </text>
        <text x="980" y="780" fontFamily="Arial, sans-serif" fontSize="10" fill="#666" textAnchor="middle">
          Sep
        </text>
        <text x="1140" y="780" fontFamily="Arial, sans-serif" fontSize="10" fill="#666" textAnchor="middle">
          Nov
        </text>
        <text x="1300" y="780" fontFamily="Arial, sans-serif" fontSize="10" fill="#666" textAnchor="middle">
          2025
        </text>

        {/* Data points */}
        <circle cx="340" cy="750" r={5} fill="#FA6B12" />
        <circle cx="630" cy="690" r={5} fill="#FA6B12" />
        <circle cx="710" cy="700" r={5} fill="#FA6B12" />
        <circle cx="1110" cy="640" r={5} fill="#FA6B12" />
        <circle cx="1300" cy="612" r={5} fill="#FA6B12" />

        {/* Bouton Retour — bas de page, à droite */}
        <g
          role="button"
          aria-label={label.back}
          tabIndex={0}
          onKeyDown={onKeyActivate}
          onClick={() => navigate(-1)} // ou navigate("/")
          style={{ cursor: "pointer" }}
          transform="translate(1240, 860)"
        >
          {/* zone cliquable confortable */}
          <rect x="-10" y="-24" width="140" height="48" rx="10" fill="rgba(57,3,126,0.08)" />
          {/* flèche vers la gauche */}
          <path d="M 100 0 L 68 0 M 100 0 L 88 -12 M 100 0 L 88 12" stroke="#39037E" strokeWidth="4" fill="none" strokeLinecap="round" />
          {/* libellé */}
          <text x="10" y="6" fontFamily="Arial, sans-serif" fontSize="16" fontWeight="bold" fill="#39037E">
            {label.back}
          </text>
        </g>
      </svg>
    </div>
  );
}
