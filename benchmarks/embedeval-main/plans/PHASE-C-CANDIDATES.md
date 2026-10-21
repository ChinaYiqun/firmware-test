---
type: scoping
task_slug: linux-tc-phase-c-candidates
status: scoping
created: 2026-04-19
last-reviewed: 2026-04-19
tags: [embedeval, phase-c, scoping, ebpf, ota, swupdate, rauc, linux-networking, kernel-dt-bindings]
---

# Phase C candidate scoping

**Purpose:** Rank the four deferred Phase C candidates identified in
Phase A/B PLANs, so the next `/myplan` can start from a sized, risk-tagged
scope instead of re-researching mid-plan.

**Current state as of commit `8423040`:**
281 TCs (233 public + 48 private), 24 categories, Phase A/B complete.
Linux userspace + Linux driver + Yocto + U-Boot all covered at baseline
depth. Next decision: which of four candidates lands as Phase C-1.

**Ranking axes:**
1. **Factor-coverage delta** — how many currently-empty 42-factor cells gain
   empirical coverage.
2. **Blast radius** — enum churn, runner/evaluator refactor, multi-file
   reference support, `case_git_hash` impact.
3. **Implementation cost** — hours calibrated against Phase A (9–12h for
   15 TCs) and Phase B (10–14h for 8 TCs + 1 enum).
4. **External dependency risk** — Docker image additions, toolchain
   requirements, kernel feature requirements.

---

## Candidate 1: eBPF multi-file reference support

**Origin:**
[PLAN-linux-tc-expansion-phase-b.md:30](PLAN-linux-tc-expansion-phase-b.md)
— "Multi-file `reference/` support is deferred to a Phase C refactor."
Phase B shipped `linux-userspace-008` as BPF-program-only so the single-file
`reference/main.c` constraint held; userspace loader + generated skeleton
header were out of scope.

**Scope sketch:**
- Infrastructure refactor (NOT TC authoring): lift the single-file
  `reference/main.c` assumption across the evaluator + runner + scripts.
  Concretely, extend `CaseMetadata` with a `reference_files: list[str] | None`
  field (default `None` → "single-file, use reference/main.c" for backwards
  compatibility) and thread it through.
- Touch sites (identified by `grep`):
  - `src/embedeval/bugfix.py:74,88,90,93` — reference loading
  - `src/embedeval/cli.py:864,920,924` — smoke-test + CMakeLists sanity
  - `src/embedeval/evaluator.py:385,1047,1126` — generated-code layout
  - `scripts/generate_expected_output.py:197`
  - `scripts/verify_negatives_oracle.py:83`
  - `scripts/verify_references_build.py:68-98`
  - `scripts/verify_results.py:129`
- LLM output contract: either (a) LLM emits multiple markdown code blocks
  with filename headers (pattern: `// FILE: foo.c` / code-block language +
  filename) or (b) test cases with >1 file only support reference evaluation,
  not LLM generation. Option (b) is simpler, lower-leverage.
- Post-infra: re-author `linux-userspace-008` to include the userspace
  loader (`.c`) + generated skeleton header stub, making the TC end-to-end
  buildable with `bpftool`. Add 2–3 more multi-file TCs that were impractical
  before: OTA descriptor + payload, Yocto multi-recipe, sd-bus vtable split.

**Factor-coverage delta:**
| Factor | Current | After Candidate 1 |
|--------|---------|-------------------|
| F6 (build integration) | partial | full (multi-file recipes addressable) |
| F1 (API hallucination) | partial | unchanged (same per-TC) |
| C8 (linker script) | Theoretical | Empirical (could add multi-module link TCs) |
| System-level integration (no factor cell) | 0 | opens door to 3–4 Empirical TCs |

Opens Phase D/E opportunities rather than directly filling existing gaps.

**Blast radius:**
- Enum change: **No**
- Runner/evaluator refactor: **Yes, ~8 touch sites** + `CaseMetadata` schema extension
- Multi-file reference support: **Yes** (the whole point)
- `case_git_hash` churn: **No** (existing TCs keep single-file layout; schema
  extension is additive with `None` default, so metadata bytes unchanged)

