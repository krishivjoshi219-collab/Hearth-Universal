#!/usr/bin/env python3
"""Hearth demo film — live recorder v2. Scene-clock driven (robust to slow CDP
under video recording): every action is anchored to absolute scene time."""
import glob
import json
import os
import re
import shutil
import sys
import time

from playwright.sync_api import sync_playwright

ROOT = "/home/k/Prototype/Amazon"
RAW = f"{ROOT}/demo_film/raw"
BASE = "http://127.0.0.1:8787"
CHROME = "/home/k/.local/bin/google-chrome"
VIEW = {"width": 1920, "height": 1080}

CURSOR_JS = r"""
(() => {
  const mk = () => {
    const cur = document.createElement('div'); cur.id = '__cur';
    const dot = document.createElement('div'); dot.id = '__dot';
    // CSP-safe: style everything via CSSOM. The server sends
    // `style-src 'self'`, so an injected <style> element is silently
    // blocked — only direct style-object mutations render.
    const s = cur.style;
    s.position = 'fixed'; s.zIndex = '2147483647';
    s.width = '40px'; s.height = '40px'; s.margin = '-20px 0 0 -20px';
    s.borderRadius = '50%';
    s.border = '2.5px solid rgba(255,255,255,.92)';
    s.boxShadow = '0 0 0 1.5px rgba(0,0,0,.35), 0 0 20px rgba(255,120,40,.55)';
    s.background = 'rgba(255,120,40,.16)'; s.pointerEvents = 'none';
    s.willChange = 'left, top';
    s.transition = 'left .13s linear, top .13s linear, transform .09s ease, background .09s ease';
    const d = dot.style;
    d.position = 'fixed'; d.zIndex = '2147483647';
    d.width = '6px'; d.height = '6px'; d.margin = '-3px 0 0 -3px';
    d.borderRadius = '50%'; d.background = '#ff9a55'; d.pointerEvents = 'none';
    d.boxShadow = '0 0 10px rgba(255,150,80,.9)';
    document.documentElement.append(cur, dot);
    const move = (e) => {
      cur.style.left = e.clientX + 'px'; cur.style.top = e.clientY + 'px';
      dot.style.left = e.clientX + 'px'; dot.style.top = e.clientY + 'px';
    };
    addEventListener('mousemove', move, true);
    addEventListener('mousedown', () => {
      cur.style.transform = 'scale(.52)';
      cur.style.background = 'rgba(255,120,40,.55)';
    }, true);
    addEventListener('mouseup', () => {
      cur.style.transform = '';
      cur.style.background = 'rgba(255,120,40,.16)';
    }, true);
    move({ clientX: 960, clientY: 540 });
  };
  if (document.readyState === 'loading') addEventListener('DOMContentLoaded', mk); else mk();
})();
"""

MOVE_COST = 0.05  # measured per mouse.move round-trip, updated in main()


class Scene:
    """One recorded scene. All pacing is anchored to absolute scene time."""

    def __init__(self, pg, total):
        self.pg = pg
        self.total = total
        self.t0 = time.monotonic()
        self.x, self.y = 960.0, 540.0

    def el(self):
        return time.monotonic() - self.t0

    def sync(self, t):
        d = t - self.el()
        if d > 0:
            self.pg.wait_for_timeout(int(d * 1000))

    def goto(self, url, settle=0.5):
        try:
            self.pg.goto(url, wait_until="domcontentloaded", timeout=20000)
        except Exception:
            pass
        self.sync(self.el() + settle)

    def gl(self, x, y, ms=800):
        x, y = float(x), float(y)
        steps = max(5, min(30, int(ms / max(30.0, MOVE_COST * 1000.0))))
        dx, dy = (x - self.x) / steps, (y - self.y) / steps
        dt = ms / 1000.0 / steps
        for _ in range(steps):
            self.x += dx
            self.y += dy
            st = time.monotonic()
            try:
                self.pg.mouse.move(self.x, self.y)
            except Exception:
                # A hung CDP move: retry once, then give up — callers that
                # must be precise (to_el) verify arrival themselves.
                time.sleep(0.2)
                try:
                    self.pg.mouse.move(self.x, self.y)
                except Exception:
                    return
            time.sleep(max(0.0, dt - (time.monotonic() - st)))
            if self.el() > self.total - 0.4:
                return

    def to_el(self, loc, dx=0, dy=0, ms=700):
        box = loc.bounding_box()
        if not box:
            raise RuntimeError("no box")
        want_x = box["x"] + box["width"] / 2 + dx
        want_y = box["y"] + box["height"] / 2 + dy
        self.gl(want_x, want_y, ms=ms)
        # Never let a click fire mid-flight: if the glide was aborted (dead
        # CDP move, scene-clock cutoff), surface it instead of clicking blind.
        if abs(self.x - want_x) > 6 or abs(self.y - want_y) > 6:
            raise RuntimeError("glide interrupted")
        return box

    def click_el(self, loc, ms=700, settle=0.35):
        self.to_el(loc, ms=ms)
        time.sleep(0.18)
        self.pg.mouse.down()
        time.sleep(0.09)
        self.pg.mouse.up()
        self.sync(self.el() + settle)

    def wheel(self, px, ms=1400, steps=8):
        per, dt = px / steps, ms / 1000.0 / steps
        for _ in range(steps):
            st = time.monotonic()
            try:
                self.pg.mouse.wheel(0, per)
            except Exception:
                return
            time.sleep(max(0.0, dt - (time.monotonic() - st)))
            if self.el() > self.total - 0.4:
                return

    def hold(self):
        pass  # sync() before each action is the hold


