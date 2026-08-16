#!/usr/bin/env python3
"""Interaktiver Test-Launcher für drivers.Rolladoino.

Beispiel:
    python3 scripts/test_rolladoino.py
"""

import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def input_choice(prompt, options, default=None):
    while True:
        if default is not None:
            value = input(f"{prompt} [{default}]: ").strip() or default
        else:
            value = input(f"{prompt}: ").strip()

        if value in options:
            return value

        print(f"Ungültig. Bitte eine der Optionen wählen: {', '.join(options)}")


def input_int(prompt, minimum=None, maximum=None, default=None):
    while True:
        raw = input(f"{prompt}{f' [{default}]' if default is not None else ''}: ").strip()
        if not raw and default is not None:
            raw = str(default)

        try:
            value = int(raw)
        except ValueError:
            print("Bitte eine ganze Zahl eingeben.")
            continue

        if minimum is not None and value < minimum:
            print(f"Wert muss >= {minimum} sein.")
            continue
        if maximum is not None and value > maximum:
            print(f"Wert muss <= {maximum} sein.")
            continue
        return value


def main():
    print("=== Rolladoino Test-Launcher ===")
    print(f"Repo-Root: {REPO_ROOT}")

    # Nach den Parametern fragen
    floor = input_choice("Stockwerk / floor", ["EGN", "EGS", "OGN", "OGS"], default="EGN")
    address = input("I2C-Adresse (z.B. 0x20 oder 32): ").strip()
    if not address:
        print("Adresse ist erforderlich.")
        sys.exit(1)

    commands = [
        "CMD_Rolladen_Hoch",
        "CMD_Rolladen_Runter",
        "CMD_Rolladen_Stop",
        "CMD_Luefter",
        "CMD_Read_Pos",
        "CMD_Summer",
    ]
    command = input_choice("Befehl", commands, default="CMD_Read_Pos")

    extra_args = []
    if command == "CMD_Luefter":
        stufe = input_int("Stufe", minimum=0, maximum=3, default=0)
        extra_args.extend(["--stufe", str(stufe)])
    elif command == "CMD_Summer":
        summer = input_int("Summer (0=aus, 1=an, 2=Toggle)", minimum=0, maximum=2, default=0)
        extra_args.extend(["--summer", str(summer)])

    script_path = REPO_ROOT / "drivers" / "Rolladoino.py"
    if not script_path.exists():
        print(f"Fehler: Rolladoino.py wurde nicht gefunden unter {script_path}")
        sys.exit(1)

    python_cmd = [sys.executable, "-m", "drivers.Rolladoino", floor, address, command, *extra_args]

    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT) + os.pathsep + env.get("PYTHONPATH", "")

    print("\nAuszuführender Befehl:")
    print(" ".join(python_cmd))

    try:
        subprocess.run(python_cmd, cwd=str(REPO_ROOT), env=env, check=False)
    except KeyboardInterrupt:
        print("\nAbbruch durch Benutzer.")
        sys.exit(130)


if __name__ == "__main__":
    main()