**Estimated effort:** **14–18h** — 6–8h infra refactor + tests, 4–6h
re-authoring linux-userspace-008 multi-file, 4h additional multi-file TCs to
justify the refactor.

**External dependency risk:**
- Docker image: needs `clang -target bpf` + `bpftool` + BTF-enabled
  kernel image for the re-authored 008 → **High**; the BPF toolchain is
  non-trivial to provision.
- Runtime dependencies: generating `vmlinux.h` at build time requires a
  kernel image with `CONFIG_DEBUG_INFO_BTF=y` — not every Yocto image has
  this. Fallback: ship a synthetic `vmlinux.h` stub in the case's
  `reference/` dir.

**Recommendation:** **Defer.** The infra refactor is valuable but the
payoff is mostly optionality (unlocks future multi-file TCs), not direct
factor-coverage delta. Phase B's BPF-only `linux-userspace-008` already
captures the eBPF failure-mode signal; making it "properly multi-file" is
polish, not a new capability. Revisit after one of the other candidates
exposes additional multi-file pressure (e.g. OTA's manifest + payload +
signature triple).

**Upstream references:**
- libbpf-bootstrap (github.com/libbpf/libbpf-bootstrap) — canonical
  `.bpf.c` + `.c` + generated skeleton layout.
- Linux `Documentation/bpf/libbpf/` — CO-RE + BTF requirements.

---

## Candidate 2: Linux OTA (SWUpdate + RAUC)

**Origin:**
[PLAN-linux-tc-expansion-phase-b.md:202](PLAN-linux-tc-expansion-phase-b.md)
— "Adding Linux OTA deserves its own mini-plan (`PLAN-linux-ota-expansion`),
not a squeeze into Phase B." User's real BSP is SWUpdate + Azure ADU per
MEMORY.md context — this candidate mirrors production reality.

**Scope sketch:**
- Reuse existing `ota` category + `embedded-linux` SDK bucket → **zero enum
  churn**. Contrast with the 9 existing Zephyr MCUboot OTA TCs
  (`cases/zephyr/ota-001..008,011`) which stay put.
