"""DECKDAEMON Gate B: source-only Tkinter viewer; no game or workflow controls.

Launch with: python -m deckdaemon_viewer.gui --snapshot-root PATH
This does not certify a mutable checkout, create a release, or run gameplay.
"""

from __future__ import annotations

import argparse
import tkinter as tk
from pathlib import Path
from tkinter import ttk

from .presentation import InspectionSession, ROSTER, TITLE
from .reader import EvidenceReadError


def build_window(snapshot_root: Path) -> tk.Tk:
    """Create a read-only viewer; caller owns the Tk event loop."""
    session = InspectionSession(snapshot_root)
    root = tk.Tk()
    root.title(TITLE)
    root.geometry("1000x650")
    root.minsize(650, 400)

    frame = ttk.Frame(root, padding=12)
    frame.pack(fill="both", expand=True)
    ttk.Label(frame, text=TITLE).pack(anchor="w")
    ttk.Label(frame, text=f"Snapshot root: {snapshot_root}").pack(anchor="w")
    ttk.Label(
        frame,
        text="Mutable local inputs are UNVERIFIED unless checked against an independent digest.",
    ).pack(anchor="w")

    content = ttk.Frame(frame)
    content.pack(fill="both", expand=True, pady=(12, 0))
    left = ttk.Frame(content)
    left.pack(side="left", fill="y", padx=(0, 12))
    ttk.Label(left, text="Preserved Prototype 0.1 decks").pack(anchor="w")
    decks = tk.Listbox(left, exportselection=False, height=16, width=24)
    for slug in ROSTER:
        decks.insert("end", slug)
    decks.pack(fill="y", expand=True)

    status = tk.StringVar(value="Select a preserved deck or Historical Baseline 005.")
    ttk.Label(frame, textvariable=status).pack(anchor="w", pady=(8, 0))
    pane = ttk.Frame(content)
    pane.pack(side="left", fill="both", expand=True)
    ttk.Label(pane, text="Evidence — read-only").pack(anchor="w")
    scrollbar = ttk.Scrollbar(pane, orient="vertical")
    scrollbar.pack(side="right", fill="y")
    view = tk.Text(pane, wrap="none", state="disabled", yscrollcommand=scrollbar.set)
    view.pack(side="left", fill="both", expand=True)
    scrollbar.configure(command=view.yview)

    def display(result: tuple[str, str]) -> None:
        label, body = result
        view.configure(state="normal")
        view.delete("1.0", "end")
        view.insert("1.0", body)
        view.configure(state="disabled")
        status.set(label)

    def show_error(error: EvidenceReadError) -> None:
        view.configure(state="normal")
        view.delete("1.0", "end")
        view.insert("1.0", f"REJECTED / NOT AVAILABLE\n{error}")
        view.configure(state="disabled")
        status.set("REJECTED — EVIDENCE NOT VERIFIED")

    def on_deck(_event: tk.Event[tk.Misc] | None = None) -> None:
        selected = decks.curselection()
        if not selected:
            return
        try:
            display(session.deck(ROSTER[selected[0]]))
        except EvidenceReadError as error:
            show_error(error)

    def on_baseline() -> None:
        decks.selection_clear(0, "end")
        try:
            display(session.baseline())
        except EvidenceReadError as error:
            show_error(error)

    decks.bind("<<ListboxSelect>>", on_deck)
    ttk.Button(left, text="Historical Baseline 005", command=on_baseline).pack(
        fill="x", pady=(12, 0)
    )
    decks.focus_set()
    return root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="DECKDAEMON read-only local inspection viewer")
    parser.add_argument(
        "--snapshot-root",
        type=Path,
        required=True,
        help="Explicit local snapshot root (never automatically discovered)",
    )
    args = parser.parse_args(argv)
    root = build_window(args.snapshot_root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
