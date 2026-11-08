"""
Screenplay parser for microdrama scripts.
Handles variations in casing, parenthetical emotions, and timestamp formats.
"""
import os
import re
from typing import List, Optional, Tuple
from .models import TimestampRange, ScriptElement, Scene, Episode

def parse_time_str_to_sec(time_str: str) -> float:
    """Converts MM:SS.ss or SS.ss into float seconds."""
    time_str = time_str.strip("()[] ")
    parts = time_str.split(":")
    if len(parts) == 2:
        minutes = float(parts[0])
        seconds = float(parts[1])
        return minutes * 60.0 + seconds
    elif len(parts) == 3:
        hours = float(parts[0])
        minutes = float(parts[1])
        seconds = float(parts[2])
        return hours * 3600.0 + minutes * 60.0 + seconds
    else:
        return float(parts[0])

def format_sec_to_time_str(sec: float) -> str:
    """Converts float seconds into MM:SS.ss string format."""
    mins = int(sec // 60)
    remaining_secs = sec - (mins * 60)
    return f"{mins:02d}:{remaining_secs:05.2f}"

class ScreenplayParser:
    """Deterministic parser for structured microdrama screenplay files."""

    TIME_REGEX = re.compile(r'Start:\s*\(?(\d{1,2}:\d{2}\.?\d*)\)?\s*\|\s*End:\s*\(?(\d{1,2}:\d{2}\.?\d*)\)?', re.IGNORECASE)
    SCENE_HEADER_REGEX = re.compile(r'^SCENE\s+(\d+)', re.IGNORECASE)
    SCENE_HEADING_REGEX = re.compile(r'^SCENE\s+HEADING:\s*(.+)', re.IGNORECASE)
    SCENE_START_REGEX = re.compile(r'^SCENE\s+START:\s*\(?(\d{1,2}:\d{2}\.?\d*)\)?', re.IGNORECASE)
    SCENE_END_REGEX = re.compile(r'^SCENE\s+END:\s*\(?(\d{1,2}:\d{2}\.?\d*)\)?', re.IGNORECASE)

    def parse_file(self, file_path: str) -> Episode:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return self.parse_text(content, file_path)

    def parse_text(self, text: str, file_path: str = "") -> Episode:
        lines = [line.rstrip() for line in text.splitlines()]
        
        # Episode metadata
        ep_num = 1
        logline = ""
        continuity = ""
        
        # Search metadata headers
        m_num = re.search(r'EPISODE NUMBER:\s*(?:Episode\s*)?(\d+)', text, re.IGNORECASE)
        if m_num:
            ep_num = int(m_num.group(1))
        elif file_path:
            # Fallback to filename: episode-001
            m_fn = re.search(r'episode-(\d+)', os.path.basename(file_path), re.IGNORECASE)
            if m_fn:
                ep_num = int(m_fn.group(1))
                
        m_log = re.search(r'EPISODE LOGLINE:\s*(.+)', text, re.IGNORECASE)
        if m_log:
            logline = m_log.group(1).strip()
            
        m_cont = re.search(r'CONTINUITY NOTES:\s*(.+)', text, re.IGNORECASE)
        if m_cont:
            continuity = m_cont.group(1).strip()

        # Parse scenes and elements
        scenes: List[Scene] = []
        current_scene: Optional[Scene] = None
        
        i = 0
        total_lines = len(lines)
        
        while i < total_lines:
            line = lines[i].strip()
            
            # Check scene divider
            m_scene = self.SCENE_HEADER_REGEX.match(line)
            if m_scene:
                if current_scene:
                    scenes.append(current_scene)
                scene_idx = int(m_scene.group(1))
                heading = "UNKNOWN HEADING"
                scene_start = 0.0
                scene_end = 0.0
                
                # Look ahead for heading, start, end
                j = i + 1
                while j < min(i + 10, total_lines):
                    next_l = lines[j].strip()
                    m_hd = self.SCENE_HEADING_REGEX.match(next_l)
                    if m_hd:
                        heading = m_hd.group(1).strip()
                    m_st = self.SCENE_START_REGEX.match(next_l)
                    if m_st:
                        scene_start = parse_time_str_to_sec(m_st.group(1))
                    m_en = self.SCENE_END_REGEX.match(next_l)
                    if m_en:
                        scene_end = parse_time_str_to_sec(m_en.group(1))
                    if "ACTIONS AND DIALOGUE:" in next_l.upper():
                        break
                    j += 1
                
                current_scene = Scene(
                    scene_number=scene_idx,
                    heading=heading,
                    timing=TimestampRange(
                        start_sec=scene_start,
                        end_sec=scene_end,
                        start_str=format_sec_to_time_str(scene_start),
                        end_str=format_sec_to_time_str(scene_end)
                    ),
                    elements=[]
                )
                i = j
                continue
            
            # Check element header: **CAMERA:**, **ACTION:**, **CHARACTER (EMOTION):**
            if line.startswith("**") and "**" in line[2:]:
                header_match = re.findall(r'\*\*([^*]+)\*\*', line)
                if header_match:
                    raw_header = header_match[0].strip().rstrip(':')
                    
                    # Next line should be timestamp
                    if i + 1 < total_lines:
                        time_line = lines[i+1].strip()
                        m_time = self.TIME_REGEX.search(time_line)
                        if m_time:
                            t_start = parse_time_str_to_sec(m_time.group(1))
                            t_end = parse_time_str_to_sec(m_time.group(2))
                            timing = TimestampRange(
                                start_sec=t_start,
                                end_sec=t_end,
                                start_str=format_sec_to_time_str(t_start),
                                end_str=format_sec_to_time_str(t_end)
                            )
                            
                            # Content lines follow until next element or header
                            content_lines = []
                            k = i + 2
                            while k < total_lines:
                                cand_l = lines[k].strip()
                                if cand_l.startswith("**") and "**" in cand_l[2:]:
                                    break
                                if self.SCENE_HEADER_REGEX.match(cand_l):
                                    break
                                if cand_l.startswith("--- SCRIPT END") or cand_l.startswith("--- SCRIPT START"):
                                    break
                                if cand_l:
                                    content_lines.append(cand_l)
                                k += 1
                            
                            content_text = " ".join(content_lines).strip().strip('"')
                            
                            # Determine type and character/emotion
                            base_type = re.sub(r'\(.*?\)', '', raw_header).strip().rstrip(':').upper()
                            is_off_screen = "O.S." in raw_header.upper() or "OFF-SCREEN" in raw_header.upper()
                            
                            if base_type in ['CAMERA']:
                                elem = ScriptElement(
                                    element_type="CAMERA",
                                    timing=timing,
                                    content=content_text
                                )
                            elif base_type in ['ACTION']:
                                elem = ScriptElement(
                                    element_type="ACTION",
                                    timing=timing,
                                    content=content_text
                                )
                            elif base_type in ['SOUND FX', 'MUSIC', 'SFX']:
                                elem = ScriptElement(
                                    element_type="SOUND FX",
                                    timing=timing,
                                    content=content_text
                                )
                            else:
                                # Dialogue block! Extract character and emotion
                                emotion_match = re.findall(r'\((.*?)\)', raw_header)
                                emotion = ", ".join(emotion_match) if emotion_match else None
                                char_name = re.sub(r'\(.*?\)', '', raw_header).replace("O.S.", "").replace(":", "").strip()
                                
                                elem = ScriptElement(
                                    element_type="DIALOGUE",
                                    timing=timing,
                                    character=char_name,
                                    emotion=emotion,
                                    content=content_text,
                                    is_off_screen=is_off_screen
                                )
                            
                            if current_scene is None:
                                current_scene = Scene(
                                    scene_number=1,
                                    heading="INT. UNKNOWN",
                                    timing=TimestampRange(0.0, timing.end_sec, "00:00.00", timing.end_str),
                                    elements=[]
                                )
                            current_scene.elements.append(elem)
                            i = k - 1
            i += 1
            
        if current_scene:
            scenes.append(current_scene)
            
        # Calculate total duration
        max_t = 0.0
        for sc in scenes:
            for el in sc.elements:
                if el.timing.end_sec > max_t:
                    max_t = el.timing.end_sec
            if sc.timing.end_sec > max_t:
                max_t = sc.timing.end_sec
                
        return Episode(
            episode_id=f"EP_{ep_num:03d}",
            episode_number=ep_num,
            title=f"Episode {ep_num}",
            logline=logline,
            continuity_notes=continuity,
            scenes=scenes,
            raw_path=file_path,
            total_duration_sec=max_t
        )
