# Harness static pilot

Scope: L0+L3 only; L1/L2 not evaluated. Harness defaults are not parameter-aligned.

| Harness | Passed | Scored | Planned | End-to-end pass rate |
|---|---:|---:|---:|---:|
| opencode | 7 | 10 | 10 | 70.0% |
| claude-code | 7 | 10 | 10 | 70.0% |

| Harness | Case | Repeat | Status | Seconds |
|---|---|---:|---|---:|
| claude-code | dma-001 | 1 | scored_pass | 53.765 |
| claude-code | dma-003 | 1 | scored_fail | 51.11 |
| claude-code | gpio-basic-001 | 1 | scored_pass | 23.657 |
| claude-code | isr-concurrency-001 | 1 | scored_fail | 94.329 |
| claude-code | spi-i2c-001 | 1 | scored_pass | 25.453 |
| claude-code | spi-i2c-002 | 1 | scored_pass | 68.313 |
| claude-code | threading-001 | 1 | scored_fail | 44.469 |
| claude-code | threading-004 | 1 | scored_pass | 27.203 |
| claude-code | timer-002 | 1 | scored_pass | 54.719 |
| claude-code | uart-001 | 1 | scored_pass | 18.812 |
| opencode | dma-001 | 1 | scored_pass | 76.875 |
| opencode | dma-003 | 1 | scored_fail | 145.016 |
| opencode | gpio-basic-001 | 1 | scored_pass | 32.688 |
| opencode | isr-concurrency-001 | 1 | scored_fail | 154.578 |
| opencode | spi-i2c-001 | 1 | scored_pass | 29.766 |
| opencode | spi-i2c-002 | 1 | scored_pass | 49.235 |
| opencode | threading-001 | 1 | scored_fail | 56.985 |
| opencode | threading-004 | 1 | scored_pass | 24.25 |
| opencode | timer-002 | 1 | scored_pass | 47.234 |
| opencode | uart-001 | 1 | scored_pass | 32.11 |
