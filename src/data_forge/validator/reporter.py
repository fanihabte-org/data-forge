from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Union
from data_forge.validator.models import (
    TableValidationResult,
    WatermarkValidationResult,
    WatermarkValidationResultResolved
)

# ANSI Terminal Colors & Formatting
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
RESET = "\033[0m"


@dataclass
class ValidationReporter:

    @staticmethod
    def _status_badge(passed: bool) -> str:
        return f"{GREEN}✔ PASSED{RESET}" if passed else f"{RED}✖ FAILED{RESET}"

    @staticmethod
    def _resolution_badge(resolved: bool) -> str:
        if resolved:
            return f"{MAGENTA}🛠 RESOLVED{RESET}"
        return f"{YELLOW}⚠️ UNRESOLVED{RESET}"

    @classmethod
    def print_result(cls, results: dict[str, dict[str, TableValidationResult]]) -> None:
        """Prints schema and column structure validation report for source and target."""
        print(f"\n{BOLD}{CYAN}===================================================={RESET}")
        print(f"{BOLD}{CYAN}              DATABASE VALIDATION REPORT            {RESET}")
        print(f"{BOLD}{CYAN}===================================================={RESET}\n")

        # 1. High-Level Table Existence Checks
        print(f"{BOLD}1. TABLE EXISTENCE CHECKS{RESET}")
        print("-" * 52)

        for env_key, env_label in [("source", "Source Database"), ("target", "Target Data Warehouse")]:
            tables_map = results.get(env_key, {})
            all_tables_exist = all(res.exists for res in tables_map.values()) if tables_map else False
            badge = cls._status_badge(all_tables_exist)

            print(f"  • {env_label:<25} [{badge}]")

            missing_tables = [name for name, res in tables_map.items() if not res.exists]
            if missing_tables:
                print(f"    {RED}Missing Tables:{RESET} {', '.join(missing_tables)}")

        print("\n" + f"{BOLD}2. COLUMN STRUCTURE CHECKS{RESET}")
        print("-" * 52)

        # 2. Detailed Column Structure Checks
        for env_key, env_label in [("source", "Source Database"), ("target", "Target Data Warehouse")]:
            tables_map = results.get(env_key, {})
            print(f"\n  {BOLD}{CYAN}[ {env_label} ]{RESET}")

            if not tables_map:
                print(f"    {YELLOW}No column checks performed.{RESET}")
                continue

            for table_name, res in tables_map.items():
                passed = res.exists and res.column_validation.all_exist
                badge = cls._status_badge(passed)

                print(f"    ├─ Table: {BOLD}{table_name:<22}{RESET} [{badge}]")

                if not res.column_validation.all_exist and res.column_validation.missing_columns:
                    missing = ", ".join(res.column_validation.missing_columns)
                    print(f"    │  └─ {RED}Missing Columns:{RESET} {missing}")

        print(f"\n{BOLD}{CYAN}===================================================={RESET}\n")

    @classmethod
    def print_watermark_result(
            cls,
            results: Mapping[str, Union[WatermarkValidationResult, WatermarkValidationResultResolved]]
    ) -> None:
        """Prints watermark check results including resolution details."""
        print(f"\n{BOLD}{CYAN}===================================================={RESET}")
        print(f"{BOLD}{CYAN}             WATERMARK VALIDATION REPORT            {RESET}")
        print(f"{BOLD}{CYAN}===================================================={RESET}\n")

        for table_name, res in results.items():
            if res.exist:
                badge = cls._status_badge(True)
                print(f"  ├─ Table: {BOLD}{table_name:<28}{RESET} [{badge}]")
                if res.watermark:
                    wm = res.watermark
                    hw_str = wm.highest_watermark.strftime("%Y-%m-%d %H:%M:%S") if wm.highest_watermark else "None"
                    run_str = wm.dw_run_timestamp.strftime("%Y-%m-%d %H:%M:%S") if wm.dw_run_timestamp else "None"

                    print(f"  │  ├─ Marking Column   : {CYAN}{wm.marking_column}{RESET}")
                    print(f"  │  ├─ Highest Watermark: {GREEN}{hw_str}{RESET}")
                    print(f"  │  └─ DW Run Timestamp : {run_str}")
            else:
                # Table watermark was missing initially
                status_badge = cls._status_badge(False)
                res_badge = cls._resolution_badge(res.resolved)
                print(f"  ├─ Table: {BOLD}{table_name:<28}{RESET} [{status_badge}] [{res_badge}]")

                # Handle resolution output details
                if isinstance(res, WatermarkValidationResultResolved):
                    synced_wm = res.synced_watermark
                    hw_str = synced_wm.highest_watermark.strftime(
                        "%Y-%m-%d %H:%M:%S") if synced_wm.highest_watermark else "None"

                    print(f"  │  ├─ Action Taken     : {MAGENTA}Synced Watermark from Target DW{RESET}")
                    print(f"  │  ├─ Marking Column   : {CYAN}{synced_wm.marking_column}{RESET}")
                    print(f"  │  └─ Synced Watermark : {GREEN}{hw_str}{RESET}")
                else:
                    print(f"  │  └─ {YELLOW}No watermark available and no resolution performed.{RESET}")

            print("  │")

        print(f"{BOLD}{CYAN}===================================================={RESET}\n")