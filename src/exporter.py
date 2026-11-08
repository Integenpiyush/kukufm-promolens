"""
Export engine for PromoLens: Generates JSON, CSV, and industry-standard EDL (Edit Decision List) files.
"""
import os
import csv
import json
from typing import List, Dict, Any
from .models import RankedPromo

def format_time_to_timecode(sec: float, fps: int = 30) -> str:
    """Converts float seconds into SMPTE timecode (HH:MM:SS:FF)."""
    hrs = int(sec // 3600)
    mins = int((sec % 3600) // 60)
    secs = int(sec % 60)
    frames = int(round((sec - int(sec)) * fps))
    if frames >= fps:
        frames = fps - 1
    return f"{hrs:02d}:{mins:02d}:{secs:02d}:{frames:02d}"

class PromoExporter:
    """Exports ranked promos into JSON, CSV, and video editor EDLs."""

    @staticmethod
    def export_json(promos: List[RankedPromo], output_path: str):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        data = [p.to_dict() for p in promos]
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @staticmethod
    def export_csv(promos: List[RankedPromo], output_path: str):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        headers = [
            "Rank", "Episode", "Promo ID", "Campaign Funnel", "Duration (s)",
            "Segment Timestamps", "Hook (<3s)", "Cliffhanger Cut", "Why It Works",
            "Hook Score", "Cliffhanger Score", "Clarity Score", "Composite Score"
        ]
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for p in promos:
                seg_times = " + ".join([f"[{s.start_str} - {s.end_str}]" for s in p.segments])
                writer.writerow([
                    p.global_rank,
                    p.episode_number,
                    p.promo_id,
                    p.campaign_category,
                    f"{p.total_duration_sec:.1f}",
                    seg_times,
                    p.hook_description,
                    p.cliffhanger_description,
                    p.why_it_works,
                    f"{p.hook_score:.1f}",
                    f"{p.cliffhanger_score:.1f}",
                    f"{p.standalone_clarity_score:.1f}",
                    f"{p.composite_score:.2f}"
                ])

    @staticmethod
    def export_edl(promo: RankedPromo, output_dir: str):
        """Generates standard CMX 3600 Edit Decision List for NLEs (Premiere / DaVinci)."""
        os.makedirs(output_dir, exist_ok=True)
        file_name = f"Promo_{promo.global_rank:02d}_EP{promo.episode_number:02d}.edl"
        edl_path = os.path.join(output_dir, file_name)
        
        lines = [
            f"TITLE: PROMO_RANK_{promo.global_rank:02d}_EP{promo.episode_number:02d}",
            "FCM: NON-DROP FRAME",
            ""
        ]
        
        record_in = 0.0
        for idx, seg in enumerate(promo.segments, start=1):
            src_in = format_time_to_timecode(seg.start_sec)
            src_out = format_time_to_timecode(seg.end_sec)
            rec_in = format_time_to_timecode(record_in)
            record_out = record_in + seg.duration_sec
            rec_out = format_time_to_timecode(record_out)
            
            # Format: 001  AX       V     C        00:00:11:10 00:00:45:00 00:00:00:00 00:00:33:20
            lines.append(f"{idx:03d}  AX       V     C        {src_in} {src_out} {rec_in} {rec_out}")
            lines.append(f"* FROM CLIP: EPISODE_{promo.episode_number:02d}.mp4")
            lines.append(f"* HOOK: {promo.hook_description[:60]}")
            lines.append(f"* CLIFFHANGER: {promo.cliffhanger_description[:60]}")
            lines.append("")
            record_in = record_out
            
        with open(edl_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))
