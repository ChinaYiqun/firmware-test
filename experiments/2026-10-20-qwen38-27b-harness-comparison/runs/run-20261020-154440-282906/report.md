# Harness static pilot

Scope: L0+L3 only; L1/L2 not evaluated. Harness defaults are not parameter-aligned.

| Harness | Passed | Scored | Planned | End-to-end pass rate |
|---|---:|---:|---:|---:|
| opencode | 2 | 8 | 10 | 20.0% |
| claude-code | 3 | 9 | 10 | 30.0% |

| Harness | Case | Repeat | Status | Seconds |
|---|---|---:|---|---:|
| claude-code | dma-001 | 1 | scored_fail | 121.453 |
| claude-code | dma-003 | 1 | scored_fail | 130.781 |
| claude-code | gpio-basic-001 | 1 | scored_fail | 16.531 |
| claude-code | isr-concurrency-001 | 1 | timeout | 600.875 |
| claude-code | spi-i2c-001 | 1 | scored_pass | 49.016 |
| claude-code | spi-i2c-002 | 1 | scored_pass | 59.656 |
| claude-code | threading-001 | 1 | scored_fail | 52.265 |
| claude-code | threading-004 | 1 | scored_fail | 16.313 |
| claude-code | timer-002 | 1 | scored_pass | 28.469 |
| claude-code | uart-001 | 1 | scored_fail | 17.781 |
| opencode | dma-001 | 1 | scored_fail | 150.829 |
| opencode | dma-003 | 1 | infra_error | 124.438 |
| opencode | gpio-basic-001 | 1 | scored_fail | 38.109 |
| opencode | isr-concurrency-001 | 1 | scored_fail | 398.765 |
| opencode | spi-i2c-001 | 1 | scored_pass | 37.063 |
| opencode | spi-i2c-002 | 1 | scored_pass | 25.531 |
| opencode | threading-001 | 1 | scored_fail | 62.953 |
| opencode | threading-004 | 1 | scored_fail | 31.297 |
| opencode | timer-002 | 1 | infra_error | 15.765 |
| opencode | uart-001 | 1 | scored_fail | 13.875 |
