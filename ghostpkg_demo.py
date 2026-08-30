#!/usr/bin/env python3
"""
GHOSTPKG — Zero-Trust Dependency Firewall
Cyberpunk terminal demo UI (rich-based)

Run:
    python ghostpkg_demo.py
    python ghostpkg_demo.py --fast     # skip most sleeps for quick reruns
    python ghostpkg_demo.py --mute     # run silent (no audio effects)

Audio:
    Sound effects are synthesized on the fly (stdlib only — no pip
    packages, no asset files) and played via whatever's native to your
    OS: winsound on Windows, afplay on macOS, paplay/aplay/ffplay on
    Linux. If none of those are available, it just runs silently.
"""

import argparse
import math
import os
import platform
import random
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import wave

from rich.align import Align
from rich.box import Box
from rich import box
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

console = Console()

# ============================================================
# CONFIG
# ============================================================

PACKAGE = "requests-http-parse"
LEGITIMATE_PACKAGE = "requests"

# Neon palette
NEON_CYAN = "#00fff2"
NEON_CYAN_DIM = "#0a8f8a"
NEON_MAGENTA = "#ff00d4"
NEON_GREEN = "#39ff14"
NEON_RED = "#ff2b4d"
NEON_YELLOW = "#f9f871"
GHOST_WHITE = "#eafcff"
BG_GRID = "#0c1e24"

FAST = "--fast" in sys.argv
MUTE = "--mute" in sys.argv
SPEED = 0.15 if FAST else 1.0


def s(seconds):
    """Scaled sleep."""
    time.sleep(seconds * SPEED)


# ============================================================
# SOUND ENGINE — synthesized tones, stdlib only, no asset files
# ============================================================

SAMPLE_RATE = 44100


