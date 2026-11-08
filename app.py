"""
Streamlit Web Application for PromoLens: AI Microdrama Promo Studio.
Designed for performance marketing teams, video editors, and interview live-demos.
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

# Custom Styling
st.markdown("""
<style>
    .main-title { font-size: 2.3rem; font-weight: 800; color: #E50914; margin-bottom: 0px; }
    .subtitle { font-size: 1.1rem; color: #888; margin-bottom: 1.5rem; }
    .score-badge { background-color: #f0f2f6; border-radius: 8px; padding: 8px 12px; font-weight: bold; }
    .hook-box { background-color: #fff5f5; border-left: 5px solid #ff4b4b; padding: 12px; border-radius: 4px; margin-bottom: 10px; }
    .cliff-box { background-color: #f0f7ff; border-left: 5px solid #1e88e5; padding: 12px; border-radius: 4px; margin-bottom: 10px; }
    .why-box { background-color: #f6ffed; border-left: 5px solid #52c41a; padding: 12px; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.image("https://kukufm.com/favicon.ico", width=40)
st.sidebar.title("🎬 PromoLens")
st.sidebar.markdown("**AI Microdrama Promo Extraction & Ranking Engine**")
st.sidebar.markdown("---")

# Engine Settings
st.sidebar.subheader("⚙️ Scoring Model")
model_choice = st.sidebar.selectbox(
    "Evaluation Model",
    ["Heuristic (Instant / Rule-Based)", "Gemini 1.5 Flash (LLM API)", "OpenAI GPT-4o-mini (LLM API)"]
)

api_key_input = ""
if "LLM" in model_choice:
    api_key_input = st.sidebar.text_input("API Key (Interview / Live)", type="password")

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Ad Constraints")
min_dur = st.sidebar.slider("Min Duration (s)", 15.0, 30.0, 20.0, 1.0)
max_dur = st.sidebar.slider("Max Duration (s)", 35.0, 75.0, 60.0, 1.0)
iou_thresh = st.sidebar.slider("Deduplication (IoU)", 0.1, 0.6, 0.3, 0.05)

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

with st.spinner("Processing 50 Microdrama Episodes..."):
    episodes, ranked_promos, diagnostics = load_and_run_pipeline(min_dur, max_dur, iou_thresh)

# Header
st.markdown('<p class="main-title">🎬 PromoLens: Microdrama Promo Studio</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Extracting, scoring, and ranking high-ROAS vertical video promos across 50 episodes of <i>"I Married a Broken Soldier. He was a Duke"</i></p>', unsafe_allow_html=True)

# KPI Metrics Bar
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Episodes Parsed", f"{len(episodes)}")
col2.metric("Total Promos Found", f"{len(ranked_promos)}")
col3.metric("Top Ranked Score", f"{ranked_promos[0].composite_score:.2f} / 10")
col4.metric("Clean Pass Rate", f"{(diagnostics['clean_promos']/len(ranked_promos))*100:.0f}%")
col5.metric("Avg Promo Duration", f"{sum(p.total_duration_sec for p in ranked_promos)/len(ranked_promos):.1f}s")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["🏆 Ranked Promos Leaderboard", "🔬 Deep Script & Timeline Inspector", "📊 Marketing Campaign Strategy", "🛠️ Test Custom Script"])

with tab1:
    st.subheader("Top Ranked Promos Across All 50 Episodes")
    
    # Filter
    filter_funnel = st.selectbox("Filter by Ad Funnel", ["All Campaigns", "Top-of-Funnel (Cold Hook)", "Mid-Funnel (Emotional Escalation)", "Retargeting (High Cliffhanger)"])
    
    filtered_promos = ranked_promos
    if filter_funnel != "All Campaigns":
        filtered_promos = [p for p in ranked_promos if p.campaign_category == filter_funnel]
        
    for p in filtered_promos[:15]:
        with st.expander(f"#{p.global_rank:02d} | Ep {p.episode_number}: {p.hook_type} ➔ {p.cliffhanger_type} ({p.total_duration_sec:.1f}s) — Score: {p.composite_score:.2f}/10"):
            c_left, c_right = st.columns([3, 1])
            with c_left:
                seg_times = " + ".join([f"**[{s.start_str} - {s.end_str}]**" for s in p.segments])
                st.markdown(f"**Segment Cuts:** {seg_times} | **Category:** `{p.campaign_category}`")
                
                st.markdown(f"""
                <div class="hook-box">
                    <strong>🪝 The Hook (&lt;3s):</strong><br/>
                    {p.hook_description}
                </div>
                <div class="cliff-box">
                    <strong>⚡ The Cliffhanger Cut:</strong><br/>
                    {p.cliffhanger_description}
                </div>
                <div class="why-box">
                    <strong>💡 Why It Works (Marketing Rationale):</strong><br/>
                    {p.why_it_works}
                </div>
                """, unsafe_allow_html=True)
                
                if p.failure_risk_notes:
                    st.warning(f"⚠️ Editorial Note: {p.failure_risk_notes}")
                    
            with c_right:
                st.markdown("### Scores")
                st.write(f"🪝 Hook: **{p.hook_score:.1f}/10**")
                st.write(f"⚡ Cliffhanger: **{p.cliffhanger_score:.1f}/10**")
                st.write(f"🔍 Clarity: **{p.standalone_clarity_score:.1f}/10**")
                st.write(f"⏱️ Pacing: **{p.pacing_score:.1f}/10**")
                st.markdown("---")
                st.markdown(f"**Composite:** `{p.composite_score:.2f}`")

with tab2:
    st.subheader("Deep Script & Timeline Inspector")
    selected_promo_rank = st.selectbox("Select Promo to Inspect", [f"Rank #{p.global_rank} (Ep {p.episode_number}: {p.hook_type})" for p in ranked_promos])
    rank_num = int(selected_promo_rank.split("#")[1].split(" ")[0])
    selected_p = next(p for p in ranked_promos if p.global_rank == rank_num)
    
    st.markdown(f"### Inspecting Rank #{selected_p.global_rank} (Episode {selected_p.episode_number})")
    ep_obj = episodes.get(selected_p.episode_number)
    if ep_obj:
        st.info(f"**Episode Logline:** {ep_obj.logline}")
        
    st.markdown("#### Cut Window Timeline")
    # Show duration progress bar
    seg0 = selected_p.segments[0]
    total_ep_dur = ep_obj.total_duration_sec if ep_obj else 120.0
    progress_val = min(1.0, seg0.end_sec / total_ep_dur)
    st.progress(progress_val)
    st.caption(f"Cut spans {seg0.start_str} to {seg0.end_str} (Duration: {selected_p.total_duration_sec:.1f}s of {total_ep_dur:.1f}s episode)")
    
    st.markdown("#### Screenplay Elements in this Promo")
    for el in seg0.elements:
        if el.element_type == 'DIALOGUE':
            st.markdown(f"🗣️ **[{el.timing.start_str} - {el.timing.end_str}] {el.character}** *({el.emotion or 'Neutral'})*: \"{el.content}\"")
        elif el.element_type == 'ACTION':
            st.markdown(f"🎬 **[{el.timing.start_str} - {el.timing.end_str}] [ACTION]**: *{el.content}*")
        elif el.element_type == 'CAMERA':
            st.markdown(f"🎥 `[{el.timing.start_str} - {el.timing.end_str}] [CAMERA]`: {el.content}")
        elif el.element_type == 'SOUND FX':
            st.markdown(f"🔊 `[{el.timing.start_str} - {el.timing.end_str}] [SFX]`: {el.content}")

with tab3:
    st.subheader("Performance Marketing Ad Strategy: Which to Post First?")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("### 🥇 Wave 1: Cold User Acquisition")
        st.markdown("**Platform**: TikTok / Meta Broad Reels")
        st.markdown("**Goal**: Maximum Thumb-Stop Ratio (<2s)")
        st.markdown("**Selection**: Universal Moral Betrayal Hooks (Ranks #1, #2, #6)")
        st.write("• **Why**: Cold audiences have zero affinity with lore. Only high-injustice betrayal stops scrolling thumbs without prior context.")
    with c2:
        st.markdown("### 🥈 Wave 2: Emotional Escalation")
        st.markdown("**Platform**: TikTok / Instagram Video")
        st.markdown("**Goal**: High Completion Rate & App Installs")
        st.markdown("**Selection**: High-Stakes Conspiracy & Poison (Ranks #3, #4, #5)")
        st.write("• **Why**: Mid-funnel prospects crave narrative momentum and high emotional escalation, leading directly to app download.")
    with c3:
        st.markdown("### 🥉 Wave 3: Cathartic Vindication")
        st.markdown("**Platform**: Retargeting Ads / YouTube Shorts")
        st.markdown("**Goal**: Reactivation & Paid Coin Conversion")
        st.markdown("**Selection**: Duke Identity Unmasking (Episode 42 & 43)")
        st.write("• **Why**: Delivers the ultimate revenge payoff, compelling dormant viewers to unlock paid episodes to see villains defeated.")

with tab4:
    st.subheader("Test Any New Microdrama Screenplay (Interview Live Demo)")
    st.markdown("Upload any new screenplay `.txt` file or paste raw script text below to test the pipeline live:")
    
    user_script_text = st.text_area("Paste Screenplay Script Here", height=200, placeholder="SCENE 01\nScene heading: INT. ROOM\n\n**CAMERA:**\nStart: (00:00.00) | End: (00:03.00)...")
    if st.button("Run PromoLens on Custom Script"):
        if user_script_text.strip():
            parser = ScreenplayParser()
            custom_ep = parser.parse_text(user_script_text, "custom_script.txt")
            gen = CandidateGenerator(min_dur, max_dur)
            custom_cands = gen.generate_single_segment_candidates(custom_ep)
            scorer = HeuristicScoringEngine()
            custom_scored = [scorer.score_candidate([c], custom_ep.episode_number) for c in custom_cands]
            custom_scored = [s for s in custom_scored if s is not None]
            
            if custom_scored:
                ranker = GlobalRanker(iou_thresh)
                top_custom = ranker.rank_season_promos(custom_scored, top_n=5)
                st.success(f"Successfully extracted {len(top_custom)} promos from custom input!")
                for p in top_custom:
                    st.markdown(f"**[{p.segments[0].start_str} - {p.segments[0].end_str}]** ({p.total_duration_sec:.1f}s) — Hook: *{p.hook_description[:60]}...* | Cliffhanger: *{p.cliffhanger_description[:60]}...*")
            else:
                st.warning("No valid 20-60s candidate windows with strong hooks found in the custom text.")