def q(pg, sel, n=0):
    try:
        loc = pg.locator(sel)
        if loc.count() > n:
            return loc.nth(n)
    except Exception:
        pass
    return None


def safe(sc, fn):
    try:
        fn()
    except Exception as e:
        print(f"    warn: {type(e).__name__}: {str(e)[:120]}")


def robust(sc, loc, ms=700, settle=0.35, tries=2):
    """A click that survives one 'glide interrupted' under load (to_el raises
    before any click, so a retry can never double-click)."""
    for _ in range(tries):
        try:
            sc.click_el(loc, ms=ms, settle=settle)
            return True
        except Exception as e:
            print(f"    warn(retry): {type(e).__name__}: {str(e)[:80]}")
    return False


CACHE = {}


def _snapshot():
    """One-time bodies for poll endpoints that block the server. /api/models
    (2.25 s) and /api/diagnostics (2.4 s) run synchronously inside the asyncio
    loop every 4 s of page polling — the decide queued behind them for 14 s on
    camera (74 ms with no page open)."""
    import urllib.request
    for path in ("/api/models", "/api/diagnostics"):
        try:
            with urllib.request.urlopen(BASE + path, timeout=20) as r:
                CACHE[path] = (r.read().decode(), r.headers.get("Content-Type") or "application/json")
        except Exception as e:
            print(f"    warn(snapshot {path}): {type(e).__name__}")


def quiet(pg):
    """Keep web2's 4-second household poll from running slow handlers while we
    record. Models + diagnostics are served from the startup snapshot (the same
    bytes the UI gets, minus the server stall); the five simulation tiles are
    skipped — they are off-camera content and each blocks the loop."""
    def _abort(route, request):
        try:
            route.abort()
        except Exception:
            pass

    def _serve(route, request):
        try:
            hit = CACHE.get(request.url.split("?")[0])
            if not hit:
                route.abort()
                return
            route.fulfill(status=200, content_type=hit[1], body=hit[0])
        except Exception:
            pass

    for pat in ("**/api/causal/**", "**/api/acoustic/**", "**/api/forensics/**",
                "**/api/mediation/**", "**/api/swarm/**", "**/api/parliament/**"):
        try:
            pg.route(pat, _abort)
        except Exception:
            pass
    pg.route(re.compile(r"/api/models(\?|$)"), _serve)
    pg.route(re.compile(r"/api/diagnostics(\?|$)"), _serve)


def reveal(pg, sel, target_y=150, tries=5):
    """Bring sel to target_y by scrolling its real scroll container — window
    scrollBy was a no-op (cockpit scrolls an inner element, so the abilities
    pill stayed hidden behind the sticky nav)."""
    js = """([sel, off]) => {
      const el = document.querySelector(sel);
      if (!el) return -1;
      let s = el.parentElement;
      while (s && !(s.scrollHeight > s.clientHeight + 8 &&
                    /(auto|scroll)/.test(getComputedStyle(s).overflowY))) s = s.parentElement;
      if (!s) s = document.scrollingElement || document.documentElement;
      const r = el.getBoundingClientRect(), cr = s.getBoundingClientRect();
      const doc = (s === document.scrollingElement || s === document.documentElement);
      const want = doc ? off : cr.top + off;
      const dy = r.top - want;
      if (Math.abs(dy) > 2) {
        if (doc) window.scrollTo({top: window.scrollY + dy, behavior: 'smooth'});
        else s.scrollTo({top: s.scrollTop + dy, behavior: 'smooth'});
      }
      return dy;
    }"""
    for _ in range(tries):
        try:
            loc = pg.locator(sel)
            if not loc.count():
                return False
            box = loc.first.bounding_box()
            if box and 96 <= box["y"] <= 340:
                return True
            pg.evaluate(js, [sel, target_y])
        except Exception:
            pass
        pg.wait_for_timeout(320)
    return False


