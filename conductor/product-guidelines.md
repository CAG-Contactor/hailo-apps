# Product Guidelines

## Core Principles
1. **Performance First:** The primary value of the Hailo accelerator is low-latency, high-throughput AI execution. All applications must minimize overhead (e.g., memory copies, inefficient post-processing) to showcase maximum hardware performance.
2. **Developer Experience (DX):** Code should serve as a clear, readable example for other developers. Complex hardware interactions should be wrapped in intuitive interfaces, favoring explicitness over cleverness.
3. **Cross-Platform Compatibility:** Features must be tested and robust across all supported environments: Ubuntu, Raspberry Pi, and Windows. Hardcoded paths and OS-specific assumptions must be avoided.
4. **AI-Driven Adaptability:** Embrace and support agentic development workflows, ensuring that application scaffolds are structured in a way that AI tools can easily parse, extend, and validate.

## Documentation & Style
- **Clarity and Precision:** Documentation must be technical, accurate, and concise. Avoid marketing fluff in technical guides.
- **Reproducibility:** Every application must include a definitive, easy-to-follow guide for environment setup, model download, and execution.
- **Code Comments:** Use descriptive comments for hardware-specific configurations (e.g., HailoRT context setups, GStreamer properties) to explain *why* a configuration is used, not just *what* it is doing.

## Architectural Guidelines
- **Modularity:** Keep models, post-processing logic, and the main execution loop logically separated.
- **Graceful Failure:** Ensure applications handle hardware unavailability (e.g., device not found, driver mismatch) gracefully with clear, actionable error messages rather than unhandled exceptions.