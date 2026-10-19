#!/usr/bin/env python3
"""Hearth demo film — live recorder v2. Scene-clock driven (robust to slow CDP
under video recording): every action is anchored to absolute scene time."""
import glob
import json
import os
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
    sc.goto(BASE + "/web2/", settle=0.8)
    sc.sync(3.4)
    tab = q(pg, '.tab[data-view="approvals"]')
    if tab:
        safe(sc, lambda: sc.click_el(tab))
    sc.sync(5.8)
    card = q(pg, ".intent", 0)
    if card:
        safe(sc, lambda: sc.to_el(card, dy=-40, ms=700))
    sc.sync(8.6); sc.wheel(150, ms=1000)
    sc.sync(11.0)
    btn = q(pg, ".intent .btn-primary", 0) or q(pg, ".intent button", 0)
    if btn:
        safe(sc, lambda: sc.click_el(btn))
    sc.sync(14.0)
    cnt = q(pg, "#apprCount")
    if cnt:
        safe(sc, lambda: sc.to_el(cnt, ms=700))
    sc.sync(16.6); sc.gl(1120, 640, ms=800)
    sc.sync(18.4); sc.gl(1010, 720, ms=700)


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
    # Anchored to the s07 VO (edge-tts sentence timings, +0.42s merge offset):
    #   <0.47s  intro "And when Hearth meets a need nobody coded..."
    #   11.93s  "Watch."                        -> click Teach it
    #   12.80s  "Intent understood." ...        -> drift down the evidence
    #   20.86s  "Then mounted, live - as tool fifty five." -> click Call it now
    #   24.26s  "Nothing was shipped..."        -> count pill + tool catalog
    #   27.00s  "And every step is on the record." -> audit hash
    sc.goto(BASE + "/web2/", settle=0.6)
    sc.sync(2.6)
    tab = q(pg, '.tab[data-view="home"]')
    if tab:
        safe(sc, lambda: sc.click_el(tab, settle=0.15))
    sc.sync(3.4)
    panel = q(pg, "#forgePanel")
    if panel:
        try:
            panel.evaluate("el => el.scrollIntoView({behavior:'smooth', block:'start'})")
        except Exception:
            pass
    sc.sync(6.0)                                # panel settles: "a rule that only your household has"
    inp = q(pg, "#forgeInput")
    if inp:
        safe(sc, lambda: sc.to_el(inp, ms=800))
    sc.sync(7.6)
    sc.gl(sc.x + 150, sc.y + 6, ms=1000)        # trace along the rule text
    sc.sync(11.35)                              # "...it doesn't wait for an update. It writes the tool itself."
    go = q(pg, "#forgeGo")
    if go:
        safe(sc, lambda: sc.to_el(go, ms=380))
    sc.sync(11.8)                               # VO: "Watch."
    if go:
        safe(sc, lambda: sc.click_el(go, ms=260, settle=0.15))
    deadline = time.monotonic() + 26            # fail fast if the forge misfires
    appeared = False
    while time.monotonic() < deadline:
        out = pg.locator("#forgeOut")
        try:
            if out.count() and out.is_visible():
                appeared = True
                break
        except Exception:
            pass
        pg.wait_for_timeout(150)
    if appeared:
        sc.sync(12.5)
        sc.gl(sc.x - 320, sc.y + 64, ms=500)    # clear the button; watch the chips
        outl = q(pg, "#forgeOut")
        if outl:
            try:
                outl.evaluate("el => el.scrollIntoView({behavior:'smooth', block:'center'})")
            except Exception:
                pass
        sc.sync(14.6)                           # "Understanding / Writing the plan" beat
        code = q(pg, "#forgeCode")
        if code:
            safe(sc, lambda: sc.to_el(code, ms=850))       # generated source appears
        sc.sync(16.6)
        safety = q(pg, "#forgeSafety")
        if safety:
            safe(sc, lambda: sc.to_el(safety, ms=750))     # "A safety gate."
        sc.sync(18.4)
        tool = q(pg, "#forgeToolName")
        if tool:
            safe(sc, lambda: sc.to_el(tool, ms=750))       # "Source verified." the mounted name
        sc.sync(20.3)
        call = q(pg, "#forgeCall")
        if call:
            safe(sc, lambda: sc.to_el(call, ms=520))
        sc.sync(21.05)                          # VO: "Then mounted, live -"
        if call:
            safe(sc, lambda: sc.click_el(call, ms=180, settle=0.1))
            try:
                pg.wait_for_function(
                    "() => { const r = document.querySelector('#forgeResult');"
                    " return r && !r.hidden && r.innerText &&"
                    " /savings|applied|execut/i.test(r.innerText); }", timeout=12000)
            except Exception:
                pg.wait_for_timeout(2200)
        sc.sync(23.6)                           # "...as tool fifty five."
        cnt = q(pg, "#forgeCount")
        if cnt:
            safe(sc, lambda: sc.to_el(cnt, ms=800))        # 54 -> 55 abilities live
        sc.sync(25.3)
        cat = q(pg, "#forgeCatalog")
        if cat:
            safe(sc, lambda: sc.to_el(cat, ms=800))        # "Nothing was shipped."
        sc.sync(26.9)
        proof = q(pg, "#forgeProof")
        if proof:
            safe(sc, lambda: sc.to_el(proof, ms=700))      # "every step is on the record"
        sc.sync(30.4)


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


SCENES = [("s01", s01), ("s02", s02), ("s03", s03), ("s04", s04), ("s05", s05),
          ("s06", s06), ("s07", s07), ("s08", s08), ("s09", s09), ("s10", s10)]


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
