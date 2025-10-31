"""Demonstrate building a configurable BioNet from YAML or JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

try:  # pragma: no cover - optional dependency
    import yaml
except Exception:  # pragma: no cover
    yaml = None

from bioneuronai.core import BioNet
from bioneuronai.networks import NetworkConfig


def load_network_config(path: Path) -> NetworkConfig:
    data_text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        if yaml is None:
            raise RuntimeError("PyYAML is required to load YAML configurations.")
        data = yaml.safe_load(data_text)
    else:
        data = json.loads(data_text)
    return NetworkConfig.from_dict(data)


def parse_inputs(values: Sequence[str]) -> list[float]:
    if not values:
        raise ValueError("No input values provided.")
    return [float(v) for v in values]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "config",
        type=Path,
        nargs="?",
        default=Path(__file__).with_name("multi_layer_topology.yaml"),
        help="Path to a YAML or JSON configuration file.",
    )
    parser.add_argument(
        "inputs",
        nargs="*",
        default=["0.2", "0.3", "0.4"],
        help="Input vector values for the network (floats).",
    )
    args = parser.parse_args()

    config = load_network_config(args.config)
    net = BioNet(network_config=config)

    input_vector = parse_inputs(args.inputs)
    if len(input_vector) != config.input_dim:
        raise ValueError(f"Input dimension {len(input_vector)} does not match config input_dim={config.input_dim}")

    final_output, previous_layer = net.forward(input_vector)
    print("Loaded topology:")
    print(json.dumps(config.to_dict(), indent=2, ensure_ascii=False))
    print("\nNetwork response:")
    print("  final layer:", final_output)
    print("  previous layer:", previous_layer)

    final_after_learning, history = net.learn(input_vector)
    print("\nAfter learning step (final layer output):", final_after_learning)
    print("Tracked layer outputs:", history)


if __name__ == "__main__":
    main()
