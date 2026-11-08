#!/usr/bin/env python3
"""
Master runner for PromoLens: AI Microdrama Promo Extraction & Ranking Pipeline.
Processes screenplay files, identifies candidate windows, scores hooks/cliffhangers,
deduplicates via temporal NMS, and exports production-ready outputs.
"""
import os
import sys
import glob
import time
import argparse
from typing import List

from src.parser import ScreenplayParser
from src.candidate_generator import CandidateGenerator
from src.scorer import HeuristicScoringEngine
from src.llm_engine import LLMScoringEngine
from src.ranker import GlobalRanker
from src.exporter import PromoExporter
from src.quality_checker import QualityChecker
from src.models import RankedPromo, Episode

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

def parse_args():
    parser = argparse.ArgumentParser(description="PromoLens: Automated Microdrama Promo Extractor")
    parser.add_argument("--input-dir", type=str, default="input_pack/I Married a Broken Soldier. He was a Duke",
                        help="Path to folder containing screenplay .txt files")
    parser.add_argument("--single-file", type=str, default=None,
                        help="Optional path to a single screenplay file to process")
    parser.add_argument("--output-dir", type=str, default="raw_outputs",
                        help="Directory to save raw outputs, CSVs, and EDLs")
    parser.add_argument("--top-n", type=int, default=25,
                        help="Number of top promos to rank for the show")
    parser.add_argument("--min-duration", type=float, default=20.0,
                        help="Minimum promo duration in seconds (platform ad constraint)")
    parser.add_argument("--max-duration", type=float, default=60.0,
                        help="Maximum promo duration in seconds (platform ad constraint)")
    parser.add_argument("--model", type=str, default="heuristic", choices=["heuristic", "gemini", "openai"],
                        help="Scoring engine to use (swappable for interview evaluation)")
    parser.add_argument("--api-key", type=str, default=None,
                        help="Optional API key if using gemini or openai")
    return parser.parse_args()

