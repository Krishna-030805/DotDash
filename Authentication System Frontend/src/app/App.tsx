import { useState, useEffect, useRef, useCallback } from "react";

type Page = "welcome" | "login" | "register" | "recovery" | "dashboard";
export type RhythmData = { presses: number[], gaps: number[] };

const MORSE: Record<string, string> = {
  A: ".-", B: "-...", C: "-.-.", D: "-..", E: ".", F: "..-.", G: "--.",
  H: "....", I: "..", J: ".---", K: "-.-", L: ".-..", M: "--", N: "-.",
  O: "---", P: ".--.", Q: "--.-", R: ".-.", S: "...", T: "-", U: "..-",
  V: "...-", W: ".--", X: "-..-", Y: "-.--", Z: "--..",
  "0": "-----", "1": ".----", "2": "..---", "3": "...--", "4": "....-",
  "5": ".....", "6": "-....", "7": "--...", "8": "---..", "9": "----.",
};

const REVERSE_MORSE: Record<string, string> = Object.fromEntries(
  Object.entries(MORSE).map(([k, v]) => [v, k])
);

function toMorse(text: string): string {
  return text
    .toUpperCase()
    .split("")
    .map((c) => (c === " " ? "/" : MORSE[c] ?? ""))
    .join("  ");
}

// ─── BACKGROUND ────────────────────────────────────────────────────────────────

function MorseBackground() {
  const symbols = useRef(
    Array.from({ length: 80 }, (_, i) => ({
      id: i,
      char: Math.random() > 0.5 ? "•" : "—",
      x: Math.random() * 100,
      y: Math.random() * 100,
      delay: Math.random() * 6,
      duration: 3 + Math.random() * 4,
      size: 0.6 + Math.random() * 0.8,
    }))
  ).current;

  return (
    <div className="fixed inset-0 overflow-hidden pointer-events-none select-none">
      {symbols.map((s) => (
        <span
          key={s.id}
          className="absolute text-primary opacity-0 font-mono"
          style={{
            left: `${s.x}%`,
            top: `${s.y}%`,
            fontSize: `${s.size}rem`,
            animation: `morseFloat ${s.duration}s ${s.delay}s infinite ease-in-out`,
          }}
        >
          {s.char}
        </span>
      ))}
      <style>{`
        @keyframes morseFloat {
          0%, 100% { opacity: 0; transform: translateY(0px); }
          40%, 60% { opacity: 0.10; transform: translateY(-8px); }
        }
        @keyframes scanline {
          0% { transform: translateY(-100%); }
          100% { transform: translateY(100vh); }
        }
        @keyframes blink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0; }
        }
        @keyframes glowPulse {
          0%, 100% { box-shadow: 0 0 8px rgba(0,168,255,0.4), 0 0 24px rgba(0,168,255,0.12); }
          50% { box-shadow: 0 0 18px rgba(0,168,255,0.7), 0 0 44px rgba(0,168,255,0.28); }
        }
        @keyframes fadeSlideUp {
          from { opacity: 0; transform: translateY(24px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes terminalIn {
          from { opacity: 0; transform: translateY(12px) scale(0.98); }
          to { opacity: 1; transform: translateY(0) scale(1); }
        }
        @keyframes tapPulse {
          0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(0,168,255,0.5); }
          60% { transform: scale(0.96); box-shadow: 0 0 0 12px rgba(0,168,255,0); }
          100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(0,168,255,0); }
        }
        @keyframes holdGlow {
          0%, 100% { box-shadow: 0 0 12px rgba(0,168,255,0.6), inset 0 0 20px rgba(0,168,255,0.08); }
          50% { box-shadow: 0 0 28px rgba(0,168,255,0.9), inset 0 0 30px rgba(0,168,255,0.18); }
        }
        @keyframes symbolPop {
          from { opacity: 0; transform: translateY(-6px) scale(0.8); }
          to { opacity: 1; transform: translateY(0) scale(1); }
        }
      `}</style>
    </div>
  );
}

function ScanlineOverlay() {
  return (
    <div
      className="fixed inset-0 pointer-events-none z-50 overflow-hidden"
      style={{ mixBlendMode: "overlay", opacity: 0.035 }}
    >
      <div
        style={{
          width: "100%",
          height: "2px",
          background: "rgba(0,168,255,0.8)",
          animation: "scanline 4s linear infinite",
        }}
      />
    </div>
  );
}

function MorseTag({ text }: { text: string }) {
  return (
    <span className="text-muted-foreground font-mono text-xs tracking-widest opacity-55 select-none">
      {toMorse(text)}
    </span>
  );
}

function BlinkCursor() {
  return (
    <span
      className="inline-block w-2.5 h-5 bg-primary ml-1 align-middle"
      style={{ animation: "blink 1s step-end infinite" }}
    />
  );
}

function Logo({ onClick }: { onClick?: () => void }) {
  return (
    <button
      onClick={onClick}
      className="flex flex-col items-start gap-0.5 cursor-pointer"
    >
      <div className="flex items-center gap-2">
        <div className="flex gap-1 items-center">
          <span className="w-2.5 h-2.5 rounded-full bg-primary" style={{ boxShadow: "0 0 8px #00a8ff" }} />
          <span className="w-7 h-2.5 rounded-sm bg-primary" style={{ boxShadow: "0 0 8px #00a8ff" }} />
          <span className="w-2.5 h-2.5 rounded-full bg-primary" style={{ boxShadow: "0 0 8px #00a8ff" }} />
        </div>
        <span
          className="font-mono text-xl font-bold text-primary tracking-widest uppercase"
          style={{ fontFamily: "'JetBrains Mono', monospace", textShadow: "0 0 12px rgba(0,168,255,0.8)" }}
        >
          MorseAuth
        </span>
      </div>
      <span className="text-muted-foreground font-mono text-[10px] tracking-[0.3em] uppercase pl-10">
        Secure Signal Protocol
      </span>
    </button>
  );
}

// ─── MORSE TAP PASSWORD INPUT ──────────────────────────────────────────────────

