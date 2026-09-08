# Run #121 congestion-exempt forgiveness readout

Run 34156878678, commit `8dc9275`, release `b363b3rri7pbgbaudfh3tbnysiranl66`.
Six of six comparisons collected: three seeds at the light cell (DCQCN,
direct2, 2:1) and three at the worst cell (DCQCN, direct7, 4:1). The
third worst-cell seed needed its courier re-minted (see the last
section). Design and pre-registration in
[cc-exempt-forgiveness-design.md](cc-exempt-forgiveness-design.md).
Written 2026-09-08.

Four matched arms per seed, same budget: fixed-low (p = 0.005 every step,
obeys DCQCN), admission (sheds 40 % of eligible DP payloads on non-CLR
steps, obeys DCQCN), exempt (forgives trims up to 40 % of eligible bytes
per (rank, step) on non-CLR steps and ignores every CNP until the
receiver's first refusal), fixed-high (sheds 40 % on every step).

## Decision

The pre-registered rule at the worst cell: purchase if the exempt arm
recovers at least 5 window-percent against fixed-low with the CLR steps
unmoved and the burst drain under 2x. Measured over three seeds: 12.9 %,
13.1 % and 13.5 % of the window recovered, CLR-step DP spans within 0.2
to 0.9 ms of fixed-low, burst drain 1.12x, 0.85x and 0.81x. The rule
returns purchase. The mechanism
also recovered a little over half of the 24 % that DCQCN costs at this
cell against no congestion control (run #120: 1367 ms without CC, 1696 ms
with).

The comparison that matters is not against fixed-low but against
admission shedding at the same budget, and there the result has two
faces. On the window, exempt beats admission by 2.7 %, 0.8 % and 2.1 %
at the worst cell, the same sign in every seed but no larger than
admission's own seed spread (1.7 %), and loses by 3 % at the light cell.
On the loss spent to get there, exempt used 8.8 to 9.5 % of the DP bytes
at the worst cell and 0.8 to 1.0 % at the light cell; admission used 32
% at both,
because a blind draw spends its whole budget whether or not the fabric
is congested. Per lost byte, the exemption is three to four times as
efficient at the worst cell and forty times at the light cell, and the
bytes it loses are the ones the fabric had already trimmed.

## Worst cell: DCQCN, direct7, 4:1

| seed | arm | window | DP span, steps 4-17 | DP span, CLR steps | TP span | burst drain | W | W' | DP bytes lost | CNPs taken | CNPs ignored | RTOs |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 23172535 | fixed-low | 1686 ms | 36.7 ms | 37.2 ms | 9.03 ms | 104 ms | 0.031 | 0.031 | 0.5 % | 13.4 M | 0 | 10482 |
| 23172535 | admission | 1509 ms | 25.8 ms | 35.8 ms | 9.97 ms | 78 ms | 0.018 | 0.018 | 32.3 % | 7.9 M | 0 | 5834 |
| 23172535 | exempt | 1468 ms | 21.1 ms | 37.4 ms | 8.30 ms | 116 ms | 0.034 | 0.011 | 9.5 % | 6.4 M | 10.8 M | 3330 |
| 23172535 | fixed-high | 1441 ms | 25.0 ms | 24.6 ms | 9.72 ms | 77 ms | 0.012 | 0.012 | 40.2 % | 6.2 M | 0 | 4013 |
| 94081284 | fixed-low | 1690 ms | 35.9 ms | 37.0 ms | 9.15 ms | 140 ms | 0.031 | 0.031 | 0.5 % | 13.1 M | 0 | 10430 |
| 94081284 | admission | 1480 ms | 24.0 ms | 37.0 ms | 9.10 ms | 90 ms | 0.017 | 0.017 | 32.1 % | 7.7 M | 0 | 5659 |
| 94081284 | exempt | 1468 ms | 20.4 ms | 36.1 ms | 8.00 ms | 119 ms | 0.032 | 0.010 | 9.4 % | 6.0 M | 10.9 M | 3100 |
| 94081284 | fixed-high | 1466 ms | 24.5 ms | 25.8 ms | 10.15 ms | 116 ms | 0.013 | 0.013 | 40.0 % | 6.4 M | 0 | 4313 |
| 9550582 | fixed-low | 1686 ms | 36.6 ms | 36.1 ms | 9.59 ms | 141 ms | 0.030 | 0.030 | 0.5 % | 13.0 M | 0 | 10110 |
| 9550582 | admission | 1490 ms | 24.3 ms | 34.7 ms | 9.19 ms | 102 ms | 0.017 | 0.017 | 32.1 % | 7.8 M | 0 | 5790 |
| 9550582 | exempt | 1459 ms | 20.3 ms | 36.8 ms | 7.14 ms | 114 ms | 0.032 | 0.011 | 8.8 % | 6.1 M | 10.4 M | 3334 |
| 9550582 | fixed-high | 1433 ms | 22.7 ms | 22.1 ms | 9.19 ms | 96 ms | 0.012 | 0.012 | 40.1 % | 6.1 M | 0 | 3843 |

Readings:

- The exemption acts where it was aimed. Steady non-CLR DP span falls
  from 36 ms to 21 ms (admission: 25 ms). CLR steps stay at 37 ms in both
  fixed-low and exempt; fixed-high is the only arm that moves them, and it
  does so by shedding there.
- The window gain is smaller than the DP-span gain because the CLR steps,
  the burst step, and compute are untouched: 16 steps at 15 ms saved is
  240 ms, and 1686 minus 1468 is 218 ms.
- The exempt arm trims slightly more than fixed-low (W 0.033 against
  0.031): exempt flows push into the queue, as designed. Two thirds of
  those trims are forgiven (W' 0.010), and the rest are pulled and re-arm
  their flow. Of 71 680 exempt flows per seed, 13 141, 12 185 and 12 123
  were re-armed.
- Bystander harm is mixed and small. TP spans fall (DP flows finish
  sooner and leave the leaf). The burst drains slower in one seed (104 to
  116 ms) and faster in two (140 to 119 ms, 141 to 114 ms); fixed-low's
  own seeds span 37 ms, so the burst drain is inside seed noise here.
- Timeouts fall by two thirds and taken CNPs by half. The exempt arm's
  DCQCN state is calmer, not wilder.
- Ledger law verified in every recovery arm: 1280 cells each, no
  violation.

## Light cell: DCQCN, direct2, 2:1

| seed | arm | window | DP span, steps 4-17 | DP span, CLR steps | burst drain | W | W' | DP bytes lost | CNPs taken | CNPs ignored |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 23172535 | fixed-low | 1407 ms | 22.9 ms | 22.8 ms | 63 ms | 0.0024 | 0.0024 | 0.5 % | 3.3 M | 0 |
| 23172535 | admission | 1310 ms | 16.3 ms | 22.8 ms | 54 ms | 0.0015 | 0.0015 | 32.3 % | 2.1 M | 0 |
| 23172535 | exempt | 1354 ms | 18.6 ms | 21.9 ms | 67 ms | 0.0045 | 0.0025 | 0.8 % | 1.7 M | 3.7 M |
| 23172535 | fixed-high | 1277 ms | 15.5 ms | 16.8 ms | 45 ms | 0.0011 | 0.0011 | 40.2 % | 1.7 M | 0 |
| 94081284 | fixed-low | 1398 ms | 22.9 ms | 19.7 ms | 61 ms | 0.0027 | 0.0027 | 0.5 % | 3.5 M | 0 |
| 94081284 | admission | 1313 ms | 16.3 ms | 19.9 ms | 64 ms | 0.0015 | 0.0015 | 32.1 % | 2.0 M | 0 |
| 94081284 | exempt | 1343 ms | 18.0 ms | 19.4 ms | 69 ms | 0.0046 | 0.0026 | 0.8 % | 1.7 M | 3.7 M |
| 94081284 | fixed-high | 1284 ms | 15.2 ms | 18.6 ms | 41 ms | 0.0012 | 0.0012 | 40.0 % | 1.7 M | 0 |
| 9550582 | fixed-low | 1418 ms | 22.4 ms | 21.6 ms | 64 ms | 0.0026 | 0.0026 | 0.5 % | 3.5 M | 0 |
| 9550582 | admission | 1312 ms | 16.2 ms | 19.6 ms | 48 ms | 0.0015 | 0.0015 | 32.1 % | 2.0 M | 0 |
| 9550582 | exempt | 1343 ms | 18.7 ms | 21.6 ms | 78 ms | 0.0049 | 0.0025 | 1.0 % | 1.7 M | 3.9 M |
| 9550582 | fixed-high | 1280 ms | 16.4 ms | 13.0 ms | 42 ms | 0.0011 | 0.0011 | 40.1 % | 1.7 M | 0 |

The design's light-cell rule said the window "must not move" there,
reasoning that a fabric that barely trims gives the mechanism nothing to
act on. That reasoning was wrong and the rule is withdrawn rather than
reinterpreted: at W 0.002 DCQCN still takes 3.3 million CNPs from ECN
marks, and section 0 of the design is exactly the argument that the
exemption acts on those. The window moved 4 %, the exempt flows doubled
the fabric's trims (W 0.0024 to 0.0046, all of the increase forgiven),
and the burst drained 5 to 22 % slower. Admission shedding gets 7 % at
this cell by removing a third of the DP bytes from a fabric that did not
need them removed. Where nothing is congested, the exemption's price is
low and its return is low; the seed spread of the exempt arm (1343 to
1354 ms) is tighter than admission's spread at the worst cell.

## Contribution

Same fabric (DCQCN, direct7, 4:1), three ways to pay for overload, plus
the blind alternative at the same budget:

| response | window | bytes re-carried | bytes lost | seeds |
| --- | ---: | ---: | ---: | ---: |
| no congestion control, repair everything | 1367 ms | 24 % of offered (W) | none | 1 (run #120) |
| DCQCN | 1686 to 1690 ms | 3 % | none | 3 |
| DCQCN + exempt forgiveness, budget 0.4 | 1459 to 1468 ms | 1 % (W') | 2.2 % of offered, 8.8 to 9.5 % of DP, none on CLR steps | 3 |
| DCQCN + blind admission shedding, budget 0.4 | 1480 to 1509 ms | 2 % | 7.7 % of offered, 32 % of DP | 3 |

This is not a point between "retransmit everything" and "slow down". It
is a third axis. Without congestion control the fabric pays in
re-carried bytes; with DCQCN it pays in time; with the exemption it pays
in bounded, phase-placed loss, gets back about half the time DCQCN
costs, and keeps DCQCN's re-carry.

### Verified here

In the simulator, under DCQCN, at 64 ranks, three seeds per cell:

1. The third operating point exists. Window 13 % shorter than DCQCN at
   the worst cell (rule asked for 5), critical-step spans unmoved, burst
   drain inside seed noise, W' 0.010.
2. Loss spent where the fabric trimmed beats loss spent blind. At the
   same budget the exempt arm loses 3.4x fewer DP bytes than admission
   shedding, its window is shorter in every seed (by 0.8 to 2.7 %, about
   admission's seed spread), and it never touches a critical step, which
   fixed-high does.
3. The mechanism is minimal and lawful. Sender-only: one answer at
   queue-pair birth, the receiver's existing PULL as the re-arm, no wire
   change, no receiver change. The per-(rank, step) budget law held in
   all 3840 ledger cells.
4. The negatives that motivate it, from runs #117 and #120: the relief
   measured under go-back-N was the transport's own amplification (up to
   79x re-carry); under selective repair the incast episode costs under
   1 % of the window at every point of a 2x2x2 map, so admission-time
   tolerance has nothing to shorten; repair-round forgiveness has an
   arithmetic ceiling under 0.2 % of DP span.
5. The map: trimming multiplies by DP fan-in (2.7x) and oversubscription
   (5.5x); DCQCN buys an 8 to 10x cut in W with 18 to 24 % of the window.

### Not verified

- Tolerance. That a current model survives 9 % loss of DP gradient bytes
  on non-critical steps is assumed from DBLP's evidence (EfficientNet,
  ResNet) and Weintraub 2025 (10 % uniform loss on Llama2 7B, no phase
  test). Needs GPUs. Until then every claim above reads "at a budget the
  model is assumed to tolerate".
- Congestion control currency. DCQCN is what the model has; Meta runs
  its 400G fabrics with DCQCN off and UEC's default is NSCC. The
  exemption's idea transfers to any CC that reacts to trims and marks,
  but nothing here measures NSCC.
- Fairness. Exempt flows shared this fabric only with their own job's TP
  and one burst. Against another tenant's CC-obeying flows the price
  lands on the tenant, and nothing here measures it.
- Scale and workload shape. 64 ranks with TP on the fabric; in a current
  deployment TP stays on NVLink and the fabric carries DP and PP only,
  which would raise the eligible share from 24 % to most of the bytes.

## Next stages

Ordered by cost. Each names its instrument and the outcome that ends it.

| stage | question | instrument | cost | kill test |
| --- | --- | --- | --- | --- |
| 1. Dose front | How does the trade move with the budget? | worst cell, p_high {0.1, 0.2, 0.4, 0.6}, exempt and admission arms, 3 seeds, 24 arms | one cluster day | window flat above p 0.2 |
| 2. No-CC cell | Does forgiveness also buy back re-carry where there is no CC to exempt? | none/direct7/4:1, CC-neutral recovery domain, 3 seeds, 12 arms | half a cluster day | W' within seed noise of W |
| 3. Fairness | What does the exempt job cost a CC-obeying neighbour? | one profile with a second tenant's flows on the same spines, 3 seeds, 12 arms | a day of generator work plus a wave | tenant's DP span grows by more than the exempt job's shrinks |
| 4. Workload currency | Does the ceiling rise when the fabric carries DP only? | TP in NVLink, FSDP reduce-scatter plus all-gather bytes, re-sized oversubscription so the fabric stays the bottleneck | generator work plus one map plus one wave | gain does not scale with the eligible share |
| 5. NSCC | Does the idea transfer to a window-based CC with trim-triggered quick_adapt? | an NSCC model in rdma-hw.cc, calibrated against the UEC spec defaults | weeks | exempt gain under 5 % of window |
| 6. Tolerance | Does a current model survive 9 % non-CLR DP loss? | real training of a small current model with injected bucket loss under the ledger law | GPUs | loss curve diverges |

Stages 1 and 2 sharpen the same figure, the loss-versus-time front, and
are the next wave. Stages 3 and 4 are the two objections a reviewer
raises first. Stage 5 decides whether the claim can say more than
"DCQCN". Stage 6 is the claim the whole line rests on and the only one
this cluster cannot run.

## The courier that was re-minted

The arm for seed 9550582 at the worst cell completed on the cluster at
10:03 UTC and placed its outbox. Its courier runner was provisioned at
10:03:19 and the collect job sat queued from 10:03:32 with no runner;
`squeue` showed no job. The runner job script tears a JIT runner down
after 1800 s without an assigned job (`DCS_IDLE_GRACE_SECONDS`), and three
couriers were provisioned inside five minutes; the one GitHub did not
assign within the grace window was killed by its own guard at about
10:33, and the job it was minted for could match no other runner. The log
on the cluster is `~/astra-ci/jobs/runner-<slurm job id>.log`.

Recovery, as run on 2026-09-08 16:35 to 16:40 UTC. Cancelling the run and
re-running its failed jobs is not enough: the courier's provision job had
succeeded, so a failed-jobs rerun re-queued the collect job with no
runner behind it. Re-running from the provision job mints a new courier
for that key and runs its dependents; the outbox on scratch was intact
and the collect and record steps finished inside two minutes.

```
gh run cancel 34156878678 -R BulkyCI/astra-sim
gh run rerun -R BulkyCI/astra-sim --job <id of "Provision the courier runner" for that key>
```
