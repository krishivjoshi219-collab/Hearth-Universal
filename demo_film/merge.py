#!/usr/bin/env python3
"""Hearth demo film — mux + concat + room-tone mix -> HEARTH_DEMO_FINAL.mp4"""
import json, os, subprocess, glob

ROOT = "/home/k/Prototype/Amazon"
FILM = f"{ROOT}/demo_film"
FPS = 30


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-800:])
    return r.stdout


def main():
    scenes = json.load(open(f"{FILM}/durations.json"))["scenes"]
    os.makedirs(f"{FILM}/scenes", exist_ok=True)
    parts, total = [], 0.0
    for sc in scenes:
        sid, T = sc["id"], sc["total_s"]
        total += T
        webm = glob.glob(f"{FILM}/raw/{sid}/*.webm")[0]
        vo = f"{FILM}/vo/{sid}.mp3"
        out = f"{FILM}/scenes/{sid}.mp4"
        fc = (
            f"[0:v]trim=0:{T},setpts=PTS-STARTPTS,"
            f"tpad=stop_mode=clone:stop_duration=8,fps={FPS},scale=1920:1080,setsar=1,"
            f"fade=t=in:st=0:d=0.35,fade=t=out:st={max(0, T - 0.7):.2f}:d=0.7[v];"
            f"[1:a]aresample=48000,adelay=420,apad,atrim=0:{T},asetpts=N/SR/TB[a]"
        )
        run(["ffmpeg", "-y", "-v", "error", "-i", webm, "-i", vo, "-filter_complex", fc,
             "-map", "[v]", "-map", "[a]", "-t", f"{T}",
             "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "192k", "-ar", "48000", out])
        parts.append(out)
        print(f"scene {sid}: {T:.2f}s muxed")
    lf = f"{FILM}/scenes/list.txt"
    open(lf, "w").write("\n".join(f"file '{p}'" for p in parts) + "\n")
    vid = f"{FILM}/scenes/_video_all.mp4"
    try:
        run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lf,
             "-c", "copy", vid])
    except Exception:
        run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lf,
             "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "192k", vid])
    final = f"{FILM}/HEARTH_DEMO_FINAL.mp4"
    fc = (f"[1:a]lowpass=f=120,volume=0.30[t];"
          f"[0:a][t]amix=inputs=2:duration=first:normalize=0,"
          f"afade=t=out:st={max(0, total - 2.2):.2f}:d=2.2[a]")
    run(["ffmpeg", "-y", "-v", "error", "-i", vid,
         "-f", "lavfi", "-i", f"anoisesrc=color=pink:amplitude=0.035:duration={total}",
         "-filter_complex", fc, "-map", "0:v", "-map", "[a]",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", final])
    dur = run(["ffprobe", "-v", "error", "-show_entries", "format=duration,size",
               "-of", "csv=p=0", final]).strip()
    print(f"FINAL: {final}\nduration,size => {dur}  (target {total:.1f}s)")


if __name__ == "__main__":
    main()
