# Run #120 regime map readout

Run 34055188995, commit `c5495bca4a4b`, release
`uwlaookzhemmwabtbwfe2yhyxepupnmw`, eight of eight cells collected, the
first wave through the single cluster path. Each cell is one fixed-low arm
(p = 0.005 every step) at 64 ranks (TP 8, PP 1, DP 8), 20 steps, selective
repair, FTD trimming, 1 ms RTO, one seed, the same seven-source 128 MiB
burst at step 18. Axes: congestion control none or DCQCN, DP fan-in direct2
or direct7, spine oversubscription 2:1 or 4:1. Pre-registered in
`next-steps-after-run-117.md` section 3. Written 2026-09-07.

## Decision

The pre-registered rule said the programme has an operating region if
some cell shows W at or above 0.5, or a step 18 plus 19 excess of at least
20 % of the window with a repair-driven tail; and that bounded loss has no
purchase on this transport if the worst cell's excess is under 5 %. The
worst W is 0.24 and the worst excess is 0.62 % of the window. The rule
returns the negative branch: under selective repair the burst episode is
not something admission-time tolerance can shorten, at any point of the
map. The forgive family stays gated and the 32-rank decisive wave is not
run.

## Findings

**1. The burst is a non-event under selective repair, in every cell.**
The DP all-rank span at steps 18 and 19, in excess of the median of
steps 4 to 17, never reaches 1 % of the 20-step window. The burst drains
in 30 to 37 ms without congestion control against an 18.8 ms serialization
floor, and in 63 to 146 ms under DCQCN because DCQCN throttles the burst
senders. Under go-back-N in run #117 the same burst cost 205 to 935 ms of
DP span and 423 to 1798 ms of drain. The storm was the transport.

| cell | window | DP span median 4-17 | step 18 | step 19 | excess, % of window |
| --- | ---: | ---: | ---: | ---: | ---: |
| none direct2 2:1 | 1201 ms | 13.8 ms | 15.4 ms | 13.2 ms | 0.08 |
| none direct7 2:1 | 1200 ms | 12.6 ms | 13.3 ms | 12.5 ms | 0.04 |
| none direct2 4:1 | 1373 ms | 22.0 ms | 29.6 ms | 23.0 ms | 0.62 |
| none direct7 4:1 | 1367 ms | 21.0 ms | 29.8 ms | 19.7 ms | 0.55 |
| dcqcn direct2 2:1 | 1421 ms | 23.3 ms | 19.0 ms | 30.7 ms | 0.23 |
| dcqcn direct7 2:1 | 1422 ms | 23.5 ms | 19.3 ms | 32.5 ms | 0.34 |
| dcqcn direct2 4:1 | 1719 ms | 37.1 ms | 37.6 ms | 46.9 ms | 0.60 |
| dcqcn direct7 4:1 | 1696 ms | 36.6 ms | 39.4 ms | 35.5 ms | 0.10 |

**2. Trimming without congestion control is a steady-state property of
the fabric's provisioning, not of the burst.** W at steps 1 to 17 equals
W over the whole run in every cell. It multiplies across the two fabric
axes: fan-in direct2 to direct7 raises it about 2.7x, oversubscription 2:1
to 4:1 about 5.5x. At 4:1 with direct7, one offered byte in four is
trimmed, three DP flows in four see at least one trim, and the fabric
re-carries 24 % of the offered bytes. The window grows 14 % from 2:1 to
4:1. No cell reaches the pre-registered W of 0.5.

| cell | W | W steps 1-17 | W step 18 | DP flows trimmed | (offered + retransmitted) / offered | trimmed / untrimmed DP FCT median |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| none direct2 2:1 | 0.0235 | 0.0227 | 0.0416 | 24 % | 1.024 | 1.98 |
| none direct7 2:1 | 0.0625 | 0.0589 | 0.0943 | 53 % | 1.064 | 1.68 |
| none direct2 4:1 | 0.1289 | 0.1271 | 0.1671 | 58 % | 1.130 | 2.63 |
| none direct7 4:1 | 0.2406 | 0.2432 | 0.2159 | 75 % | 1.243 | 2.65 |
| dcqcn direct2 2:1 | 0.0023 | 0.0023 | 0.0023 | 7 % | 1.004 | 7.34 |
| dcqcn direct7 2:1 | 0.0077 | 0.0074 | 0.0051 | 21 % | 1.009 | 3.99 |
| dcqcn direct2 4:1 | 0.0187 | 0.0178 | 0.0182 | 29 % | 1.030 | 7.32 |
| dcqcn direct7 4:1 | 0.0317 | 0.0307 | 0.0320 | 48 % | 1.037 | 6.55 |