function MorseTapInput({
  label,
  value,
  onChange,
  onRhythmChange,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  onRhythmChange?: (rhythm: RhythmData) => void;
}) {
  const [currentSymbols, setCurrentSymbols] = useState(""); // dots/dashes in progress
  const [pressing, setPressing] = useState(false);
  const [lastAction, setLastAction] = useState<"dot" | "dash" | null>(null);
  const pressStart = useRef(0);
  const lastPressEnd = useRef(0);
  const presses = useRef<number[]>([]);
  const gaps = useRef<number[]>([]);
  const letterTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const DOT_THRESHOLD = 300; // ms — under = dot, over = dash
  const LETTER_DELAY = 750;  // ms after last tap to commit letter

  const commitLetter = useCallback(
    (symbols: string) => {
      const char = REVERSE_MORSE[symbols];
      if (char) {
        onChange(value + char);
      }
      setCurrentSymbols("");
    },
    [value, onChange]
  );

  const scheduleCommit = useCallback(
    (symbols: string) => {
      if (letterTimer.current) clearTimeout(letterTimer.current);
      letterTimer.current = setTimeout(() => {
        commitLetter(symbols);
      }, LETTER_DELAY);
    },
    [commitLetter]
  );

  const handlePressStart = useCallback((e: React.MouseEvent | React.TouchEvent | any) => {
    e.preventDefault();
    if (letterTimer.current) clearTimeout(letterTimer.current);
    if (lastPressEnd.current > 0) {
      gaps.current.push(Date.now() - lastPressEnd.current);
    }
    pressStart.current = Date.now();
    setPressing(true);
  }, []);

  const handlePressEnd = useCallback(
    (e: React.MouseEvent | React.TouchEvent | any) => {
      e.preventDefault();
      const duration = Date.now() - pressStart.current;
      presses.current.push(duration);
      lastPressEnd.current = Date.now();
      
      const symbol = duration < DOT_THRESHOLD ? "." : "-";
      setLastAction(symbol === "." ? "dot" : "dash");
      setPressing(false);
      const next = currentSymbols + symbol;
      setCurrentSymbols(next);
      scheduleCommit(next);
      if (onRhythmChange) {
        onRhythmChange({ presses: [...presses.current], gaps: [...gaps.current] });
      }
    },
    [currentSymbols, scheduleCommit, onRhythmChange]
  );

  const handleBackspace = () => {
    if (letterTimer.current) clearTimeout(letterTimer.current);
    setCurrentSymbols("");
    onChange(value.slice(0, -1));
  };

  const handleClear = () => {
    if (letterTimer.current) clearTimeout(letterTimer.current);
    setCurrentSymbols("");
    onChange("");
    presses.current = [];
    gaps.current = [];
    lastPressEnd.current = 0;
    if (onRhythmChange) onRhythmChange({ presses: [], gaps: [] });
  };

  useEffect(() => {
    return () => { if (letterTimer.current) clearTimeout(letterTimer.current); };
  }, []);

  // Keyboard support: space = tap (handled via onKeyDown/onKeyUp on the button itself now)

  const charCount = value.length;

  return (
    <div className="flex flex-col gap-2">
      {/* Label row */}
      <div className="flex items-center justify-between">
        <label className="font-mono text-xs tracking-widest uppercase text-foreground"
          style={{ fontFamily: "'JetBrains Mono', monospace" }}>
          {label}
        </label>
        <span className="font-mono text-[10px] text-muted-foreground opacity-50 tracking-wider">
          {toMorse("PASS")}
        </span>
      </div>

      {/* Decoded display */}
      <div
        className="w-full px-4 py-3 font-mono text-sm bg-card border border-border flex items-center gap-1 min-h-[46px]"
        style={{ borderColor: pressing ? "#00a8ff" : undefined, boxShadow: pressing ? "0 0 0 1px #00a8ff, 0 0 16px rgba(0,168,255,0.2)" : "none" }}
      >
        {charCount === 0 && !currentSymbols && (
          <span className="text-muted-foreground/40 text-xs tracking-widest">tap to enter password</span>
        )}
        {Array.from({ length: charCount }).map((_, i) => (
          <span key={i} className="text-primary text-base leading-none" style={{ textShadow: "0 0 8px rgba(0,168,255,0.7)" }}>•</span>
        ))}
        {/* In-progress morse symbols */}
        {currentSymbols && (
          <span className="text-accent font-mono text-sm tracking-widest ml-1">
            {currentSymbols.split("").map((s, i) => (
              <span key={i} style={{ animation: "symbolPop 0.15s ease both" }}>{s}</span>
            ))}
          </span>
        )}
        {pressing && (
          <span
            className="inline-block ml-1"
            style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#00a8ff", boxShadow: "0 0 8px #00a8ff", animation: "blink 0.4s step-end infinite" }}
          />
        )}
      </div>

      {/* Tap button */}
      <button
        type="button"
        onMouseDown={handlePressStart}
        onMouseUp={handlePressEnd}
        onMouseLeave={(e) => { if (pressing) handlePressEnd(e); }}
        onTouchStart={handlePressStart}
        onTouchEnd={handlePressEnd}
        onKeyDown={(e) => {
          if (e.code === "Space" && !e.repeat) {
            e.preventDefault();
            handlePressStart(e as any);
          }
        }}
        onKeyUp={(e) => {
          if (e.code === "Space") {
            e.preventDefault();
            handlePressEnd(e as any);
          }
        }}
        className="w-full py-5 font-mono font-bold text-sm tracking-[0.3em] uppercase border select-none transition-colors duration-75"
        style={{
          fontFamily: "'JetBrains Mono', monospace",
          background: pressing ? "rgba(0,168,255,0.15)" : "transparent",
          borderColor: pressing ? "#00a8ff" : "rgba(0,168,255,0.3)",
          color: pressing ? "#00a8ff" : "rgba(0,168,255,0.6)",
          animation: pressing ? "holdGlow 0.8s ease-in-out infinite" : "none",
          userSelect: "none",
          WebkitUserSelect: "none",
        }}
      >
        {pressing
          ? "— HOLD FOR DASH —"
          : lastAction === "dot"
          ? "· DOT ADDED"
          : lastAction === "dash"
          ? "— DASH ADDED"
          : "TAP · HOLD FOR DASH"}
      </button>

      {/* Hint + controls */}
      <div className="flex items-center justify-between">
        <span className="font-mono text-[10px] text-muted-foreground tracking-widest opacity-60">
          {currentSymbols
            ? `current: ${currentSymbols} → ${REVERSE_MORSE[currentSymbols] ?? "?"}`
            : `SPACEBAR also works · ${charCount} chars`}
        </span>
        <div className="flex gap-3">
          <button
            type="button"
            onClick={handleBackspace}
            disabled={charCount === 0}
            className="font-mono text-[10px] text-muted-foreground hover:text-primary transition-colors tracking-widest disabled:opacity-30"
          >
            ⌫ DEL
          </button>
          <button
            type="button"
            onClick={handleClear}
            disabled={charCount === 0}
            className="font-mono text-[10px] text-destructive hover:brightness-125 transition-colors tracking-widest disabled:opacity-30"
          >
            CLR
          </button>
        </div>
      </div>

      {/* Morse reference strip */}
      <div className="grid grid-cols-4 gap-x-4 gap-y-0.5 pt-1 border-t border-border mt-1">
        {["A .-", "B -...", "E .", "I ..", "N -.", "O ---", "S ...", "T -"].map((entry) => {
          const [ch, code] = entry.split(" ");
          return (
            <div key={ch} className="flex gap-1 items-baseline">
              <span className="font-mono text-[9px] text-primary opacity-70">{ch}</span>
              <span className="font-mono text-[9px] text-muted-foreground opacity-40 tracking-wider">{code}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─── REGULAR FIELD ─────────────────────────────────────────────────────────────

function Field({
  label, type, placeholder, morseLabel, value, onChange,
}: {
  label: string; type: string; placeholder: string; morseLabel: string;
  value: string; onChange: (v: string) => void;
}) {
  const [focused, setFocused] = useState(false);
  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center justify-between">
        <label className="font-mono text-xs tracking-widest uppercase text-foreground"
          style={{ fontFamily: "'JetBrains Mono', monospace" }}>
          {label}
        </label>
        <span className="font-mono text-[10px] text-muted-foreground opacity-50 tracking-wider">
          {morseLabel}
        </span>
      </div>
      <input
        type={type}
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        className="w-full px-4 py-3 font-mono text-sm bg-card text-foreground border border-border placeholder:text-muted-foreground/35 outline-none transition-all duration-200"
        style={{
          fontFamily: "'JetBrains Mono', monospace",
          boxShadow: focused ? "0 0 0 1px #00a8ff, 0 0 16px rgba(0,168,255,0.2)" : "none",
          borderColor: focused ? "#00a8ff" : undefined,
        }}
      />
    </div>
  );
}

// ─── MORSE SYMBOL INPUT (type . and - directly) ───────────────────────────────

function MorseSymbolInput({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
}) {
  const [morseText, setMorseText] = useState("");
  const [focused, setFocused] = useState(false);

  function decode(morse: string): string {
    return morse
      .trim()
      .split(/\s+/)
      .map((s) => REVERSE_MORSE[s] ?? (s ? "?" : ""))
      .join("");
  }

  function handleChange(raw: string) {
    const filtered = raw.replace(/[^.\- /]/g, "");
    setMorseText(filtered);
    const decoded = filtered.trim() ? decode(filtered) : "";
    onChange(decoded);
  }

  const hasInvalid = value.includes("?");

  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center justify-between">
        <label
          className="font-mono text-xs tracking-widest uppercase text-foreground"
          style={{ fontFamily: "'JetBrains Mono', monospace" }}
        >
          {label}
        </label>
        <span className="font-mono text-[10px] text-muted-foreground opacity-50 tracking-wider">
          type · and —
        </span>
      </div>

      {/* Symbol input */}
      <input
        type="text"
        value={morseText}
        onChange={(e) => handleChange(e.target.value)}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        placeholder=". -  . . . .  -"
        className="w-full px-4 py-3 font-mono text-sm bg-card text-foreground border border-border placeholder:text-muted-foreground/30 outline-none transition-all duration-200 tracking-widest"
        style={{
          fontFamily: "'JetBrains Mono', monospace",
          letterSpacing: "0.25em",
          boxShadow: focused
            ? "0 0 0 1px #00a8ff, 0 0 16px rgba(0,168,255,0.2)"
            : "none",
          borderColor: focused ? "#00a8ff" : undefined,
        }}
      />

      {/* Decoded display */}
      {morseText.trim() && (
        <div className="flex items-center gap-2 px-3 py-2 bg-secondary border border-border">
          <span className="font-mono text-[10px] text-muted-foreground tracking-widest">DECODED →</span>
          <span className="flex gap-1">
            {value.split("").map((ch, i) =>
              ch === "?" ? (
                <span key={i} className="font-mono text-xs text-destructive">?</span>
              ) : (
                <span
                  key={i}
                  className="text-primary text-base leading-none"
                  style={{ textShadow: "0 0 8px rgba(0,168,255,0.7)" }}
                >
                  •
                </span>
              )
            )}
          </span>
          {hasInvalid && (
            <span className="font-mono text-[10px] text-destructive ml-auto">INVALID SYMBOL</span>
          )}
        </div>
      )}

      {/* Mini reference */}
      <div className="grid grid-cols-6 gap-x-2 gap-y-0.5 pt-1">
        {["A .-", "B -...", "E .", "I ..", "N -.", "O ---", "S ...", "T -", "U ..-", "M --", "R .-.", "H ...."].map((entry) => {
          const parts = entry.split(" ");
          return (
            <div key={parts[0]} className="flex gap-0.5 items-baseline">
              <span className="font-mono text-[9px] text-primary opacity-60">{parts[0]}</span>
              <span className="font-mono text-[9px] text-muted-foreground opacity-35 tracking-wide">{parts[1]}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─── STATUS BAR ────────────────────────────────────────────────────────────────

function StatusBar({ status, details, successMessage = "✓ ACCESS GRANTED", errorMessage = "✗ INVALID CREDENTIALS", loadingMessage = "▶ AUTHENTICATING SIGNAL..." }: { status: "loading" | "success" | "error" | null, details?: any, successMessage?: string, errorMessage?: string, loadingMessage?: string }) {
  if (!status) return null;
  return (
    <div className="flex flex-col gap-2 w-full animate-fade-in" style={{ animation: "fadeSlideUp 0.3s ease both" }}>
      <div
        className={`font-mono text-xs tracking-widest px-3 py-2 border flex items-center justify-between ${
          status === "loading" ? "border-muted-foreground text-muted-foreground"
          : status === "success" ? "border-primary text-primary"
          : "border-destructive text-destructive"
        }`}
        style={{
          boxShadow: status === "success" ? "0 0 10px rgba(0,168,255,0.3)"
            : status === "error" ? "0 0 10px rgba(255,51,51,0.3)" : "none",
        }}
      >
        <span>
          {status === "loading" && loadingMessage}
          {status === "success" && successMessage}
          {status === "error" && errorMessage}
        </span>
        {details && (
          <span className="font-bold opacity-80">
            VOTES: {details.votes}
          </span>
        )}
      </div>
      
      {details && status !== "loading" && (
        <div className="flex flex-col gap-1 p-2 border border-border bg-black/40 text-[10px] font-mono text-muted-foreground">
          <div className="flex justify-between border-b border-border/50 pb-1 mb-1 text-primary">
            <span>MODEL</span>
            <span>STATUS</span>
            <span>CONFIDENCE</span>
          </div>
          {["euclidean", "manhattan", "dtw", "svm"].map((m) => (
            details[m] && (
              <div key={m} className="flex justify-between">
                <span className="uppercase w-24">{m}</span>
                <span className={details[m].accepted ? "text-primary" : "text-destructive"}>
                  {details[m].accepted ? "PASS" : "FAIL"}
                </span>
                <span className="w-16 text-right">
                  {(details[m].confidence * 100).toFixed(0)}%
                </span>
              </div>
            )
          ))}
        </div>
      )}
    </div>
  );
}

function TerminalCard({ children, subtitle }: { children: React.ReactNode; subtitle: string }) {
  return (
    <div
      className="border border-border bg-card p-8 flex flex-col gap-6"
      style={{ boxShadow: "0 0 0 1px rgba(0,168,255,0.05), 0 8px 40px rgba(0,0,0,0.6)" }}
    >
      <div className="flex items-center gap-2 -mt-2 pb-4 border-b border-border">
        <span className="w-2.5 h-2.5 rounded-full bg-destructive opacity-70" />
        <span className="w-2.5 h-2.5 rounded-full bg-accent opacity-70" />
        <span className="w-2.5 h-2.5 rounded-full bg-primary opacity-70" />
        <span className="ml-3 font-mono text-xs text-muted-foreground tracking-widest">
          {subtitle}
        </span>
      </div>
      {children}
    </div>
  );
}

// ─── WELCOME PAGE ──────────────────────────────────────────────────────────────

function WelcomePage({ navigate }: { navigate: (p: Page) => void }) {
  const phrases = ["LEARN.", "CONNECT.", "TRANSMIT.", "SECURE."];
  const [phraseIdx, setPhraseIdx] = useState(0);

  useEffect(() => {
    const t = setInterval(() => setPhraseIdx((i) => (i + 1) % phrases.length), 2200);
    return () => clearInterval(t);
  }, []);

  return (
    <div
      className="min-h-screen flex flex-col items-center justify-center relative px-6 pb-16"
      style={{ animation: "fadeSlideUp 0.7s ease both" }}
    >
      <div className="absolute inset-0 pointer-events-none" style={{
        backgroundImage: "linear-gradient(rgba(0,168,255,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(0,168,255,0.04) 1px, transparent 1px)",
        backgroundSize: "60px 60px",
      }} />

      <div className="relative z-10 flex flex-col items-center gap-10 max-w-2xl w-full text-center">

        <div className="flex items-center gap-2 px-4 py-1.5 border border-border bg-card text-muted-foreground font-mono text-xs tracking-widest uppercase">
          <span className="w-1.5 h-1.5 rounded-full bg-primary" style={{ boxShadow: "0 0 6px #00a8ff", animation: "blink 1.2s step-end infinite" }} />
          System Online · v2.4.1
        </div>

        <div className="flex flex-col gap-4">
          <h1
            className="font-mono font-bold text-5xl sm:text-7xl text-foreground leading-none tracking-tight"
            style={{ fontFamily: "'JetBrains Mono', monospace", textShadow: "0 0 30px rgba(0,168,255,0.2)" }}
          >
            MORSE
            <br />
            <span className="text-primary" style={{ textShadow: "0 0 34px rgba(0,168,255,0.75)" }}>
              AUTH
            </span>
            <BlinkCursor />
          </h1>
          <MorseTag text="MORSE AUTH" />
        </div>

        <div className="h-8 flex items-center">
          <span
            key={phraseIdx}
            className="font-mono text-accent text-lg tracking-[0.3em] uppercase"
            style={{ animation: "fadeSlideUp 0.5s ease both", textShadow: "0 0 10px rgba(255,179,0,0.6)" }}
          >
            {phrases[phraseIdx]}
          </span>
        </div>

        <p className="font-mono text-muted-foreground text-sm leading-relaxed max-w-md tracking-wide">
          A next-generation authentication protocol inspired by the oldest
          reliable signal system known to humanity. Tap in. Stay secure.
        </p>

        <div className="flex items-center gap-3 w-full">
          <div className="flex-1 h-px bg-border" />
          <span className="font-mono text-xs text-muted-foreground tracking-widest">·  ·  ·  — — —  ·  ·  ·</span>
          <div className="flex-1 h-px bg-border" />
        </div>

        {/* Buttons — no brackets */}
        <div className="flex flex-col sm:flex-row gap-4 w-full max-w-sm">
          <button
            onClick={() => navigate("login")}
            className="flex-1 py-4 px-8 font-mono font-bold text-sm tracking-[0.25em] uppercase text-primary-foreground bg-primary border border-primary transition-all duration-200 hover:brightness-110"
            style={{
              animation: "glowPulse 2.5s ease-in-out infinite",
              fontFamily: "'JetBrains Mono', monospace",
            }}
          >
            LOGIN
          </button>
          <button
            onClick={() => navigate("register")}
            className="flex-1 py-4 px-8 font-mono font-bold text-sm tracking-[0.25em] uppercase text-primary border border-primary bg-transparent transition-all duration-200 hover:bg-primary hover:text-primary-foreground"
            style={{ fontFamily: "'JetBrains Mono', monospace" }}
          >
            REGISTER
          </button>
        </div>

        <div className="flex gap-6 text-muted-foreground font-mono text-xs tracking-widest opacity-50">
          <span>·−</span><span>−···</span><span>−·−·</span><span>··</span><span>·−·</span>
        </div>
      </div>
    </div>
  );
}

// ─── LOGIN PAGE ────────────────────────────────────────────────────────────────

function LoginPage({ navigate, onSuccess }: { navigate: (p: Page) => void, onSuccess: (user: string) => void }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [rhythm, setRhythm] = useState<RhythmData | null>(null);
  const [status, setStatus] = useState<null | "loading" | "success" | "error">(null);
  const [authDetails, setAuthDetails] = useState<any>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!username || !password || !rhythm) return;
    setStatus("loading");
    setAuthDetails(null);
    
    try {
      const res = await fetch("http://localhost:5000/api/authenticate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: username.toLowerCase(),
          attempt: rhythm
        })
      });
      const data = await res.json();
      
      if (data.results) {
        setAuthDetails(data.results);
      }
      
      if (data.status === "success" && data.final_decision) {
        setStatus("success");
        setTimeout(() => { 
          setStatus(null); 
          setAuthDetails(null); 
          onSuccess(username);
        }, 3000);
      } else {
        setStatus("error");
        setTimeout(() => { 
          setStatus(null); 
          setAuthDetails(null); 
          navigate("recovery");
        }, 4000);
      }
    } catch (err) {
      console.error(err);
      setStatus("error");
      setTimeout(() => setStatus(null), 3000);
    }
  }

  return (
    <div
      className="min-h-screen flex flex-col items-center justify-center px-6 py-12 pb-20 relative"
      style={{ animation: "terminalIn 0.5s ease both" }}
    >
      <div className="absolute inset-0 pointer-events-none" style={{
        backgroundImage: "linear-gradient(rgba(0,168,255,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(0,168,255,0.04) 1px, transparent 1px)",
        backgroundSize: "60px 60px",
      }} />
      <div className="w-full max-w-md flex flex-col gap-8 relative z-10">

        <div className="flex flex-col gap-4">
          <Logo onClick={() => navigate("welcome")} />
          <div className="h-px bg-border" />
          <div className="flex flex-col gap-1">
            <div className="flex items-center gap-2">
              <span className="font-mono text-2xl font-bold text-foreground tracking-tight"
                style={{ fontFamily: "'JetBrains Mono', monospace" }}>
                Signal In
              </span>
              <BlinkCursor />
            </div>
            <MorseTag text="LOGIN" />
          </div>
        </div>

        <TerminalCard subtitle="morseauth · login · v2.4.1">
          <form onSubmit={handleSubmit} className="flex flex-col gap-5">
            <Field
              label="Username"
              type="text"
              placeholder="operator_callsign"
              morseLabel={toMorse("USER")}
              value={username}
              onChange={setUsername}
            />
            <MorseTapInput
              label="Password"
              value={password}
              onChange={setPassword}
              onRhythmChange={setRhythm}
            />
            <StatusBar status={status} details={authDetails} />
            <button
              type="submit"
              disabled={status === "loading" || !password || !username}
              className="w-full py-4 font-mono font-bold text-sm tracking-[0.25em] uppercase text-primary-foreground bg-primary border border-primary transition-all duration-200 hover:brightness-110 disabled:opacity-60 disabled:cursor-not-allowed mt-1"
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                boxShadow: "0 0 20px rgba(0,168,255,0.3)",
              }}
            >
              {status === "loading" ? "· · ·" : "TRANSMIT"}
            </button>
          </form>
        </TerminalCard>

        <div className="flex items-center justify-between font-mono text-xs text-muted-foreground">
          <button onClick={() => navigate("welcome")} className="hover:text-primary transition-colors tracking-widest uppercase">
            ← BASE
          </button>
          <div className="flex items-center gap-2">
            <span>No account?</span>
            <button onClick={() => navigate("register")} className="text-primary hover:brightness-125 transition-all tracking-widest uppercase underline underline-offset-4">
              Register
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── REGISTER PAGE ─────────────────────────────────────────────────────────────


function RegisterPage({ navigate }: { navigate: (p: Page) => void }) {
  const [name, setName] = useState("");
  const [username, setUsername] = useState("");
  const [morseKey, setMorseKey] = useState("");   
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [thirdPassword, setThirdPassword] = useState("");
  
  const [rhythm1, setRhythm1] = useState<RhythmData | null>(null);
  const [rhythm2, setRhythm2] = useState<RhythmData | null>(null);
  const [rhythm3, setRhythm3] = useState<RhythmData | null>(null);
  
  const [step, setStep] = useState<1 | 2>(1);
  const [questions, setQuestions] = useState(Array(6).fill({ prompt: "", answer: "" }));
  
  const [status, setStatus] = useState<null | "loading" | "success" | "error">(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    
    if (step === 1) {
      const r1Valid = rhythm1 && rhythm1.presses.length > 0;
      const r2Valid = rhythm2 && rhythm2.presses.length > 0;
      const r3Valid = rhythm3 && rhythm3.presses.length > 0;
      if (!username || !r1Valid || !r2Valid || !r3Valid || !morseKey) {
        setStatus("error");
        setTimeout(() => setStatus(null), 2500);
        return;
      }
      setStep(2);
      return;
    }
    
    // Step 2 submit
    const allFilled = questions.every(q => q.prompt.trim() !== "" && q.answer.trim() !== "");
    if (!allFilled) {
      setStatus("error");
      setTimeout(() => setStatus(null), 2500);
      return;
    }
    setStatus("loading");
    
    try {
      const enrollRes = await fetch("http://localhost:5000/api/enroll", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: username.toLowerCase(),
          decoded_word: morseKey,
          samples: [rhythm1, rhythm2, rhythm3]
        })
      });
      const enrollData = await enrollRes.json();
      
      if (enrollData.status !== "success") throw new Error(enrollData.error || "Enroll failed");
      
      const recovRes = await fetch("http://localhost:5000/api/recovery/setup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: username.toLowerCase(),
          questions: questions
        })
      });
      const recovData = await recovRes.json();
      
      if (recovData.status === "success") {
        setStatus("success");
        setTimeout(() => navigate("welcome"), 3000);
      } else {
        setStatus("error");
        setTimeout(() => setStatus(null), 2500);
      }
    } catch (err) {
      console.error(err);
      setStatus("error");
      setTimeout(() => setStatus(null), 2500);
    }
  }

  const updateQuestion = (index: number, field: "prompt" | "answer", value: string) => {
    const newQ = [...questions];
    newQ[index] = { ...newQ[index], [field]: value };
    setQuestions(newQ);
  };

  return (
    <div
      className="min-h-screen flex flex-col items-center justify-center px-6 py-12 pb-20 relative"
      style={{ animation: "terminalIn 0.5s ease both" }}
    >
      <div className="absolute inset-0 pointer-events-none" style={{
        backgroundImage: "linear-gradient(rgba(0,168,255,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(0,168,255,0.04) 1px, transparent 1px)",
        backgroundSize: "60px 60px",
      }} />

      <div className="w-full max-w-md flex flex-col gap-8 relative z-10">

        <div className="flex flex-col gap-4">
          <Logo onClick={() => navigate("welcome")} />
          <div className="h-px bg-border" />
          <div className="flex flex-col gap-1">
            <div className="flex items-center gap-2">
              <span className="font-mono text-2xl font-bold text-foreground tracking-tight"
                style={{ fontFamily: "'JetBrains Mono', monospace" }}>
                New Operator
              </span>
              <BlinkCursor />
            </div>
            <MorseTag text="REGISTER" />
          </div>
        </div>

        <TerminalCard subtitle="morseauth · register · v2.4.1">
          <form onSubmit={handleSubmit} className="flex flex-col gap-5">
            <Field
              label="Username"
              type="text"
              placeholder="operator_callsign"
              morseLabel={toMorse("USER")}
              value={username}
              onChange={setUsername}
            />

            {step === 1 && (
              <>
                <div className="border-t border-border pt-4">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="font-mono text-[10px] text-primary tracking-widest uppercase">Step 1 · Morse Code Key</span>
                    <div className="flex-1 h-px bg-border" />
                  </div>
                  <MorseSymbolInput
                    label="Morse Symbol Password"
                    value={morseKey}
                    onChange={setMorseKey}
                  />
                </div>

                <div className="border-t border-border pt-4 flex flex-col gap-5">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-[10px] text-primary tracking-widest uppercase">Step 2 · Tap Password</span>
                    <div className="flex-1 h-px bg-border" />
                  </div>
                  <MorseTapInput
                    label="Sample 1"
                    value={password}
                    onChange={setPassword}
                    onRhythmChange={setRhythm1}
                  />
                  <MorseTapInput
                    label="Sample 2"
                    value={confirmPassword}
                    onChange={setConfirmPassword}
                    onRhythmChange={setRhythm2}
                  />
                  <MorseTapInput
                    label="Sample 3"
                    value={thirdPassword}
                    onChange={setThirdPassword}
                    onRhythmChange={setRhythm3}
                  />
                  {/* Show how many rhythm samples have been collected */}
                  {(rhythm1 || rhythm2 || rhythm3) && (() => {
                    const collected = [rhythm1, rhythm2, rhythm3].filter(r => r && r.presses.length > 0).length;
                    return (
                      <div
                        className="font-mono text-[10px] tracking-widest -mt-3"
                        style={{ color: collected === 3 ? "#00a8ff" : "#ffb300" }}
                      >
                        {collected === 3 ? "✓ ALL 3 SAMPLES RECORDED" : `${collected}/3 SAMPLES RECORDED`}
                      </div>
                    );
                  })()}
                </div>
              </>
            )}
            
            {step === 2 && (
              <div className="border-t border-border pt-4 flex flex-col gap-5">
                <div className="flex items-center gap-2 mb-2">
                  <span className="font-mono text-[10px] text-primary tracking-widest uppercase">Step 3 · Recovery Questions</span>
                  <div className="flex-1 h-px bg-border" />
                </div>
                <p className="font-mono text-xs text-muted-foreground leading-tight -mt-2">
                  Set 6 custom questions. If your biometric rhythm drifts, you'll need to answer 3 of these randomly.
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {questions.map((q, i) => (
                    <div key={i} className="flex flex-col gap-2 p-3 border border-border/50 bg-black/20">
                      <span className="font-mono text-[10px] text-muted-foreground uppercase tracking-wider">Question {i + 1}</span>
                      <input 
                        type="text" placeholder="Prompt (e.g. Favorite color)" value={q.prompt}
                        onChange={(e) => updateQuestion(i, "prompt", e.target.value)}
                        className="w-full px-3 py-2 font-mono text-xs bg-card border border-border placeholder:text-muted-foreground/35 outline-none focus:border-primary"
                      />
                      <input 
                        type="text" placeholder="Answer" value={q.answer}
                        onChange={(e) => updateQuestion(i, "answer", e.target.value)}
                        className="w-full px-3 py-2 font-mono text-xs bg-card border border-border placeholder:text-muted-foreground/35 outline-none focus:border-primary"
                      />
                    </div>
                  ))}
                </div>
              </div>
            )}

            <StatusBar 
              status={status} 
              successMessage="✓ OPERATOR ENROLLED: SECURE CHANNEL ESTABLISHED"
              loadingMessage="▶ ENROLLING NEW OPERATOR..."
            />

            <button
              type="submit"
              disabled={status === "loading"}
              className="w-full py-4 font-mono font-bold text-sm tracking-[0.25em] uppercase text-primary-foreground bg-primary border border-primary transition-all duration-200 hover:brightness-110 disabled:opacity-60 disabled:cursor-not-allowed"
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                boxShadow: "0 0 20px rgba(0,168,255,0.3)",
              }}
            >
              {status === "loading" ? "· · ·" : step === 1 ? "NEXT" : "ENROLL"}
            </button>
          </form>
        </TerminalCard>

        <div className="flex items-center justify-between font-mono text-xs text-muted-foreground">
          <button onClick={() => navigate("welcome")} className="hover:text-primary transition-colors tracking-widest uppercase">
            ← BASE
          </button>
          <div className="flex items-center gap-2">
            <span>Have account?</span>
            <button onClick={() => navigate("login")} className="text-primary hover:brightness-125 transition-all tracking-widest uppercase underline underline-offset-4">
              Login
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── RECOVERY PAGE ─────────────────────────────────────────────────────────────

