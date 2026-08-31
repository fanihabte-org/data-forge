from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping
from data_forge.validator.models import (
    TableValidationResult,
    WatermarkValidationResult,
    ValidationResult,
)

# ANSI Terminal Colors & Formatting
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


@dataclass
class ValidationReporter:

    @staticmethod
    def _status_badge(passed: bool) -> str:
        return f"{GREEN}✔ PASSED{RESET}" if passed else f"{RED}✖ FAILED{RESET}"

    @classmethod
    def _print_table_validation(cls, label: str, table_res: TableValidationResult) -> None:
        passed = table_res.exists and table_res.column_validation.all_exist
        badge = cls._status_badge(passed)
        print(f"  ├─ [{label}] Table: {BOLD}{table_res.table_name:<20}{RESET} [{badge}]")

        if not table_res.exists:
            print(f"  │  └─ {RED}Status:{RESET} Table does not exist in environment")
        elif not table_res.column_validation.all_exist and table_res.column_validation.missing_columns:
            missing = ", ".join(table_res.column_validation.missing_columns)
            print(f"  │  └─ {RED}Missing Columns:{RESET} {missing}")

    @classmethod
    def _print_watermark_validation(cls, watermark_res: WatermarkValidationResult) -> None:
        badge = cls._status_badge(watermark_res.exist)
        print(f"  ├─ [Watermark] Check                   [{badge}]")

        if watermark_res.exist and watermark_res.watermark:
            wm = watermark_res.watermark
            hw_str = (
                wm.highest_watermark.strftime("%Y-%m-%d %H:%M:%S")
                if wm.highest_watermark
                else "None"
            )
            run_str = (
                wm.dw_run_timestamp.strftime("%Y-%m-%d %H:%M:%S")
                if wm.dw_run_timestamp
                else "None"
            )
            print(f"  │  ├─ Marking Column   : {CYAN}{wm.marking_column}{RESET}")
            print(f"  │  ├─ Highest Watermark: {GREEN}{hw_str}{RESET}")
            print(f"  │  └─ DW Run Timestamp : {run_str}")
        else:
            print(f"  │  └─ {YELLOW}No watermark offset found.{RESET}")

    @classmethod
    def print_result(cls, results: ValidationResult) -> None:
        """Prints validation report for a single table across Source, Target, and Watermark."""
        print(f"\n{BOLD}{CYAN}===================================================={RESET}")
        print(f"{BOLD}{CYAN}             SINGLE TABLE VALIDATION                {RESET}")
        print(f"{BOLD}{CYAN}===================================================={RESET}\n")

        cls._print_table_validation("Source", results.source)
        cls._print_table_validation("Target", results.target)
        cls._print_watermark_validation(results.watermark)

        print(f"\n{BOLD}{CYAN}===================================================={RESET}\n")

    @classmethod
    def print_results(cls, results: Mapping[str, ValidationResult]) -> None:
        """Prints validation report for an entire catalog of tables."""
        print(f"\n{BOLD}{CYAN}===================================================={RESET}")
        print(f"{BOLD}{CYAN}             CATALOG VALIDATION REPORT              {RESET}")
        print(f"{BOLD}{CYAN}===================================================={RESET}\n")

        for table_name, validation_result in results.items():
            print(f"{BOLD}► TABLE: {CYAN}{table_name}{RESET}")
            print("-" * 52)
            cls._print_table_validation("Source", validation_result.source)
            cls._print_table_validation("Target", validation_result.target)
            cls._print_watermark_validation(validation_result.watermark)
            print("  │")

        print(f"{BOLD}{CYAN}===================================================={RESET}\n")