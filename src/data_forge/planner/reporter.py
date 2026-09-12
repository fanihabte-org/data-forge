# data_forge/planner/reporter.py
from __future__ import annotations

import time
from dataclasses import dataclass, field
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


@dataclass
class ExecutionReporter:
    table_name: str
    execution_type: str  # "BULK", "INCREMENTAL", "SKIP", "SYNC_WATERMARK"

    start_time: float = field(init=False)
    units_processed: int = field(default=0, init=False)
    batch_count: int = field(default=0, init=False)

    def start(self) -> None:
        """Prints initial banner when execution starts."""
        self.start_time = time.perf_counter()
        badge = (
            f"{MAGENTA}⚡ BULK{RESET}"
            if self.execution_type == "BULK"
            else f"{GREEN}🔄 INCREMENTAL{RESET}"
        )
        print(f"\n{BOLD}{CYAN}► EXECUTING PIPELINE:{RESET} {BOLD}{self.table_name}{RESET} [{badge}]")

    def report_bulk_chunk(self, chunk_bytes: int) -> None:
        """Callback/Method for bulk streaming progress."""
        self.units_processed += chunk_bytes
        self.batch_count += 1

        elapsed = time.perf_counter() - self.start_time
        mb = self.units_processed / (1024 * 1024)
        speed = mb / elapsed if elapsed > 0 else 0

        print(
            f"\033[2K\r  ├─ [{CYAN}TRANSFERRING{RESET}] "
            f"Chunk #{self.batch_count:<4} | {BOLD}{mb:,.2f} MB{RESET} "
            f"({YELLOW}{speed:,.2f} MB/s{RESET})",
            end="",
            flush=True,
        )

    def report_incremental_batch(self, row_count: int) -> None:
        """Callback/Method for incremental batch insertion progress."""
        self.units_processed += row_count
        self.batch_count += 1

        elapsed = time.perf_counter() - self.start_time
        speed = self.units_processed / elapsed if elapsed > 0 else 0

        print(
            f"\033[2K\r  ├─ [{CYAN}INSERTING{RESET}] "
            f"Batch #{self.batch_count:<4} | {BOLD}{self.units_processed:,} rows{RESET} "
            f"({YELLOW}{speed:,.0f} rows/s{RESET})",
            end="",
            flush=True,
        )

    def report_skip(self) -> None:
        """Method for skipped executions."""
        print(f"  ├─ [{BOLD}{self.table_name}{RESET}] {YELLOW}⏭  SKIPPED{RESET} (0 egress rows)")

    def finish(self) -> None:
        """Prints summary upon execution completion."""
        elapsed = time.perf_counter() - self.start_time
        print("\033[2K\r", end="")  # Clear current line

        if self.execution_type == "BULK":
            mb = self.units_processed / (1024 * 1024)
            speed = mb / elapsed if elapsed > 0 else 0
            print(
                f"  └─ {GREEN}✔ COMPLETED{RESET} | Total: {BOLD}{mb:,.2f} MB{RESET} | "
                f"Chunks: {self.batch_count} | Time: {elapsed:.2f}s ({speed:,.2f} MB/s)"
            )
        elif self.execution_type == "INCREMENTAL":
            speed = self.units_processed / elapsed if elapsed > 0 else 0
            print(
                f"  └─ {GREEN}✔ COMPLETED{RESET} | Total: {BOLD}{self.units_processed:,} rows{RESET} | "
                f"Batches: {self.batch_count} | Time: {elapsed:.2f}s ({speed:,.0f} rows/s)"
            )