// src/components/NavBar.tsx
import React from "react";

type Lang = "FR" | "NL" | "EN";
type src ="../assets/CEVORA-CEFORA_Logo+baseline_RGB.svg"
export type NavBarProps = {
  logoSrc: src;                
  currentLang: Lang;
  onLangChange?: (lang: Lang) => void;
  className?: string;
};

export default function NavBar({
  logoSrc,
  currentLang,
  onLangChange,
  className,
}: NavBarProps) {
  const langs: Lang[] = ["FR", "NL", "EN"];

  return (
    <nav
      className={`w-full bg-[#39037E] text-white ${className ?? ""}`}
      aria-label="Main"
    >
      <div className="mx-auto flex h-16 max-w-[1200px] items-center justify-between px-4">
        {/* Logo + Brand */}
        <div className="flex items-center gap-3">
          <img
            src={logoSrc}
            alt="Cefora"
            className="h-8 w-auto"
            draggable={false}
          />
          <span className="text-lg font-bold tracking-wide">VacaViz</span>
        </div>

        {/* Language buttons */}
        <div className="flex items-center gap-2">
          {langs.map((l) => {
            const active = l === currentLang;
            return (
              <button
                key={l}
                type="button"
                onClick={onLangChange ? () => onLangChange(l) : undefined}
                aria-pressed={active}
                className={[
                  "rounded-full px-3 py-1 text-sm transition-colors",
                  active
                    ? "bg-white text-[#39037E] font-semibold"
                    : "hover:bg-white/15",
                ].join(" ")}
              >
                {l}
              </button>
            );
          })}
        </div>
      </div>
    </nav>
  );
}
