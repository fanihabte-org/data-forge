from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping
from data_forge.analyzer.analyzes import VolumeAnalysis

# ANSI Terminal Colors & Formatting
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
RESET = "\033[0m"


@dataclass
class AnalysesReporter:

    @classmethod
    def print_report(cls, pipeline_name: str, analyses: Mapping[str, VolumeAnalysis]) -> None:
        """Prints the volume analysis metrics for all tables in a pipeline."""
        header = f"{pipeline_name.upper()} PIPELINE ANALYSIS"
        print(f"\n{BOLD}{CYAN}===================================================={RESET}")
        print(f"{BOLD}{CYAN}{header:^52}{RESET}")
        print(f"{BOLD}{CYAN}===================================================={RESET}\n")

        for table_name, analysis in analyses.items():
            volume = analysis.egress_volume

            # Format row volume color
            if volume > 200_000:
                vol_str = f"{RED}{volume:,}{RESET}"
            elif volume > 0:
                vol_str = f"{GREEN}{volume:,}{RESET}"
            else:
                vol_str = f"{YELLOW}{volume:,}{RESET}"

            print(f"  ├─ Table: {BOLD}{table_name:<28}{RESET}")
            print(f"  │  ├─ Schema       : {analysis.schema_name}")
            print(f"  │  └─ Egress Volume: {vol_str} rows")
            print("  │")

        print(f"{BOLD}{CYAN}===================================================={RESET}\n")