# ---------------------------------------------------------------- scenes

def s01(sc, pg):
    sc.goto(BASE + "/", settle=0.6)
    sc.sync(2.1); sc.gl(940, 430, ms=900)      # hero — drift onto the number
    sc.sync(2.7); sc.wheel(960, ms=1500)       # stats band
    sc.sync(4.6); sc.gl(520, 330, ms=700)
    sc.sync(5.2); sc.wheel(190, ms=800)        # leak head
    sc.sync(6.2); sc.gl(960, 620, ms=700)      # leak story
    sc.sync(7.4); sc.wheel(800, ms=1500)       # what it does
    sc.sync(9.2); sc.gl(600, 520, ms=700)
    sc.sync(9.9); sc.wheel(1570, ms=1800)      # conversation strip
    sc.sync(11.8); sc.gl(1280, 520, ms=800)
    sc.sync(12.7); sc.wheel(1880, ms=2100)     # promises + the Robux story
    sc.sync(15.0); sc.gl(980, 660, ms=800)


def s02(sc, pg):
    sc.goto(BASE + "/echo", settle=0.4)
    # park the cursor near the composer (overlay eases over 130 ms)
    pg.mouse.move(620, 1012); sc.x, sc.y = 620.0, 1012.0
    sc.sync(1.9)
    inp = q(pg, "#askText")
    if inp:
        safe(sc, lambda: sc.click_el(inp, ms=200, settle=0.1))
        sc.sync(sc.el() + 0.1)
        pg.keyboard.type("Save me $800.", delay=38)
    sc.sync(3.6)
    send = q(pg, "#askSend")
    sx, sy = 1266.0, 1012.0
    if send:
        try:
            sb = send.bounding_box()
            if sb:
                sx, sy = sb["x"] + sb["width"] / 2, sb["y"] + sb["height"] / 2
        except Exception:
            pass
    sc.gl(sx, sy, ms=200)                      # move to the send button
    if abs(sc.x - sx) <= 8 and abs(sc.y - sy) <= 8:   # never click mid-flight
        time.sleep(0.12)
        try:
            pg.mouse.down(); time.sleep(0.06); pg.mouse.up()
        except Exception:
            pass
    # the live brain thinks on camera — wait for the answer, then tour the
    # four display modes while it is on screen (settings sheet stays open).
    deadline = sc.el() + 26
    while time.monotonic() - sc.t0 < deadline:
        try:
            if pg.evaluate("() => { const r = document.querySelector('#response');"
                           " return !!(r && r.innerText && r.innerText.trim().length > 20); }"):
                break
        except Exception:
            pass
        pg.wait_for_timeout(280)
    sc.sync(sc.el() + 1.0)
    btn = q(pg, "#settingsBtn")
    if btn:
        safe(sc, lambda: sc.click_el(btn, ms=340, settle=0.12))
    sc.sync(sc.el() + 0.55)
    for mode in ("fullscreen", "hydrated", "voice-only", "inline"):
        chip = q(pg, '[data-mode="%s"]' % mode)
        if chip:
            safe(sc, lambda chip=chip: sc.click_el(chip, ms=260, settle=0.12))
        sc.sync(sc.el() + 0.6)
    close = q(pg, "#settingsCloseBtn")
    if close:
        safe(sc, lambda: sc.click_el(close, ms=280, settle=0.12))
    sc.sync(sc.el() + 0.6)
    sc.gl(940, 520, ms=500)


def s03(sc, pg):
    sc.goto(BASE + "/web2/", settle=0.7)
    for i, t in enumerate((3.0, 5.2, 7.4)):
        el = q(pg, ".stat", i)
        if el:
            sc.sync(t - 0.85)
            safe(sc, lambda el=el: sc.to_el(el, ms=800))
    sc.sync(9.2); sc.wheel(760, ms=1700)
    sc.sync(11.4); sc.gl(760, 860, ms=800)
    sc.sync(12.8); sc.gl(1210, 780, ms=850)
    sc.sync(14.4); sc.wheel(-760, ms=1500)
    sc.sync(16.4); sc.gl(960, 320, ms=900)


