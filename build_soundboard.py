#!/usr/bin/env python3
"""Build soundboard.html — an RWR-panel demo that plays the ACTUAL radio WAVs
(embedded as base64) for each event, so you can preview what the TX15 will do.

Run build_sounds.py first, then: python3 build_soundboard.py
"""
import io, os, base64

HERE = os.path.dirname(os.path.abspath(__file__))
SND  = os.path.join(HERE, "sdcard", "SOUNDS", "en")
OUT  = os.path.join(HERE, "soundboard.html")

# event -> (file, label, EdgeTX trigger, sound descriptor, severity)
EVENTS = [
    ("armed.wav",  "WEAPON ARMED",  "SE down + stick seen idle (L3)",        "ALR-67 missile-launch deedle x4",          "go"),
    ("disarm.wav", "WEAPON SAFE",   "SE up / disarm (!L3)",                  "'Deedle-deedle' RWR tone",                 "safe"),
    ("caution.wav","MASTER CAUTION","Throttle commanded while safe (L12)",   "A320 cavalry charge x4",                   "warn"),
    ("lowbat.wav", "LOW BATTERY",   "RxBt < 7.0 V for 1 s (L10), every 5 s", "'Fuel low' voice callout",                 "warn"),
    ("critbat.wav","CRITICAL BATT", "RxBt < 6.6 V for 1 s (L11), every 2 s", "'Bingo!' callout - low volume, constant",  "crit"),
]

def b64(fn):
    with io.open(os.path.join(SND, fn), "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")

def tiles():
    out = []
    for fn, label, trig, desc, sev in EVENTS:
        key = fn.replace(".wav", "")
        out.append(f'''      <button class="tile sev-{sev}" data-snd="{key}" aria-label="Play {label}">
        <span class="led"></span>
        <span class="name">{label}</span>
        <span class="trig">{trig}</span>
        <span class="desc">{desc}</span>
        <span class="play"><span class="tri"></span> PLAY</span>
      </button>''')
    return "\n".join(out)

def audios():
    return "\n".join(
        f'  <audio id="snd-{fn.replace(".wav","")}" preload="auto" '
        f'src="data:audio/wav;base64,{b64(fn)}"></audio>'
        for fn, *_ in EVENTS)

