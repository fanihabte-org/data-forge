from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from data_forge.validator.validator import ValidationResult

# Color ANSI Codes
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
    def print_result(cls, result: ValidationResult) -> None:
        print(f"\n{BOLD}{CYAN}===================================================={RESET}")
        print(f"{BOLD}{CYAN}              DATABASE VALIDATION REPORT            {RESET}")
        print(f"{BOLD}{CYAN}===================================================={RESET}\n")

        # 1. High-Level Table Existence Checks
        print(f"{BOLD}1. TABLE EXISTENCE CHECKS{RESET}")
        print("-" * 52)

        for env_name, check in [
            ("Source Database", result.tables_in_source),
            ("Target Data Warehouse", result.tables_in_target),
        ]:
            badge = cls._status_badge(check.all_tables_exist)
            print(f"  • {env_name:<25} [{badge}]")
            if not check.all_tables_exist and check.missing_tables:
                print(f"    {RED}Missing Tables:{RESET} {', '.join(check.missing_tables)}")

        print("\n" + f"{BOLD}2. COLUMN STRUCTURE CHECKS{RESET}")
        print("-" * 52)

        # 2. Detailed Column Structure Checks
        environments = [
            ("Source Database", result.table_columns_in_source),
            ("Target Data Warehouse", result.table_columns_in_target),
        ]

        for env_name, tables in environments:
            print(f"\n  {BOLD}{CYAN}[ {env_name} ]{RESET}")
            if not tables:
                print(f"    {YELLOW}No column checks performed.{RESET}")
                continue

            for table_name, check in tables.items():
                badge = cls._status_badge(check.all_tables_exist)
                print(f"    ├─ Table: {BOLD}{table_name:<22}{RESET} [{badge}]")

                if not check.all_tables_exist and check.missing_tables:
                    missing = ", ".join(check.missing_tables)
                    print(f"    │  └─ {RED}Missing Columns:{RESET} {missing}")

        print(f"\n{BOLD}{CYAN}===================================================={RESET}\n")
