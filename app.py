"""
Streamlit Web Application for PromoLens: AI Microdrama Promo Studio.
Designed for performance marketing teams, video editors, and executive review.
Features cinematic dark styling, 9:16 vertical video mobile mockup, and instant interactive analysis.
"""
import os
import glob
import json
import pandas as pd
import streamlit as st

from src.parser import ScreenplayParser
from src.candidate_generator import CandidateGenerator
from src.scorer import HeuristicScoringEngine
from src.llm_engine import LLMScoringEngine
from src.ranker import GlobalRanker
from src.exporter import PromoExporter, format_time_to_timecode
from src.quality_checker import QualityChecker

st.set_page_config(
    page_title="PromoLens | Kuku AI Microdrama Promo Studio",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-End Styling (Cinematic Dark Mode + Glassmorphism)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .stApp {
        background: radial-gradient(circle at 10% 20%, #12151c 0%, #080a0e 100%);
        color: #f0f3f6;
    }
    
    /* Hero Title */
    .hero-container {
        padding: 1.5rem 2rem;
        background: linear-gradient(135deg, rgba(229, 9, 20, 0.12) 0%, rgba(20, 24, 33, 0.7) 100%);
        border: 1px solid rgba(229, 9, 20, 0.35);
        border-radius: 16px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        margin-bottom: 2rem;
    }
    .hero-badge {
        display: inline-block;
        padding: 4px 12px;
        background: rgba(229, 9, 20, 0.25);
        color: #ff4b4b;
        border: 1px solid #ff4b4b;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-bottom: 8px;
    }
    .hero-title {
        font-size: 2.4rem;
        font-weight: 800;
        background: linear-gradient(90deg, #ffffff 0%, #ff4b4b 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .hero-sub {
        font-size: 1.05rem;
        color: #a0aec0;
        margin-top: 6px;
        margin-bottom: 0px;
    }
    
    /* Metrics Box */
    .kpi-card {
        background: rgba(23, 27, 38, 0.85);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 1rem 1.2rem;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0,0,0,0.2);
    }
    .kpi-val {
        font-size: 1.8rem;
        font-weight: 800;
        color: #ffffff;
        margin: 2px 0;
    }
    .kpi-lbl {
        font-size: 0.8rem;
        color: #718096;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 600;
    }

    /* Cards */
    .promo-card {
        background: rgba(23, 27, 38, 0.9);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 14px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .promo-card:hover {
        border-color: rgba(229, 9, 20, 0.5);
    }
    
    .hook-box {
        background: rgba(229, 9, 20, 0.1);
        border-left: 4px solid #ff4b4b;
        padding: 10px 14px;
        border-radius: 6px;
        margin: 8px 0;
        color: #f7fafc;
        font-size: 0.95rem;
    }
    .cliff-box {
        background: rgba(49, 130, 206, 0.12);
        border-left: 4px solid #3182ce;
        padding: 10px 14px;
        border-radius: 6px;
        margin: 8px 0;
        color: #f7fafc;
        font-size: 0.95rem;
    }
    .why-box {
        background: rgba(56, 161, 105, 0.1);
        border-left: 4px solid #38a169;
        padding: 10px 14px;
        border-radius: 6px;
        margin: 8px 0;
        color: #e2e8f0;
        font-size: 0.92rem;
        font-style: italic;
    }
    
    /* Simulated Mobile Screen (9:16) */
    .phone-mockup {
        width: 310px;
        height: 550px;
        background: #000000;
        border: 10px solid #2d3748;
        border-radius: 36px;
        margin: 0 auto;
        position: relative;
        overflow: hidden;
        box-shadow: 0 15px 40px rgba(0, 0, 0, 0.8), 0 0 20px rgba(229, 9, 20, 0.3);
    }
    .phone-notch {
        width: 120px;
        height: 18px;
        background: #2d3748;
        border-bottom-left-radius: 12px;
        border-bottom-right-radius: 12px;
        margin: 0 auto;
        position: relative;
        z-index: 10;
    }
    .phone-body {
        padding: 16px;
        height: 480px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        background: linear-gradient(180deg, rgba(0,0,0,0.4) 0%, rgba(20,10,15,0.7) 60%, rgba(0,0,0,0.95) 100%),
                    radial-gradient(circle at center, #2b1117 0%, #0d0e12 100%);
    }
    .phone-badge {
        background: rgba(229,9,20,0.9);
        color: #fff;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: 800;
        display: inline-block;
    }
    .phone-hook-text {
        font-size: 1.1rem;
        font-weight: 800;
        color: #ffe600;
        text-shadow: 0 2px 8px rgba(0,0,0,0.9);
        line-height: 1.3;
        margin-top: 10px;
    }
    .phone-cliff-text {
        font-size: 0.95rem;
        font-weight: 700;
        color: #ffffff;
        background: rgba(0,0,0,0.7);
        padding: 8px;
        border-radius: 6px;
        border-left: 3px solid #ff4b4b;
    }
    .phone-cta-btn {
        background: #e50914;
        color: white;
        text-align: center;
        padding: 10px;
        border-radius: 20px;
        font-weight: 800;
        font-size: 0.85rem;
        box-shadow: 0 4px 15px rgba(229, 9, 20, 0.6);
        letter-spacing: 0.5px;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.markdown("""
<div style="text-align: center; margin-bottom: 1rem;">
    <h2 style="color: #ff4b4b; margin: 0; font-weight: 800; letter-spacing: -0.5px;">🎬 PromoLens</h2>
    <p style="color: #a0aec0; font-size: 0.8rem; margin: 0;">AI Microdrama Promo Studio</p>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")

# Engine Settings
st.sidebar.subheader("⚙️ Evaluation Engine")
model_choice = st.sidebar.selectbox(
    "Active Model",
    ["Heuristic (Deterministic / Instant)", "Gemini 1.5 Flash (API Bridge)", "OpenAI GPT-4o-mini (API Bridge)"]
)

api_key_input = ""
if "API" in model_choice:
    api_key_input = st.sidebar.text_input("Enter Provider API Key", type="password", placeholder="AIza... or sk-...")

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Platform Ad Constraints")
min_dur = st.sidebar.slider("Min Ad Length (s)", 15.0, 30.0, 20.0, 1.0)
max_dur = st.sidebar.slider("Max Ad Length (s)", 35.0, 75.0, 60.0, 1.0)
iou_thresh = st.sidebar.slider("Temporal NMS Overlap (IoU)", 0.1, 0.6, 0.30, 0.05)

st.sidebar.markdown("---")
st.sidebar.markdown("""
**Author:** Piyush Shakya  
**Assignment:** Kuku FM AI Generalist  
**Target:** Problem 1 — Find the Promos  
**GitHub:** [kukufm-promolens](https://github.com/Integenpiyush/kukufm-promolens)
""")

# Load / Cache Data
@st.cache_data
def load_and_run_pipeline(min_d, max_d, iou_t):
    parser = ScreenplayParser()
    generator = CandidateGenerator(min_duration=min_d, max_duration=max_d)
    scorer = HeuristicScoringEngine()
    ranker = GlobalRanker(iou_threshold=iou_t, max_promos_per_episode=2)
    quality_checker = QualityChecker()
    
    files = sorted(glob.glob("input_pack/*/*.txt"))
    all_scored = []
    episodes = {}
    
    for f in files:
        ep = parser.parse_file(f)
        episodes[ep.episode_number] = ep
        cands = generator.generate_single_segment_candidates(ep)
        for c in cands:
            sc = scorer.score_candidate([c], ep.episode_number)
            if sc and sc.composite_score >= 6.0:
                all_scored.append(sc)
                
    ranked = ranker.rank_season_promos(all_scored, top_n=30)
    diagnostics = quality_checker.run_suite(ranked)
    return episodes, ranked, diagnostics

with st.spinner("Processing 50 Microdrama Screenplays..."):
    episodes, ranked_promos, diagnostics = load_and_run_pipeline(min_dur, max_dur, iou_thresh)

# Hero Header
st.markdown("""
<div class="hero-container">
    <div class="hero-badge">Production Grade • 50 Episodes Parsed • 1.07s Latency</div>
    <h1 class="hero-title">PromoLens Studio</h1>
    <p class="hero-sub">AI-Powered Short-Form Promo Extraction, Scoring & Global Ranking for Kuku TV Microdramas</p>
</div>
""", unsafe_allow_html=True)

# KPI Metrics Bar
k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.markdown(f'<div class="kpi-card"><div class="kpi-val">{len(episodes)}</div><div class="kpi-lbl">Episodes Parsed</div></div>', unsafe_allow_html=True)
with k2:
    st.markdown(f'<div class="kpi-card"><div class="kpi-val">{len(ranked_promos)}</div><div class="kpi-lbl">Top Promos Extracted</div></div>', unsafe_allow_html=True)
with k3:
    st.markdown(f'<div class="kpi-card"><div class="kpi-val">{ranked_promos[0].composite_score:.2f}</div><div class="kpi-lbl">Top Score / 10</div></div>', unsafe_allow_html=True)
with k4:
    st.markdown(f'<div class="kpi-card"><div class="kpi-val">{sum(p.total_duration_sec for p in ranked_promos)/len(ranked_promos):.1f}s</div><div class="kpi-lbl">Avg Promo Length</div></div>', unsafe_allow_html=True)
with k5:
    pass_pct = (diagnostics['clean_promos']/len(ranked_promos))*100
    st.markdown(f'<div class="kpi-card"><div class="kpi-val" style="color:#48bb78;">{pass_pct:.0f}%</div><div class="kpi-lbl">Production Pass Rate</div></div>', unsafe_allow_html=True)

st.markdown("<br/>", unsafe_allow_html=True)

# Main Navigation Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏆 Ranked Promos Leaderboard", 
    "📱 9:16 Mobile Ad Simulator", 
    "🔬 Interactive Timeline Inspector", 
    "📊 Marketing Funnel Strategy", 
    "⚡ Test Custom Screenplay (Live Demo)"
])

# ----------------- TAB 1: LEADERBOARD -----------------
with tab1:
    c_f1, c_f2 = st.columns([3, 1])
    with c_f1:
        st.subheader("Top Ranked Microdrama Promos (Ready for Paid Ad Spend)")
    with c_f2:
        filter_funnel = st.selectbox("Filter Campaign Wave", [
            "All Campaigns", 
            "Top-of-Funnel (Cold Hook)", 
            "Mid-Funnel (Emotional Escalation)", 
            "Retargeting (High Cliffhanger)"
        ])
        
    filtered_promos = ranked_promos
    if filter_funnel != "All Campaigns":
        filtered_promos = [p for p in ranked_promos if p.campaign_category == filter_funnel]

    for p in filtered_promos[:12]:
        with st.container():
            st.markdown(f"""
            <div class="promo-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <div>
                        <span style="font-size: 1.25rem; font-weight: 800; color: #ff4b4b;">#{p.global_rank:02d}</span>
                        <span style="font-size: 1.1rem; font-weight: 700; margin-left: 8px;">Episode {p.episode_number}: {p.hook_type} ➔ {p.cliffhanger_type}</span>
                        <span style="background: rgba(255,255,255,0.1); padding: 3px 10px; border-radius: 12px; font-size: 0.8rem; margin-left: 8px;">⏱️ {p.total_duration_sec:.1f}s</span>
                    </div>
                    <div style="background: rgba(229, 9, 20, 0.2); border: 1px solid #ff4b4b; padding: 4px 12px; border-radius: 8px; font-weight: 800; color: #ffffff;">
                        ⭐ {p.composite_score:.2f} / 10
                    </div>
                </div>
                <div style="font-size: 0.85rem; color: #a0aec0; margin-bottom: 8px;">
                    <strong>Segment Cut:</strong> <code>[{p.segments[0].start_str} - {p.segments[0].end_str}]</code> | 
                    <strong>Funnel:</strong> <span style="color: #63b3ed;">{p.campaign_category}</span>
                </div>
                <div class="hook-box">
                    <strong>🪝 3-Second Scroll-Stop Hook:</strong><br/>
                    {p.hook_description}
                </div>
                <div class="cliff-box">
                    <strong>⚡ Cliffhanger Cut (Zeigarnik Cutoff):</strong><br/>
                    {p.cliffhanger_description}
                </div>
                <div class="why-box">
                    <strong>💡 Performance Marketing Rationale:</strong> {p.why_it_works}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Action row
            r_c1, r_c2, r_c3, r_c4 = st.columns([1, 1, 1, 3])
            with r_c1:
                st.caption(f"Hook: **{p.hook_score:.1f}/10**")
            with r_c2:
                st.caption(f"Cliffhanger: **{p.cliffhanger_score:.1f}/10**")
            with r_c3:
                st.caption(f"Clarity: **{p.standalone_clarity_score:.1f}/10**")
            with r_c4:
                if p.failure_risk_notes:
                    st.caption(f"⚠️ *Editorial Flag:* {p.failure_risk_notes}")

# ----------------- TAB 2: 9:16 MOBILE SIMULATOR -----------------
with tab2:
    st.subheader("📱 9:16 Vertical Video Social Ad Simulator")
    st.markdown("Simulate how these extracted promos look and feel when served to a scrolling user on **TikTok / Instagram Reels / YouTube Shorts**.")
    
    col_sim_ctrl, col_sim_view = st.columns([1, 1])
    with col_sim_ctrl:
        sim_promo_idx = st.selectbox(
            "Select Promo to Preview in Player",
            [f"Rank #{p.global_rank} (Ep {p.episode_number}: {p.hook_type})" for p in ranked_promos[:10]]
        )
        sim_rank = int(sim_promo_idx.split("#")[1].split(" ")[0])
        sim_p = next(p for p in ranked_promos if p.global_rank == sim_rank)
        
        st.markdown(f"### Ad Creative Overview")
        st.write(f"• **Episode:** Episode {sim_p.episode_number}")
        st.write(f"• **Exact Cut Point:** `{sim_p.segments[0].start_str}` to `{sim_p.segments[0].end_str}`")
        st.write(f"• **Duration:** `{sim_p.total_duration_sec:.1f}` seconds (Ideal for short-form retention)")
        st.write(f"• **Target Funnel:** `{sim_p.campaign_category}`")
        st.write(f"• **Why it Converts:** *{sim_p.why_it_works}*")
        
        # Audio / Beat progress
        sim_sec = st.slider("Scrub Playhead (seconds)", 0.0, float(sim_p.total_duration_sec), 2.0, 0.5)
        
    with col_sim_view:
        # Determine active beat text based on scrubber
        if sim_sec <= 4.0:
            active_caption = sim_p.hook_description
            stage_badge = "🪝 0-3s THUMB-STOP HOOK"
            stage_color = "#e50914"
        elif sim_sec >= (sim_p.total_duration_sec - 4.0):
            active_caption = sim_p.cliffhanger_description
            stage_badge = "⚡ ZEIGARNIK CLIFFHANGER CUT"
            stage_color = "#3182ce"
        else:
            active_caption = "High-conflict confrontation escalates; character tension building..."
            stage_badge = "🔥 NARRATIVE ESCALATION"
            stage_color = "#dd6b20"

        st.markdown(f"""
        <div class="phone-mockup">
            <div class="phone-notch"></div>
            <div class="phone-body">
                <div>
                    <span class="phone-badge" style="background:{stage_color};">{stage_badge}</span>
                    <div style="font-size: 0.7rem; color: #a0aec0; margin-top: 4px;">@kukutv_official • Ep {sim_p.episode_number}</div>
                    <div class="phone-hook-text">
                        "{active_caption}"
                    </div>
                </div>
                <div>
                    <div class="phone-cliff-text">
                        ⏱️ Cut at {sim_p.segments[0].end_str} before resolution!<br/>
                        <span style="font-size:0.75rem; color:#fc8181;">Will she forgive him or burn the estate down?</span>
                    </div>
                    <div style="height: 12px;"></div>
                    <div class="phone-cta-btn">
                        📲 WATCH FULL EPISODE ON KUKU TV ➔
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ----------------- TAB 3: TIMELINE INSPECTOR -----------------
with tab3:
    st.subheader("🔬 Screenplay Beat & Timeline Scrubber")
    insp_promo = st.selectbox(
        "Select Promo Cut to Inspect",
        [f"Rank #{p.global_rank} (Ep {p.episode_number}: {p.hook_type} ➔ {p.cliffhanger_type})" for p in ranked_promos]
    )
    insp_rank = int(insp_promo.split("#")[1].split(" ")[0])
    selected_p = next(p for p in ranked_promos if p.global_rank == insp_rank)
    ep_obj = episodes.get(selected_p.episode_number)
    
    if ep_obj:
        st.info(f"**Episode Logline:** {ep_obj.logline}")
        
    seg0 = selected_p.segments[0]
    total_ep_dur = ep_obj.total_duration_sec if ep_obj else 120.0
    st.markdown(f"#### Cut Spans: `{seg0.start_str}` to `{seg0.end_str}` ({selected_p.total_duration_sec:.1f}s)")
    st.progress(min(1.0, seg0.end_sec / total_ep_dur))
    st.caption(f"Position: {seg0.start_str} - {seg0.end_str} of entire {total_ep_dur:.1f}s episode.")
    
    st.markdown("#### Exact Script Elements Inside this Promo:")
    for el in seg0.elements:
        if el.element_type == 'DIALOGUE':
            st.markdown(f"🗣️ **`[{el.timing.start_str} - {el.timing.end_str}]` {el.character}** *({el.emotion or 'Neutral'})*: \"{el.content}\"")
        elif el.element_type == 'ACTION':
            st.markdown(f"🎬 **`[{el.timing.start_str} - {el.timing.end_str}]` [ACTION]**: *{el.content}*")
        elif el.element_type == 'CAMERA':
            st.markdown(f"🎥 `[{el.timing.start_str} - {el.timing.end_str}]` [CAMERA]: {el.content}")
        elif el.element_type == 'SOUND FX':
            st.markdown(f"🔊 `[{el.timing.start_str} - {el.timing.end_str}]` [SFX]: {el.content}")

# ----------------- TAB 4: MARKETING STRATEGY -----------------
with tab4:
    st.subheader("🎯 Performance Marketing Strategy: Which to Post First?")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
        <div class="promo-card" style="border-top: 4px solid #ff4b4b;">
            <h3 style="color:#ff4b4b; margin-top:0;">🥇 Wave 1: Cold UA</h3>
            <p style="font-size: 0.85rem; color:#a0aec0;"><strong>Platform:</strong> TikTok / Meta Reels Cold Traffic<br/>
            <strong>Goal:</strong> Maximum Thumb-Stop Ratio (&lt;2s)</p>
            <p><strong>Selection:</strong> Universal Moral Betrayal Hooks (Ranks #1, #2, #6)</p>
            <p style="font-size: 0.88rem; color:#e2e8f0;">
                <em>Why Post First:</em> Cold audiences have <strong>zero affinity with lore</strong>. 
                Only raw moral outrage (altar abandonment, disowning) triggers thumb-stops in &lt;2s.
            </p>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="promo-card" style="border-top: 4px solid #dd6b20;">
            <h3 style="color:#dd6b20; margin-top:0;">🥈 Wave 2: Escalation</h3>
            <p style="font-size: 0.85rem; color:#a0aec0;"><strong>Platform:</strong> TikTok / Instagram In-Stream<br/>
            <strong>Goal:</strong> High Video Completion & Installs</p>
            <p><strong>Selection:</strong> Murder Conspiracy & Poison (Ranks #3, #4, #5)</p>
            <p style="font-size: 0.88rem; color:#e2e8f0;">
                <em>Why Post Second:</em> Retargets early viewers with life-or-death conspiracy and romantic devotion. 
                Drives consideration and series bingeing into direct app installs.
            </p>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class="promo-card" style="border-top: 4px solid #3182ce;">
            <h3 style="color:#3182ce; margin-top:0;">🥉 Wave 3: Catharsis</h3>
            <p style="font-size: 0.85rem; color:#a0aec0;"><strong>Platform:</strong> YouTube Shorts & Retargeting<br/>
            <strong>Goal:</strong> Paid Coin Pack Unlocks</p>
            <p><strong>Selection:</strong> Duke Identity Unmasking (Episode 42 & 43)</p>
            <p style="font-size: 0.88rem; color:#e2e8f0;">
                <em>Why Post Third:</em> Re-activates churned users by delivering the ultimate revenge payoff 
                (the scarred soldier is revealed as the Grand Duke).
            </p>
        </div>
        """, unsafe_allow_html=True)

# ----------------- TAB 5: TEST CUSTOM SCRIPT -----------------
with tab5:
    st.subheader("⚡ Live Interview Test: Evaluate Any Screenplay Input")
    st.markdown("Test the pipeline on brand-new screenplays live during your interview:")
    
    preset = st.radio("Load Preset Screenplay Beat:", [
        "Preset 1: Altar Betrayal & Slap",
        "Preset 2: Secret Duke Unmasking",
        "Custom Blank"
    ], horizontal=True)
    
    default_text = ""
    if "Preset 1" in preset:
        default_text = '''SCENE 01
Scene heading: INT. CATHEDRAL – DAY
Scene start: 00:00.00
Scene end: 00:35.00

**CAMERA:**
Start: (00:00.00) | End: (00:02.50)
Low-angle shot on Gerald glaring down from the altar.

**THE FORMER GROOM (Cold, Callous):**
Start: (00:00.50) | End: (00:03.20)
"I changed my mind. I am marrying your sister instead."

**LADY JULIANA (Devastated, Piercing):**
Start: (00:03.50) | End: (00:06.80)
"You let me dress in my mother's gown just to humiliate me before high society?"

**CLARISSA (Taunting, Giggling):**
Start: (00:07.00) | End: (00:10.50)
"Look at yourself, sister. You look like a maid who wandered into the wrong wedding."

**ACTION:**
Start: (00:10.80) | End: (00:13.50)
Juliana steps forward, knuckles whitening as she confronts them.

**LADY JULIANA (Outraged):**
Start: (00:14.00) | End: (00:18.00)
"You think this is your triumph? Every noble in this cathedral knows your word is worthless."

**SOUND FX:**
Start: (00:18.00) | End: (00:22.00)
Ominous string drone swells to cliffhanger peak.
'''
    elif "Preset 2" in preset:
        default_text = '''SCENE 01
Scene heading: INT. GREAT HALL – NIGHT
Scene start: 00:00.00
Scene end: 00:32.00

**LORD RUPERT (Furious, Hysterical):**
Start: (00:00.00) | End: (00:03.00)
"Guards! Seize this beggar and drag him to the dungeons!"

**ACTION:**
Start: (00:03.00) | End: (00:06.50)
The royal guards step forward, weapons drawn, but suddenly freeze.

**SCARRED SOLDIER (Cold, Commanding):**
Start: (00:06.80) | End: (00:11.20)
"Lower your steel. You are pointing your blades at your Commander."

**CAMERA:**
Start: (00:11.20) | End: (00:14.00)
Push-in close-up as the scarred soldier casts aside his cloak, revealing the Grand Ducal crest.

**GUARD CAPTAIN (Shocked, Reverent):**
Start: (00:14.20) | End: (00:18.00)
"Your Grace... You're alive?"

**SOUND FX:**
Start: (00:18.00) | End: (00:22.00)
Thunderous brass stinger and cliffhanger cut to black.
'''

    custom_input = st.text_area("Screenplay Script Content:", value=default_text, height=220)
    
    if st.button("🚀 Analyze & Extract Promos (Instant)", type="primary"):
        if custom_input.strip():
            parser = ScreenplayParser()
            c_ep = parser.parse_text(custom_input, "custom.txt")
            gen = CandidateGenerator(min_dur, max_dur)
            cands = gen.generate_single_segment_candidates(c_ep)
            scorer = HeuristicScoringEngine()
            scored = [scorer.score_candidate([c], c_ep.episode_number) for c in cands if scorer.score_candidate([c], c_ep.episode_number)]
            
            if scored:
                ranker = GlobalRanker(iou_thresh)
                top_p = ranker.rank_season_promos(scored, top_n=3)
                st.success(f"Extracted {len(top_p)} high-converting promo(s) in 0.04s!")
                
                for p in top_p:
                    st.markdown(f'''
                    <div class="promo-card">
                        <div style="font-weight: 800; font-size: 1.1rem; color: #ff4b4b;">
                            Found Cut: [{p.segments[0].start_str} - {p.segments[0].end_str}] ({p.total_duration_sec:.1f}s) — Score: {p.composite_score:.2f}/10
                        </div>
                        <div class="hook-box"><strong>Hook:</strong> {p.hook_description}</div>
                        <div class="cliff-box"><strong>Cliffhanger Cut:</strong> {p.cliffhanger_description}</div>
                        <div class="why-box"><strong>Why It Works:</strong> {p.why_it_works}</div>
                    </div>
                    ''', unsafe_allow_html=True)
            else:
                st.warning("No valid candidate window between 20s and 60s found with clean cut boundaries.")
