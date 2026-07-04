// Radial SVG progress ring used for PR readiness score & countdowns.
export function ProgressRing({ value = 0, size = 120, stroke = 9, label, sub, color = "#0066FF", trackClass = "text-secondary" }) {
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const offset = c - (Math.min(100, Math.max(0, value)) / 100) * c;
  return (
    <div className="relative grid place-items-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} strokeWidth={stroke} className={trackClass} stroke="currentColor" fill="none" />
        <circle
          cx={size / 2} cy={size / 2} r={r} strokeWidth={stroke} stroke={color} fill="none"
          strokeDasharray={c} strokeDashoffset={offset} strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 1s ease" }}
        />
      </svg>
      <div className="absolute inset-0 grid place-content-center text-center">
        <span className="font-display text-2xl font-bold leading-none">{value}%</span>
        {label && <span className="mt-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">{label}</span>}
        {sub && <span className="text-[11px] text-muted-foreground">{sub}</span>}
      </div>
    </div>
  );
}