function RecoveryPage({ navigate }: { navigate: (p: Page) => void }) {
  const [username, setUsername] = useState("");
  const [step, setStep] = useState<"username" | "questions" | "decision" | "re_enroll">("username");
  
  // questions step
  const [sessionId, setSessionId] = useState("");
  const [questions, setQuestions] = useState<{question_id: string, prompt: string}[]>([]);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  
  // re_enroll step
  const [morseKey, setMorseKey] = useState("");   
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [thirdPassword, setThirdPassword] = useState("");
  
  const [rhythm1, setRhythm1] = useState<RhythmData | null>(null);
  const [rhythm2, setRhythm2] = useState<RhythmData | null>(null);
  const [rhythm3, setRhythm3] = useState<RhythmData | null>(null);

  const [status, setStatus] = useState<null | "loading" | "success" | "error">(null);
  const [message, setMessage] = useState<string>("");

  async function handleStart(e: React.FormEvent) {
    e.preventDefault();
    if (!username) return;
    setStatus("loading");
    
    try {
      const res = await fetch("http://localhost:5000/api/recovery/start", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: username.toLowerCase() })
      });
      const data = await res.json();
      if (data.status === "success") {
        setSessionId(data.session_id);
        setQuestions(data.questions);
        setStep("questions");
        setStatus(null);
      } else {
        setStatus("error");
        setMessage(data.error || "User not found");
        setTimeout(() => setStatus(null), 3000);
      }
    } catch (err) {
      setStatus("error");
      setTimeout(() => setStatus(null), 3000);
    }
  }

  async function handleVerify(e: React.FormEvent) {
    e.preventDefault();
    setStatus("loading");
    try {
      const res = await fetch("http://localhost:5000/api/recovery/verify", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, answers })
      });
      const data = await res.json();
      if (data.identity_verified) {
        setStatus("success");
        setStep("decision");
        setTimeout(() => setStatus(null), 2000);
      } else {
        setStatus("error");
        setMessage(`Failed: ${data.message} (Attempts: ${data.attempt_count})`);
        if (data.session_status === "FAILED") {
           setTimeout(() => navigate("welcome"), 3000);
        } else {
           setTimeout(() => setStatus(null), 3000);
        }
      }
    } catch (err) {
      setStatus("error");
      setTimeout(() => setStatus(null), 3000);
    }
  }

  async function handleReEnroll(e: React.FormEvent) {
    e.preventDefault();
    const r1Valid = rhythm1 && rhythm1.presses.length > 0;
    const r2Valid = rhythm2 && rhythm2.presses.length > 0;
    const r3Valid = rhythm3 && rhythm3.presses.length > 0;
    
    if (!username || !r1Valid || !r2Valid || !r3Valid || !morseKey) {
      setStatus("error");
      setTimeout(() => setStatus(null), 2500);
      return;
    }
    setStatus("loading");
    
    try {
      const res = await fetch("http://localhost:5000/api/enroll", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: username.toLowerCase(),
          decoded_word: morseKey,
          samples: [rhythm1, rhythm2, rhythm3]
        })
      });
      const data = await res.json();
      if (data.status === "success") {
        setStatus("success");
        setTimeout(() => navigate("login"), 2500);
      } else {
        setStatus("error");
        setTimeout(() => setStatus(null), 2500);
      }
    } catch (err) {
      setStatus("error");
      setTimeout(() => setStatus(null), 2500);
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-6 py-12 pb-20 relative" style={{ animation: "terminalIn 0.5s ease both" }}>
      <div className="absolute inset-0 pointer-events-none" style={{ backgroundImage: "linear-gradient(rgba(0,168,255,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(0,168,255,0.04) 1px, transparent 1px)", backgroundSize: "60px 60px" }} />
      <div className="w-full max-w-md flex flex-col gap-8 relative z-10">
        <div className="flex flex-col gap-4">
          <Logo onClick={() => navigate("welcome")} />
          <div className="h-px bg-border" />
          <div className="flex flex-col gap-1">
            <div className="flex items-center gap-2">
              <span className="font-mono text-2xl font-bold text-foreground tracking-tight" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
                System Recovery
              </span>
              <BlinkCursor />
            </div>
            <MorseTag text="RECOVER" />
          </div>
        </div>

        <TerminalCard subtitle={`morseauth · recovery · step ${step === 'username' ? 1 : step === 'questions' ? 2 : step === 'decision' ? 3 : 4}`}>
          {step === "username" && (
            <form onSubmit={handleStart} className="flex flex-col gap-5">
              <p className="font-mono text-xs text-muted-foreground">Enter your callsign to begin the recovery process.</p>
              <Field
                label="Username" type="text" placeholder="operator_callsign" morseLabel={toMorse("USER")}
                value={username} onChange={setUsername}
              />
              {status === "error" && <div className="text-destructive font-mono text-xs">{message}</div>}
              <button type="submit" disabled={status === "loading" || !username} className="w-full py-4 font-mono font-bold text-sm tracking-[0.25em] uppercase text-primary-foreground bg-primary border border-primary transition-all duration-200 hover:brightness-110 disabled:opacity-60 disabled:cursor-not-allowed">
                {status === "loading" ? "· · ·" : "START RECOVERY"}
              </button>
            </form>
          )}

          {step === "questions" && (
            <form onSubmit={handleVerify} className="flex flex-col gap-5">
              <p className="font-mono text-xs text-muted-foreground">Answer the following security questions.</p>
              {questions.map((q, i) => (
                <div key={q.question_id} className="flex flex-col gap-2">
                  <span className="font-mono text-xs text-primary">{q.prompt}</span>
                  <input
                    type="text" placeholder="Answer" value={answers[q.question_id] || ""}
                    onChange={(e) => setAnswers({ ...answers, [q.question_id]: e.target.value })}
                    className="w-full px-4 py-3 font-mono text-sm bg-card border border-border outline-none focus:border-primary"
                  />
                </div>
              ))}
              {status === "error" && <div className="text-destructive font-mono text-xs">{message}</div>}
              <button type="submit" disabled={status === "loading"} className="w-full py-4 font-mono font-bold text-sm tracking-[0.25em] uppercase text-primary-foreground bg-primary border border-primary transition-all duration-200 hover:brightness-110 disabled:opacity-60 disabled:cursor-not-allowed">
                {status === "loading" ? "· · ·" : "VERIFY IDENTITY"}
              </button>
            </form>
          )}

          {step === "decision" && (
            <div className="flex flex-col gap-5">
              <div className="p-4 bg-primary/10 border border-primary text-primary font-mono text-xs">
                ✓ IDENTITY VERIFIED SUCCESSFULLY
              </div>
              <p className="font-mono text-xs text-muted-foreground">
                Your identity has been verified. What would you like to do?
              </p>
              <button onClick={() => setStep("re_enroll")} className="w-full py-4 font-mono font-bold text-xs tracking-[0.1em] uppercase text-primary-foreground bg-primary border border-primary transition-all duration-200 hover:brightness-110">
                Set a New Password (Re-Enroll)
              </button>
              <button onClick={() => setStep("re_enroll")} className="w-full py-4 font-mono font-bold text-xs tracking-[0.1em] uppercase text-primary border border-primary hover:bg-primary hover:text-primary-foreground transition-all duration-200">
                Keep Password but Re-Record Rhythm
              </button>
            </div>
          )}

          {step === "re_enroll" && (
            <form onSubmit={handleReEnroll} className="flex flex-col gap-5">
              <div className="border-t border-border pt-4">
                <div className="flex items-center gap-2 mb-3">
                  <span className="font-mono text-[10px] text-primary tracking-widest uppercase">Step 1 · Morse Code Key</span>
                  <div className="flex-1 h-px bg-border" />
                </div>
                <MorseSymbolInput label="Morse Symbol Password" value={morseKey} onChange={setMorseKey} />
              </div>
              <div className="border-t border-border pt-4 flex flex-col gap-5">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-[10px] text-primary tracking-widest uppercase">Step 2 · Tap Password</span>
                  <div className="flex-1 h-px bg-border" />
                </div>
                <MorseTapInput label="Sample 1" value={password} onChange={setPassword} onRhythmChange={setRhythm1} />
                <MorseTapInput label="Sample 2" value={confirmPassword} onChange={setConfirmPassword} onRhythmChange={setRhythm2} />
                <MorseTapInput label="Sample 3" value={thirdPassword} onChange={setThirdPassword} onRhythmChange={setRhythm3} />
              </div>
              <StatusBar status={status} />
              <button type="submit" disabled={status === "loading"} className="w-full py-4 font-mono font-bold text-sm tracking-[0.25em] uppercase text-primary-foreground bg-primary border border-primary transition-all duration-200 hover:brightness-110 disabled:opacity-60 disabled:cursor-not-allowed">
                {status === "loading" ? "· · ·" : "SAVE NEW RHYTHM"}
              </button>
            </form>
          )}
        </TerminalCard>

        <div className="flex items-center justify-between font-mono text-xs text-muted-foreground">
          <button onClick={() => navigate("login")} className="hover:text-primary transition-colors tracking-widest uppercase">
            ← BACK TO LOGIN
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── DASHBOARD PAGE ────────────────────────────────────────────────────────────

function DashboardPage({ navigate, username }: { navigate: (p: Page) => void, username: string }) {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-6 relative" style={{ animation: "terminalIn 0.5s ease both" }}>
      <div className="absolute inset-0 pointer-events-none" style={{ backgroundImage: "linear-gradient(rgba(0,168,255,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(0,168,255,0.04) 1px, transparent 1px)", backgroundSize: "60px 60px" }} />
      <div className="flex flex-col gap-6 w-full max-w-2xl text-center items-center relative z-10">
        <Logo onClick={() => navigate("welcome")} />
        <div className="h-px bg-border w-full max-w-md my-4" />
        <h1 className="font-mono text-3xl sm:text-4xl text-primary font-bold tracking-tight" style={{ textShadow: "0 0 20px rgba(0,168,255,0.4)" }}>
          SECURE CHANNEL OPEN
        </h1>
        <p className="font-mono text-sm text-muted-foreground mt-2 tracking-widest uppercase">
          Welcome, Operator <span className="text-foreground">[{username}]</span>. Your signal has been verified.
        </p>
        
        <div className="mt-8 p-6 bg-black/40 border border-primary/30 text-left w-full max-w-md font-mono text-xs text-muted-foreground tracking-wide flex flex-col gap-3">
          <div className="flex justify-between border-b border-primary/20 pb-2 mb-2">
            <span className="text-primary">SYSTEM STATUS</span>
            <span className="text-primary">ONLINE</span>
          </div>
          <div>&gt; INITIALIZING MODULES... OK</div>
          <div>&gt; SYNCING SECURE PROTOCOLS... OK</div>
          <div>&gt; AWAITING COMMAND...</div>
          <BlinkCursor />
        </div>

        <button 
          onClick={() => navigate("welcome")} 
          className="mt-8 py-3 px-8 font-mono text-xs uppercase text-muted-foreground border border-border hover:text-destructive hover:border-destructive hover:bg-destructive/10 transition-all tracking-widest"
        >
          CLOSE CONNECTION
        </button>
      </div>
    </div>
  );
}

