"""
Map Animation — "uzaydan konuma iniş" seyahat girişi (ücretsiz, OpenStreetMap, key'siz).

Google Maps ToS-kısıtlı (monetize video). OSM (ODbL, atıfla serbez) kullanılır:
- Geocode: Nominatim → lat/lon
- Harita görselleri: staticmap (OSM tile render), artan zoom seviyeleri, işaretçili
- Animasyon: ffmpeg crossfade + hafif zoom → ülke→bölge→şehir→pin iniş

Atıf notu: açıklamaya "Map data © OpenStreetMap contributors" eklenir.
"""
from __future__ import annotations
import os
import json
import subprocess
import urllib.request
import urllib.parse
from typing import Optional, Tuple, List

_UA = {"User-Agent": "ZezeLabs-Travel/1.0 (contact: media@zezelabs)"}
OSM_ATTRIBUTION = "Map data © OpenStreetMap contributors"


def geocode(place: str) -> Optional[Tuple[float, float]]:
    try:
        u = "https://nominatim.openstreetmap.org/search?format=json&limit=1&q=" + urllib.parse.quote(place)
        r = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers=_UA), timeout=20).read())
        return (float(r[0]["lat"]), float(r[0]["lon"])) if r else None
    except Exception:
        return None


def _render(lat: float, lon: float, zoom: int, out: str, W: int, H: int) -> Optional[str]:
    try:
        from staticmap import StaticMap, CircleMarker
        m = StaticMap(W, H, url_template="https://tile.openstreetmap.org/{z}/{x}/{y}.png")
        m.add_marker(CircleMarker((lon, lat), "#e02020", 16))
        m.add_marker(CircleMarker((lon, lat), "#ffffff", 26))
        img = m.render(zoom=zoom)
        img.save(out)
        return out if os.path.exists(out) else None
    except Exception:
        return None


def build_map_intro(place: str, out_path: str, vertical: bool = True,
                    duration: float = 7.0, zooms: Optional[List[int]] = None) -> Optional[dict]:
    """Destinasyon → 'uzaydan pin'e iniş' animasyonu (crossfade'li zoom seviyeleri)."""
    coord = geocode(place)
    if not coord:
        return {"success": False, "error": f"geocode başarısız: {place}"}
    lat, lon = coord
    work = os.path.dirname(out_path)
    os.makedirs(work, exist_ok=True)
    W, H = (1080, 1920) if vertical else (1920, 1080)
    zooms = zooms or [3, 6, 9, 12]  # dünya → ülke → bölge → şehir
    # her zoom için harita + hafif Ken Burns'lü klip
    per = duration / len(zooms)
    clips = []
    for i, z in enumerate(zooms):
        png = os.path.join(work, f"map_z{z}.png")
        if not _render(lat, lon, z, png, W, H):
            continue
        clip = os.path.join(work, f"map_c{i}.mp4")
        vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,"
              f"zoompan=z='min(zoom+0.0015,1.25)':d={int(per*30)}:s={W}x{H}:fps=30,"
              f"eq=contrast=1.05:saturation=1.1")
        subprocess.run(["ffmpeg", "-y", "-loop", "1", "-i", png, "-t", str(per), "-vf", vf,
                        "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", clip],
                       capture_output=True, timeout=120)
        if os.path.exists(clip) and os.path.getsize(clip) > 5000:
            clips.append(clip)
    if not clips:
        return {"success": False, "error": "harita klipleri üretilemedi (tile/ağ?)"}
    # crossfade zincir (iniş hissi)
    cur, off = clips[0], per - 0.6
    for k in range(1, len(clips)):
        nx = os.path.join(work, f"map_xf{k}.mp4")
        fc = f"[0:v][1:v]xfade=transition=fadewhite:duration=0.6:offset={off}[v]"
        subprocess.run(["ffmpeg", "-y", "-i", cur, "-i", clips[k], "-filter_complex", fc, "-map", "[v]",
                        "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", nx],
                       capture_output=True, timeout=300)
        if os.path.exists(nx) and os.path.getsize(nx) > 5000:
            cur = nx; off += (per - 0.6)
        else:
            break
    subprocess.run(["ffmpeg", "-y", "-i", cur, "-c", "copy", out_path], capture_output=True, timeout=120)
    ok = os.path.exists(out_path)
    return {"success": ok, "path": out_path if ok else cur, "coord": [lat, lon],
            "attribution": OSM_ATTRIBUTION}
