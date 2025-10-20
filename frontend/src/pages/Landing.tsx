// src/pages/LandingPage.tsx
import React from "react";
// Import logo URL
import ceforaLogoUrl from "../assets/CEVORA-CEFORA_Logo+baseline_RGB.png?url";
import { useNavigate } from "react-router-dom";

import { useLanguage, type Lang } from "../i18n/LanguageProvider";

// Définition des traductions
const translations = {
  FR: {
    title1: "DÉCOUVREZ LES",
    title2: "TENDANCES DU MARCHÉ",
    subtitle: "Restez Jobtimal",
    quickSearch: "Recherche Rapide",
    selectRegion: "Sélectionner Région",
    selectSector: "Sélectionner Secteur",
    searchProfession: "Rechercher Profession ou Compétence",
    exploreDashboard: "Explorer Tableau de Bord →",
    askAssistant: "Demander à l'Assistant →"
  },
  NL: {
    title1: "ONTDEK DE",
    title2: "ARBEIDSMARKTTRENDS",
    subtitle: "Blijf Jobtimal",
    quickSearch: "Snelle Zoekopdracht",
    selectRegion: "Selecteer Regio",
    selectSector: "Selecteer Sector",
    searchProfession: "Zoek Beroep of Vaardigheid",
    exploreDashboard: "Verken Dashboard →",
    askAssistant: "Vraag Assistent →"
  },
  EN: {
    title1: "DISCOVER JOB",
    title2: "MARKET TRENDS",
    subtitle: "Stay Jobtimal",
    quickSearch: "Quick Search",
    selectRegion: "Select Region",
    selectSector: "Select Sector",
    searchProfession: "Search Profession or Skill",
    exploreDashboard: "Explore Dashboard →",
    askAssistant: "Ask Assistant →"
  }
};

