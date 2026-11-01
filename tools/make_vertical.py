"""16:9 成片 → 9:16 竖版（模糊铺底 + 居中正片），供抖音/视频号使用。"""
import subprocess, sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
ch = sys.argv[1]
src = ROOT / "final-videos" / ch / f"{ch}-bilibili-safe.mp4"
out = ROOT / "final-videos" / ch / f"{ch}-vertical.mp4"
vf = ("[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
      "gblur=sigma=28,eq=brightness=-0.08[b];"
      "[0:v]scale=1080:-2[v];[b][v]overlay=(W-w)/2:(H-h)/2")
cmd = ["ffmpeg","-y","-i",str(src),"-filter_complex",vf,"-map","0:a?",
       "-c:v","libx264","-crf","23","-preset","veryfast","-c:a","aac","-b:a","128k",str(out)]
print("[vert]", ch, "->", out.name, flush=True)
subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("[done]", out.name, out.stat().st_size // 1024, "KB", flush=True)