def s04(sc, pg):
    # PnE + one-tap take-back. VO anchors (edge-tts, -4%, +0.42s mux offset):
    #   0.47s "Here is the line Hearth never crosses."  -> open the OK list
    #   3.41s "It proposes."                            -> the staged cards answer
    #   6.29s "Every action waits for you..."           -> dwell on what / why / saves
    #   9.4s  click Do It — the receipt lands inside the same line
    #  11.83s "Approve once — and Hearth carries it out." -> the receipt row reads out
    #  14.64s "Trust is built in the pauses."           -> take it back; list settles
    gate = {"props": True}

    # The app refreshes the list 800 ms after a decision, which wipes the
    # receipt row (and its Take it back) — the whole point of the beat. Hold
    # the proposals feed from the click until just after the undo, then let it
    # settle back: the receipt stays readable, and the card returns to waiting.
    pg.route(re.compile(r"/api/proposals(\?|$)"),
             lambda route, request: route.continue_() if gate["props"] else route.abort())
    quiet(pg)
    sc.goto(BASE + "/web2/", settle=0.8)
    sc.sync(3.4)
    tab = q(pg, '.tab[data-view="approvals"]')
    if tab:
        safe(sc, lambda: sc.click_el(tab))
    sc.sync(5.8)
    card = q(pg, ".intent", 0)
    if card:
        safe(sc, lambda: sc.to_el(card, dy=-40, ms=700))
    sc.sync(8.4); sc.wheel(150, ms=900)
    sc.sync(9.0)
    gate["props"] = False
    sc.sync(9.4)
    btn = q(pg, ".intent .btn-primary", 0) or q(pg, ".intent button", 0)
    if btn:
        safe(sc, lambda: sc.click_el(btn))
    undo_ready = False
    t_cap = time.monotonic() + 6.0
    while time.monotonic() < t_cap and sc.el() < 13.2:
        try:
            u = pg.locator(".btn-undo")
            if u.count() and u.first.is_visible():
                undo_ready = True
                break
        except Exception:
            pass
        pg.wait_for_timeout(120)
    if undo_ready:
        sc.sync(11.9)
        sc.gl(sc.x - 290, sc.y + 40, ms=760)              # read the receipt with the camera
        sc.sync(13.9)
        undo = q(pg, ".btn-undo", 0)
        if undo:
            safe(sc, lambda: sc.click_el(undo, ms=420))   # the take-back, on camera
    sc.sync(14.7)
    gate["props"] = True
    try:
        pg.evaluate("() => import('/web2/js/store.js').then(m => m.refresh())")
    except Exception:
        pass
    sc.sync(15.4)
    sc.gl(1120, 648, ms=500)                          # the card settles back to waiting
    sc.sync(16.7)
    sc.gl(1010, 724, ms=420)
    sc.sync(17.6)


def s05(sc, pg):
    sc.goto(BASE + "/web2/", settle=0.8)
    sc.sync(3.4)
    tab = q(pg, '.tab[data-view="activity"]')
    if tab:
        safe(sc, lambda: sc.click_el(tab))
    sc.sync(5.6)
    sm = (q(pg, "#timeline .event details summary", 0)
          or q(pg, "#timeline details summary", 0)
          or q(pg, "#timeline .event", 0))
    if sm:
        safe(sc, lambda: sc.click_el(sm))
    sc.sync(8.2); sc.wheel(170, ms=1000)
    sc.sync(10.6); sc.wheel(170, ms=1000)
    sc.sync(13.0)
    ev2 = q(pg, "#timeline .event", 1)
    if ev2:
        safe(sc, lambda: sc.to_el(ev2, dy=-30, ms=700))


def s06(sc, pg):
    sc.goto(BASE + "/web2/", settle=0.8)
    sc.sync(2.9)
    tab = q(pg, '.tab[data-view="insights"]')
    if tab:
        safe(sc, lambda: sc.click_el(tab))
    sc.sync(4.8); sc.wheel(360, ms=1300)
    sc.sync(6.4); sc.wheel(360, ms=1300)
    sc.sync(8.1); sc.wheel(300, ms=1200)
    sc.sync(9.9)
    cb = q(pg, "#causalBox")
    if cb:
        try:
            cb.evaluate("el => el.scrollIntoView({behavior:'smooth', block:'center'})")
        except Exception:
            pass
    sc.sync(12.2); sc.gl(1120, 700, ms=800)
    sc.sync(13.6); sc.gl(880, 780, ms=700)


