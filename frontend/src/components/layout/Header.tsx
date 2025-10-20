// Header with Cefora branding and language selector
import { useState } from 'react'
import CeforaLogo from '../ui/CeforaLogo'

type Language = 'FR' | 'NL' | 'EN'

const Header = () => {
  const [currentLang, setCurrentLang] = useState<Language>('EN')
  const languages: Language[] = ['FR', 'NL', 'EN']

  return (
    <header className="w-full bg-cefora-violet py-4 px-8 flex justify-between items-center">
      {/* Cefora Logo */}
      <CeforaLogo />

      {/* Language Selector */}
      <div className="flex gap-1 text-white text-sm font-medium">
        {languages.map((lang, index) => (
          <span key={lang} className="flex items-center">
            <button
              onClick={() => setCurrentLang(lang)}
              className={`transition-colors ${
                currentLang === lang ? 'text-white' : 'text-white/70 hover:text-white'
              }`}
            >
              {lang}
            </button>
            {index < languages.length - 1 && (
              <span className="mx-2 text-white/50">|</span>
            )}
          </span>
        ))}
      </div>
    </header>
  )
}

export default Header