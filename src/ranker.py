"""
Global ranking and Non-Maximum Suppression (NMS) engine for PromoLens.
Eliminates near-duplicate promo cuts and applies performance marketing campaign ranking.
"""
from typing import List, Dict, Any
from .models import RankedPromo, PromoSegment

def compute_temporal_iou(seg1: PromoSegment, seg2: PromoSegment) -> float:
    """Computes Intersection over Union (IoU) of two temporal segments."""
    inter_start = max(seg1.start_sec, seg2.start_sec)
    inter_end = min(seg1.end_sec, seg2.end_sec)
    intersection = max(0.0, inter_end - inter_start)
    
    union = (seg1.end_sec - seg1.start_sec) + (seg2.end_sec - seg2.start_sec) - intersection
    if union <= 0.0:
        return 0.0
    return intersection / union

class GlobalRanker:
    """Ranks and diversifies promo candidates across the entire season."""

    def __init__(self, iou_threshold: float = 0.30, max_promos_per_episode: int = 2):
        self.iou_threshold = iou_threshold
        self.max_promos_per_episode = max_promos_per_episode

    def apply_temporal_nms(self, promos: List[RankedPromo]) -> List[RankedPromo]:
        """
        Suppresses redundant promo variations of the same scene using Non-Maximum Suppression.
        Keeps the highest-scoring cut within each temporal cluster.
        """
        # Sort descending by composite score
        sorted_promos = sorted(promos, key=lambda p: p.composite_score, reverse=True)
        keep: List[RankedPromo] = []
        
        for cand in sorted_promos:
            suppressed = False
            for selected in keep:
                # Only compare promos within the same episode
                if cand.episode_number == selected.episode_number:
                    # Check overlap with first segments
                    iou = compute_temporal_iou(cand.segments[0], selected.segments[0])
                    if iou > self.iou_threshold:
                        suppressed = True
                        break
            if not suppressed:
                keep.append(cand)
                
        return keep

    def rank_season_promos(self, all_candidates: List[RankedPromo], top_n: int = 25) -> List[RankedPromo]:
        """
        Ranks promos across all episodes, enforcing season-level diversity and campaign strategy.
        Assigns global rank 1..N.
        """
        # Step 1: Temporal NMS per episode
        deduped = self.apply_temporal_nms(all_candidates)
        
        # Step 2: Enforce per-episode diversity cap so one episode does not monopolize all top spots
        ep_counts: Dict[int, int] = {}
        diversified: List[RankedPromo] = []
        
        # Sort primarily by composite score
        sorted_deduped = sorted(deduped, key=lambda p: p.composite_score, reverse=True)
        
        for p in sorted_deduped:
            count = ep_counts.get(p.episode_number, 0)
            if count < self.max_promos_per_episode:
                diversified.append(p)
                ep_counts[p.episode_number] = count + 1
            if len(diversified) >= top_n:
                break
                
        # Step 3: Assign Global Rank and format
        for rank_idx, promo in enumerate(diversified, start=1):
            promo.global_rank = rank_idx
            
        return diversified