export default function LandingPage() {
  const { lang, setLang } = useLanguage();
// Récupérer les textes selon la langue sélectionnée
  const t = translations[lang];
  const navigate = useNavigate();
  const onKeyActivate: React.KeyboardEventHandler<SVGGElement> = (e) => {
    if (e.key === "Enter" || e.key === " ") (e.currentTarget as any).click?.();
  };


  return (
    <div className="w-full min-h-screen flex flex-col items-center justify-start bg-white">
      <svg
        viewBox="0 0 1200 800"
        xmlns="http://www.w3.org/2000/svg"
        className="w-full h-auto"
      >
        {/* === Gradients === */}
        <defs>
          <linearGradient id="heroGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#39037E" />
            <stop offset="100%" stopColor="#B49BFF" />
          </linearGradient>
          <linearGradient id="buttonGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#FA6B12" />
            <stop offset="100%" stopColor="#FFBAE8" />
          </linearGradient>
        </defs>

        {/* === Background === */}
        <rect width="1200" height="800" fill="url(#heroGradient)" />
        
        {/* === Header === */}
        <rect x="0" y="0" width="1200" height="100" fill="#39037E" opacity="0.95" />
        {/* plaque claire sous le logo (contraste) */}
        <rect x="28" y="12" width="290" height="75" rx="14" fill="#ffffffff" opacity="0.75" />
        {/* Logo CEFORA - Grande taille visible */}
        <image
          href={ceforaLogoUrl}
          x="30"
          y="15"
          width="280"     /* Augmenté de 200 à 280 */
          height="70"     /* Augmenté de 60 à 70 */
          preserveAspectRatio="xMidYMid meet"
          aria-label="Cefora logo"
        />

        {/* Language selector (right side) */}
        <g>
          {(["FR", "NL", "EN"] as Lang[]).map((l, i) => (
            <g key={l}>
              <text
                x={1070 + i * 50}
                y="55"
                fontFamily="Arial, sans-serif"
                fontSize="18"
                fill="#FFFFFF"
                fontWeight={l === lang ? "bold" : "500"}
                textAnchor="middle"
                cursor="pointer"
                opacity={l === lang ? 1 : 0.6}
                onClick={() => setLang(l)}
                style={{ userSelect: "none" }}
              >
                {l}
              </text>
              {i < 2 && (
                <text
                  x={1095 + i * 50}
                  y="55"
                  fontFamily="Arial, sans-serif"
                  fontSize="18"
                  fill="#FFFFFF"
                  opacity="0.6"
                >
                  |
                </text>
              )}
            </g>
          ))}
        </g>

        {/* === Hero Title (centered) === */}
        <g transform="translate(600, 270)">
          <text
            x="0"
            y="0"
            fontFamily="Arial, sans-serif"
            fontSize="56"
            fontWeight="bold"
            fill="#FFFFFF"
            textAnchor="middle"
            letterSpacing="2"
          >
            {t.title1}
          </text>
          <text
            x="0"
            y="65"
            fontFamily="Arial, sans-serif"
            fontSize="56"
            fontWeight="bold"
            fill="#FFFFFF"
            textAnchor="middle"
            letterSpacing="2"
          >
            {t.title2}
          </text>
          <text
            x="0"
            y="115"
            fontFamily="Arial, sans-serif"
            fontSize="28"
            fill="#BAE0DE"
            textAnchor="middle"
            fontWeight="600"
          >
            {t.subtitle}
          </text>
        </g>

        {/* === Quick Search Card === */}
        <rect x="340" y="440" width="520" height="230" rx="16" fill="#FFFFFF" opacity="0.96" />
        <text
          x="600"
          y="475"
          fontFamily="Arial, sans-serif"
          fontSize="20"
          fontWeight="bold"
          fill="#39037E"
          textAnchor="middle"
        >
          {t.quickSearch}
        </text>

        {/* Filter fields */}
        <rect x="360" y="505" width="230" height="45" rx="8" fill="#F5F5F5" stroke="#B49BFF" strokeWidth={2} />
        <text x="475" y="532" fontFamily="Arial, sans-serif" fontSize="14" fill="#666" textAnchor="middle">
          {t.selectRegion}
        </text>

        <rect x="610" y="505" width="230" height="45" rx="8" fill="#F5F5F5" stroke="#B49BFF" strokeWidth={2} />
        <text x="725" y="532" fontFamily="Arial, sans-serif" fontSize="14" fill="#666" textAnchor="middle">
          {t.selectSector}
        </text>

        <rect x="360" y="565" width="480" height="45" rx="8" fill="#F5F5F5" stroke="#B49BFF" strokeWidth={2} />
        <text x="600" y="592" fontFamily="Arial, sans-serif" fontSize="14" fill="#666" textAnchor="middle">
          {t.searchProfession}
        </text>

        {/* === CTA Buttons === */}
        <g transform="translate(600, 700)">
          {/* Explore Dashboard */}
          <g
            role="button"
            aria-label="Explore Dashboard"
            tabIndex={0}
            onKeyDown={onKeyActivate}
            onClick={() => navigate("/dashboard")}
            style={{ cursor: "pointer" }}
          >
            <rect x="-260" y="0" width="250" height="55" rx="10" fill="url(#buttonGradient)" />
            <text
              x="-135"
              y="34"
              fontFamily="Arial, sans-serif"
              fontSize="18"
              fontWeight="bold"
              fill="#FFFFFF"
              textAnchor="middle"
            >
              {t.exploreDashboard}
            </text>
          </g>

          {/* Ask Assistant */}
          <g
            role="button"
            aria-label="Ask Assistant"
            tabIndex={0}
            onKeyDown={onKeyActivate}
            onClick={() => navigate("/assistant")}
            style={{ cursor: "pointer" }}
          >
            <rect x="10" y="0" width="250" height="55" rx="10" fill="#BAE0DE" />
            <text
              x="135"
              y="34"
              fontFamily="Arial, sans-serif"
              fontSize="18"
              fontWeight="bold"
              fill="#39037E"
              textAnchor="middle"
            >
              {t.askAssistant}
            </text>
          </g>
        </g>
        {/* === Decorative Arrow (left) === */}
        <path 
          d="M 50 280 L 200 400 L 50 520 L 90 520 L 240 400 L 90 280 Z" 
          fill="white" 
          opacity="0.12"
        />
        
      </svg>
    </div>
  );
}