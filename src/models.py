"""
Data models for PromoLens: Kuku AI Microdrama Promo Extraction Pipeline
"""
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any

@dataclass
class TimestampRange:
    start_sec: float
    end_sec: float
    start_str: str
    end_str: str

    @property
    def duration(self) -> float:
        return max(0.0, self.end_sec - self.start_sec)

@dataclass
class ScriptElement:
    element_type: str  # 'CAMERA', 'ACTION', 'SOUND FX', 'DIALOGUE'
    timing: TimestampRange
    character: Optional[str] = None
    emotion: Optional[str] = None
    content: str = ""
    is_off_screen: bool = False

@dataclass
class Scene:
    scene_number: int
    heading: str
    timing: TimestampRange
    elements: List[ScriptElement] = field(default_factory=list)

@dataclass
class Episode:
    episode_id: str
    episode_number: int
    title: str
    logline: str
    continuity_notes: str
    scenes: List[Scene] = field(default_factory=list)
    raw_path: str = ""
    total_duration_sec: float = 0.0

@dataclass
class PromoSegment:
    episode_number: int
    start_sec: float
    end_sec: float
    start_str: str
    end_str: str
    duration_sec: float
    elements: List[ScriptElement] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "episode": self.episode_number,
            "start": self.start_str,
            "end": self.end_str,
            "start_sec": round(self.start_sec, 2),
            "end_sec": round(self.end_sec, 2),
            "duration_sec": round(self.duration_sec, 2),
        }

@dataclass
class RankedPromo:
    promo_id: str
    episode_number: int
    title: str
    segments: List[PromoSegment]
    total_duration_sec: float
    
    # Core assignment criteria
    hook_description: str
    hook_type: str  # e.g., 'Altar Betrayal', 'Physical Action', 'Status Reversal', 'Shocking Revelation'
    cliffhanger_description: str
    cliffhanger_type: str  # e.g., 'Unanswered Threat', 'Lethal Intervention', 'Unresolved Ultimatum'
    why_it_works: str  # 1-line psychological/marketing rationale
    
    # Quantitative scores (0 to 10 scale)
    hook_score: float
    cliffhanger_score: float
    standalone_clarity_score: float
    pacing_score: float
    composite_score: float
    
    # Marketing categorization
    campaign_category: str  # 'Top-of-Funnel (Cold Hook)', 'Mid-Funnel (Emotional Escalation)', 'Retargeting (Plot Twist)'
    global_rank: int = 0
    failure_risk_notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "promo_id": self.promo_id,
            "global_rank": self.global_rank,
            "episode": self.episode_number,
            "campaign_category": self.campaign_category,
            "total_duration_sec": round(self.total_duration_sec, 2),
            "segments": [s.to_dict() for s in self.segments],
            "hook": self.hook_description,
            "hook_type": self.hook_type,
            "cliffhanger": self.cliffhanger_description,
            "cliffhanger_type": self.cliffhanger_type,
            "why_it_works": self.why_it_works,
            "scores": {
                "hook_score": round(self.hook_score, 2),
                "cliffhanger_score": round(self.cliffhanger_score, 2),
                "standalone_clarity_score": round(self.standalone_clarity_score, 2),
                "pacing_score": round(self.pacing_score, 2),
                "composite_score": round(self.composite_score, 2),
            },
            "failure_risk_notes": self.failure_risk_notes or ""
        }
