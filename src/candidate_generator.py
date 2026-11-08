"""
Candidate window generator for microdrama screenplays.
Generates valid candidate cuts adhering to strict duration (20s-60s) and boundary constraints.
"""
from typing import List, Tuple
from .models import Episode, Scene, ScriptElement, PromoSegment, TimestampRange
from .parser import format_sec_to_time_str

class CandidateGenerator:
    """Generates boundary-aligned candidate promo segments from episode scripts."""

    def __init__(self, min_duration: float = 20.0, max_duration: float = 60.0):
        self.min_duration = min_duration
        self.max_duration = max_duration

    def generate_single_segment_candidates(self, episode: Episode) -> List[PromoSegment]:
        """
        Generates candidate windows within single scenes (or contiguous transitions).
        Start cuts align with element start timestamps.
        End cuts align with element end timestamps.
        """
        candidates: List[PromoSegment] = []
        
        # Collect all actionable cut boundaries across episode elements
        all_elements: List[ScriptElement] = []
        for scene in episode.scenes:
            all_elements.extend(scene.elements)
            
        if not all_elements:
            return candidates

        n = len(all_elements)
        for i in range(n):
            start_elem = all_elements[i]
            t_start = start_elem.timing.start_sec
            
            # Hook candidates: must start with meaningful dialogue or action (not silence or empty sound fx)
            if start_elem.element_type not in ['DIALOGUE', 'ACTION', 'CAMERA']:
                continue
                
            for j in range(i, n):
                end_elem = all_elements[j]
                t_end = end_elem.timing.end_sec
                duration = t_end - t_start
                
                # Check duration window
                if duration < self.min_duration:
                    continue
                if duration > self.max_duration:
                    break  # elements are sorted by time, so further j will exceed max_duration
                    
                # Clean cut condition:
                # End on a completed dialogue beat, dramatic action, or sound fx swell
                if end_elem.element_type in ['DIALOGUE', 'ACTION', 'SOUND FX']:
                    cand_elements = all_elements[i : j + 1]
                    segment = PromoSegment(
                        episode_number=episode.episode_number,
                        start_sec=t_start,
                        end_sec=t_end,
                        start_str=format_sec_to_time_str(t_start),
                        end_str=format_sec_to_time_str(t_end),
                        duration_sec=duration,
                        elements=cand_elements
                    )
                    candidates.append(segment)
                    
        return candidates

    def generate_stitched_candidates(self, episode: Episode, top_single_candidates: List[PromoSegment]) -> List[List[PromoSegment]]:
        """
        Generates 2-segment stitched candidates (e.g., Hook Beat [5-10s] + Tension Cliffhanger [20-40s]).
        Total combined duration must still adhere to [20s, 60s].
        """
        stitched: List[List[PromoSegment]] = []
        all_elements: List[ScriptElement] = []
        for scene in episode.scenes:
            all_elements.extend(scene.elements)
            
        if len(all_elements) < 10:
            return stitched

        # Look for short 5-10s explosive hooks early in the episode
        short_hooks: List[PromoSegment] = []
        for i in range(min(15, len(all_elements))):
            start_el = all_elements[i]
            if start_el.element_type not in ['DIALOGUE', 'ACTION']:
                continue
            for j in range(i, min(i + 6, len(all_elements))):
                end_el = all_elements[j]
                dur = end_el.timing.end_sec - start_el.timing.start_sec
                if 4.0 <= dur <= 12.0:
                    short_hooks.append(PromoSegment(
                        episode_number=episode.episode_number,
                        start_sec=start_el.timing.start_sec,
                        end_sec=end_el.timing.end_sec,
                        start_str=format_sec_to_time_str(start_el.timing.start_sec),
                        end_str=format_sec_to_time_str(end_el.timing.end_sec),
                        duration_sec=dur,
                        elements=all_elements[i: j + 1]
                    ))

        # Combine with later 18-35s cliffhanger escalations
        for hook_seg in short_hooks[:5]:
            for single_cand in top_single_candidates[:10]:
                # Must be later in time with at least 5s gap
                if single_cand.start_sec > hook_seg.end_sec + 5.0:
                    comb_dur = hook_seg.duration_sec + single_cand.duration_sec
                    if self.min_duration <= comb_dur <= self.max_duration:
                        stitched.append([hook_seg, single_cand])
                        if len(stitched) >= 5:
                            return stitched
                            
        return stitched
