# Congestion-exempt forgiveness: design

The regime map ([run-120-regime-map.md](run-120-regime-map.md)) found one
tail that bounded loss can act on: DCQCN cuts W eight to ten times and
pays 18 to 24 % of the training window for it, with 3 to 13 million rate
cuts per run. The forgive protocol as built
([forgive-protocol-design.md](forgive-protocol-design.md)) is congestion
neutral by design: a forgiven trim still costs the sender a rate cut. This
design adds a third shedding domain in which an eligible flow on a
non-critical step, while its budget lasts, does not slow down at all. It
pays for congestion in bounded loss instead of time. C++17, Python 3.11,
written 2026-09-07.

## 0. Why the exemption must cover ECN, not only trims

The generator's DCQCN table marks ECN from 800 KB of queue at 400G (`KMIN`)
with `PMAX` 0.2 at 3.2 MB, and the switch trims at a full 4 MiB data
queue. Marks precede trims. At the map's worst DCQCN cell the sender took
13.5 million CNPs against 3.4 million trim notifications, so at least 74 %
of the rate cuts came from ECN-marked ACKs, not from trims. A design that
only stops the trim-originated CNP on a forgiven range leaves three cuts in
four in place and cannot move the window. The exemption therefore covers
every CNP the flow would take, and the budget bounds it: the receiver's
first refusal to forgive, which is a PULL, re-arms the flow's congestion
control.

## 1. Domain model

Python (`experiments/ring_3d/generate.py`), the one parse boundary for a
profile:

```python
class SheddingDomain(StrEnum):
    ADMISSION = "admission"            # shed whole payloads before offering
    RECOVERY = "recovery"              # forgive trimmed ranges, CC neutral
    RECOVERY_EXEMPT = "recovery_exempt"  # forgive, and ignore CNPs while budget lasts

# SelectionPolicy unchanged in shape; semantics gains a third string:
#   recovery_exempt -> "recovery_forgiveness_cc_exempt"
```

Invariants at parse, each a refusal by name: `recovery_exempt` requires
everything `recovery` requires (`selective_repair: true`, trimming `ftd`,
an explicit CLR schedule) and additionally `congestion_control.mode ==
"dcqcn"`. Under `none` the exemption is vacuous and a profile that asks
for it is a mistake, not a no-op.

Frontend (`astra-sim/network_frontend/ns3/ExperimentConfig.hh`):

```cpp
enum class SheddingDomain : uint8_t { Admission = 0, Recovery, RecoveryExempt };

// The one eliminator every existing `== SheddingDomain::Recovery` test
// becomes. Exhaustive: a fourth variant fails to compile here.
constexpr bool forgives(SheddingDomain d) {
    switch (d) {
        case SheddingDomain::Admission: return false;
        case SheddingDomain::Recovery: return true;
        case SheddingDomain::RecoveryExempt: return true;
    }
    return false;
}

struct FlowRecord {            // gains three telemetry fields
    bool cc_exempt = false;        // answered true at queue-pair creation
    uint32_t cnp_ignored = 0;      // CNPs the sender discarded while exempt
    uint64_t cc_rearmed_ns = 0;    // simulated time of the first PULL; 0 = never
};
```

ns-3 sender (`extern/network_backend/ns-3/src/point-to-point/model`):

```cpp
// rdma-queue-pair.h, RdmaQueuePair gains:
//   Congestion response is a two-variant sum {Obey, Exempt}; a bool carries
//   it because the transition is one-way and the value is read on the CNP
//   path. Exempt is set once at birth and cleared once by the first PULL.
bool m_cc_exempt;
uint32_t m_cnp_ignored;
uint64_t m_cc_rearmed_ns;

// rdma-hw.h, RdmaHw gains:
bool m_congestionExemption;   // attribute "CongestionExemption", default false
typedef Callback<bool, uint32_t /*sip*/, uint32_t /*dip*/, uint16_t /*sport*/,
                 uint16_t /*dport*/> CongestionExemptionCallback;
CongestionExemptionCallback m_congestionExemptionCallback;
```

Invariants: `m_cc_exempt` is true only if `m_congestionExemption` was true
at creation and the callback answered true; a QP created under
`Forgiveness false` is never exempt; `m_cc_rearmed_ns != 0` implies
`m_cc_exempt == false`. ns-3 stays semantics-blind: it asks one question at
birth and learns nothing about steps, phases, or budgets.