def s07(sc, pg):
    # Forge, braked to the 18.5s VO. Anchors (edge-tts, -4%, +0.42s mux offset):
    #   0.47s "And when Hearth meets a need nobody coded..."
    #   4.95s kick it early so the ~3s generation hides inside the long line
    #   8.01s "It writes the tool itself."      -> the generated source lands
    #   9.83s "Watch." ... "A safety gate."     -> the gate badge
    #  11.96s "Then mounted, live — as tool fifty five." -> name + 54 -> 55 pill
    #  15.25s "Nothing was shipped."            -> the catalog
    #  16.53s "And every step is on the record."-> the audit hash
    def wait_vis(sel, until, ms_hard):
        t_cap = time.monotonic() + ms_hard
        while time.monotonic() < t_cap and sc.el() < until:
            try:
                loc = pg.locator(sel)
                if loc.count() and loc.is_visible():
                    return True
            except Exception:
                pass
            pg.wait_for_timeout(120)
        return False

    quiet(pg)
    sc.goto(BASE + "/web2/", settle=0.4)
    sc.sync(1.6)
    tab = q(pg, '.tab[data-view="home"]')
    if tab:
        safe(sc, lambda: sc.click_el(tab, settle=0.15))
    sc.sync(2.6)
    panel = q(pg, "#forgePanel")
    if panel:
        try:
            panel.evaluate("el => el.scrollIntoView({behavior:'smooth', block:'start'})")
        except Exception:
            pass
    sc.sync(4.1)
    inp = q(pg, "#forgeInput")
    if inp:
        safe(sc, lambda: sc.to_el(inp, ms=520))    # the rule, pre-filled
    sc.sync(4.65)
    go = q(pg, "#forgeGo")
    if go:
        safe(sc, lambda: sc.to_el(go, ms=260))
    sc.sync(4.95)
    if go:
        safe(sc, lambda: sc.click_el(go, ms=180, settle=0.1))
    if wait_vis("#forgeOut", 8.6, 6000):
        sc.sync(5.6)
        sc.gl(sc.x - 320, sc.y + 64, ms=420)       # clear the button; watch the chips
        outl = q(pg, "#forgeOut")
        if outl:
            try:
                outl.evaluate("el => el.scrollIntoView({behavior:'smooth', block:'center'})")
            except Exception:
                pass
        wait_vis("#forgeCode", 9.6, 6000)
        code = q(pg, "#forgeCode")
        if code:
            safe(sc, lambda: sc.to_el(code, ms=600))       # "It writes the tool itself."
        sc.sync(9.5)
        wait_vis("#forgeSafety", 11.0, 4000)
        safety = q(pg, "#forgeSafety")
        if safety:
            safe(sc, lambda: sc.to_el(safety, ms=560))     # "Watch. A safety gate."
        sc.sync(11.5)
        wait_vis("#forgeToolName", 12.3, 4000)
        tool = q(pg, "#forgeToolName")
        if tool:
            safe(sc, lambda: sc.to_el(tool, ms=580))       # "Then mounted, live —"
        sc.sync(12.7)
        reveal(pg, "#forgeCount")                          # ease the abilities pill into frame
        sc.sync(13.5)
        cnt = q(pg, "#forgeCount")
        if cnt:
            safe(sc, lambda: sc.to_el(cnt, ms=420))        # "...as tool fifty five." 54 -> 55
        sc.sync(14.9)
        call = q(pg, "#forgeCall")
        if call:
            safe(sc, lambda: sc.to_el(call, ms=400))
        sc.sync(15.05)                                     # invoke it, live
        if call:
            safe(sc, lambda: sc.click_el(call, ms=150, settle=0.08))
            try:
                pg.wait_for_function(
                    "() => { const r = document.querySelector('#forgeResult');"
                    " return r && !r.hidden && r.innerText &&"
                    " /savings|applied|execut/i.test(r.innerText); }", timeout=8000)
            except Exception:
                pass
        sc.sync(16.3)
        cat = q(pg, "#forgeCatalog")
        if cat:
            safe(sc, lambda: sc.to_el(cat, ms=560))        # "Nothing was shipped."
        sc.sync(17.2)
        proof = q(pg, "#forgeProof")
        if proof:
            safe(sc, lambda: sc.to_el(proof, ms=520))      # "And every step is on the record."
        sc.sync(19.4)


def s08(sc, pg):
    sc.goto(BASE + "/web2/", settle=0.8)
    sc.sync(3.2)
    tab = q(pg, '.tab[data-view="insights"]')
    if tab:
        safe(sc, lambda: sc.click_el(tab))
    sc.sync(4.8)
    box = q(pg, "#forensicsBox")
    if box:
        try:
            box.evaluate("el => el.scrollIntoView({behavior:'smooth', block:'center'})")
        except Exception:
            pass
    sc.sync(7.4)
    btn = q(pg, "#forensicsScanBtn")
    if btn:
        safe(sc, lambda: sc.click_el(btn, settle=0.2))
    try:
        pg.wait_for_selector("#scrim:not([hidden])", timeout=12000)
    except Exception:
        pass
    sc.sync(12.6)
    body = q(pg, "#dlgBody")
    if body:
        safe(sc, lambda: sc.to_el(body, dy=40, ms=700))
    sc.sync(15.2); sc.wheel(200, ms=1000)
    sc.sync(17.4); sc.gl(1160, 780, ms=800)


def s09(sc, pg):
    sc.goto(f"file://{ROOT}/demo_film/endcard.html?t={sc.total:.2f}", settle=0.3)
    sc.gl(1905, 1070, ms=350)


