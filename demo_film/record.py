#!/usr/bin/env python3
"""Hearth demo film — live recorder v2. Scene-clock driven (robust to slow CDP
under video recording): every action is anchored to absolute scene time."""
import json, os, shutil, time, glob, sys
from playwright.sync_api import sync_playwright

ROOT = "/home/k/Prototype/Amazon"
RAW = f"{ROOT}/demo_film/raw"
BASE = "http://127.0.0.1:8787"
CHROME = "/home/k/.local/bin/google-chrome"
VIEW = {"width": 1920, "height": 1080}

CURSOR_JS = r"""
(() => {
  const st = document.createElement('style');
  st.textContent = `
    * { cursor: none !important; }
    #__cur { position: fixed; z-index: 2147483647; width: 40px; height: 40px;
      margin: -20px 0 0 -20px; border-radius: 50%;
      border: 2.5px solid rgba(255,255,255,.92);
      box-shadow: 0 0 0 1.5px rgba(0,0,0,.35), 0 0 20px rgba(255,120,40,.55);
      background: rgba(255,120,40,.16); pointer-events: none; will-change: left, top;
      transition: left .13s linear, top .13s linear, transform .09s ease, background .09s ease; }
    #__cur.press { transform: scale(.52); background: rgba(255,120,40,.55); }
    #__dot { position: fixed; z-index: 2147483647; width: 6px; height: 6px;
      margin: -3px 0 0 -3px; border-radius: 50%; background: #ff9a55;
      pointer-events: none; box-shadow: 0 0 10px rgba(255,150,80,.9); }`;
  const add = () => {
    document.head.appendChild(st);
    const cur = document.createElement('div'); cur.id = '__cur';
    const dot = document.createElement('div'); dot.id = '__dot';
    document.documentElement.append(cur, dot);
    const move = (e) => {
      cur.style.left = e.clientX + 'px'; cur.style.top = e.clientY + 'px';
      dot.style.left = e.clientX + 'px'; dot.style.top = e.clientY + 'px';
    };
    addEventListener('mousemove', move, true);
    addEventListener('mousedown', () => cur.classList.add('press'), true);
    addEventListener('mouseup', () => cur.classList.remove('press'), true);
    move({ clientX: 960, clientY: 540 });
  };
  if (document.readyState === 'loading') addEventListener('DOMContentLoaded', add); else add();
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
                return
            time.sleep(max(0.0, dt - (time.monotonic() - st)))
            if self.el() > self.total - 0.4:
                return

    def to_el(self, loc, dx=0, dy=0, ms=700):
        box = loc.bounding_box()
        if not box:
            raise RuntimeError("no box")
        self.gl(box["x"] + box["width"] / 2 + dx, box["y"] + box["height"] / 2 + dy, ms=ms)
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
    sc.sync(2.2); sc.gl(620, 300, ms=1000)
    sc.sync(3.6); sc.gl(1270, 400, ms=1100)
    sc.sync(5.2); sc.gl(940, 520, ms=800)
    sc.sync(6.4); sc.wheel(430, ms=1500)
    sc.sync(8.4); sc.wheel(440, ms=1500)
    sc.sync(10.4); sc.wheel(440, ms=1500)
    sc.sync(12.2); sc.wheel(260, ms=1100)
    sc.sync(13.4); sc.gl(720, 830, ms=800)
    sc.sync(14.2); sc.gl(1190, 700, ms=800)


def s02(sc, pg):
    sc.goto(BASE + "/echo", settle=0.6)
    sc.sync(2.4)
    inp = q(pg, "#askText")
    if inp:
        safe(sc, lambda: sc.click_el(inp))
        pg.keyboard.type("Save me $800.", delay=55)
    sc.sync(5.3)
    send = q(pg, "#askSend")
    if send:
        safe(sc, lambda: sc.click_el(send))
    try:
        pg.wait_for_function(
            "() => { const r = document.querySelector('#response');"
            " return r && r.innerText && r.innerText.trim().length > 20; }", timeout=12000)
    except Exception:
        pass
    sc.sync(9.6)
    chip = q(pg, '[data-mode="fullscreen"]')
    if chip:
        safe(sc, lambda: sc.click_el(chip, settle=0.25))
    sc.sync(12.6)
    chip = q(pg, '[data-mode="hydrated"]')
    if chip:
        safe(sc, lambda: sc.click_el(chip, settle=0.25))
    sc.sync(15.6)
    chip = q(pg, '[data-mode="voice-only"]')
    if chip:
        safe(sc, lambda: sc.click_el(chip, settle=0.25))
    sc.sync(18.4)
    chip = q(pg, '[data-mode="inline"]')
    if chip:
        safe(sc, lambda: sc.click_el(chip, settle=0.25))
    sc.sync(20.0); sc.gl(760, 800, ms=800)


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
    sc.goto(BASE + "/web2/", settle=0.8)
    sc.sync(2.7)
    tab = q(pg, '.tab[data-view="home"]')
    if tab:
        safe(sc, lambda: sc.click_el(tab, settle=0.2))
    sc.sync(3.4)
    panel = q(pg, "#forgePanel")
    if panel:
        try:
            panel.evaluate("el => el.scrollIntoView({behavior:'smooth', block:'center'})")
        except Exception:
            pass
    sc.sync(5.2)
    inp = q(pg, "#forgeInput")
    if inp:
        safe(sc, lambda: sc.to_el(inp, ms=700))
    sc.sync(8.0)
    go = q(pg, "#forgeGo")
    if go:
        safe(sc, lambda: sc.click_el(go, settle=0.2))
    deadline = sc.el() + 85
    appeared = False
    while time.monotonic() - sc.t0 < deadline:
        out = pg.locator("#forgeOut")
        try:
            if out.count() and out.is_visible():
                appeared = True
                break
        except Exception:
            pass
        safe(sc, lambda: sc.gl(sc.x + 14, min(980, sc.y + 24), ms=600))
        pg.wait_for_timeout(500)
    if appeared:
        sc.sync(sc.el() + 2.0)
        res = q(pg, "#forgeResult")
        if res:
            safe(sc, lambda: sc.to_el(res, ms=700))
        sc.sync(sc.el() + 1.6)
        call = q(pg, "#forgeCall")
        if call:
            safe(sc, lambda: sc.click_el(call))
            try:
                pg.wait_for_function(
                    "() => { const r = document.querySelector('#forgeResult');"
                    " return r && !r.hidden && r.innerText &&"
                    " /savings|applied|execut|ok/i.test(r.innerText); }", timeout=22000)
            except Exception:
                pg.wait_for_timeout(3000)
            sc.sync(sc.el() + 1.2)
            sc.gl(1180, 760, ms=700)
        cnt = q(pg, "#forgeCount")
        if cnt:
            safe(sc, lambda: sc.to_el(cnt, ms=700))
        sc.sync(sc.el() + 1.4)


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


SCENES = [("s01", s01), ("s02", s02), ("s03", s03), ("s04", s04), ("s05", s05),
          ("s06", s06), ("s07", s07), ("s08", s08), ("s09", s09)]


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