// ─── ROOT ──────────────────────────────────────────────────────────────────────

export default function App() {
  const [page, setPage] = useState<Page>("welcome");
  const [currentUser, setCurrentUser] = useState("");

  const handleLoginSuccess = (user: string) => {
    setCurrentUser(user);
    setPage("dashboard");
  };

  return (
    <div
      className="min-h-screen bg-background text-foreground relative overflow-x-hidden"
      style={{ fontFamily: "'JetBrains Mono', monospace" }}
    >
      <MorseBackground />
      <ScanlineOverlay />

      {/* Side morse strip */}
      <div className="fixed left-4 top-1/2 -translate-y-1/2 hidden lg:flex flex-col gap-3 items-center z-20">
        <div className="w-px h-20 bg-border" />
        <span
          className="font-mono text-[10px] text-muted-foreground tracking-widest opacity-35 rotate-180"
          style={{ writingMode: "vertical-lr" }}
        >
          ·· −· ·−· ··− −·· −···
        </span>
        <div className="w-px h-20 bg-border" />
      </div>

      {page === "welcome" && <WelcomePage navigate={setPage} />}
      {page === "login" && <LoginPage navigate={setPage} onSuccess={handleLoginSuccess} />}
      {page === "register" && <RegisterPage navigate={setPage} />}
      {page === "recovery" && <RecoveryPage navigate={setPage} />}
      {page === "dashboard" && <DashboardPage navigate={setPage} username={currentUser} />}

      {/* Bottom status bar */}
      <div className="fixed bottom-0 left-0 right-0 px-6 py-2 border-t border-border bg-background/80 backdrop-blur-sm flex items-center justify-between z-30">
        <span className="font-mono text-[10px] text-muted-foreground tracking-widest opacity-55">
          SIG · {new Date().toISOString().slice(11, 19)} UTC
        </span>
        <div className="flex gap-4 items-center">
          {(["welcome", "login", "register"] as Page[]).map((p) => (
            <button
              key={p}
              onClick={() => setPage(p)}
              className="font-mono text-[10px] tracking-widest uppercase transition-colors hover:text-primary"
              style={{ color: page === p ? "#00a8ff" : undefined }}
            >
              {p === "welcome" ? "·−" : p === "login" ? "·−·" : "·−−"}
            </button>
          ))}
        </div>
        <span className="font-mono text-[10px] text-muted-foreground tracking-widest opacity-55">
          ENC · AES-256
        </span>
      </div>
    </div>
  );
}