def s10(sc, pg):
    # Amazon late-delivery clawback beat. VO anchors (edge-tts, -4%, +0.42s mux offset):
    #   0.42s "Your Prime box is late."  -> glide to the lane button
    #   1.9s  "Hearth already knows."    -> click; the claim card builds (~2.5s latency)
    #   3.3s  "Five dollars drafted."    -> drift across the card
    #   4.7s  "One tap claims it."       -> click the Waiting List approve
    #   6.0s  "Sealed in the ledger."    -> the receipt sheet opens with the proof
    sc.goto(BASE + "/echo", settle=0.7)
    sc.sync(1.1)
    lane = q(pg, 'button[data-go="/api/commerce/delivery-clawback"]')
    if lane:
        safe(sc, lambda: sc.click_el(lane, ms=640, settle=0.15))
    sc.sync(3.0)
    sc.gl(1210, 560, ms=760)                    # across "+$5.00 / credit drafted"
    sc.sync(4.6)
    sc.gl(1450, 700, ms=520)                    # down toward the Waiting List
    sc.sync(5.05)
    appr = q(pg, "#trayBody .btn.btn-primary")
    if appr:
        safe(sc, lambda: sc.click_el(appr, ms=420, settle=0.1))
    sc.sync(6.6)
    card = q(pg, "#receiptCard")
    if card:
        safe(sc, lambda: sc.to_el(card, dy=-40, ms=620))   # receipt sheet: the proof
    sc.sync(8.15)
    code = q(pg, "#receiptCode")
    if code:
        safe(sc, lambda: sc.to_el(code, dy=0, ms=420))     # end on the receipt code
    sc.sync(8.85)


def s11(sc, pg):
    # Groceries / Subscribe & Save. VO anchors (edge-tts, -4%, +0.42s mux offset):
    #   0.47s "And when the pantry runs dry?"    -> the lane chip
    #   2.53s "Hearth builds the cart — ..."     -> click; cart card builds (~60ms route)
    #   9.04s "Thirty-five dollars you keep."    -> across the save line
    #  11.01s "Nothing is bought until you tap." -> tap approve in the Waiting List
    sc.goto(BASE + "/echo", settle=0.6)
    sc.sync(1.0)
    chip = q(pg, 'button[data-go="/api/commerce/autopilot-checkout"]')
    if chip:
        safe(sc, lambda: sc.to_el(chip, ms=560))
    sc.sync(2.35)
    if chip:
        safe(sc, lambda: sc.click_el(chip, ms=180, settle=0.12))
    deadline = sc.el() + 3.6                          # deterministic: answers instantly
    while sc.el() < deadline:
        try:
            if pg.evaluate("() => { const r = document.querySelector('#response');"
                           " return !!(r && r.innerText && r.innerText.trim().length > 60); }"):
                break
        except Exception:
            pass
        pg.wait_for_timeout(120)
    sc.sync(3.4)
    sc.gl(1210, 560, ms=800)                          # across the cart ($73.65 total)
    sc.sync(5.4)
    sc.gl(1330, 700, ms=620)                          # the save line: "$35.32 with S&S"
    sc.sync(7.6)
    sc.gl(1210, 860, ms=700)                          # settle toward the Waiting List
    sc.sync(9.6)
    appr = q(pg, "#trayBody .btn.btn-primary")
    if appr:
        safe(sc, lambda: sc.to_el(appr, ms=620))
    sc.sync(11.05)
    if appr:
        safe(sc, lambda: sc.click_el(appr, ms=220, settle=0.12))
    sc.sync(12.6)
    card = q(pg, "#receiptCard")
    if card:
        safe(sc, lambda: sc.to_el(card, dy=-30, ms=560))   # the receipt, once it seals
    sc.sync(13.5)
    code = q(pg, "#receiptCode")
    if code:
        safe(sc, lambda: sc.to_el(code, ms=380))
    sc.sync(14.0)