**3. DCQCN trades trims for time, and its tail is rate-cut driven.** DCQCN
cuts W by 8 to 10x in every fabric and lengthens the window by 18 to 24 %,
the steady DP span by 1.7x, and the burst drain by 2 to 4x. It takes 3.3
to 13.5 million rate cuts per run and fires 2 000 to 10 500 retransmission
timeouts where the no-CC cells fire about 100. A trimmed DP flow takes 4 to
7x as long as an untrimmed one under DCQCN, against 1.7 to 2.7x without
CC. This is hypothesis H3 confirmed: with CC on, the tail mechanism is the
rate cut, which a CC-neutral forgiveness cannot touch and which admission
shedding touches only through the trim count.

| cell | rate cuts (CNP) | RTOs fired | burst drain | trim to first repair, p50 |
| --- | ---: | ---: | ---: | ---: |
| none direct2 2:1 | 0 | 96 | 30.4 ms | 0 ns |
| none direct7 2:1 | 0 | 85 | 31.4 ms | 261 ns |
| none direct2 4:1 | 0 | 98 | 35.2 ms | 26 ns |
| none direct7 4:1 | 0 | 109 | 37.0 ms | 269 ns |
| dcqcn direct2 2:1 | 3 298 919 | 1 949 | 63.4 ms | 990 us |
| dcqcn direct7 2:1 | 5 279 161 | 2 349 | 80.3 ms | 989 us |
| dcqcn direct2 4:1 | 11 224 453 | 10 547 | 115.5 ms | 209 ns |
| dcqcn direct7 4:1 | 13 535 668 | 10 166 | 146.4 ms | 985 us |

**4. The step-18 burst does register, but as W, not as time.** Without CC
the burst step's W is 1.5 to 1.8x the steady W at 2:1 and about 1.3x at
4:1. The extra trims are repaired inside the step: the span excess in
finding 1 is what they cost.

## What the map does not settle

- One seed per cell. The numbers above have no error bar; run #117's
  seed band was 6.6 % of makespan under go-back-N and is unknown under
  selective repair. The ordering across cells is monotone in both fabric
  axes and the effect sizes are 5 to 10x, so the map's shape does not
  depend on the seed; the third decimal of W does.
- Hypothesis H2, burst intensity and persistence, was not on the map.
  Every cell ran the same 7 x 128 MiB burst once at step 18. A burst every
  step would be steady load, which the 4:1 cells already represent; a
  7 x 1 GiB burst would drain 8x longer and, under selective repair, cost
  the collective the spine share for that long and nothing more. Neither
  is expected to reach the 20 % excess the rule asks for, but neither was
  measured.
- Whether a matched policy arm at the worst cell (none, direct7, 4:1)
  moves W or the window. A fixed-high arm at p = 0.6 removes 60 % of the
  DP bytes, which are 24 % of the offered bytes; that reduces spine load
  and so trims, but it is the dose lever from run #117, not a phase
  effect, and its only purpose is to feed a tolerance claim the simulator
  cannot test.

## Reporting defects found while reading

- "Wire per offered byte" is 2.51 to 2.76 in every cell. The
  `data_arrival` counter is connected per device, so the ratio is a
  hop-weighted byte count, not bytes receivers saw. The repair-inclusive
  ratio, (offered + retransmitted) / offered from `flow_events.csv`, is
  1.004 to 1.243 and is the number the caption describes. Fix the counter
  or the caption in `analyze.py` before the metric is quoted.
- "First trim to first repair (p50)" reads 0 to 269 ns in five cells and
  985 to 990 us in three, all under DCQCN. The three near 1 ms match the
  RTO. Either half the repairs in those cells wait for a timeout, which
  the RTO counts do not support, or the per-flow `first_repair_ns` is
  taken from a different event in those cells. Unresolved; do not quote
  it.
- The run is marked failed because the three aggregate jobs need the
  `always` family, which this dispatch excluded. The eight cells and the
  ledger are complete. A map-only dispatch should skip the aggregates
  rather than fail them.

## Sources for the currency claims in the review

- UEC Specification 1.0, released 2025-06-11; RUD (selective, sprayed,
  out-of-order at the receiver) is the default bulk mode and packet
  trimming is optional at the switch:
  <https://ultraethernet.org/ultra-ethernet-consortium-uec-launches-specification-1-0-transforming-ethernet-for-ai-and-hpc-at-scale/>,
  <https://arxiv.org/pdf/2508.08906>.
- Meta runs its 400G training fabrics with DCQCN off, PFC plus
  receiver-driven admission in the collective library (SIGCOMM 2024):
  <https://engineering.fb.com/wp-content/uploads/2024/08/sigcomm24-final246.pdf>.
- Llama 4 trained on more than 100 000 H100s, starting at 32 000 GPUs in
  one job (Meta, October 2024 to 2025):
  <https://www.tomshardware.com/tech-industry/artificial-intelligence/meta-is-using-more-than-100-000-nvidia-h100-ai-gpus-to-train-llama-4-mark-zuckerberg-says-that-llama-4-is-being-trained-on-a-cluster-bigger-than-anything-that-ive-seen>.
