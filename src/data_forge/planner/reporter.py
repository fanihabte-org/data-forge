from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, TYPE_CHECKING
from data_forge.planner.models import ExecutionType
from data_forge.analyzer.models import LazyAnalysis

if TYPE_CHECKING:
    from data_forge.planner.planner import Plan

# ANSI Terminal Colors & Formatting
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
RESET = "\033[0m"


@dataclass
class PipelineReporter:

    @staticmethod
    def _execution_badge(exec_type: ExecutionType) -> str:
        if exec_type == ExecutionType.BULK:
            return f"{MAGENTA}⚡ BULK{RESET}"
        elif exec_type == ExecutionType.INCREMENTAL:
            return f"{GREEN}🔄 INCREMENTAL{RESET}"
        elif exec_type == ExecutionType.SKIP:
            return f"{YELLOW}⏭  SKIP{RESET}"
        return str(exec_type)

    @classmethod
    def print_analysis_report(cls, pipeline_name: str, analyses: Mapping[str, LazyAnalysis]) -> None:
        """Prints the preflight analysis metrics for all tables in a pipeline."""
        header = f"{pipeline_name.upper()} PIPELINE ANALYSIS"
        print(f"\n{BOLD}{CYAN}===================================================={RESET}")
        print(f"{BOLD}{CYAN}{header:^52}{RESET}")
        print(f"{BOLD}{CYAN}===================================================={RESET}\n")

        for table_name, analysis in analyses.items():
            watermark_val = (
                str(analysis.watermark_check.object.highest_watermark)
                if analysis.watermark_check.exists and analysis.watermark_check.object
                else f"{RED}None (Epoch Default){RESET}"
            )
            volume = analysis.ingress_volume.egress_volume
            vol_str = f"{RED}{volume:,}{RESET}" if volume > 200_000 else f"{GREEN}{volume:,}{RESET}"

            print(f"  ├─ Table: {BOLD}{table_name:<28}{RESET}")
            print(f"  │  ├─ Watermark Exists : {analysis.watermark_check.exists}")
            print(f"  │  ├─ Highest Watermark: {watermark_val}")
            print(f"  │  └─ Ingress Volume   : {vol_str} rows")
            print("  │")

        print(f"{BOLD}{CYAN}===================================================={RESET}\n")

    @classmethod
    def print_execution_plan(cls, pipeline_name: str, plans: Mapping[str, Plan]) -> None:
        """Prints the scheduled execution strategy for each table."""
        header = f"{pipeline_name.upper()} PIPELINE EXECUTION PLAN"
        print(f"\n{BOLD}{CYAN}===================================================={RESET}")
        print(f"{BOLD}{CYAN}{header:^52}{RESET}")
        print(f"{BOLD}{CYAN}===================================================={RESET}\n")

        # Summary statistics
        bulk_count = sum(1 for p in plans.values() if p.execution_type == ExecutionType.BULK)
        inc_count = sum(1 for p in plans.values() if p.execution_type == ExecutionType.INCREMENTAL)
        skip_count = sum(1 for p in plans.values() if p.execution_type == ExecutionType.SKIP)

        print(f"{BOLD}PLAN SUMMARY:{RESET} Total Tables: {len(plans)} | "
              f"{MAGENTA}Bulk: {bulk_count}{RESET} | "
              f"{GREEN}Incremental: {inc_count}{RESET} | "
              f"{YELLOW}Skip: {skip_count}{RESET}\n")
        print("-" * 52)

        for table_name, plan in plans.items():
            badge = cls._execution_badge(plan.execution_type)
            print(f"  • Table: {BOLD}{table_name:<26}{RESET} [{badge}]")

        print(f"\n{BOLD}{CYAN}===================================================={RESET}\n")