HTML = f'''<title>Combat RWR Panel</title>
<style>
  /* Layout: a dark avionics annunciator panel — a column of warning tiles that
     light and sound when tapped. Committed single-theme (a cockpit panel is dark). */
  :root {{
    --bg:#070b09; --panel:#0e1512; --panel2:#111a16; --edge:#1f2d26;
    --fg:#cdebd8; --muted:#6f8b7e;
    --go:#36d07a; --safe:#49a6ff; --warn:#ffb02e; --crit:#ff4133;
    --mono:"Share Tech Mono",ui-monospace,Menlo,Consolas,monospace;
    --sans:"Barlow Semi Condensed",system-ui,-apple-system,sans-serif;
    color-scheme:dark;
  }}
  * {{ box-sizing:border-box; }}
  body {{ background:
      radial-gradient(120% 80% at 50% -10%, #0c1813 0%, var(--bg) 60%);
      color:var(--fg); font-family:var(--sans); }}
  .wrap {{ max-width:720px; margin:0 auto; padding-block:28px; padding-inline:16px; }}

  header {{ border:1px solid var(--edge); border-radius:10px; background:
      linear-gradient(var(--panel),var(--panel2)); padding:18px 18px 16px;
      box-shadow:inset 0 1px 0 #ffffff10, 0 8px 30px #0008; }}
  .eyebrow {{ font-family:var(--mono); font-size:12px; letter-spacing:.28em;
      color:var(--go); text-transform:uppercase; }}
  h1 {{ font-family:var(--mono); font-weight:400; font-size:clamp(26px,6vw,38px);
      margin:.15em 0 .1em; letter-spacing:.04em; text-wrap:balance; }}
  .sub {{ color:var(--muted); font-size:14px; max-width:60ch; line-height:1.5; }}
  .statusbar {{ display:flex; gap:10px; flex-wrap:wrap; margin-top:14px;
      font-family:var(--mono); font-size:11px; letter-spacing:.14em; color:var(--muted); }}
  .statusbar b {{ color:var(--fg); font-weight:400; }}

  .grid {{ display:grid; gap:12px; margin-top:16px; }}
  .tile {{ display:grid; grid-template-columns:auto 1fr auto; grid-template-areas:
      "led name play" "led trig play" "led desc play";
      gap:2px 14px; align-items:center; width:100%; text-align:left;
      background:linear-gradient(var(--panel),var(--panel2)); color:var(--fg);
      border:1px solid var(--edge); border-left:4px solid var(--sev);
      border-radius:10px; padding:14px 16px; cursor:pointer; font:inherit;
      transition:transform .06s ease, box-shadow .15s ease, background .15s ease; }}
  .tile:hover {{ box-shadow:0 0 0 1px var(--sev), 0 6px 20px #0007; }}
  .tile:active {{ transform:translateY(1px); }}
  .tile:focus-visible {{ outline:2px solid var(--sev); outline-offset:2px; }}
  .tile.playing {{ background:linear-gradient(#16241d,#12201a); box-shadow:0 0 0 1px var(--sev), 0 0 22px -4px var(--sev); }}

  .sev-go   {{ --sev:var(--go); }}
  .sev-safe {{ --sev:var(--safe); }}
  .sev-warn {{ --sev:var(--warn); }}
  .sev-crit {{ --sev:var(--crit); }}

  .led {{ grid-area:led; width:16px; height:16px; border-radius:50%;
      background:var(--sev); box-shadow:0 0 10px -1px var(--sev), inset 0 0 4px #0006;
      opacity:.45; transition:opacity .1s; }}
  .tile.playing .led {{ opacity:1; animation:blink .4s steps(2,jump-none) infinite; }}
  @keyframes blink {{ 50% {{ opacity:.3; }} }}

  .name {{ grid-area:name; font-family:var(--mono); font-size:18px; letter-spacing:.06em; }}
  .trig {{ grid-area:trig; font-family:var(--mono); font-size:11.5px; color:var(--sev); letter-spacing:.03em; }}
  .desc {{ grid-area:desc; font-size:13px; color:var(--muted); min-width:0; }}
  .play {{ grid-area:play; align-self:center; font-family:var(--mono); font-size:12px;
      letter-spacing:.12em; color:var(--muted); display:flex; align-items:center; gap:7px;
      border:1px solid var(--edge); border-radius:6px; padding:9px 11px; white-space:nowrap; }}
  .tile.playing .play {{ color:var(--sev); border-color:var(--sev); }}
  .tri {{ width:0; height:0; border-left:9px solid currentColor;
      border-top:6px solid transparent; border-bottom:6px solid transparent; }}

  footer {{ margin-top:18px; color:var(--muted); font-size:12px; line-height:1.6; }}
  footer code {{ font-family:var(--mono); color:var(--fg); }}
  @media (prefers-reduced-motion:reduce) {{ .tile.playing .led {{ animation:none; }} }}
  @media (max-width:430px) {{
    .tile {{ grid-template-columns:auto 1fr; grid-template-areas:"led name" "led trig" "desc desc" "play play"; }}
    .play {{ justify-content:center; margin-top:8px; }}
  }}
</style>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Barlow+Semi+Condensed:wght@400;600&display=swap">

<div class="wrap">
  <header>
    <div class="eyebrow">ALR-67 · TX15 · ANT</div>
    <h1>Combat RWR Panel</h1>
    <p class="sub">F/A-18-themed event sounds for the combat-robot radio. Each tile is
      a real EdgeTX trigger from the model; tap to hear the exact WAV the TX15 plays.</p>
    <div class="statusbar">
      <span>MODEL <b>model3 / ANT</b></span>
      <span>PACK <b>2S LiHV</b></span>
      <span>SOUNDS <b>sdcard/SOUNDS/en</b></span>
    </div>
  </header>

  <div class="grid">
{tiles()}
  </div>

  <footer>
    These are the actual files generated by <code>build_sounds.py</code> and played on
    the radio via <code>PLAY_TRACK</code> special functions. Audio starts on tap
    (browsers block autoplay). Mix/levels verify in the EdgeTX simulator; final
    loudness-over-motor-noise is a bench check.
  </footer>
</div>

{audios()}

<script>
  (function () {{
    var current = null, tile = null;
    function stop() {{
      if (current) {{ try {{ current.pause(); current.currentTime = 0; }} catch (e) {{}} }}
      if (tile) tile.classList.remove("playing");
      current = null; tile = null;
    }}
    document.querySelectorAll(".tile").forEach(function (btn) {{
      btn.addEventListener("click", function () {{
        var el = document.getElementById("snd-" + btn.dataset.snd);
        if (!el) return;
        var same = (current === el);
        stop();
        if (same) return;            // tapping the playing tile stops it
        current = el; tile = btn;
        btn.classList.add("playing");
        el.currentTime = 0;
        el.play().catch(function () {{ stop(); }});
        el.onended = stop;
      }});
    }});
  }})();
</script>
'''

def main():
    io.open(OUT, "w", encoding="utf-8").write(HTML)
    kb = os.path.getsize(OUT) / 1024
    print("wrote", os.path.relpath(OUT, HERE), "(%.0f KB)" % kb)

if __name__ == "__main__":
    main()
