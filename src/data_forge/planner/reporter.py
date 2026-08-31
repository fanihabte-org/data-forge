# data_forge/planner/reporter.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, TYPE_CHECKING

from data_forge.planner.plans import ExecutionType

if TYPE_CHECKING:
    from data_forge.planner.plans import Plan

# ANSI Terminal Colors & Formatting
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"


@dataclass
class PlanReporter:

    @staticmethod
    def _execution_badge(exec_type: ExecutionType) -> str:
        if exec_type == ExecutionType.SYNC_WATERMARK:
            return f"{BLUE}🔄 SYNC_WATERMARK{RESET}"
        elif exec_type == ExecutionType.BULK:
            return f"{MAGENTA}⚡ BULK_LOAD{RESET}"
        elif exec_type == ExecutionType.INCREMENTAL:
            return f"{GREEN}🔄 INCREMENTAL{RESET}"
        elif exec_type == ExecutionType.SKIP:
            return f"{YELLOW}⏭  SKIP{RESET}"
        return str(exec_type)

    @classmethod
    def print_plan(cls, plan: Plan, pipeline_name: str) -> None:
        """Prints the execution plan for a single table."""
        header = f"{pipeline_name.upper()} TABLE EXECUTION PLAN"
        badge = cls._execution_badge(plan.execution_type)

        hw_val = (
            plan.watermark.highest_watermark.strftime("%Y-%m-%d %H:%M:%S")
            if plan.watermark and plan.watermark.highest_watermark
            else "None"
        )
        run_str = plan.run_datetime.strftime("%Y-%m-%d %H:%M:%S")

        print(f"\n{BOLD}{CYAN}===================================================={RESET}")
        print(f"{BOLD}{CYAN}{header:^52}{RESET}")
        print(f"{BOLD}{CYAN}===================================================={RESET}\n")

        print(f"  ├─ Table            : {BOLD}{CYAN}{plan.table.name}{RESET}")
        print(f"  ├─ Execution Plan   : [{badge}]")
        print(f"  ├─ Scheduled Run    : {run_str}")
        print(f"  └─ Watermark Offset : {GREEN}{hw_val}{RESET}")

        print(f"\n{BOLD}{CYAN}===================================================={RESET}\n")

    @classmethod
    def print_plans(cls, plans: Mapping[str, Plan], pipeline_name: str) -> None:
        """Prints the execution plan summary across an entire catalog."""
        header = f"{pipeline_name.upper()} PIPELINE EXECUTION PLAN"
        print(f"\n{BOLD}{CYAN}===================================================={RESET}")
        print(f"{BOLD}{CYAN}{header:^52}{RESET}")
        print(f"{BOLD}{CYAN}===================================================={RESET}\n")

        # Summary statistics across all execution types
        bulk_count = sum(1 for p in plans.values() if p.execution_type == ExecutionType.BULK)
        inc_count = sum(1 for p in plans.values() if p.execution_type == ExecutionType.INCREMENTAL)
        skip_count = sum(1 for p in plans.values() if p.execution_type == ExecutionType.SKIP)

        print(
            f"{BOLD}PLAN SUMMARY:{RESET} Total Tables: {len(plans)} | "
            f"{MAGENTA}Bulk: {bulk_count}{RESET} | "
            f"{GREEN}Incremental: {inc_count}{RESET} | "
            f"{YELLOW}Skip: {skip_count}{RESET}\n"
        )
        print("-" * 52)

        for table_name, plan in plans.items():
            badge = cls._execution_badge(plan.execution_type)
            print(f"  ├─ Table: {BOLD}{table_name:<26}{RESET} [{badge}]")

        print(f"\n{BOLD}{CYAN}===================================================={RESET}\n")