- Target TC count: **6–8 TCs** across two tools:
  - SWUpdate (4 TCs):
    - `ota-swupdate-001`: `sw-description` with minimal image triple
      (bootloader + kernel + rootfs), dual-bank layout
    - `ota-swupdate-002`: A/B bootcnt failback (matches user's BSP-deploy
      dual-bank mechanism — see user's `bsp-deploy` skill)
    - `ota-swupdate-003`: signed update (RSA/SHA256) — image verify +
      signature reject path
    - `ota-swupdate-004`: embedded scripts (pre/post-install handlers) +
      idempotency
  - RAUC (2–4 TCs):
    - `ota-rauc-001`: `manifest.raucm` minimal bundle (INI grammar,
      [update]/[bundle]/[image.<slot>] sections)
    - `ota-rauc-002`: slot config + atomic switchover
    - `ota-rauc-003` (stretch): hooks + custom scripts
    - `ota-rauc-004` (stretch): handler integration with systemd
      `rauc.service`
- Directive-heavy grammar → implicit-prompt exemption applies per Phase A/B
  policy (same treatment as systemd unit directives, udev rule keys, Yocto
  bbclass).

**Factor-coverage delta:**
| Factor | Current | After Candidate 2 |
|--------|---------|-------------------|
| E4 (rollback & recovery) | Empirical (Zephyr MCUboot) | strengthened — Linux A/B slot + failback |
| E2 (return value checking) | Empirical | unchanged |
| F6 (build/tool integration) | Empirical | + SWUpdate libconfig + RAUC INI grammar |
| F4 (SDK version) | Research | + strengthens with SWUpdate/RAUC versioning |
| A-series (HW awareness) | — | low delta |

Factor novelty is modest (E4 already empirical from Zephyr side). Real
value: **production-realism + cross-platform E4 discriminator** — LLMs
likely over-train on MCUboot and generalize poorly to Linux A/B slot
mechanics.

**Blast radius:**
- Enum change: **No**
- Runner/evaluator refactor: **None** (text-file TCs, `native_sim` platform,
  reuse existing OTA category's check patterns)
- Multi-file reference support: **Not required** for 001–002 per tool (single
  `sw-description` or `manifest.raucm` file); 003–004 scripts TCs likely
  need multi-file (trigger Candidate 1 dependency or defer scripts TCs).
- `case_git_hash` churn: **No**

**Estimated effort:** **8–12h** — 4 SWUpdate TCs (~5h) + 2 minimal RAUC TCs
(~3h) + shared helper module in `check_utils.py` for SWUpdate/RAUC parsers
(~2h) + baseline benchmark (~2h).

**External dependency risk:**
- Docker image: ideally `swupdate` binary for `swupdate -c` config
  parse-check, and `rauc` binary for `rauc info`. Both available in kirkstone
  Yocto layers (meta-swupdate, meta-rauc). → **Medium**; static regex checks
  work without binaries but compile validation would require them.
- No kernel feature requirements for static TCs; runtime validation needs a
  Linux VM + partitions (out of scope for Phase C-1 regardless).
- Text-only TCs fall back cleanly to `native_sim` + `l1_skip: true`.

**Recommendation:** **Go — strongest Phase C-1 candidate.** Matches user's
production BSP, directly complements the existing 9 Zephyr OTA TCs, zero
infrastructure churn, directive-grammar pattern well-established from
Phase B's systemd/udev work. Implicit-prompt discipline carries over with
minimal policy extension.

**Upstream references:**
- SWUpdate docs: sbabic.github.io/swupdate/ (`sw-description` syntax,
  signed update chain, handlers).
- RAUC docs: rauc.readthedocs.io/ (`manifest.raucm`, slot definitions,
  system.conf).
- meta-swupdate / meta-rauc kirkstone branches.

---

## Candidate 3: Linux networking kernel (netfilter / sockets / netlink)

**Origin:** Phase A gap analysis
([PLAN-linux-tc-expansion-phase-a.md:81](PLAN-linux-tc-expansion-phase-a.md))
— existing `networking` category is 8 Zephyr TCs + 1 ESP-IDF WiFi + 1 STM32
UART; kernel-space networking (netfilter hooks, `sk_buff` handling, socket
filter BPF, netlink) is not represented.

**Scope sketch:**
- Category decision: reuse `networking` category with `sdk: embedded-linux`,
  OR extend with a new `linux-networking-kernel` category. **Reuse is
  preferred** — the category is about the problem domain, not the platform.
  → **zero enum churn**.
- Target TC count: **5–7 TCs**:
  - `networking-kernel-001`: netfilter hook (NF_INET_PRE_ROUTING) —
    register/unregister lifecycle, context restrictions (softirq-safe)
  - `networking-kernel-002`: `sk_buff` consume/dequeue error paths
  - `networking-kernel-003`: netlink socket create + bind + recvmsg
  - `networking-kernel-004`: packet socket (`AF_PACKET`) + classic BPF
    filter (sock_filter / BPF_JMP / BPF_RET)
  - `networking-kernel-005`: socket options (TCP_NODELAY, SO_TIMESTAMP)
    + `setsockopt` error handling
  - `networking-kernel-006` (stretch): generic netlink family registration
  - `networking-kernel-007` (stretch): TC (traffic control) classifier hook

**Factor-coverage delta:**
| Factor | Current | After Candidate 3 |
|--------|---------|-------------------|
| D4/D5/D6 (concurrency) | Empirical (linux-driver) | + softirq context discipline (distinct from IRQ/process context) |
| E1 (error path cleanup) | Empirical | + netfilter hook unregister on failure |
| E2 (return value checking) | Empirical | + `skb_dequeue` / `netlink_unicast` error paths |
| F5 (header knowledge) | Empirical | + `linux/netfilter.h`, `net/sock.h`, `linux/netlink.h` |

Incremental factor strengthening, not new factor cells. Value: **distinct
concurrency context** — softirq vs IRQ vs process vs ISR — is a knowledge
gap the existing `linux-driver` TCs don't cover.

**Blast radius:**
- Enum change: **No** (reuse `networking` category)
- Runner/evaluator refactor: **None** (C source, `platform: docker_only`
  with `l1_skip: true` pattern)
- Multi-file reference support: **Not required** (single-file kernel
  modules)
- `case_git_hash` churn: **No**

**Estimated effort:** **10–14h** — 5 TCs (~8h) + 2 stretch TCs (~3h) +
shared helper for netlink/netfilter/sk_buff parsers (~2h) + baseline
benchmark (~2h).

**External dependency risk:**
- Docker image: kernel headers for 5.15 (already present from Phase A);
  netfilter + netlink headers included by default. → **Low**.
- No special toolchain; compile-check possible with existing Docker image.
- `l1_skip: true` fallback for TCs that trigger kernel-version-specific
  netfilter API differences (5.15 vs 6.x).

**Recommendation:** **Go — strong Phase C-2 candidate.** Smaller factor
delta than OTA but very clean execution path: no enum churn, no infra
refactor, reuses Phase A's linux-driver patterns (static + behavior +
negatives + 12-mutation oracle). A natural "Phase C-2" after OTA.

**Upstream references:**
- Linux `Documentation/networking/` — netfilter hooks, netlink sockets.
- `net/core/skbuff.c` + `net/netfilter/core.c` in kernel 5.15.
- Rostedt et al., "Linux Kernel Networking" book — canonical patterns.

---

## Candidate 4: Kernel DT bindings YAML

**Origin:** Phase A gap
([PLAN-linux-tc-expansion-phase-a.md:81](PLAN-linux-tc-expansion-phase-a.md))
— existing `device-tree` category is 8 Zephyr DT overlays
(`cases/zephyr/device-tree-001..008`). Kernel DT bindings
(`Documentation/devicetree/bindings/<vendor>/<device>.yaml`) are a distinct
artifact: YAML schema files validated by `dt-validate`.

**Scope sketch:**
- Category decision: reuse `device-tree` category with `sdk: embedded-linux`
  → **zero enum churn**.
- Target TC count: **4–6 TCs**:
  - `dt-binding-001`: simple sensor binding YAML (`compatible`,
    `properties`, `required`, single `example`)
  - `dt-binding-002`: allOf reference to common binding
    (`spi-peripheral-props.yaml`) — composition pattern
  - `dt-binding-003`: `enum` + `minimum`/`maximum` constraints on a register
    property
  - `dt-binding-004`: interrupt binding with `interrupts` +
    `interrupt-names`
  - `dt-binding-005` (stretch): GPIO hogs pattern
  - `dt-binding-006` (stretch): clocks + clock-names + `#clock-cells`
- Directive-heavy grammar (YAML schema + dt-schema DSL) → implicit-prompt
  exemption applies.

**Factor-coverage delta:**
| Factor | Current | After Candidate 4 |
|--------|---------|-------------------|
| A7 (Device Tree / HW description) | Empirical (Zephyr overlays) | + kernel binding YAML schema |
| F6 (build integration) | Empirical | + binding file location + `Documentation/devicetree/bindings/vendor/vendor-prefixes.yaml` |
| F5 (header knowledge) | Empirical | unchanged |

A7 strengthening, no new factor cells. Value: **kernel DT bindings validation
is a distinct failure mode** (schema-level) vs Zephyr DT overlays (node-level)
— LLMs often blur the two.

**Blast radius:**
- Enum change: **No**
- Runner/evaluator refactor: **None**
- Multi-file reference support: **Not required** (single YAML file per TC)
- `case_git_hash` churn: **No**

**Estimated effort:** **6–8h** — 4 TCs (~5h) + 2 stretch (~2h) + yaml/dt-
validate parser helper (~1h) + baseline benchmark (~1h).

**External dependency risk:**
- Docker image: `dt-validate` (from `dtschema` pip package) + `yamllint`
  for structural validation. Both available via pip; ~15MB. → **Low**.
- No kernel version dependencies; the binding schema lives in upstream
  `dt-schema` and is largely version-stable.

**Recommendation:** **Defer.** Smallest factor delta of the four; the A7
cell is already Empirical from Zephyr side. Useful for completeness, but
lower ROI than OTA (production realism) or networking-kernel (new
concurrency context). Good "filler" Phase D candidate once OTA +
networking-kernel land.

**Upstream references:**
- `dt-schema` on github (devicetree-org/dt-schema).
- Linux `Documentation/devicetree/bindings/writing-schema.rst`.
- dtschema-doc python package.

---

## Ranking + recommended next PLAN

| # | Candidate | Factor delta | Blast radius | Effort | Dep. risk | Overall |
|---|-----------|--------------|--------------|--------|-----------|---------|
| 1 | eBPF multi-file reference | Low (opens doors) | **High** (infra refactor) | 14–18h | High | **Defer** |
| 2 | Linux OTA (SWUpdate+RAUC) | Med (E4 strengthen + production realism) | Low | **8–12h** | Med | **Go — Phase C-1** |
| 3 | linux-networking-kernel | Med (softirq context, new D-cell strengthen) | Low | 10–14h | Low | **Go — Phase C-2** |
| 4 | Kernel DT bindings YAML | Low (A7 strengthen) | Low | 6–8h | Low | **Defer — Phase D filler** |

### Recommended next PLAN slug: `linux-ota-expansion-phase-c`

**Rationale:** Linux OTA (SWUpdate + RAUC) offers the best balance of (a)
production realism — the user's BSP uses SWUpdate, so TCs will surface
failure modes the user actually cares about; (b) factor coverage — E4
(rollback/recovery) strengthens across a second platform beyond Zephyr
MCUboot, proving cross-platform E4 discrimination; (c) zero infrastructure
cost — reuses `ota` category, `embedded-linux` bucket, Phase B's text-only
TC patterns (systemd/udev precedent), no runner/evaluator changes; (d)
implicit-prompt discipline already generalised for directive-heavy grammar
in Phase B.

Candidate 3 (`linux-networking-kernel`) is the preferred Phase C-2
follow-up: same pattern as Phase A `linux-driver`, clean blast radius,
adds softirq concurrency context which is genuinely absent today.

Candidates 1 (eBPF multi-file) and 4 (kernel DT bindings YAML) should defer.
Candidate 1's infra refactor lacks direct factor-coverage payoff; revisit
when a later candidate exposes multi-file pressure (OTA signed-update +
payload + signature triple is the likely trigger). Candidate 4 overlaps
heavily with existing Zephyr DT coverage — low ROI until the easier wins
are in.

### Next step

Run `/myplan linux-ota-expansion-phase-c` with this doc as reference.
That PLAN should:
- Lock TC count (recommend 4 SWUpdate + 2 RAUC = 6 TCs, with 2 more
  SWUpdate stretch if schedule allows).
- Inherit Phase B's implicit-prompt directive exemption policy; extend
  the FORBIDDEN/ALLOWED lists with SWUpdate (`sw-description`,
  `images:`, `files:`, `scripts:`, `hw-compatibility:`) and RAUC
  (`[update]`, `[bundle]`, `[image.*]`, `compatible=`, `version=`).
- Add a `check_utils.py` helper module for libconfig (SWUpdate) + INI
  (RAUC) parsing with ≥3 unit tests each.
- Specify Docker image addition (`swupdate` binary for `-c` config-check)
  with `l1_skip: true` fallback if unavailable.
- Target: 281 → 287 TCs after Phase C-1 complete.
