from __future__ import annotations

import time
from dataclasses import dataclass, field

# ANSI Terminal Colors & Formatting
GREEN = "\033[92m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
YELLOW = "\033[93m"
BOLD = "\033[1m"
RESET = "\033[0m"


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