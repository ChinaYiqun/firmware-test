# OpenRouter Qwen 27B / OpenCode：219 题全量静态评测

模型 ID：`qwen/qwen3.8-27b`；实际接口：`https://openrouter.ai/api/v1/messages`（Anthropic Messages 兼容协议）。
OpenCode `1.19.3`，并发 2，每题 600 秒，每题一次；只评 L0/L3，未做 SDK 编译或硬件运行。

运行区间（北京时间）：2026-10-21 19:08:29 至 2026-10-22 10:05:15。中间发生中断后续跑，该跨度包含停机时间，不能视为连续执行耗时。

| 指标 | 结果 |
|---|---:|
| 已结束 / 计划题数 | 219/219 |
| 通过 / 计划（端到端成功率） | 120/219（54.79%） |
| 通过 / 已评分 | 120/210（57.14%） |
| 评分失败 / 超时 / 无提交 | 90 / 6 / 3 |
| 最新每题耗时累加 | 25263.045 秒 |
| 平均 / 中位每题耗时 | 115.356 / 65.953 秒 |
| 观测 Token 总量 | 6,357,899 |
| 用量记录完整 / 部分 / 未知 | 213 / 5 / 1 |
| 尝试记录数（含中断记录） | 221 |

Token 为 CLI 事件累计，含输入、缓存及输出（含推理），存在不完整用量；不能当作准确账单，费用未知。耗时累加采用每题最新尝试，不等于并发后的墙钟时间，也不含被中断尝试的完整耗时。

请求参数沿用 OpenCode 默认值；本次未显式指定 temperature、top_p、top_k 或思考开关。不能将本轮与显式 temperature=0、关闭 thinking、不同输出预算及协议适配的本地 FP8 实验视为严格受控的模型对比。模型身份按请求 ID 记录，未独立验证 OpenRouter 后端权重。

## 逐题结果

完整的 219 题最新结果、221 条尝试元数据及静态检查通过/失败明细见 [results.json](results.json)。下表采用每题最新尝试。原始日志、提交、数据库和工作区仅保存在运行电脑；JSON 中的 local_artifact_directory 是本地路径，不是仓库链接。

