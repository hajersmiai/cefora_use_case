import React from "react";

export type Lang = "FR" | "NL" | "EN";

type Ctx = { lang: Lang; setLang: (l: Lang) => void };
const LanguageContext = React.createContext<Ctx | undefined>(undefined);

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLangState] = React.useState<Lang>(() => {
    const saved = localStorage.getItem("app.lang") as Lang | null;
    return saved ?? "FR";
  });

  const setLang = (l: Lang) => {
    setLangState(l);
    localStorage.setItem("app.lang", l);
    document.documentElement.lang = l.toLowerCase();
  };

  React.useEffect(() => {
    document.documentElement.lang = lang.toLowerCase();
  }, [lang]);

  return (
    <LanguageContext.Provider value={{ lang, setLang }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const ctx = React.useContext(LanguageContext);
  if (!ctx) throw new Error("useLanguage must be used inside <LanguageProvider>");
  return ctx;
}