def main():
    args = parse_args()
    start_time = time.time()
    
    console.print(Panel.fit(
        "[bold cyan]PromoLens: AI Microdrama Promo Extraction Engine[/bold cyan]\n"
        "[italic]Finding high-converting vertical video promos across microdrama screenplays[/italic]",
        border_style="cyan"
    ))

    # 1. Discover files
    if args.single_file:
        files = [args.single_file]
    else:
        files = sorted(glob.glob(os.path.join(args.input_dir, "*.txt")))
        
    if not files:
        console.print(f"[bold red]Error: No screenplay files found in '{args.input_dir}'[/bold red]")
        sys.exit(1)

    console.print(f"[green]✔[/green] Discovered [bold]{len(files)}[/bold] screenplay episodes to process.")

    # 2. Initialize Pipeline Modules
    parser = ScreenplayParser()
    generator = CandidateGenerator(min_duration=args.min_duration, max_duration=args.max_duration)
    
    if args.model == "heuristic":
        scorer = HeuristicScoringEngine()
    else:
        scorer = LLMScoringEngine(provider=args.model, api_key=args.api_key)
        
    ranker = GlobalRanker(iou_threshold=0.30, max_promos_per_episode=2)
    quality_checker = QualityChecker()

    # 3. Process Episodes & Extract Candidates
    all_scored_promos: List[RankedPromo] = []
    total_candidates_generated = 0
    episodes: List[Episode] = []

    with console.status("[bold green]Parsing screenplays and evaluating candidate windows...") as status:
        for idx, file_path in enumerate(files, start=1):
            episode = parser.parse_file(file_path)
            episodes.append(episode)
            
            # Generate single continuous candidates
            candidates = generator.generate_single_segment_candidates(episode)
            total_candidates_generated += len(candidates)
            
            # Score each candidate window
            for cand in candidates:
                ranked = scorer.score_candidate([cand], episode.episode_number)
                if ranked and ranked.composite_score >= 6.0:
                    all_scored_promos.append(ranked)
                    
            # Generate stitched 2-segment candidates if candidate pool allows
            if len(candidates) > 5:
                stitched_cands = generator.generate_stitched_candidates(episode, candidates)
                for pair in stitched_cands:
                    ranked_stitched = scorer.score_candidate(pair, episode.episode_number)
                    if ranked_stitched and ranked_stitched.composite_score >= 7.0:
                        all_scored_promos.append(ranked_stitched)

    console.print(f"[green]✔[/green] Parsed [bold]{len(episodes)}[/bold] episodes.")
    console.print(f"[green]✔[/green] Evaluated [bold]{total_candidates_generated}[/bold] boundary-aligned candidate windows.")
    console.print(f"[green]✔[/green] Retained [bold]{len(all_scored_promos)}[/bold] high-potential promo candidates.")

    # 4. Global Ranking, Non-Maximum Suppression & Diversity Filter
    with console.status("[bold blue]Applying temporal NMS, global ranking & campaign strategy...") as status:
        final_ranked_promos = ranker.rank_season_promos(all_scored_promos, top_n=args.top_n)

    # 5. Quality Diagnostics & Honest Error Analysis
    quality_report = quality_checker.run_suite(final_ranked_promos)

    # 6. Export Production Assets
    os.makedirs(args.output_dir, exist_ok=True)
    json_path = os.path.join(args.output_dir, "all_promos.json")
    csv_path = os.path.join(args.output_dir, "top_ranked_promos.csv")
    quality_path = os.path.join(args.output_dir, "quality_diagnostics.json")
    edl_dir = os.path.join(args.output_dir, "edl_exports")

    PromoExporter.export_json(final_ranked_promos, json_path)
    PromoExporter.export_csv(final_ranked_promos, csv_path)
    
    with open(quality_path, 'w', encoding='utf-8') as f:
        import json
        json.dump(quality_report, f, indent=2)

    for p in final_ranked_promos[:10]:
        PromoExporter.export_edl(p, edl_dir)

    elapsed = time.time() - start_time

    # 7. Print Terminal Summary
    console.print("\n[bold green]Pipeline Execution Completed Successfully![/bold green]")
    console.print(f"Elapsed Time: [bold cyan]{elapsed:.2f} seconds[/bold cyan] (Processing rate: {elapsed/len(files):.2f}s/episode)\n")

    # Display Top 10 Table
    table = Table(title="[bold yellow]Top 10 Ranked Microdrama Promos (Ready for Ad Spend)[/bold yellow]")
    table.add_column("Rank", justify="center", style="cyan", no_wrap=True)
    table.add_column("Episode", justify="center", style="magenta")
    table.add_column("Timestamps", justify="center", style="green")
    table.add_column("Duration", justify="center")
    table.add_column("Campaign Funnel", style="bold")
    table.add_column("Hook (<3s)", style="italic")
    table.add_column("Cliffhanger Cut", style="italic")
    table.add_column("Score", justify="right", style="bold yellow")

    for p in final_ranked_promos[:10]:
        t_str = " + ".join([f"{s.start_str}-{s.end_str}" for s in p.segments])
        table.add_row(
            f"#{p.global_rank}",
            f"Ep {p.episode_number}",
            t_str,
            f"{p.total_duration_sec:.1f}s",
            p.campaign_category,
            p.hook_description[:35] + "...",
            p.cliffhanger_description[:35] + "...",
            f"{p.composite_score:.2f}"
        )

    console.print(table)

    # Display Quality & Failure Mode Summary
    q_table = Table(title="[bold red]Automated Quality Diagnostic & Failure Mode Analysis[/bold red]")
    q_table.add_column("Diagnostic Metric", style="cyan")
    q_table.add_column("Value / Count", style="bold")
    q_table.add_column("Editorial Action", style="italic")

    q_table.add_row("Clean Promos (Production Ready)", f"{quality_report['clean_promos']} / {quality_report['total_evaluated']}", "Approve for immediate rendering")
    q_table.add_row("Flagged for Context Review", f"{quality_report['flagged_for_editorial_review']}", "Check pronoun or speaker clarity")
    q_table.add_row("Weak Cliffhanger Warnings", f"{quality_report['warning_revisions_needed']}", "Adjust cut boundary by ±2s")
    
    for issue, count in quality_report["failure_mode_breakdown"].items():
        q_table.add_row(f"  • {issue}", str(count), "Specific heuristic edge case detected")

    console.print("\n", q_table)

    console.print(f"\n[bold]Generated Raw Outputs:[/bold]")
    console.print(f"  1. Comprehensive JSON: [cyan]{json_path}[/cyan]")
    console.print(f"  2. Tabular CSV: [cyan]{csv_path}[/cyan]")
    console.print(f"  3. Diagnostic Audit: [cyan]{quality_path}[/cyan]")
    console.print(f"  4. NLE Premiere EDLs: [cyan]{edl_dir}/[/cyan] (10 files)")

if __name__ == "__main__":
    main()
