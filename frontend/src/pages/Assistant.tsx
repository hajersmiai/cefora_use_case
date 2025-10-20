import React from "react";
import { useNavigate } from "react-router-dom";
import { useLanguage } from "../i18n/LanguageProvider";

type Lang = "FR" | "NL" | "EN";

interface Message {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: string;
}

const T: Record<Lang, any> = {
  FR: {
    title: "VacaViz Assistant",
    poweredBy: "Propulsé par",
    back: "← Accueil",
    placeholder: "Posez votre question...",
    send: "Envoyer",
    welcome:
      "👋 Bonjour ! Je suis votre assistant VacaViz.\nJe peux vous aider à explorer les tendances du marché de l'emploi,\nanalyser les données et répondre à vos questions.",
    chip1: "Compétences en demande 🔥",
    input1: "Quelles sont les compétences les plus demandées ?",
    chip2: "Tendances salariales 💰",
    input2: "Quelles sont les tendances salariales ?",
    chip3: "Emplois à distance 🏠",
    input3: "Où trouver des emplois à distance ?",
  },
  NL: {
    title: "VacaViz Assistent",
    poweredBy: "Mogelijk gemaakt door",
    back: "← Home",
    placeholder: "Stel uw vraag...",
    send: "Verzenden",
    welcome:
      "👋 Hallo! Ik ben uw VacaViz assistent.\nIk help u arbeidsmarkttrends te verkennen,\ngegevens te analyseren en vragen te beantwoorden.",
    chip1: "Gevraagde skills 🔥",
    input1: "Wat zijn de meest gevraagde vaardigheden?",
    chip2: "Salaristrends 💰",
    input2: "Wat zijn de salaristrends?",
    chip3: "Thuiswerk 🏠",
    input3: "Waar vind ik thuiswerk?",
  },
  EN: {
    title: "VacaViz Assistant",
    poweredBy: "Powered by",
    back: "← Home",
    placeholder: "Ask your question...",
    send: "Send",
    welcome:
      "👋 Hello! I'm your VacaViz assistant.\nI can help you explore job-market trends,\nanalyze data, and answer your questions.",
    chip1: "In-demand skills 🔥",
    input1: "What are the most in-demand skills?",
    chip2: "Salary trends 💰",
    input2: "What are the salary trends?",
    chip3: "Remote jobs 🏠",
    input3: "Where to find remote jobs?",
  },
};

export type ChatbotPanelProps = {
  className?: string;
  modelName?: string; // e.g. "TinyLlama"
  onClose?: () => void;
  onSendText?: (text: string) => Promise<string> | string;
};