| 题号 | SDK | 难度 | 状态 | 秒 | 观测 Token |
|---|---|---|---|---:|---:|
| boot-uboot-001 | embedded-linux | easy | scored_pass | 8.625 | 7854 |
| boot-uboot-002 | embedded-linux | hard | scored_pass | 113.656 | 33843 |
| boot-uboot-003 | embedded-linux | medium | scored_pass | 13.625 | 13056 |
| boot-uboot-004 | embedded-linux | hard | scored_pass | 99.422 | 39667 |
| linux-driver-001 | embedded-linux | hard | scored_pass | 24.469 | 13448 |
| linux-driver-002 | embedded-linux | medium | scored_pass | 24.078 | 9306 |
| linux-driver-003 | embedded-linux | medium | scored_fail | 17.656 | 11097 |
| linux-driver-004 | embedded-linux | hard | scored_pass | 53.625 | 22213 |
| linux-driver-005 | embedded-linux | hard | scored_pass | 11.047 | 10169 |
| linux-driver-006 | embedded-linux | hard | scored_fail | 110.860 | 19154 |
| linux-driver-007 | embedded-linux | hard | scored_pass | 22.250 | 11088 |
| linux-driver-008 | embedded-linux | medium | scored_pass | 20.453 | 11837 |
| linux-driver-009 | embedded-linux | hard | scored_fail | 32.265 | 14470 |
| linux-driver-010 | embedded-linux | hard | scored_pass | 188.797 | 64797 |
| linux-driver-011 | embedded-linux | hard | scored_fail | 99.812 | 48573 |
| linux-driver-012 | embedded-linux | hard | scored_pass | 307.313 | 23695 |
| linux-driver-013 | embedded-linux | hard | scored_fail | 50.516 | 25078 |
| linux-driver-014 | embedded-linux | hard | scored_pass | 55.328 | 16520 |
| linux-driver-015 | embedded-linux | medium | scored_pass | 87.407 | 27864 |
| linux-driver-016 | embedded-linux | medium | scored_fail | 85.610 | 27123 |
| linux-userspace-001 | embedded-linux | medium | scored_fail | 113.234 | 47619 |
| linux-userspace-002 | embedded-linux | hard | timeout | 600.578 | 未知 |
| linux-userspace-003 | embedded-linux | medium | scored_pass | 24.359 | 9755 |
| linux-userspace-004 | embedded-linux | medium | scored_pass | 28.266 | 16486 |
| linux-userspace-005 | embedded-linux | hard | scored_pass | 15.640 | 9998 |
| linux-userspace-006 | embedded-linux | hard | scored_pass | 20.671 | 11820 |
| linux-userspace-007 | embedded-linux | hard | scored_pass | 62.937 | 28317 |
| linux-userspace-008 | embedded-linux | hard | scored_fail | 186.812 | 49418 |
| networking-kernel-001 | embedded-linux | hard | scored_fail | 296.813 | 49053 |
| networking-kernel-002 | embedded-linux | hard | scored_fail | 197.016 | 31345 |
| networking-kernel-003 | embedded-linux | hard | scored_fail | 157.593 | 49639 |
| networking-kernel-004 | embedded-linux | hard | no_submission | 285.859 | 36187 |
| networking-kernel-005 | embedded-linux | medium | scored_pass | 51.938 | 11430 |
| ota-rauc-001 | embedded-linux | medium | scored_pass | 23.468 | 12011 |
| ota-rauc-002 | embedded-linux | hard | scored_fail | 16.047 | 10814 |
| ota-swupdate-001 | embedded-linux | medium | scored_fail | 91.813 | 23454 |
| ota-swupdate-002 | embedded-linux | hard | scored_fail | 35.110 | 20234 |
| ota-swupdate-003 | embedded-linux | hard | scored_fail | 87.421 | 36791 |
| ota-swupdate-004 | embedded-linux | medium | scored_fail | 65.953 | 34057 |
| yocto-001 | embedded-linux | medium | scored_pass | 14.469 | 9384 |
| yocto-002 | embedded-linux | easy | scored_pass | 38.500 | 39661 |
| yocto-003 | embedded-linux | medium | scored_pass | 329.391 | 19860 |
| yocto-004 | embedded-linux | medium | scored_pass | 308.094 | 27628 |
| yocto-005 | embedded-linux | hard | scored_pass | 130.719 | 27596 |
| yocto-006 | embedded-linux | hard | scored_pass | 43.782 | 33752 |
| yocto-007 | embedded-linux | medium | scored_fail | 17.047 | 8994 |
| yocto-008 | embedded-linux | hard | scored_pass | 92.625 | 23366 |
| yocto-009 | embedded-linux | medium | scored_fail | 48.141 | 9839 |
| yocto-010 | embedded-linux | hard | scored_pass | 26.875 | 33650 |
| yocto-011 | embedded-linux | hard | scored_pass | 27.078 | 9735 |
| yocto-012 | embedded-linux | medium | scored_fail | 14.032 | 13507 |
| esp-gpio-001 | esp-idf | easy | scored_pass | 17.671 | 10369 |
| esp-i2c-001 | esp-idf | medium | scored_fail | 182.422 | 15903 |
| esp-spi-001 | esp-idf | medium | scored_pass | 82.594 | 17851 |
| esp-timer-001 | esp-idf | medium | scored_pass | 66.953 | 26198 |
| esp-wifi-001 | esp-idf | medium | scored_pass | 46.516 | 30151 |
| stm32-freertos-001 | freertos | medium | scored_fail | 212.063 | 37014 |
| stm32-gpio-001 | stm32-hal | medium | scored_pass | 48.735 | 21345 |
| stm32-i2c-001 | stm32-hal | medium | scored_fail | 318.500 | 74257 |
| stm32-spi-001 | stm32-hal | medium | scored_fail | 66.203 | 51295 |
| stm32-uart-001 | stm32-hal | medium | timeout | 600.516 | ≥31957 |
| adc-001 | zephyr | medium | scored_fail | 35.484 | 24934 |
| adc-002 | zephyr | hard | scored_pass | 73.422 | 33884 |
| ble-001 | zephyr | hard | no_submission | 196.625 | 44604 |
| ble-002 | zephyr | easy | scored_pass | 115.078 | 52144 |
| ble-003 | zephyr | medium | scored_fail | 163.765 | 55413 |
| ble-004 | zephyr | medium | scored_pass | 210.953 | 28116 |
| ble-005 | zephyr | hard | scored_pass | 198.844 | 47030 |
| ble-006 | zephyr | hard | scored_pass | 141.125 | 33879 |
| ble-007 | zephyr | medium | scored_fail | 84.157 | 22348 |
| ble-008 | zephyr | hard | scored_fail | 446.578 | 76789 |
| boot-001 | zephyr | medium | timeout | 600.484 | ≥39975 |
| boot-003 | zephyr | medium | scored_pass | 20.297 | 18582 |
| boot-004 | zephyr | medium | scored_pass | 18.656 | 18321 |
| boot-005 | zephyr | hard | scored_pass | 64.156 | 18845 |
| boot-006 | zephyr | hard | scored_pass | 9.641 | 8291 |
| boot-007 | zephyr | medium | scored_pass | 11.250 | 8170 |
| boot-008 | zephyr | medium | scored_pass | 35.078 | 18120 |
| device-tree-001 | zephyr | medium | scored_pass | 51.938 | 9456 |
| device-tree-002 | zephyr | easy | scored_pass | 17.438 | 8573 |
| device-tree-003 | zephyr | easy | scored_fail | 23.281 | 10694 |
| device-tree-004 | zephyr | medium | scored_pass | 21.047 | 20292 |
| device-tree-005 | zephyr | hard | scored_pass | 16.844 | 10290 |
| device-tree-006 | zephyr | hard | scored_pass | 21.281 | 19004 |
| device-tree-007 | zephyr | medium | scored_pass | 35.094 | 24781 |
| device-tree-008 | zephyr | hard | scored_pass | 11.437 | 8575 |
| dma-001 | zephyr | medium | scored_fail | 53.125 | 22817 |
| dma-002 | zephyr | easy | timeout | 600.469 | ≥34099 |
| dma-003 | zephyr | hard | scored_fail | 122.844 | 36948 |
| dma-004 | zephyr | medium | scored_fail | 133.296 | 48882 |
| dma-005 | zephyr | hard | scored_fail | 41.109 | 15311 |
| dma-006 | zephyr | hard | scored_pass | 69.594 | 26655 |
| dma-007 | zephyr | hard | scored_fail | 314.046 | 63984 |
| dma-008 | zephyr | hard | scored_pass | 210.094 | 33491 |
| dma-009 | zephyr | hard | timeout | 600.515 | ≥8057 |
| dma-011 | zephyr | hard | scored_fail | 170.969 | 57667 |
| dma-012 | zephyr | hard | scored_fail | 183.828 | 70760 |
| gpio-basic-001 | zephyr | easy | scored_fail | 19.063 | 9827 |
| gpio-basic-005 | zephyr | medium | scored_fail | 28.907 | 9206 |
| gpio-basic-006 | zephyr | hard | scored_pass | 102.843 | 29881 |
| isr-concurrency-001 | zephyr | hard | scored_fail | 142.140 | 33148 |
| isr-concurrency-002 | zephyr | medium | scored_fail | 33.875 | 23261 |
| isr-concurrency-003 | zephyr | medium | scored_fail | 94.219 | 38854 |
| isr-concurrency-004 | zephyr | hard | scored_pass | 145.719 | 27982 |
| isr-concurrency-005 | zephyr | hard | scored_fail | 178.031 | 31985 |
| isr-concurrency-006 | zephyr | hard | scored_fail | 163.547 | 37067 |
| isr-concurrency-007 | zephyr | hard | scored_pass | 114.453 | 54617 |
| isr-concurrency-008 | zephyr | hard | scored_pass | 242.750 | 35131 |
| isr-concurrency-011 | zephyr | hard | scored_fail | 379.500 | 69807 |
| isr-concurrency-012 | zephyr | hard | scored_pass | 162.984 | 17484 |
| kconfig-001 | zephyr | easy | scored_fail | 17.438 | 9379 |
| kconfig-002 | zephyr | medium | scored_pass | 65.156 | 16629 |
| kconfig-003 | zephyr | easy | scored_pass | 57.969 | 23158 |
| kconfig-004 | zephyr | medium | scored_fail | 21.656 | 19679 |
| kconfig-005 | zephyr | hard | scored_fail | 417.360 | 74195 |
| kconfig-006 | zephyr | hard | scored_pass | 29.688 | 23901 |
| kconfig-007 | zephyr | medium | scored_pass | 26.078 | 18561 |
| kconfig-008 | zephyr | hard | scored_pass | 17.234 | 13381 |
| memory-opt-001 | zephyr | medium | scored_fail | 52.968 | 13335 |
| memory-opt-002 | zephyr | easy | scored_fail | 150.156 | 28986 |
| memory-opt-003 | zephyr | medium | scored_fail | 266.813 | 24802 |
| memory-opt-004 | zephyr | medium | scored_fail | 185.594 | 76019 |
| memory-opt-005 | zephyr | hard | scored_fail | 297.078 | 74075 |
| memory-opt-006 | zephyr | hard | scored_fail | 99.812 | 37697 |
| memory-opt-007 | zephyr | medium | scored_pass | 66.953 | 41990 |
| memory-opt-008 | zephyr | hard | scored_fail | 276.625 | 91649 |
| memory-opt-011 | zephyr | hard | scored_pass | 29.297 | 12776 |
| memory-opt-012 | zephyr | hard | no_submission | 179.219 | 35705 |
| networking-001 | zephyr | medium | scored_fail | 387.062 | 95465 |
| networking-002 | zephyr | easy | scored_pass | 22.656 | 19379 |
| networking-003 | zephyr | medium | scored_pass | 237.110 | 33051 |
| networking-004 | zephyr | medium | scored_pass | 348.359 | 36249 |
| networking-005 | zephyr | hard | scored_pass | 61.750 | 23120 |
| networking-006 | zephyr | hard | scored_pass | 31.282 | 12988 |
| networking-007 | zephyr | hard | scored_pass | 182.391 | 45089 |
| networking-008 | zephyr | medium | scored_fail | 45.312 | 18455 |
| ota-001 | zephyr | hard | scored_pass | 82.187 | 28825 |
| ota-002 | zephyr | easy | scored_pass | 15.031 | 9865 |
| ota-003 | zephyr | medium | scored_pass | 36.734 | 19746 |
| ota-004 | zephyr | medium | scored_pass | 64.719 | 13455 |
| ota-005 | zephyr | hard | scored_fail | 146.734 | 49073 |
| ota-006 | zephyr | hard | scored_pass | 50.719 | 27838 |
| ota-007 | zephyr | medium | scored_pass | 205.047 | 31022 |
| ota-008 | zephyr | hard | scored_pass | 61.969 | 37025 |
| ota-011 | zephyr | hard | scored_fail | 110.250 | 12568 |
| power-mgmt-001 | zephyr | medium | scored_fail | 176.406 | 40754 |
| power-mgmt-002 | zephyr | easy | scored_pass | 101.454 | 16626 |
| power-mgmt-003 | zephyr | medium | scored_pass | 16.844 | 10057 |
| power-mgmt-004 | zephyr | medium | scored_pass | 86.015 | 52678 |
| power-mgmt-005 | zephyr | hard | scored_pass | 447.765 | 73846 |
| power-mgmt-006 | zephyr | hard | scored_fail | 91.813 | 35292 |
| power-mgmt-007 | zephyr | medium | scored_pass | 27.781 | 23149 |
| power-mgmt-008 | zephyr | hard | scored_pass | 28.266 | 13936 |
| pwm-001 | zephyr | easy | scored_fail | 96.015 | 30379 |
| security-001 | zephyr | hard | scored_fail | 82.000 | 34225 |
| security-002 | zephyr | medium | scored_pass | 230.328 | 86825 |
| security-003 | zephyr | medium | scored_fail | 30.797 | 27766 |
| security-004 | zephyr | hard | scored_pass | 33.484 | 21794 |
| security-005 | zephyr | hard | scored_pass | 91.203 | 22275 |
| security-006 | zephyr | hard | scored_fail | 23.453 | 12101 |
| security-007 | zephyr | hard | scored_fail | 166.578 | 25814 |
| security-008 | zephyr | medium | scored_pass | 88.796 | 18351 |
| sensor-driver-001 | zephyr | medium | scored_pass | 80.203 | 13517 |
| sensor-driver-002 | zephyr | easy | scored_pass | 58.859 | 29861 |
| sensor-driver-003 | zephyr | medium | scored_fail | 17.047 | 11031 |
| sensor-driver-004 | zephyr | medium | scored_pass | 30.062 | 24709 |
| sensor-driver-005 | zephyr | hard | scored_pass | 72.578 | 35204 |
| sensor-driver-006 | zephyr | hard | scored_pass | 278.047 | 46363 |
| sensor-driver-007 | zephyr | medium | scored_fail | 24.875 | 13523 |
| sensor-driver-008 | zephyr | hard | scored_pass | 31.890 | 26602 |
| spi-i2c-001 | zephyr | medium | scored_pass | 21.047 | 18948 |
| spi-i2c-002 | zephyr | easy | scored_pass | 44.922 | 15259 |
| spi-i2c-003 | zephyr | medium | scored_pass | 38.922 | 20932 |
| spi-i2c-004 | zephyr | medium | scored_pass | 108.531 | 39997 |
| spi-i2c-005 | zephyr | hard | scored_fail | 118.250 | 23966 |
| spi-i2c-006 | zephyr | hard | scored_pass | 27.469 | 13659 |
| spi-i2c-007 | zephyr | medium | scored_pass | 17.438 | 11262 |
| spi-i2c-008 | zephyr | hard | scored_pass | 40.078 | 15026 |
| storage-001 | zephyr | medium | scored_fail | 16.859 | 9635 |
| storage-002 | zephyr | easy | scored_fail | 38.125 | 14501 |
| storage-003 | zephyr | medium | scored_fail | 459.969 | 67512 |
| storage-004 | zephyr | medium | scored_pass | 22.266 | 10033 |
| storage-005 | zephyr | hard | scored_pass | 217.937 | 98383 |
| storage-006 | zephyr | hard | scored_fail | 96.828 | 30749 |
| storage-007 | zephyr | medium | scored_pass | 82.594 | 36767 |
| storage-008 | zephyr | hard | scored_pass | 61.750 | 33275 |
| storage-012 | zephyr | hard | timeout | 600.547 | ≥21776 |
| storage-013 | zephyr | hard | scored_fail | 74.609 | 24187 |
| threading-001 | zephyr | medium | scored_fail | 22.453 | 11519 |
| threading-002 | zephyr | easy | scored_pass | 22.843 | 11347 |
| threading-003 | zephyr | medium | scored_pass | 122.516 | 29583 |
| threading-004 | zephyr | hard | scored_fail | 171.000 | 69706 |
| threading-005 | zephyr | hard | scored_pass | 16.485 | 10694 |
| threading-006 | zephyr | hard | scored_pass | 37.297 | 17405 |
| threading-007 | zephyr | medium | scored_fail | 26.094 | 10998 |
| threading-008 | zephyr | hard | scored_pass | 39.094 | 26872 |
| threading-011 | zephyr | hard | scored_fail | 31.484 | 15093 |
| threading-012 | zephyr | hard | scored_fail | 214.109 | 50396 |
| threading-013 | zephyr | hard | scored_fail | 520.109 | 51703 |
| threading-014 | zephyr | hard | scored_fail | 61.188 | 30426 |
| timer-001 | zephyr | easy | scored_fail | 17.656 | 18698 |
| timer-002 | zephyr | medium | scored_fail | 67.156 | 21707 |
| timer-003 | zephyr | medium | scored_pass | 27.266 | 15924 |
| timer-004 | zephyr | easy | scored_fail | 8.625 | 8094 |
| timer-005 | zephyr | hard | scored_pass | 14.453 | 10037 |
| timer-006 | zephyr | hard | scored_pass | 153.360 | 50837 |
| timer-007 | zephyr | medium | scored_fail | 40.312 | 24568 |
| timer-008 | zephyr | hard | scored_pass | 17.485 | 14148 |
| uart-001 | zephyr | easy | scored_fail | 14.031 | 9395 |
| uart-002 | zephyr | medium | scored_pass | 61.453 | 41887 |
| watchdog-001 | zephyr | easy | scored_fail | 139.906 | 26990 |
| watchdog-002 | zephyr | medium | scored_pass | 17.453 | 9903 |
| watchdog-003 | zephyr | easy | scored_fail | 25.469 | 21885 |
| watchdog-004 | zephyr | medium | scored_fail | 156.015 | 77299 |
| watchdog-005 | zephyr | hard | scored_fail | 278.016 | 47792 |
| watchdog-006 | zephyr | hard | scored_fail | 142.344 | 41497 |
| watchdog-007 | zephyr | medium | scored_fail | 107.610 | 42612 |
| watchdog-008 | zephyr | hard | scored_pass | 99.641 | 24885 |
| watchdog-010 | zephyr | hard | scored_pass | 289.875 | 101701 |
