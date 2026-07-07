import { useState, useEffect, useRef, useCallback } from "react";

type Page = "welcome" | "login" | "register";

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
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
}) {
  const [currentSymbols, setCurrentSymbols] = useState(""); // dots/dashes in progress
  const [pressing, setPressing] = useState(false);
  const [lastAction, setLastAction] = useState<"dot" | "dash" | null>(null);
  const pressStart = useRef(0);
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

  const handlePressStart = useCallback((e: React.MouseEvent | React.TouchEvent) => {
    e.preventDefault();
    if (letterTimer.current) clearTimeout(letterTimer.current);
    pressStart.current = Date.now();
    setPressing(true);
  }, []);

  const handlePressEnd = useCallback(
    (e: React.MouseEvent | React.TouchEvent) => {
      e.preventDefault();
      const duration = Date.now() - pressStart.current;
      const symbol = duration < DOT_THRESHOLD ? "." : "-";
      setLastAction(symbol === "." ? "dot" : "dash");
      setPressing(false);
      const next = currentSymbols + symbol;
      setCurrentSymbols(next);
      scheduleCommit(next);
    },
    [currentSymbols, scheduleCommit]
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
  };

  useEffect(() => {
    return () => { if (letterTimer.current) clearTimeout(letterTimer.current); };
  }, []);

  // Keyboard support: space = tap
  useEffect(() => {
    let kStart = 0;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.code === "Space" && !e.repeat) {
        e.preventDefault();
        if (letterTimer.current) clearTimeout(letterTimer.current);
        kStart = Date.now();
        setPressing(true);
      }
    };
    const onKeyUp = (e: KeyboardEvent) => {
      if (e.code === "Space") {
        e.preventDefault();
        const duration = Date.now() - kStart;
        const symbol = duration < DOT_THRESHOLD ? "." : "-";
        setLastAction(symbol === "." ? "dot" : "dash");
        setPressing(false);
        setCurrentSymbols((prev) => {
          const next = prev + symbol;
          scheduleCommit(next);
          return next;
        });
      }
    };
    window.addEventListener("keydown", onKeyDown);
    window.addEventListener("keyup", onKeyUp);
    return () => {
      window.removeEventListener("keydown", onKeyDown);
      window.removeEventListener("keyup", onKeyUp);
    };
  }, [scheduleCommit]);

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

function StatusBar({ status }: { status: "loading" | "success" | "error" | null }) {
  if (!status) return null;
  return (
    <div
      className={`font-mono text-xs tracking-widest px-3 py-2 border ${
        status === "loading" ? "border-muted-foreground text-muted-foreground"
        : status === "success" ? "border-primary text-primary"
        : "border-destructive text-destructive"
      }`}
      style={{
        boxShadow: status === "success" ? "0 0 10px rgba(0,168,255,0.3)"
          : status === "error" ? "0 0 10px rgba(255,51,51,0.3)" : "none",
        animation: "fadeSlideUp 0.3s ease both",
      }}
    >
      {status === "loading" && "▶ AUTHENTICATING SIGNAL..."}
      {status === "success" && "✓ ACCESS GRANTED · WELCOME OPERATOR"}
      {status === "error" && "✗ INVALID CREDENTIALS · SIGNAL REJECTED"}
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

function LoginPage({ navigate }: { navigate: (p: Page) => void }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [status, setStatus] = useState<null | "loading" | "success" | "error">(null);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setStatus("loading");
    setTimeout(() => {
      setStatus(username && password ? "success" : "error");
      setTimeout(() => setStatus(null), 2500);
    }, 1200);
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
            />
            <StatusBar status={status} />
            <button
              type="submit"
              disabled={status === "loading"}
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
  const [email, setEmail] = useState("");
  const [morseKey, setMorseKey] = useState("");   // decoded from symbol input
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [status, setStatus] = useState<null | "loading" | "success" | "error">(null);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (password !== confirmPassword) {
      setStatus("error");
      setTimeout(() => setStatus(null), 2500);
      return;
    }
    setStatus("loading");
    setTimeout(() => {
      setStatus("success");
      setTimeout(() => setStatus(null), 2500);
    }, 1400);
  }

  return (
    <div
      className="min-h-screen flex flex-col items-center justify-center px-6 py-12 pb-20 relative"
      style={{ animation: "terminalIn 0.5s ease both" }}
    >
      {/* Grid background — same as welcome page */}
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
              label="Full Name"
              type="text"
              placeholder="Ada Lovelace"
              morseLabel={toMorse("NAME")}
              value={name}
              onChange={setName}
            />
            <Field
              label="Email Address"
              type="email"
              placeholder="operator@signal.net"
              morseLabel={toMorse("EMAIL")}
              value={email}
              onChange={setEmail}
            />

            {/* Step 1: Morse symbol input — type . and - directly */}
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

            {/* Step 2 & 3: Tap password + confirm */}
            <div className="border-t border-border pt-4 flex flex-col gap-5">
              <div className="flex items-center gap-2">
                <span className="font-mono text-[10px] text-primary tracking-widest uppercase">Step 2 · Tap Password</span>
                <div className="flex-1 h-px bg-border" />
              </div>
              <MorseTapInput
                label="Password"
                value={password}
                onChange={setPassword}
              />
              <MorseTapInput
                label="Confirm Password"
                value={confirmPassword}
                onChange={setConfirmPassword}
              />
              {confirmPassword.length > 0 && (
                <div
                  className="font-mono text-[10px] tracking-widest -mt-3"
                  style={{ color: confirmPassword === password ? "#00a8ff" : "#ff3333" }}
                >
                  {confirmPassword === password ? "✓ PASSWORDS MATCH" : "✗ MISMATCH"}
                </div>
              )}
            </div>

            <StatusBar status={status} />

            <button
              type="submit"
              disabled={status === "loading"}
              className="w-full py-4 font-mono font-bold text-sm tracking-[0.25em] uppercase text-primary-foreground bg-primary border border-primary transition-all duration-200 hover:brightness-110 disabled:opacity-60 disabled:cursor-not-allowed"
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                boxShadow: "0 0 20px rgba(0,168,255,0.3)",
              }}
            >
              {status === "loading" ? "· · ·" : "ENROLL"}
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

// ─── ROOT ──────────────────────────────────────────────────────────────────────

export default function App() {
  const [page, setPage] = useState<Page>("welcome");

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
      {page === "login" && <LoginPage navigate={setPage} />}
      {page === "register" && <RegisterPage navigate={setPage} />}

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