def s12(sc, pg):
    # Leo child block. VO anchors (edge-tts, -4%, +0.42s mux offset):
    #   0.47s "Here is the line that matters most."
    #   2.95s "Switch to Leo, age nine."         -> open Display & AI, flip the profile
    #   5.24s "Buy five thousand Robux."         -> the ask goes in
    #   7.09s "Blocked."                         -> the guardrail card (~2.9s route)
    #   7.96s "Unlock the front door."           -> the second ask
    #  10.33s "That guardrail is not a promise." -> hold on the evidence
    def ask(text, t_set, t_send):
        # One JS write instead of typing: per-key CDP round-trips ran ~0.6 s
        # each under load and blew the scene twice. The composer shows the ask
        # instantly; the page's "heard" quote carries the beat on screen.
        inp = q(pg, "#askText")
        if inp:
            safe(sc, lambda: sc.click_el(inp, ms=120, settle=0.02))
        sc.sync(t_set)
        try:
            pg.evaluate(
                "(v) => { const i = document.querySelector('#askText');"
                " if (!i) return; i.value = v; i.focus();"
                " i.dispatchEvent(new Event('input', {bubbles: true})); }", text)
        except Exception:
            try:
                pg.keyboard.type(text, delay=12)
            except Exception:
                pass
        sc.sync(t_send)
        # The page ignores a send while it is still answering — retry until the
        # composer clears (each pass also fires the plain DOM click).
        for _ in range(5):
            send = q(pg, "#askSend")
            if send:
                robust(sc, send, ms=120, settle=0.08)
            pg.wait_for_timeout(260)
            try:
                left = (pg.evaluate(
                    "() => (document.querySelector('#askText')||{}).value || '") or "").strip()
            except Exception:
                left = ""
            if left != text.strip():
                break
            try:
                pg.evaluate("() => document.querySelector('#askSend')?.click()")
            except Exception:
                pass
            pg.wait_for_timeout(300)

    def wait_answer(prev, until, ms_hard=6000):
        t_cap = time.monotonic() + ms_hard / 1000.0
        while time.monotonic() < t_cap and sc.el() < until:
            try:
                txt = pg.evaluate("() => (document.querySelector('#response')||{}).innerText || ''")
                if len((txt or "").strip()) > 60 and (txt or "").strip() != prev:
                    return True
            except Exception:
                pass
            pg.wait_for_timeout(140)
        return False

    quiet(pg)

    def _brain_local(route, request):
        # The household's configured cloud brain is timing out tonight (25 s
        # 504s). Hearth's built-in agentic engine answers the same guardrail
        # blocks in ~200 ms — the same engine the card footer names.
        try:
            payload = json.loads(request.post_data or "{}")
            payload["provider"] = "local"
            route.continue_(post_data=json.dumps(payload))
        except Exception:
            try:
                route.continue_()
            except Exception:
                pass

    pg.route(re.compile(r"/api/chat$"), _brain_local)
    sc.goto(BASE + "/echo", settle=0.6)
    ready = sc.el()
    sc.t0 += (ready - 0.8)                 # scripted t=0.8 is "page ready" (trim anchor)
    print(f"    s12 ready at {ready:.2f}s -> trim from {ready - 0.8:.2f}s")
    sc.sync(1.0)
    gear = q(pg, "#settingsBtn")
    if gear:
        safe(sc, lambda: sc.to_el(gear, ms=520))
    sc.sync(1.95)
    if gear:
        safe(sc, lambda: sc.click_el(gear, ms=200, settle=0.15))
    # the sheet rises: wait until the Profile row is visible AND still —
    # gliding at a moving target is what threw "glide interrupted" last take
    t_cap = time.monotonic() + 3.0
    last_y = None
    while time.monotonic() < t_cap and sc.el() < 2.65:
        try:
            b = pg.locator("#personaToggleBtn")
            if b.count() and b.first.is_visible():
                y = b.first.bounding_box()["y"]
                if last_y is not None and abs(y - last_y) < 1.5:
                    break
                last_y = y
        except Exception:
            pass
        pg.wait_for_timeout(140)
    sc.sync(2.72)
    pers = q(pg, "#personaToggleBtn")
    if pers:
        safe(sc, lambda: sc.to_el(pers, ms=380))
    sc.sync(2.95)                                      # VO: "Switch to Leo, age nine."
    if pers:
        for _ in range(3):
            try:
                sc.click_el(pers, ms=200, settle=0.22)
                break
            except Exception as e:
                print(f"    warn(persona): {type(e).__name__}")

    def _persona():
        try:
            return pg.evaluate(
                "() => { const b = document.querySelector('#personaToggleBtn');"
                " return b ? (b.innerText || '').trim() : ''; }")
        except Exception:
            return ""

    # verify the flip (short patience: with the loop unblocked the POST is ~10 ms)
    t_cap = time.monotonic() + 1.5
    while time.monotonic() < t_cap and "Leo" not in _persona():
        pg.wait_for_timeout(140)
    if "Leo" not in _persona():
        try:
            pg.evaluate("() => document.querySelector('#personaToggleBtn')?.click()")
            print("    persona via JS fallback")
        except Exception:
            pass
    sc.sync(3.6)
    cls = q(pg, "#settingsCloseBtn")
    if cls:
        for _ in range(3):
            try:
                sc.click_el(cls, ms=240, settle=0.12)
                break
            except Exception as e:
                print(f"    warn(close): {type(e).__name__}")

    def _sheet_up():
        try:
            return pg.evaluate(
                "() => { const p = document.querySelector('#settingsPanel');"
                " return !!(p && !p.hidden); }")
        except Exception:
            return False

    t_cap = time.monotonic() + 1.2
    while time.monotonic() < t_cap and _sheet_up():
        pg.wait_for_timeout(120)
    if _sheet_up():
        try:
            pg.evaluate("() => document.querySelector('#settingsCloseBtn')?.click()")
            print("    sheet close via JS fallback")
        except Exception:
            pass
    prev = pg.evaluate("() => (document.querySelector('#response')||{}).innerText || ''")
    ask("Buy five thousand Robux.", 4.6, 4.8)          # VO: "Buy five thousand Robux."
    wait_answer(prev, 7.4)                             # card 1 on screen first
    sc.sync(sc.el() + 2.2)                             # let the first block be read
    sc.gl(1210, 560, ms=500)                            # across the guardrail card
    prev = pg.evaluate("() => (document.querySelector('#response')||{}).innerText || ''")
    ask("Unlock the front door.", 8.6, 8.8)            # VO: "Unlock the front door."
    wait_answer(prev, 11.0)
    sc.sync(10.8)
    sc.gl(1250, 620, ms=600)                            # hold on the second block
    sc.sync(12.4)
    sc.gl(1140, 700, ms=400)
    sc.sync(13.4)
    sc.gl(1010, 780, ms=350)
    sc.sync(15.2)