## 2. Transitions (pure core)

Sender, per queue pair:

| State | Event | Result |
| --- | --- | --- |
| birth | `AddQueuePair` | `m_cc_exempt = m_congestionExemption && !cb.IsNull() && cb(sip, dip, sport, dport)`; rate starts at link rate as today |
| Exempt | CNP arrives (ECN-marked ACK, forgive ACK, or trim notification) | `m_cnp_ignored++`; `ReportTransportEvent("cnp_ignored", 0)`; no alpha or rate change |
| Exempt | PULL arrives (`RecoverTrimmedQueue`, before the stale check) | `m_cc_exempt = false`; `m_cc_rearmed_ns = now`; `ReportTransportEvent("cc_rearmed", 0)`; then the existing path, so the PULL's own CNP is taken |
| Obey | CNP arrives | existing `cnp_received_mlx` |
| Obey | PULL arrives | existing path |

The re-arm sits before the stale check: a stale PULL is still the
receiver's refusal, and refusal is the only signal that ends the
exemption. The receiver is unchanged. Its forgive ACK still carries
`FLAG_CNP`; an exempt sender discards it, a re-armed sender takes it, and
so the CC-neutral domain keeps its meaning with the same receiver code.

Frontend predicate, total, called once per queue pair at creation; it
mutates nothing but the flow's own `cc_exempt` field:

```
exempt(sip, dip, sport, dport):
  flow = registry[(src, dst, sport)]                 -- absent -> false
  if !enabled or domain != RecoveryExempt -> false
  if flow.kind != ForegroundPayload or !flow.admission_eligible -> false
  step = flow.operation.training_step
  clr = clr_mask[step]                               -- absent -> false
  if clr -> false                                    -- critical steps obey CC
  if !ledger.may_forgive(dst, step, 0, p_high_threshold) -> false   -- budget already spent
  flow.cc_exempt = true; -> true
```

The verdict function `evaluate_forgiveness` is unchanged except that its
domain test becomes `forgives(domain)`. A QP exempt at birth whose (dst,
step) budget is exhausted later by other flows is re-armed by its own next
trim, which the receiver pulls. A QP that is never trimmed after
exhaustion stays exempt; it is not the flow causing trims, and the
exemption ends with the flow.

Budget law unchanged: `forgiven(dst, s) + shed(dst, s) <= p(s) *
eligible(dst, s)`, `p(s) = p_low` on CLR steps, else `p_high`. The
exemption never spends budget; only forgiving does. What the exemption
adds is that the bytes the fabric trims from an exempt flow are the bytes
the budget pays for, instead of bytes a rate cut would have delayed.

## 3. Effect boundary

| Effect | Where | Notes |
| --- | --- | --- |
| Callback at QP creation | `RdmaHw::AddQueuePair` | one lookup, no mutation outside the flow's own field; idempotent per QP |
| CNP discard | `cnp_received_mlx` early return | counter only |
| Re-arm | `RecoverTrimmedQueue` | one-way; the PULL that triggers it is already on the wire |
| Telemetry | `flow_events.csv` gains `cc_exempt,cnp_ignored,cc_rearmed_ns` after `delivered_bytes`; `transport_summary.csv` gains events `cnp_ignored`, `cc_rearmed` (control plane, 0 bytes) | copied from the QP at `qp_finish` beside `cnp_received` |
| Config | `experiment.json` `selection_policy.domain` accepts `recovery_exempt`, semantics `recovery_forgiveness_cc_exempt`; `SetupNetwork` gains a `congestion_exemption` callback and bool beside the verdict ones | unknown keys still rejected |

No new wire verb, no header change, no receiver change.

## 4. Complexity budget

| Operation | n per 64-rank run | Bound | Structure |
| --- | --- | --- | --- |
| exemption query | 3.8e5 QPs | O(log a), a <= 1e4 active flows | existing `std::map` registry |
| CNP discard | up to 1.4e7 | O(1) | bool test |
| re-arm | <= 3.8e5 | O(1) | bool write |
| analyze sums | 3.8e5 rows | O(rows) | existing per-arm pass |

Nothing here has a size that matters; the fork's cost was measured at 0.56
% per event and this adds one bool test on the CNP path.

## 5. Rejected alternatives

