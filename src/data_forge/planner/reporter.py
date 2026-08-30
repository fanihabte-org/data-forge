from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, TYPE_CHECKING

from data_forge.planner.plans import ExecutionType

if TYPE_CHECKING:
    from data_forge.planner.plans import Plan

# ANSI Terminal Colors & Formatting
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"


@dataclass
class ExecutionReporter:

    @staticmethod
    def _execution_badge(exec_type: ExecutionType) -> str:
        if exec_type == ExecutionType.SYNC_WATERMARK:
            return f"{BLUE}🔄 SYNC_WM{RESET}"
        elif exec_type == ExecutionType.BULK:
            return f"{MAGENTA}⚡ BULK{RESET}"
        elif exec_type == ExecutionType.INCREMENTAL:
            return f"{GREEN}🔄 INCREMENTAL{RESET}"
        elif exec_type == ExecutionType.SKIP:
            return f"{YELLOW}⏭  SKIP{RESET}"
        return str(exec_type)

    @classmethod
    def print_report(cls, pipeline_name: str, plans: Mapping[str, Plan]) -> None:
        """Prints the scheduled execution strategy for each table."""
        header = f"{pipeline_name.upper()} PIPELINE EXECUTION PLAN"
        print(f"\n{BOLD}{CYAN}===================================================={RESET}")
        print(f"{BOLD}{CYAN}{header:^52}{RESET}")
        print(f"{BOLD}{CYAN}===================================================={RESET}\n")

        # Summary statistics across all 4 execution types
        sync_wm_count = sum(1 for p in plans.values() if p.execution_type == ExecutionType.SYNC_WATERMARK)
        bulk_count = sum(1 for p in plans.values() if p.execution_type == ExecutionType.BULK)
        inc_count = sum(1 for p in plans.values() if p.execution_type == ExecutionType.INCREMENTAL)
        skip_count = sum(1 for p in plans.values() if p.execution_type == ExecutionType.SKIP)

        print(
            f"{BOLD}PLAN SUMMARY:{RESET} Total Tables: {len(plans)} | "
            f"{BLUE}Sync Watermark: {sync_wm_count}{RESET} | "
            f"{MAGENTA}Bulk: {bulk_count}{RESET} | "
            f"{GREEN}Incremental: {inc_count}{RESET} | "
            f"{YELLOW}Skip: {skip_count}{RESET}\n"
        )
        print("-" * 52)

        for table_name, plan in plans.items():
            badge = cls._execution_badge(plan.execution_type)
            print(f"  • Table: {BOLD}{table_name:<26}{RESET} [{badge}]")

        print(f"\n{BOLD}{CYAN}===================================================={RESET}\n")