export default function ChatbotPanel({
  className,
  modelName = "TinyLlama",
  onClose,
  onSendText,
}: ChatbotPanelProps) {
  const navigate = useNavigate();
  const { lang, setLang } = useLanguage();
  const t = T[lang as Lang];

  const [input, setInput] = React.useState("");
  const [messages, setMessages] = React.useState<Message[]>([]);
  const tailRef = React.useRef<HTMLDivElement>(null);

  // Pour typer proprement xmlns dans foreignObject
  const XHTML_NS = { xmlns: "http://www.w3.org/1999/xhtml" } as any;

  React.useEffect(() => {
    setMessages([
      {
        id: "welcome",
        text: t.welcome,
        isUser: false,
        timestamp: new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
      },
    ]);
  }, [lang]);

  React.useEffect(() => {
    tailRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async () => {
    const text = input.trim();
    if (!text) return;

    const now = new Date().toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });

    setMessages((m) => [
      ...m,
      { id: crypto.randomUUID(), text, isUser: true, timestamp: now },
    ]);
    setInput("");

    let reply: string;
    if (onSendText) {
      const r = await onSendText(text);
      reply = typeof r === "string" ? r : "";
    } else {
      reply =
        lang === "FR"
          ? `Merci pour votre question: « ${text} ». J’analyse et je reviens avec des insights.`
          : lang === "NL"
          ? `Bedankt voor uw vraag: “${text}”. Ik analyseer en kom terug met inzichten.`
          : `Thanks for your question: “${text}”. I’ll analyze and return insights.`;
    }

    setMessages((m) => [
      ...m,
      {
        id: crypto.randomUUID(),
        text: reply,
        isUser: false,
        timestamp: new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
      },
    ]);
  };

  const onTextKeyDown: React.KeyboardEventHandler<HTMLTextAreaElement> = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  // UI inline (cohérence BG + distribution)
  const ui = {
    headerRow: {
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      height: "58px",
      padding: "6px 8px",
      color: "#fff",
      fontFamily: "Inter, Arial, sans-serif",
    } as React.CSSProperties,
    backBtn: {
      background: "rgba(255,255,255,0.25)",
      border: "1px solid rgba(255,255,255,0.35)",
      color: "#fff",
      padding: "6px 10px",
      borderRadius: 10,
      fontSize: 12,
      cursor: "pointer",
    } as React.CSSProperties,
    langBtn: (active: boolean): React.CSSProperties => ({
      background: active ? "#fff" : "transparent",
      color: active ? "#39037E" : "rgba(255,255,255,0.92)",
      border: "1px solid rgba(255,255,255,0.35)",
      padding: "6px 10px",
      borderRadius: 12,
      fontWeight: 600,
      fontSize: 14,
      marginLeft: 8,
      cursor: "pointer",
    }),
    msgsWrap: {
      width: "100%",
      height: "100%",
      background: "#FFFFFF",
      fontFamily: "Inter, Arial, sans-serif",
    } as React.CSSProperties,
    msgs: {
      height: "100%",
      overflowY: "auto",
      padding: "14px 18px",
      display: "flex",
      flexDirection: "column",
      gap: 10,
    } as React.CSSProperties,
    bubbleBase: {
      maxWidth: "90%",
      padding: "10px 12px",
      borderRadius: 14,
      fontSize: 16,
      lineHeight: 1.35,
      whiteSpace: "pre-wrap",
    } as React.CSSProperties,
    user: {
      alignSelf: "flex-end",
      background: "rgba(180,155,255,0.18)",
      border: "1px solid rgba(180,155,255,0.45)",
      color: "#39037E",
    } as React.CSSProperties,
    bot: {
      alignSelf: "flex-start",
      background: "#fff",
      border: "1px solid #BAE0DE",
      color: "#39037E",
    } as React.CSSProperties,
    time: { fontSize: 12, color: "#8a8a8a", marginTop: 6 } as React.CSSProperties,
    chipsRow: {
      display: "flex",
      gap: 10,
      padding: "8px 16px",
      background: "#F5F5F5",
      borderTop: "1px solid #E5E5E5",
      alignItems: "center",
      height: 50,
    } as React.CSSProperties,
    chip: {
      padding: "6px 10px",
      borderRadius: 9999,
      background: "#E8E3F5",
      color: "#39037E",
      fontSize: 12,
      cursor: "pointer",
      border: "none",
    } as React.CSSProperties,
    inputBar: {
      display: "flex",
      gap: 8,
      alignItems: "center",
      padding: "12px",
      background: "#F5F5F5",
      borderTop: "1px solid #E5E5E5",
      height: 120,
    } as React.CSSProperties,
    textarea: {
      flex: 1,
      resize: "none",
      height: 72,
      padding: "10px 12px",
      borderRadius: 12,
      border: "2px solid #B49BFF",
      outline: "none",
      fontSize: 14,
      background: "#FFFFFF",
    } as React.CSSProperties,
    sendBtn: {
      padding: "12px 14px",
      borderRadius: 10,
      background: "#FA6B12",
      color: "#fff",
      border: "none",
      cursor: "pointer",
      fontWeight: 700,
      height: 44,
      minWidth: 100,
    } as React.CSSProperties,
  };

  return (
    <div className={className ?? ""}>
      <svg
        viewBox="0 0 450 800"
        xmlns="http://www.w3.org/2000/svg"
        className="w-full h-auto"
        role="img"
        aria-labelledby="panelTitle panelDesc"
      >
        <title id="panelTitle">{t.title}</title>
        <desc id="panelDesc">Chat with messages list, quick chips and input.</desc>

        <defs>
          <linearGradient id="headerGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#39037E" />
            <stop offset="100%" stopColor="#B49BFF" />
          </linearGradient>
        </defs>

        {/* Background global */}
        <rect width="450" height="800" fill="#F8F8FF" />

        {/* HEADER */}
        <rect x="0" y="0" width="450" height="70" fill="url(#headerGrad)" />
        <circle cx="40" cy="40" r="22" fill="#FFFFFF" />
        <text x="40" y="49" textAnchor="middle" fontFamily="Arial, sans-serif" fontSize="20" fill="#39037E">🤖</text>
        <text x="75" y="35" fontFamily="Arial, sans-serif" fontSize="22" fontWeight="bold" fill="#FFFFFF">
          {t.title}
        </text>
        <text x="75" y="56" fontFamily="Arial, sans-serif" fontSize="13" fill="#BAE0DE">
          {t.poweredBy} {modelName}
        </text>

        {/* Close */}
        <g onClick={onClose} style={{ cursor: onClose ? "pointer" : "default" }}>
          <circle cx="410" cy="40" r="16" fill="#FFFFFF" opacity="0.3" />
          <text x="410" y="46" textAnchor="middle" fontFamily="Arial, sans-serif" fontSize="16" fill="#FFFFFF">✕</text>
        </g>

    

        {/* ZONES SVG pour assurer la cohérence visuelle */}
        {/* Messages */}
        <rect x="0" y="80" width="450" height="510" fill="#FFFFFF" />
        {/* Chips */}
        <rect x="0" y="590" width="450" height="50" fill="#F5F5F5" />
        {/* Input */}
        <rect x="0" y="640" width="450" height="120" fill="#F5F5F5" />

        {/* Messages (HTML) */}
        <foreignObject x="0" y="100" width="450" height="510">
          <div {...XHTML_NS} style={ui.msgsWrap}>
            <div style={ui.msgs}>
              {messages.map((m) => (
                <div
                  key={m.id}
                  style={{
                    display: "flex",
                    justifyContent: m.isUser ? "flex-end" : "flex-start",
                  }}
                >
                  <div style={{ ...ui.bubbleBase, ...(m.isUser ? ui.user : ui.bot) }}>
                    {m.text}
                    <div style={ui.time}>{m.timestamp}</div>
                  </div>
                </div>
              ))}
              <div ref={tailRef} />
            </div>
          </div>
        </foreignObject>

        {/* Chips (HTML) */}
        <foreignObject x="0" y="590" width="450" height="50">
          <div {...XHTML_NS} style={ui.chipsRow}>
            <button style={ui.chip} onClick={() => setInput(t.input1)}>{t.chip1}</button>
            <button style={ui.chip} onClick={() => setInput(t.input2)}>{t.chip2}</button>
            <button style={ui.chip} onClick={() => setInput(t.input3)}>{t.chip3}</button>
          </div>
        </foreignObject>

        {/* Barre d'input (HTML) */}
        <foreignObject x="0" y="640" width="450" height="120">
          <div {...XHTML_NS} style={ui.inputBar}>
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={onTextKeyDown}
              placeholder={t.placeholder}
              style={ui.textarea}
            />
            <button style={ui.sendBtn} onClick={send}>{t.send}</button>
          </div>
        </foreignObject>

        {/* Flèche RETOUR — bas gauche */}
        <g
          role="button"
          aria-label="Retour"
          tabIndex={0}
          onClick={() => navigate(-1)}
          onKeyDown={(e: any) => (e.key === "Enter" || e.key === " ") && navigate(-1)}
          style={{ cursor: "pointer" }}
          transform="translate(16, 776)"
        >
          {/* zone cliquable confortable */}
          <rect x="0" y="-12" width="100" height="30" rx="10" fill="rgba(57,3,126,0.08)" />
          {/* flèche gauche */}
         
          <text x="8" y="7" fontFamily="Arial, sans-serif" fontSize="16" fontWeight="bold" fill="#39037E">
            {t.back}
          </text>
        </g>
      </svg>
    </div>
  );
}
