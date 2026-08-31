# data_forge/resolver/reporter.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from data_forge.resolver.models import Resolution, WatermarkSyncResolution

# ANSI Terminal Colors & Formatting
GREEN = "\033[92m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
YELLOW = "\033[93m"
BOLD = "\033[1m"
RESET = "\033[0m"

# Default epoch watermark timestamp threshold
DEFAULT_EPOCH = datetime(1970, 1, 1, 0, 0, 0)


@dataclass
class ResolutionReporter:

    @classmethod
    def print_water_sync_resolution(
        cls, water_sync_resolution: WatermarkSyncResolution
    ) -> None:
        """Prints details when a watermark offset is missing and resolved."""
        table = water_sync_resolution.table
        synced_wm = water_sync_resolution.synced_watermark

        hw = synced_wm.highest_watermark
        hw_str = hw.strftime("%Y-%m-%d %H:%M:%S") if hw else "None"
        run_str = (
            synced_wm.dw_run_timestamp.strftime("%Y-%m-%d %H:%M:%S")
            if synced_wm.dw_run_timestamp
            else "None"
        )

        is_default = (hw is None) or (hw == DEFAULT_EPOCH)

        if is_default:
            action_desc = f"{YELLOW}Set Default Watermark (1970-01-01 00:00:00){RESET}"
            source_desc = f"{YELLOW}Default Initializer{RESET}"
        else:
            action_desc = f"{MAGENTA}Synced Watermark from Main Table{RESET}"
            source_desc = f"{CYAN}Target DW Table Max Column{RESET}"

        print(f"\n{BOLD}{MAGENTA}===================================================={RESET}")
        print(f"{BOLD}{MAGENTA}             WATERMARK RESOLUTION REPORT            {RESET}")
        print(f"{BOLD}{MAGENTA}===================================================={RESET}\n")

        print(f"  ├─ Table            : {BOLD}{CYAN}{table.name}{RESET}")
        print(f"  ├─ Action           : {action_desc}")
        print(f"  ├─ Origin Source    : {source_desc}")
        print(f"  ├─ Marking Column   : {synced_wm.marking_column}")
        print(f"  ├─ Resolved Value   : {GREEN}{hw_str}{RESET}")
        print(f"  └─ DW Run Timestamp : {run_str}")

        print(f"\n{BOLD}{MAGENTA}===================================================={RESET}\n")

    @classmethod
    def print_table_creation(cls, table_resolution: Resolution) -> None:
        """Prints details when a missing table is created in the target DW including PKs and columns."""
        table = table_resolution.table

        print(f"\n{BOLD}{MAGENTA}===================================================={RESET}")
        print(f"{BOLD}{MAGENTA}            TABLE CREATION RESOLUTION               {RESET}")
        print(f"{BOLD}{MAGENTA}===================================================={RESET}\n")

        print(f"  ├─ Table            : {BOLD}{CYAN}{table.name}{RESET}")
        print(f"  ├─ Action           : {MAGENTA}Created Table via DDL Execution{RESET}")
        print(f"  ├─ Status           : {GREEN}✔ Successfully Created{RESET}")

        # Extract primary keys if available
        primary_keys = getattr(table, "primary_keys", []) or []
        pk_set = set(primary_keys)

        if primary_keys:
            pk_str = ", ".join(primary_keys)
            print(f"  ├─ Primary Key(s)   : {YELLOW}🔑 [{pk_str}]{RESET}")

        # Format and display created columns
        if hasattr(table, "columns") and table.target_columns:
            column_count = len(table.target_columns)
            print(f"  ├─ Columns Created  : {BOLD}{column_count}{RESET} total columns")

            # Print each column with name, data type, and PK badge
            for idx, col in enumerate(table.target_columns):
                is_last = idx == len(table.target_columns) - 1
                branch = "  │  └─" if is_last else "  │  ├─"
                col_name = getattr(col, "name", str(col))
                col_type = getattr(col, "data_type", getattr(col, "type", ""))

                type_str = f" ({CYAN}{col_type}{RESET})" if col_type else ""
                pk_badge = f" {YELLOW}[PK]{RESET}" if col_name in pk_set else ""

                print(f"{branch} {col_name}{type_str}{pk_badge}")
        else:
            print(f"  └─ Columns Created  : {YELLOW}No column metadata specified{RESET}")

        print(f"\n{BOLD}{MAGENTA}===================================================={RESET}\n")