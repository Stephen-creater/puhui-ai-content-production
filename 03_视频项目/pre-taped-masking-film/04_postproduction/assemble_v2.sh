#!/bin/zsh
set -euo pipefail

ROOT="${0:A:h}"
PROJECT="${ROOT:h}"
VISUAL_BANK="$PROJECT/03_generation/visual-bank-v1"
VOICE="$ROOT/voice"
CTA="$PROJECT/03_generation/native-audio-cta/clips/variant-01/scene-01.mp4"
BASE="$PROJECT/05_deliverables/v2/pre-taped-film-ad-v2-base.mp4"
FINAL="$PROJECT/05_deliverables/v2/pre-taped-film-ad-v2-final.mp4"

ffmpeg -y -hide_banner \
  -i "$VISUAL_BANK/clips/variant-01/scene-05.mp4" \
  -i "$VISUAL_BANK/clips/variant-01/scene-06.mp4" \
  -i "$VISUAL_BANK/clips/variant-01/scene-01.mp4" \
  -i "$VISUAL_BANK/clips/variant-01/scene-02.mp4" \
  -i "$VISUAL_BANK/clips/variant-01/scene-03.mp4" \
  -i "$VISUAL_BANK/clips/variant-01/scene-04.mp4" \
  -i "$VISUAL_BANK/clips/variant-01/scene-05.mp4" \
  -i "$VISUAL_BANK/clips/variant-01/scene-06.mp4" \
  -i "$CTA" \
  -i "$VOICE/vo01_hook.mp3" \
  -i "$VOICE/vo02_product.mp3" \
  -i "$VOICE/vo03_tape.mp3" \
  -i "$VOICE/vo04_pull.mp3" \
  -i "$VOICE/vo05_tear.mp3" \
  -i "$VOICE/vo06_protect.mp3" \
  -i "$VOICE/vo07_peel.mp3" \
  -filter_complex "
    [0:v]trim=start=0:end=1.5,setpts=PTS-STARTPTS,scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=24,format=yuv420p[hooka];
    [1:v]trim=start=2.5:end=4,setpts=PTS-STARTPTS,scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=24,format=yuv420p[hookb];
    [hooka][hookb]concat=n=2:v=1:a=0[sv0];
    [2:v]trim=duration=4,setpts=PTS-STARTPTS,scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=24,format=yuv420p,tpad=stop_mode=clone:stop_duration=1[sv1];
    [3:v]trim=duration=4,setpts=PTS-STARTPTS,scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=24,format=yuv420p[sv2];
    [4:v]trim=duration=4,setpts=PTS-STARTPTS,scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=24,format=yuv420p[sv3];
    [5:v]trim=duration=4,setpts=PTS-STARTPTS,scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=24,format=yuv420p,tpad=stop_mode=clone:stop_duration=0.2[sv4];
    [6:v]trim=duration=3.2,setpts=PTS-STARTPTS,scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=24,format=yuv420p[sv5];
    [7:v]trim=duration=4,setpts=PTS-STARTPTS,scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=24,format=yuv420p,tpad=stop_mode=clone:stop_duration=0.4[sv6];
    [8:v]trim=duration=8,setpts=PTS-STARTPTS,scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=24,format=yuv420p[sv7];
    [sv0][sv1][sv2][sv3][sv4][sv5][sv6][sv7]concat=n=8:v=1:a=0[outv];
    [9:a]loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000,aformat=channel_layouts=stereo,apad,atrim=duration=3,asetpts=PTS-STARTPTS[sa0];
    [10:a]loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000,aformat=channel_layouts=stereo,apad,atrim=duration=5,asetpts=PTS-STARTPTS[sa1];
    [11:a]loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000,aformat=channel_layouts=stereo,apad,atrim=duration=4,asetpts=PTS-STARTPTS[sa2];
    [12:a]loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000,aformat=channel_layouts=stereo,apad,atrim=duration=4,asetpts=PTS-STARTPTS[sa3];
    [13:a]loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000,aformat=channel_layouts=stereo,apad,atrim=duration=4.2,asetpts=PTS-STARTPTS[sa4];
    [14:a]loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000,aformat=channel_layouts=stereo,apad,atrim=duration=3.2,asetpts=PTS-STARTPTS[sa5];
    [15:a]loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000,aformat=channel_layouts=stereo,apad,atrim=duration=4.4,asetpts=PTS-STARTPTS[sa6];
    [8:a]atrim=duration=8,loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000,aformat=channel_layouts=stereo,apad,atrim=duration=8,asetpts=PTS-STARTPTS[sa7];
    [sa0][sa1][sa2][sa3][sa4][sa5][sa6][sa7]concat=n=8:v=0:a=1[outa]
  " \
  -map '[outv]' -map '[outa]' \
  -c:v libx264 -preset medium -crf 18 -c:a aac -b:a 192k -movflags +faststart "$BASE"

python3 "$ROOT/render_overlays.py"

ffmpeg -y -hide_banner -i "$BASE" \
  -loop 1 -i "$ROOT/overlays/scene-01.png" \
  -loop 1 -i "$ROOT/overlays/scene-02.png" \
  -loop 1 -i "$ROOT/overlays/scene-03.png" \
  -loop 1 -i "$ROOT/overlays/scene-04.png" \
  -loop 1 -i "$ROOT/overlays/scene-05.png" \
  -loop 1 -i "$ROOT/overlays/scene-06.png" \
  -loop 1 -i "$ROOT/overlays/scene-07.png" \
  -loop 1 -i "$ROOT/overlays/scene-08.png" \
  -filter_complex "
    [0:v][1:v]overlay=0:0:enable='between(t,0,3)'[v1];
    [v1][2:v]overlay=0:0:enable='between(t,3,8)'[v2];
    [v2][3:v]overlay=0:0:enable='between(t,8,12)'[v3];
    [v3][4:v]overlay=0:0:enable='between(t,12,16)'[v4];
    [v4][5:v]overlay=0:0:enable='between(t,16,20.2)'[v5];
    [v5][6:v]overlay=0:0:enable='between(t,20.2,23.4)'[v6];
    [v6][7:v]overlay=0:0:enable='between(t,23.4,27.8)'[v7];
    [v7][8:v]overlay=0:0:enable='between(t,27.8,35.8)'[outv]
  " \
  -map '[outv]' -map 0:a -t 35.8 \
  -c:v libx264 -preset medium -crf 18 -c:a copy -movflags +faststart "$FINAL"

echo "$FINAL"
