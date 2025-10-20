import React, { useMemo } from "react";

export type ExportFormat = "csv" | "pdf";

export type ExportModalProps = {
  open?: boolean;
  className?: string;
  selectionLabel?: string; // e.g., "IT Sector, Brussels Region"
  recordsLabel?: string; // e.g., "2,453 job offers"
  chosenFormat?: ExportFormat; // controlled selected format
  onChooseFormat?: (fmt: ExportFormat) => void;
  onCancel?: () => void;
  onDownload?: () => void;
  onClose?: () => void; // close via overlay or X
};

/**
 * Accessible, responsive React/TSX conversion of your Export Modal SVG.
 * The two format cards (CSV/PDF) and action buttons are interactive.
 */
export default function ExportModal({
  open = true,
  className,
  selectionLabel = "IT Sector, Brussels Region",
  recordsLabel = "2,453 job offers",
  chosenFormat,
  onChooseFormat,
  onCancel,
  onDownload,
  onClose,
}: ExportModalProps) {
  const csvActive = useMemo(() => chosenFormat === "csv", [chosenFormat]);
  const pdfActive = useMemo(() => chosenFormat === "pdf", [chosenFormat]);

  const onKeyActivate: React.KeyboardEventHandler<SVGGElement> = (e) => {
    if (e.key === "Enter" || e.key === " ") {
      (e.currentTarget as any).click?.();
    }
  };

  if (!open) return null;

  return (
    <div className={className ?? ""}>
      <svg
        viewBox="0 0 800 600"
        xmlns="http://www.w3.org/2000/svg"
        role="dialog"
        aria-labelledby="exportTitle"
        aria-modal="true"
        className="w-full h-auto"
      >
        <defs>
          <linearGradient id="exportGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#39037E" stopOpacity={1} />
            <stop offset="100%" stopColor="#FA6B12" stopOpacity={1} />
          </linearGradient>
          <filter id="shadow">
            <feDropShadow dx="0" dy="4" stdDeviation="12" floodOpacity="0.3" />
          </filter>
        </defs>

        {/* Overlay Background (click to close) */}
        <g
          role="button"
          aria-label="Close export modal"
          tabIndex={0}
          onKeyDown={onKeyActivate}
          onClick={onClose}
          style={{ cursor: onClose ? "pointer" : "default" }}
        >
          <rect width="800" height="600" fill="#000000" opacity={0.5} />
        </g>

        {/* Modal Container */}
        <rect x="150" y="100" width="500" height="400" rx={20} fill="#FFFFFF" filter="url(#shadow)" />

        {/* Modal Header */}
        <rect x="150" y="100" width="500" height="80" rx={20} fill="url(#exportGradient)" />
        <rect x="150" y="160" width="500" height="20" fill="url(#exportGradient)" />

        <text id="exportTitle" x="400" y="145" fontFamily="Arial, sans-serif" fontSize={24} fontWeight="bold" fill="#FFFFFF" textAnchor="middle">
          Export Your Data
        </text>

        {/* Close Button (X) */}
        <g
          role="button"
          aria-label="Close export modal"
          tabIndex={0}
          onKeyDown={onKeyActivate}
          onClick={onClose}
          style={{ cursor: onClose ? "pointer" : "default" }}
        >
          <circle cx={610} cy={135} r={18} fill="#FFFFFF" opacity={0.3} />
          <text x={610} y={142} fontFamily="Arial, sans-serif" fontSize={18} fill="#FFFFFF" textAnchor="middle">✕</text>
        </g>

        {/* Modal Content */}
        <text x={180} y={215} fontFamily="Arial, sans-serif" fontSize={16} fill="#666">
          Choose your export format:
        </text>

        {/* CSV Option */}
        <g
          role="button"
          aria-label="Choose CSV format"
          tabIndex={0}
          onKeyDown={onKeyActivate}
          onClick={onChooseFormat ? () => onChooseFormat("csv") : undefined}
          style={{ cursor: onChooseFormat ? "pointer" : "default" }}
        >
          <rect x={180} y={240} width={220} height={120} rx={12} fill="#F8F8FF" stroke={csvActive ? "#39037E" : "#B49BFF"} strokeWidth={2} />
          <rect x={190} y={250} width={60} height={60} rx={8} fill="#BAE0DE" />
          <text x={220} y={290} fontFamily="Arial, sans-serif" fontSize={32} fill="#39037E" textAnchor="middle">📊</text>

          <text x={270} y={275} fontFamily="Arial, sans-serif" fontSize={18} fontWeight="bold" fill="#39037E">CSV File</text>
          <text x={270} y={300} fontFamily="Arial, sans-serif" fontSize={13} fill="#666">Spreadsheet format</text>
          <text x={270} y={320} fontFamily="Arial, sans-serif" fontSize={13} fill="#666">Easy to analyze</text>
          <text x={270} y={340} fontFamily="Arial, sans-serif" fontSize={13} fill="#666">Excel compatible</text>
        </g>

        {/* PDF Option */}
        <g
          role="button"
          aria-label="Choose PDF format"
          tabIndex={0}
          onKeyDown={onKeyActivate}
          onClick={onChooseFormat ? () => onChooseFormat("pdf") : undefined}
          style={{ cursor: onChooseFormat ? "pointer" : "default" }}
        >
          <rect x={420} y={240} width={220} height={120} rx={12} fill="#F8F8FF" stroke={pdfActive ? "#39037E" : "#B49BFF"} strokeWidth={2} />
          <rect x={430} y={250} width={60} height={60} rx={8} fill="#FFBAE8" />
          <text x={460} y={290} fontFamily="Arial, sans-serif" fontSize={32} fill="#39037E" textAnchor="middle">📄</text>

          <text x={510} y={275} fontFamily="Arial, sans-serif" fontSize={18} fontWeight="bold" fill="#39037E">PDF Report</text>
          <text x={510} y={300} fontFamily="Arial, sans-serif" fontSize={13} fill="#666">Professional format</text>
          <text x={510} y={320} fontFamily="Arial, sans-serif" fontSize={13} fill="#666">Includes charts</text>
          <text x={510} y={340} fontFamily="Arial, sans-serif" fontSize={13} fill="#666">Ready to share</text>
        </g>

        {/* Export Settings */}
        <rect x={180} y={380} width={460} height={60} rx={8} fill="#FCFAC7" opacity={0.3} />
        <text x={200} y={405} fontFamily="Arial, sans-serif" fontSize={14} fill="#39037E">📁 Current selection: {selectionLabel}</text>
        <text x={200} y={425} fontFamily="Arial, sans-serif" fontSize={14} fill="#39037E">📈 Records to export: {recordsLabel}</text>

        {/* Action Buttons */}
        <g
          role="button"
          aria-label="Cancel export"
          tabIndex={0}
          onKeyDown={onKeyActivate}
          onClick={onCancel}
          style={{ cursor: onCancel ? "pointer" : "default" }}
        >
          <rect x={180} y={460} width={200} height={50} rx={10} fill="#E0E0E0" />
          <text x={280} y={490} fontFamily="Arial, sans-serif" fontSize={16} fill="#666" textAnchor="middle">Cancel</text>
        </g>

        <g
          role="button"
          aria-label="Download export"
          tabIndex={0}
          onKeyDown={onKeyActivate}
          onClick={onDownload}
          style={{ cursor: onDownload ? "pointer" : "default" }}
        >
          <rect x={400} y={460} width={240} height={50} rx={10} fill="url(#exportGradient)" />
          <text x={520} y={490} fontFamily="Arial, sans-serif" fontSize={16} fontWeight="bold" fill="#FFFFFF" textAnchor="middle">Download Export →</text>
        </g>

        {/* Decorative Arrow */}
        <path d="M 220 520 L 260 520" stroke="#B49BFF" strokeWidth={3} fill="none" opacity={0.5} />
        <path d="M 260 520 L 250 513 M 260 520 L 250 527" stroke="#B49BFF" strokeWidth={3} fill="none" opacity={0.5} />
      </svg>
    </div>
  );
}