- Suppress only the trim-originated and forgive-ACK CNPs, keep ECN
  obedience. Killed by section 0: ECN marks start at 800 KB, trims at 4
  MiB, and at least 74 % of cuts at the worst cell are ECN. The window
  would not move and the null would be built in.
- A sender-side budget mirror that ends the exemption when the sender's
  own count of forgiven bytes reaches the budget. Killed because the
  ledger is per (dst, step) and shared across every sender's flows to
  that rank; no sender can see it. The receiver's PULL is the ledger's
  refusal made visible and already exists.
- A new verb or header bit telling the sender "exempt" or "obey". Killed
  because birth-time classification plus PULL-driven re-arm covers every
  transition without a byte on the wire.

## 6. Experiment: profiles, matrix, estimands

Profiles (`experiments/ring_3d/profiles`):

- `exempt_smoke_8.json`: `forgiveness_dcqcn_8.json` with domain
  `recovery_exempt`. Gate in `forgiveness_smoke.sh`, new check
  `--congestion-exempt` in `check_forgiveness.py`: every flow completed;
  `cc_exempt` true only on eligible DP payload flows on non-CLR steps;
  `cnp_ignored > 0` on at least one exempt flow; `cnp_ignored == 0` on
  every non-exempt flow; every re-armed flow has `cc_rearmed_ns > 0`,
  `cc_exempt` true and `cnp_received > 0` after; ledger law holds; the
  existing `--congestion-neutral` check on `forgiveness_dcqcn_8` still
  passes unchanged.
- `regime_64_dcqcn_direct7_4to1_exempt.json`: the map's worst DCQCN cell,
  `selection_policy {p_low 0.005, p_high 0.4, domain recovery_exempt}`,
  name `ring-3d-regime-64-dcqcn-direct7-4to1-exempt`; everything else
  identical to `regime_64_dcqcn_direct7_4to1.json`.
- `regime_64_dcqcn_direct2_2to1_exempt.json`: the lightest DCQCN cell (W
  0.0023), same policy. Control: on a fabric that barely trims, exemption
  should change the window little and must not raise the burst drain.

Matrix (`.github/workflows/evaluation-matrix.json`): delete the 32-rank
`llama3_70b_32_direct_forgive` flagship record (the map moots its fabric);
keep `no_incast_8_forgive`; add six records, gate `forgive`, kind
`comparison`, `arm_count` 4, `require_congestion` true, seeds 9550582,
23172535, 94081284 (pi chunks 17 to 19) for each of the two cells,
`execution_timeout_minutes` 2880, `simulation_timeout_seconds` 43200
(the map's DCQCN arms took 4 to 6 h each), notes carrying the walltime
backstop sentence the matrix test requires.

Four matched arms per seed, from `compare.py` as built:
`fixed_p_low_baseline` (0.005 everywhere, obeys CC), `dblp_policy`
(admission shedding 0.4 outside CLR), `recovery_policy` (this design at
the same budget), `fixed_p_high_baseline` (admission 0.4 everywhere).

Pre-registered estimands, exempt arm against fixed-low, per seed:

1. Primary: 20-step window; DP all-rank span median over steps 4 to 17.
2. Leak check: DP span on steps 1, 2, 3, 20 equal to fixed-low within
   seed noise. The exemption never touches a critical step.
3. Budget: forgiven bytes per (dst, step) at or under `0.4 x eligible`;
   W' reported beside W.
4. Bystander harm: burst drain at step 18 and TP all-rank span median,
   both against fixed-low. Exempt flows push on the burst and on
   CC-obeying flows; the price is reported, not hidden.
5. Mechanism counters: exempt flows, CNPs ignored, flows re-armed.

Decision rule, fixed before the wave: the CC penalty at the worst cell is
24 % of window (1367 to 1696 ms). The exempt arm has purchase if it
recovers at least 5 window-percent of that at the worst cell with the
leak check clean. It is dead if it recovers under 5 %, or if the CLR
steps move, or if the burst drain more than doubles. The light cell is
the control: a window change there above seed noise means the mechanism
acts where nothing is trimmed, which is a defect.

## 7. Open questions, defaults assumed

1. Re-arm on a stale PULL: yes, refusal is refusal.
2. Last-hop trims: no special case; the receiver pulls or forgives them
   as today and the sender's exemption is indifferent to the DSCP.
3. A flow exempt at birth on a step whose budget is later exhausted and
   that is never trimmed again: stays exempt to completion.
