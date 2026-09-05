#!/usr/bin/env python3
"""Assert the simulator refuses a configuration it cannot honour.

Each case breaks one field of a run the smoke already materialized, so the
inputs are the real ones and only the named field differs. A refusal must
exit nonzero, name the field, and leave no telemetry: a run directory holding
headers and no rows reads as a started run to every other tool in the chain.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable

if __package__ in (None, ""):  # pragma: no cover - script entry
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.ring_3d.run import find_default_binary  # noqa: E402


def _drop_the_clr_mask(run_dir: Path) -> list[str]:
    """Recovery reads the mask per trim and pulls on a step it cannot find."""
    return ["--clr-mask-configuration=empty"]


def _disagree_with_the_scaled_threshold(run_dir: Path) -> list[str]:
    """The integer the analyzer applies must equal llround of the float."""
    path = run_dir / "experiment.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    document["selection_policy"]["p_low_threshold"] += 1
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    return []


def _claim_more_ranks_than_the_fabric_has(run_dir: Path) -> list[str]:
    """The ledger is sized from scale.ranks; the fabric decides how many exist."""
    path = run_dir / "experiment.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    document["scale"]["ranks"] += 1
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    return []


# Each case breaks one field and names the phrase the refusal must carry.
CASES: tuple[tuple[str, Callable[[Path], list[str]], str], ...] = (
    ("recovery without a CLR mask", _drop_the_clr_mask, "clr-mask-configuration"),
    (
        "a scaled threshold that disagrees with its probability",
        _disagree_with_the_scaled_threshold,
        "p_low_threshold",
    ),
    (
        "a rank count the topology cannot supply",
        _claim_more_ranks_than_the_fabric_has,
        "does not match the topology",
    ),
)


def _run(binary: Path, run_dir: Path, extra: list[str]) -> subprocess.CompletedProcess:
    telemetry = run_dir / "refused_telemetry"
    command = [
        str(binary),
        f"--workload-configuration={run_dir / 'workload' / 'ring_3d'}",
        f"--system-configuration={run_dir / 'system.json'}",
        f"--network-configuration={run_dir / 'network_config.txt'}",
        f"--remote-memory-configuration={run_dir / 'remote_memory.json'}",
        f"--logical-topology-configuration={run_dir / 'logical_topology.json'}",
        f"--comm-group-configuration={run_dir / 'communicator_groups.json'}",
        f"--experiment-configuration={run_dir / 'experiment.json'}",
        f"--clr-mask-configuration={run_dir / 'clr_mask.csv'}",
        f"--experiment-output-dir={telemetry}",
        "--ns3-rng-seed=1",
        "--ns3-rng-run=1",
    ]
    for override in extra:
        flag = override.split("=", 1)[0]
        command = [argument for argument in command if not argument.startswith(flag)]
        command.append(override)
    return subprocess.run(command, capture_output=True, text=True, cwd=run_dir)


def check(source: Path, binary: Path) -> list[str]:
    """Return every case the simulator failed to refuse."""
    failures: list[str] = []
    for name, break_it, phrase in CASES:
        with tempfile.TemporaryDirectory() as scratch:
            run_dir = Path(scratch) / "run"
            shutil.copytree(source, run_dir)
            shutil.rmtree(run_dir / "telemetry", ignore_errors=True)
            extra = break_it(run_dir)
            result = _run(binary, run_dir, extra)
            output = result.stdout + result.stderr
            if result.returncode == 0:
                failures.append(f"{name} was accepted")
            elif phrase not in output:
                failures.append(
                    f"{name} was refused without naming it: "
                    f"{output.strip().splitlines()[-1:]!r}"
                )
            if (run_dir / "refused_telemetry").exists():
                failures.append(f"{name} left a telemetry directory behind")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "run", type=Path, help="a materialized recovery-domain run directory"
    )
    parser.add_argument("--binary", type=Path)
    arguments = parser.parse_args()
    binary = (
        arguments.binary.resolve()
        if arguments.binary is not None
        else find_default_binary()
    )
    failures = check(arguments.run.resolve(), binary)
    if failures:
        for failure in failures:
            print(f"refusal check failed: {failure}")
        return 1
    print(f"refusal checks passed: {len(CASES)} configurations refused")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
