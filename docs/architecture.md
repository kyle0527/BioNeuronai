# BioNeuronAI Architecture Whitepaper

BioNeuronAI brings together biologically inspired learning rules, novelty detection, and responsible security modules. This whitepaper clarifies the learning mechanisms, novelty computation pipeline, and module boundaries that structure the project.

## Learning Rules

BioNeuronAI adopts a Hebbian-style update rule that strengthens synapses when inputs and outputs co-activate. The `BioNeuron` class in `bioneuronai.core` records short-term input traces and applies a weighted update:

- **Input trace buffering** captures the last *N* input patterns and exponentially decays them so the neuron can respond to temporal correlations.
- **Hebbian weight update** increases or decreases synaptic weights proportional to the product of the current input and target activation, modulated by a configurable learning rate.
- **Stability clamp** in `ImprovedBioNeuron` ensures weights remain in biologically plausible bounds, preventing runaway excitation.

Higher-level constructs (`BioLayer`, `BioNet`) coordinate the learning procedure across layers, batching calls to each neuron and consolidating novelty scores for downstream pipelines.

## Novelty Computation

Novelty gating separates BioNeuronAI from conventional feed-forward architectures. Each neuron maintains a moving baseline of typical activations. When a new input deviates significantly from that baseline, a novelty score is emitted and propagated:

1. **Baseline estimation** keeps a rolling average of activation statistics per neuron.
2. **Deviation scoring** computes the absolute difference between the current activation and the baseline, normalized by standard deviation-like heuristics.
3. **Network aggregation** in `BioNet` merges per-neuron scores and exposes aggregate novelty metrics that pipelines or assistants can consume.
4. **Feedback for adaptation** optionally raises the learning rate when novelty exceeds a configurable threshold, enabling faster adaptation to new situations.

This mechanism supports tool gating, RAG orchestration, and safety monitors that require novelty awareness.

## Module Boundaries

The repository separates concerns so experimentation and production features remain maintainable:

- **Core neurons and networks** (`bioneuronai.core`, `bioneuronai.improved_core`) deliver the fundamental learning and novelty primitives.
- **Security hardening modules** (`bioneuronai.enhanced_auth_module`, `bioneuronai.production_idor_module`, `bioneuronai.production_sqli_module`) contain safeguards and detection heuristics that can wrap or monitor AI pipelines.
- **Pipelines and integrations** live in helper utilities such as `smart_assistant.py`, which consumes novelty metrics to guide developer workflows.
- **Documentation & tooling** under `docs/` and `.github/` ensure clarity, reproducibility, and automated validation via CI.

Each module exposes explicit entry points and docstrings that feed the API Reference. Integrators can import from the `bioneuronai` package boundary without reaching into private attributes, keeping the surface stable across releases.
