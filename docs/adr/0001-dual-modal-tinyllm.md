# 0001 - Keep Dual-Modal TinyLLM as an Architecture Path

## Status

Accepted

## Context

The project contains a TinyLLM implementation that supports text generation and numeric trading-signal mode. Existing deployment documentation also distinguishes the formal trading checkpoint from the ChatEngine checkpoint.

## Decision

Keep the dual-modal TinyLLM architecture as the target model path, while documenting current checkpoint separation clearly in public docs.

## Consequences

- README can describe the dual-modal architecture without claiming that every production path already uses one physical checkpoint.
- The project needs separate evidence for language quality, signal quality, and shared-weight behavior.
- Future training work can converge checkpoints only after walk-forward and chat-quality regression tests pass.