class SoundFX:
    """Generates and plays short WAV sound effects with zero pip deps.

    Tones are synthesized with `wave`/`struct`/`math`, cached to a temp
    dir, and dispatched to a native OS player. If no player is found
    (or playback ever fails), it disables itself and the rest of the
    demo just runs silently — audio never blocks or crashes the show.
    """

    def __init__(self, enabled=True):
        self.enabled = enabled
        self.player = self._detect_player() if enabled else None
        if self.player is None:
            self.enabled = False
        self._tmpdir = tempfile.mkdtemp(prefix="ghostpkg_sfx_")
        self._cache = {}

    def status(self):
        if not self.enabled:
            return "muted" if MUTE else "unavailable"
        return f"{self.player}"

    def _detect_player(self):
        system = platform.system()
        try:
            if system == "Windows":
                import winsound  # noqa: F401
                return "winsound"
            if system == "Darwin":
                return "afplay" if shutil.which("afplay") else None
            for candidate in ("paplay", "aplay", "ffplay"):
                if shutil.which(candidate):
                    return candidate
        except Exception:
            return None
        return None

    def _samples(self, freq, duration, volume, shape):
        n = int(SAMPLE_RATE * duration)
        out = []
        for i in range(n):
            t = i / SAMPLE_RATE
            phase = 2 * math.pi * freq * t
            if shape == "square":
                val = 1.0 if math.sin(phase) >= 0 else -1.0
            elif shape == "saw":
                val = 2 * (t * freq - math.floor(0.5 + t * freq))
            else:
                val = math.sin(phase)
            out.append(val * volume)
        fade = min(int(SAMPLE_RATE * 0.008), n // 2)
        for i in range(fade):
            out[i] *= i / fade
            out[-(i + 1)] *= i / fade
        return out

    def _wav_path(self, key, segments):
        """segments: list of (freq, duration, volume, shape), concatenated."""
        if key in self._cache:
            return self._cache[key]
        samples = []
        for freq, duration, volume, shape in segments:
            samples.extend(self._samples(freq, duration, volume, shape))
        path = os.path.join(self._tmpdir, f"{key}.wav")
        with wave.open(path, "w") as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(SAMPLE_RATE)
            frames = b"".join(
                struct.pack("<h", int(max(-1.0, min(1.0, v)) * 32000)) for v in samples
            )
            f.writeframes(frames)
        self._cache[key] = path
        return path

    def _play(self, path):
        if not self.enabled:
            return
        try:
            if self.player == "winsound":
                import winsound
                winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            elif self.player == "afplay":
                subprocess.Popen(["afplay", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif self.player == "ffplay":
                subprocess.Popen(
                    ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            else:  # paplay / aplay
                subprocess.Popen([self.player, path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            # Never let audio take the demo down — just go quiet.
            self.enabled = False

    # ---- effect library, one per UI moment -----------------------

    def blip(self):
        self._play(self._wav_path("blip", [(1400, 0.035, 0.18, "square")]))

    def boot_tick(self):
        self._play(self._wav_path("boot_tick", [(900, 0.05, 0.15, "square")]))

    def online_chime(self):
        self._play(self._wav_path(
            "online_chime",
            [(523, 0.08, 0.22, "sine"), (659, 0.08, 0.22, "sine"),
             (784, 0.08, 0.22, "sine"), (1046, 0.14, 0.24, "sine")],
        ))

    def anomaly(self):
        self._play(self._wav_path(
            "anomaly", [(620, 0.11, 0.28, "square"), (440, 0.16, 0.28, "square")]
        ))

    def alert_ping(self):
        self._play(self._wav_path("alert_ping", [(280, 0.09, 0.25, "saw")]))

    def siren(self):
        segs = []
        for _ in range(4):
            segs.append((820, 0.14, 0.24, "square"))
            segs.append((520, 0.14, 0.24, "square"))
        self._play(self._wav_path("siren", segs))

    def stamp(self):
        self._play(self._wav_path("stamp", [(140, 0.22, 0.32, "square")]))

    def agent_tick(self):
        self._play(self._wav_path("agent_tick", [(1600, 0.025, 0.12, "square")]))

    def fixed_ding(self):
        self._play(self._wav_path(
            "fixed_ding", [(784, 0.08, 0.22, "sine"), (1046, 0.14, 0.24, "sine")]
        ))

    def success_fanfare(self):
        self._play(self._wav_path(
            "success_fanfare",
            [(523, 0.1, 0.22, "sine"), (659, 0.1, 0.22, "sine"),
             (784, 0.1, 0.22, "sine"), (1046, 0.1, 0.24, "sine"),
             (1318, 0.22, 0.26, "sine")],
        ))


sfx = SoundFX(enabled=not MUTE)


# ============================================================
# GRADIENT / GLITCH TEXT HELPERS
# ============================================================

def _hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def _rgb_to_hex(rgb):
    return "#%02x%02x%02x" % rgb


def gradient_text(text, start, end, bold=True, justify="left"):
    """Render a string with a smooth left-to-right color gradient."""
    t = Text(justify=justify)
    n = max(len(text) - 1, 1)
    c0, c1 = _hex_to_rgb(start), _hex_to_rgb(end)
    for i, ch in enumerate(text):
        ratio = i / n
        rgb = tuple(int(c0[k] + (c1[k] - c0[k]) * ratio) for k in range(3))
        style = _rgb_to_hex(rgb)
        if bold:
            style = f"bold {style}"
        t.append(ch, style=style)
    return t


GLITCH_CHARS = "!<>-_\\/[]{}—=+*^?#$%01"


def glitch_reveal(text, style=f"bold {NEON_CYAN}", passes=6, delay=0.02):
    """Typewriter reveal where each char flickers through glitch chars first."""
    line = list(" " * len(text))
    with Live(Text("".join(line)), console=console, refresh_per_second=60) as live:
        for i, ch in enumerate(text):
            for _ in range(passes if not FAST else 1):
                line[i] = random.choice(GLITCH_CHARS)
                live.update(Text("".join(line), style=style))
                time.sleep(delay * SPEED)
            line[i] = ch
            live.update(Text("".join(line), style=style))
    console.print()


def flicker_print(renderable, times=2, on_delay=0.09, off_delay=0.06):
    with Live(renderable, console=console, refresh_per_second=60) as live:
        for _ in range(times):
            live.update(Text(""))
            time.sleep(off_delay * SPEED)
            live.update(renderable)
            time.sleep(on_delay * SPEED)


# ============================================================
# MATRIX RAIN INTRO
# ============================================================

def matrix_rain(duration=1.6, density=0.08):
    width = shutil.get_terminal_size((100, 30)).columns
    height = 16
    chars = "アイウエオカキクケコサシスセソタチツテト01ｸﾗｳﾄﾞ$#@&%"
    columns = [random.randint(-height, 0) for _ in range(width)]
    speeds = [random.randint(1, 3) for _ in range(width)]

    end_time = time.time() + (duration * SPEED)
    with Live(console=console, refresh_per_second=30) as live:
        while time.time() < end_time:
            grid = []
            for row in range(height):
                line = Text()
                for col in range(width):
                    head = columns[col]
                    if row == head:
                        line.append(random.choice(chars), style=f"bold {GHOST_WHITE}")
                    elif 0 <= head - row <= 6:
                        fade = 1 - (head - row) / 6
                        g = int(80 + fade * 175)
                        line.append(random.choice(chars), style=f"#00{g:02x}44")
                    else:
                        line.append(" ")
                grid.append(line)
            live.update(Group(*grid))
            for col in range(width):
                columns[col] += speeds[col]
                if columns[col] > height + random.randint(0, 20):
                    columns[col] = random.randint(-height, 0)
            time.sleep(0.045)
    console.clear()


# ============================================================
# BOOT SCREEN
# ============================================================

GHOST_ART = r'''
        .-""""""-.
       /  .------.  \
      /  /  o  o  \  \
      |  |    ▽    |  |
      \  \  ------  /  /
       \  '--------'  /
        '-..______..-'
           |  ||  |
           |  ||  |
          _|  ||  |_
'''


def boot_sequence():
    console.clear()
    matrix_rain(duration=1.4)

    logo = Text(justify="center")
    logo.append(GHOST_ART, style=f"bold {NEON_CYAN_DIM}")
    console.print(Align.center(logo))

    title = gradient_text("G H O S T P K G", NEON_MAGENTA, NEON_CYAN, justify="center")
    console.print(Align.center(title))
    console.print(
        Align.center(
            Text("ZERO-TRUST DEPENDENCY FIREWALL", style=f"bold {NEON_CYAN_DIM}")
        )
    )
    console.print(Align.center(Text("v2.4.1 // agentic-supply-chain-defense", style="dim")))
    console.print(Align.center(Text(f"♪ audio: {sfx.status()}", style="dim")))
    console.print()

    boot_steps = [
        ("Initializing GhostPkg security core", NEON_CYAN),
        ("Loading dependency intelligence graph", NEON_CYAN),
        ("Handshaking with PyPI registry", NEON_CYAN),
        ("Spinning up isolation sandbox", NEON_MAGENTA),
        ("Calibrating Levenshtein similarity engine", NEON_MAGENTA),
        ("Security core online", NEON_GREEN),
    ]

    for step, color in boot_steps:
        with Progress(
            SpinnerColumn(spinner_name="dots12", style=color),
            TextColumn(f"[{color}]{{task.description}}"),
            console=console,
            transient=True,
        ) as progress:
            progress.add_task(step, total=None)
            sfx.boot_tick()
            s(0.4)

    console.print()
    sfx.online_chime()
    console.print(
        Align.center(
            Panel(
                Text("✓  GHOSTPKG ONLINE  ✓", style=f"bold {NEON_GREEN}", justify="center"),
                border_style=NEON_GREEN,
                box=box.HEAVY,
                width=40,
            )
        )
    )
    s(0.6)
    console.print()


# ============================================================
# PACKAGE HEADER / HUD
# ============================================================

def package_header(package):
    sfx.blip()
    console.print(Rule(style=NEON_CYAN_DIM))
    table = Table(box=box.HEAVY_HEAD, border_style=NEON_CYAN, show_header=False, expand=True)
    table.add_column("Property", style=f"bold {NEON_CYAN}", width=16)
    table.add_column("Value", style=GHOST_WHITE)

    table.add_row("▶ TARGET", f"[bold]{package}[/bold]")
    table.add_row("▶ REGISTRY", "PyPI")
    table.add_row("▶ MODE", f"[bold {NEON_MAGENTA}]ZERO-TRUST[/bold {NEON_MAGENTA}]")
    table.add_row("▶ REQUESTED BY", "autonomous coding agent")
    table.add_row("▶ TIMESTAMP", time.strftime("%Y-%m-%d %H:%M:%S"))

    console.print(table)
    console.print(Rule(style=NEON_CYAN_DIM))
    console.print()


# ============================================================
# STATIC ANALYSIS
# ============================================================

def phase_banner(number, title, subtitle, color):
    console.print(
        Panel(
            f"[bold {color}]{number}  {title}[/bold {color}]\n[dim]{subtitle}[/dim]",
            border_style=color,
            box=box.HEAVY,
        )
    )


def static_analysis(package):
    phase_banner("01", "STATIC INTELLIGENCE", "Analyzing package metadata and identity", NEON_CYAN)

    checks = [
        "Querying PyPI registry",
        "Verifying package existence",
        "Cross-checking registry age",
        "Analyzing maintainer footprint",
        "Computing Levenshtein similarity",
    ]

    with Progress(
        SpinnerColumn(style=NEON_CYAN),
        TextColumn(f"[{NEON_CYAN}]{{task.description}}"),
        BarColumn(complete_style=NEON_CYAN, finished_style=NEON_GREEN),
        TextColumn(f"[{NEON_CYAN}]{{task.percentage:>3.0f}}%"),
        console=console,
    ) as progress:
        task = progress.add_task(checks[0], total=100)
        for check in checks:
            progress.update(task, description=check, completed=0)
            sfx.blip()
            for _ in range(25):
                progress.advance(task, 4)
                s(0.02)

    console.print()
    sfx.anomaly()
    console.print(f"[bold {NEON_YELLOW}]⚠ ANOMALY DETECTED[/bold {NEON_YELLOW}]")
    console.print(f"[dim]Package resembles a trusted library:[/dim] [bold]{LEGITIMATE_PACKAGE}[/bold]")
    console.print(f"[dim]Similarity score:[/dim] [bold {NEON_YELLOW}]0.91[/bold {NEON_YELLOW}] [dim](threshold 0.80)[/dim]")
    console.print()


# ============================================================
# DETONATION CHAMBER
# ============================================================

def detonation_chamber(package):
    phase_banner("02", "DETONATION CHAMBER", "Dynamic analysis inside an ephemeral sandbox", NEON_MAGENTA)

    steps = [
        "Spawning isolated Docker container",
        "Mounting read-only filesystem overlay",
        f"Attempting install: {package}",
        "Monitoring network egress",
        "Monitoring filesystem writes",
        "Collecting sandbox telemetry",
    ]

    with Progress(
        SpinnerColumn(style=NEON_MAGENTA),
        TextColumn(f"[{NEON_MAGENTA}]{{task.description}}"),
        BarColumn(complete_style=NEON_MAGENTA, finished_style=NEON_GREEN),
        TextColumn(f"[{NEON_MAGENTA}]{{task.percentage:>3.0f}}%"),
        console=console,
    ) as progress:
        task = progress.add_task(steps[0], total=100)
        for step in steps:
            progress.update(task, description=step, completed=0)
            sfx.blip()
            for _ in range(20):
                progress.advance(task, 5)
                s(0.03)

    console.print()
    sfx.alert_ping()
    console.print(f"[{NEON_RED}]▸ unexpected outbound connection attempt logged[/{NEON_RED}]")
    sfx.alert_ping()
    console.print(f"[{NEON_RED}]▸ suspicious base64 payload detected in setup script[/{NEON_RED}]")
    console.print(f"[bold {NEON_GREEN}]✓ Sandbox analysis complete — connection blocked[/bold {NEON_GREEN}]")
    console.print()
    s(0.4)


# ============================================================
# THREAT ALERT
# ============================================================

def threat_alert(package):
    console.print()
    sfx.siren()
    siren_frames = [NEON_RED, "bold white on #7a0010", NEON_RED]
    for frame_color in siren_frames * 2:
        console.print("\033[2J\033[H", end="")
        console.print(
            Align.center(
                Panel(
                    Align.center(Text("⚠  S E C U R I T Y   T H R E A T  ⚠", style=f"bold {frame_color}")),
                    border_style=NEON_RED,
                    box=box.DOUBLE,
                    width=60,
                )
            )
        )
        s(0.12)

    console.print("\033[2J\033[H", end="")
    body = Text(justify="center")
    body.append("\n🚨  THREAT DETECTED  🚨\n\n", style=f"bold {NEON_RED}")
    body.append(f"PACKAGE      ", style="bold white")
    body.append(f"{package}\n", style=f"bold {NEON_RED}")
    body.append(f"LOOKALIKE    ", style="bold white")
    body.append(f"{LEGITIMATE_PACKAGE}\n", style=f"bold {NEON_YELLOW}")
    body.append(f"RISK         ", style="bold white")
    body.append("CRITICAL\n\n", style=f"bold reverse {NEON_RED}")
    body.append("⛔  INSTALLATION BLOCKED  ⛔\n", style=f"bold {NEON_RED}")

    console.print(
        Align.center(
            Panel(
                body,
                title="[bold]GHOSTPKG FIREWALL[/bold]",
                border_style=NEON_RED,
                box=box.DOUBLE,
                padding=(1, 6),
            )
        )
    )
    console.print()
    s(0.9)


# ============================================================
# SECURITY DETAILS
# ============================================================

def security_report():
    sfx.stamp()
    table = Table(
        title="[bold]SECURITY REPORT[/bold]",
        border_style=NEON_CYAN,
        box=box.HEAVY_HEAD,
        expand=True,
    )

    table.add_column("Security Layer", style="bold white")
    table.add_column("Result", style="dim")
    table.add_column("Status", justify="right")

    table.add_row("PyPI Registry", "Package not verified", f"[bold {NEON_RED}]FAILED[/bold {NEON_RED}]")
    table.add_row("Similarity Engine", "High-risk lookalike (0.91)", f"[bold {NEON_YELLOW}]WARNING[/bold {NEON_YELLOW}]")
    table.add_row("Docker Sandbox", "Outbound connection blocked", f"[bold {NEON_RED}]BLOCKED[/bold {NEON_RED}]")
    table.add_row(
        "Final Verdict",
        "Malicious / hallucinated dependency",
        f"[bold reverse {NEON_RED}] DENIED [/bold reverse {NEON_RED}]",
    )

    console.print(table)
    console.print()


# ============================================================
# AI SELF HEALING
# ============================================================

def ai_recovery():
    phase_banner("03", "AI SELF-HEALING", "Returning structured feedback to the coding agent", NEON_MAGENTA)

    messages = [
        "Streaming security verdict to AI agent",
        "Agent parsing rejection payload",
        "Agent cross-referencing trusted package index",
        "Agent identified invalid dependency",
        "Generating corrected import",
    ]

    with Progress(
        SpinnerColumn(spinner_name="bouncingBar", style=NEON_MAGENTA),
        TextColumn(f"[{NEON_MAGENTA}]{{task.description}}"),
        console=console,
    ) as progress:
        task = progress.add_task(messages[0], total=None)
        for message in messages:
            progress.update(task, description=message)
            sfx.agent_tick()
            s(0.5)

    console.print()
    sfx.fixed_ding()
    console.print(
        Panel(
            Text.from_markup(
                f"[bold {NEON_RED}]✗ Rejected:[/bold {NEON_RED}]   {PACKAGE}\n"
                f"[bold {NEON_GREEN}]✓ Corrected:[/bold {NEON_GREEN}]  {LEGITIMATE_PACKAGE}\n\n"
                f"[bold {NEON_GREEN}]AUTONOMOUS AGENT RETRYING INSTALL...[/bold {NEON_GREEN}]"
            ),
            title="[bold]AUTONOMOUS RECOVERY[/bold]",
            border_style=NEON_MAGENTA,
            box=box.ROUNDED,
        )
    )
    s(0.8)


# ============================================================
# SUCCESS
# ============================================================

def final_success():
    console.print()
    sfx.success_fanfare()
    for _ in range(2):
        console.print(
            Align.center(
                Panel(
                    Align.center(
                        Text("\n✓  DEPENDENCY VERIFIED\n\nSYSTEM SECURED\n", style=f"bold {NEON_GREEN}")
                    ),
                    border_style=NEON_GREEN,
                    box=box.DOUBLE,
                )
            )
        )
        s(0.3)

    console.print()
    console.print(
        Align.center(
            gradient_text(
                "GhostPkg prevented a supply-chain attack in real time.",
                NEON_GREEN,
                NEON_CYAN,
                justify="center",
            )
        )
    )
    console.print()
    console.print(Rule(style=NEON_CYAN_DIM))
    console.print(Align.center(Text("GHOSTPKG • ZERO-TRUST DEPENDENCY FIREWALL", style="dim")))
    console.print()


# ============================================================
# MAIN DEMO
# ============================================================

def main():
    boot_sequence()
    package_header(PACKAGE)
    static_analysis(PACKAGE)
    detonation_chamber(PACKAGE)
    threat_alert(PACKAGE)
    security_report()
    ai_recovery()
    final_success()


if __name__ == "__main__":
    main()