SCENES = [("s01", s01), ("s02", s02), ("s03", s03), ("s04", s04),
          ("s06", s06), ("s07", s07), ("s08", s08), ("s09", s09),
          ("s10", s10), ("s11", s11), ("s12", s12)]


def main():
    global MOVE_COST
    only = set(sys.argv[1:]) or None
    ds = {s["id"]: s for s in json.load(open(f"{ROOT}/demo_film/durations.json"))["scenes"]}
    os.makedirs(RAW, exist_ok=True)
    actuals = json.load(open(f"{ROOT}/demo_film/actuals.json")) if os.path.exists(f"{ROOT}/demo_film/actuals.json") else {}
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=CHROME,
            args=["--no-sandbox", "--hide-scrollbars", "--autoplay-policy=no-user-gesture-required"])
        # measure mouse.move round-trip cost (inform glide step count)
        probe_ctx = browser.new_context(viewport=VIEW)
        pp = probe_ctx.new_page()
        pp.goto("about:blank")
        t0 = time.monotonic()
        for i in range(6):
            pp.mouse.move(400 + i * 50, 300 + i * 30)
        MOVE_COST = max(0.01, (time.monotonic() - t0) / 6)
        probe_ctx.close()
        print(f"move round-trip ~{MOVE_COST*1000:.0f}ms")
        _snapshot()
        for sid, fn in SCENES:
            if only and sid not in only:
                continue
            meta = ds[sid]
            target = meta["total_s"]
            d = f"{RAW}/{sid}"
            shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
            ctx = browser.new_context(viewport=VIEW, record_video_dir=d, record_video_size=VIEW)
            # HEARTH_NOCURSOR_SCENES=s01,s09 records matching scenes without the
            # cursor overlay (used to keep a cut consistent when some scenes
            # were captured before the CSP-proof overlay landed).
            _skip = {x.strip() for x in os.environ.get("HEARTH_NOCURSOR_SCENES", "").split(",") if x.strip()}
            if sid not in _skip:
                ctx.add_init_script(CURSOR_JS)
            pg = ctx.new_page()
            t0 = time.monotonic()
            sc = Scene(pg, target)
            try:
                fn(sc, pg)
            except Exception as e:
                print(f"[{sid}] action warn: {type(e).__name__}: {str(e)[:140]}")
            if sid == "s07":
                target = max(target, sc.el() + 1.3)
            rem = target - sc.el() - 0.35
            if rem > 0:
                pg.wait_for_timeout(int(rem * 1000))
            # encoder tail cushion: Playwright's video writer lags wall clock by
            # up to ~2.5s under load, so keep recording past the target and let
            # merge.py's trim=0:T discard the extra — cheaper than a re-take.
            pg.wait_for_timeout(3200)
            ctx.close()
            actuals[sid] = round(time.monotonic() - t0, 2)
            files = glob.glob(f"{d}/*.webm")
            print(f"[{sid}] {meta['slug']:10s} target {target:6.2f}s actual {actuals[sid]:6.2f}s "
                  f"file {'ok' if files else 'MISSING'}")
        browser.close()
    json.dump(actuals, open(f"{ROOT}/demo_film/actuals.json", "w"), indent=1)
    print("done")


if __name__ == "__main__":
    main()
