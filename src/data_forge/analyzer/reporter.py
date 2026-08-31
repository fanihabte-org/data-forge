# data_forge/analyzer/reporter.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping
from data_forge.analyzer.analyzes import VolumeAnalysis

# ANSI Terminal Colors & Formatting
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


@dataclass
class AnalysesReporter:

    @staticmethod
    def _format_volume(volume: int) -> str:
        """Formats egress volume with dynamic threshold coloring."""
        if volume > 200_000:
            return f"{RED}{volume:,}{RESET} rows"
        elif volume > 0:
            return f"{GREEN}{volume:,}{RESET} rows"
        return f"{YELLOW}{volume:,}{RESET} rows (Empty)"

    @classmethod
    def report_analysis(cls, pipeline_name: str, volume_analysis: VolumeAnalysis) -> None:
        """Prints volume analysis metrics for a single table."""
        header = f"{pipeline_name.upper()} TABLE ANALYSIS"
        vol_str = cls._format_volume(volume_analysis.egress_volume)

        print(f"\n{BOLD}{CYAN}===================================================={RESET}")
        print(f"{BOLD}{CYAN}{header:^52}{RESET}")
        print(f"{BOLD}{CYAN}===================================================={RESET}\n")

        print(f"  ├─ Table          : {BOLD}{CYAN}{volume_analysis.table_name}{RESET}")
        print(f"  ├─ Schema         : {volume_analysis.schema_name}")
        print(f"  └─ Egress Volume  : {vol_str}")

        print(f"\n{BOLD}{CYAN}===================================================={RESET}\n")

    @classmethod
    def report_analyses(cls, pipeline_name: str, volume_analyses: Mapping[str, VolumeAnalysis]) -> None:
        """Prints volume analysis metrics for an entire catalog pipeline."""
        header = f"{pipeline_name.upper()} PIPELINE ANALYSIS"
        print(f"\n{BOLD}{CYAN}===================================================={RESET}")
        print(f"{BOLD}{CYAN}{header:^52}{RESET}")
        print(f"{BOLD}{CYAN}===================================================={RESET}\n")

        for table_name, analysis in volume_analyses.items():
            vol_str = cls._format_volume(analysis.egress_volume)

            print(f"  ├─ Table          : {BOLD}{table_name:<28}{RESET}")
            print(f"  │  ├─ Schema       : {analysis.schema_name}")
            print(f"  │  └─ Egress Volume: {vol_str}")
            print("  │")

        print(f"{BOLD}{CYAN}===================================================={RESET}\n")