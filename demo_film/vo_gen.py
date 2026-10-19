#!/usr/bin/env python3
"""Generate the film's voiceover with edge-tts and rebuild durations.json.

Reads vo.json (scene texts + tails), synthesizes demo_film/vo/{id}.mp3,
measures each mp3, and writes durations.json (vo_s + total_s per scene).
Scene totals drive both the recorder's pacing and the merge's trims.
"""
import json
import os
import subprocess

ROOT = "/home/k/Prototype/Amazon"
FILM = f"{ROOT}/demo_film"
CFG_PATH = os.environ.get("HEARTH_VO_CFG", f"{FILM}/vo.json")
OUT_PATH = os.environ.get("HEARTH_DUR_OUT", f"{FILM}/durations.json")


def dur(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", path], capture_output=True, text=True)
    return float(out.stdout.strip())


def main():
    cfg = json.load(open(CFG_PATH))
    voice = cfg["fallback_voice"]["voice"]
    rate = cfg["fallback_voice"]["rate"]
    os.makedirs(f"{FILM}/vo", exist_ok=True)
    scenes, total = [], 0.0
    for sc in cfg["scenes"]:
        mp3 = f"{FILM}/vo/{sc['id']}.mp3"
        srt = f"{FILM}/vo/{sc['id']}.srt"
        r = subprocess.run(["edge-tts", "--voice", voice, f"--rate={rate}",
                           "--write-subtitles", srt,
                           "--text", sc["text"], "--write-media", mp3],
                           capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit(f"edge-tts failed for {sc['id']}: {r.stderr[-300:]}")
        vo_s = round(dur(mp3), 2)
        total_s = round(vo_s + float(sc.get("tail", 2.0)), 2)
        total += total_s
        scenes.append({**sc, "vo_s": vo_s, "total_s": total_s})
        print(f"{sc['id']} vo={vo_s:6.2f}s tail={sc['tail']:>4} total={total_s:6.2f}s")
    out = {k: v for k, v in cfg.items() if k != "scenes"}
    out["scenes"] = scenes
    json.dump(out, open(OUT_PATH, "w"), indent=1)
    print(f"TOTAL {total:.2f}s ({total / 60:.2f} min) -> {OUT_PATH}")


if __name__ == "__main__":
    main()
