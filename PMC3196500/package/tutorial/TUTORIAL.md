<!-- Generated from tutorial.ipynb by check_package.py --write. Do not edit by hand. -->

# oisim tutorial

`oisim` measures how often a cumulative random-effects meta-analysis overestimates an intervention effect by chance alone, and computes the optimal information size (OIS) that a meta-analysis should reach. It pools trials with the DerSimonian-Laird random-effects model after each new trial, simulates the paper's scenarios, and reads off how many patients and events it takes for the probability of an overestimated relative risk reduction (RRR above 20% or 30%) to drop below 10%, 5% or 1%.

Thorlund K, Imberger G, Walsh M, Chu R, Gluud C, Wetterslev J, Guyatt G, Devereaux PJ, Thabane L. The number of patients and events required to limit the risk of overestimation of intervention effects in meta-analysis - a simulation study. *PLoS ONE* 6(10):e25491 (2011). doi:10.1371/journal.pone.0025491

## 1. Install

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC3196500/package"
```

```python
import oisim

print("oisim", oisim.__version__)
```

```text
oisim 0.1.0
```

## 2. The example input

Twelve two-arm trials in the order they were published: events and patients in the treatment and the control arm. They were drawn as the paper's Appendix S2 describes (one of its scenarios, with no true effect). Trial T03 has no events in its treatment arm.

```python
path = oisim.example_path("cumulative_trials.csv")
trials = oisim.read_trials(path)
print(path.name, "-", len(trials["trial"]), "trials")
print("trial  events_t  n_t  events_c  n_c")
for i, t in enumerate(trials["trial"]):
    print(f"{t:5}  {trials['events_treatment'][i]:8}  {trials['n_treatment'][i]:4}  {trials['events_control'][i]:8}  {trials['n_control'][i]:4}")
```

```text
cumulative_trials.csv - 12 trials
trial  events_t  n_t  events_c  n_c
T01           3    79         9    79
T02         231  2067       247  2067
T03           0   824        50   824
T04           1    40         2    40
T05           2   101         6   101
T06          23   228        38   228
T07           5    48         7    48
T08           1    11         1    11
T09          22   228        29   228
T10           7   167         6   167
T11           7   174        11   174
T12         165  1409       106  1409
```

## 3. Run the method

`cumulative` pools the trials after each new one: the cumulative number of patients and events, the pooled relative risk (RR), the relative risk reduction RRR = 1 - RR, and the DerSimonian-Laird between-trial variance tau^2. A trial with a zero cell gets 0.5 added to each of its cells.

```python
rows = oisim.cumulative(trials)
print("trial  patients  events     RRR    tau2")
for r in rows:
    print(f"{r['trial']:5}  {r['cum_patients']:8}  {r['cum_events']:6}  {r['rrr']:6.3f}  {r['tau2']:6.3f}")
```

```text
trial  patients  events     RRR    tau2
T01         158      12   0.667   0.000
T02        4292     490   0.318   0.319
T03        5940     540   0.751   1.878
T04        6020     543   0.693   1.409
T05        6222     551   0.667   1.040
T06        6678     612   0.507   0.303
T07        6774     624   0.460   0.243
T08        6796     626   0.438   0.216
T09        7252     677   0.370   0.132
T10        7586     690   0.326   0.113
T11        7934     708   0.321   0.096
T12       10752     979   0.238   0.161
```

## 4. Compare with the expected output

`cumulative_expected.csv` was computed with plain Python loops written from the paper's Appendix S1, not with the package (see `data/README.md`). Every value must agree to a relative tolerance of 1e-8.

```python
import csv, math

with open(oisim.example_path("cumulative_expected.csv"), newline="") as f:
    expected = list(csv.DictReader(f))
same = sum(
    r["trial"] == e["trial"] and r["cum_patients"] == int(e["cum_patients"]) and r["cum_events"] == int(e["cum_events"])
    and all(math.isclose(r[k], float(e[k]), rel_tol=1e-8, abs_tol=1e-12) for k in ("rr", "rrr", "tau2"))
    for r, e in zip(rows, expected)
)
print(f"{same} of {len(expected)} cumulative analyses match the expected output")
assert same == len(expected)
```

```text
12 of 12 cumulative analyses match the expected output
```

The optimal information size against the paper's Table 2 (PC 3%, RRR 30%, as printed). The paper rounds its cells inconsistently, so each unrounded value must lie within one rounding step of the printed one.

```python
with open(oisim.example_path("table2_printed.csv"), newline="") as f:
    table2 = list(csv.DictReader(f))
within = 0
for r in table2:
    o = oisim.ois(float(r["pc"]), float(r["rrr"]), float(r["i2"]), beta=float(r["beta"]))
    step = 500 if o["patients"] > 10000 else 100
    ok = abs(o["patients"] - int(r["patients_printed"])) <= step and abs(o["events"] - int(r["events_printed"])) <= 50
    within += ok
    print(f"I2 {float(r['i2']):.2f}  power {1 - float(r['beta']):.0%}:  {o['patients']:8.0f} patients (printed {r['patients_printed']:>5}), "
          f"{o['events']:6.0f} events (printed {r['events_printed']:>4})")
print(f"{within} of {len(table2)} OIS values within one rounding step of Table 2")
assert within == len(table2)
```

```text
I2 0.00  power 80%:      9632 patients (printed  9600),    246 events (printed  250)
I2 0.00  power 90%:     12894 patients (printed 13000),    329 events (printed  350)
I2 0.00  power 95%:     15946 patients (printed 16000),    407 events (printed  400)
I2 0.25  power 80%:     12842 patients (printed 13000),    327 events (printed  350)
I2 0.25  power 90%:     17192 patients (printed 17000),    438 events (printed  450)
I2 0.25  power 95%:     21262 patients (printed 21500),    542 events (printed  550)
I2 0.50  power 80%:     19263 patients (printed 19500),    491 events (printed  500)
I2 0.50  power 90%:     25788 patients (printed 26000),    658 events (printed  650)
I2 0.50  power 95%:     31893 patients (printed 32000),    813 events (printed  800)
9 of 9 OIS values within one rounding step of Table 2
```

## 5. The command line

The same analysis from the shell, and an OIS.

```python
!oisim cumulative "{path}" | head -4
!oisim ois --pc 0.10 --rrr 0.20 --i2 0.25 --beta 0.10
```

```text
trial,cum_patients,cum_events,rr,rrr,tau2
T01,158,12,0.3333333333,0.6666666667,0
T02,4292,490,0.6816449205,0.3183550795,0.3188732649
T03,5940,540,0.2491855469,0.7508144531,1.878429937
{
 "patients": 11474.10598309317,
 "events": 1032.6695384783854,
 "p": 0.09000000000000001,
 "patients_rounded": 11500,
 "events_rounded": 1050
}
```

## 6. A simulated scenario

One of the paper's 36 scenarios at a small size (500 meta-analyses of 100 trials instead of 20,000, so it runs in a second): trial sizes from the Cochrane Heart Group survey, control risk 5% to 15%, tau^2 = 0.15, no true effect. The result is the number of patients and events at which the probability of a pooled RRR above 30% (or 20%) drops below 10%, 5% and 1%. The paper's Table 1 gives 1500/2500/6500 patients and 150/250/600 events for RRR > 30%; at this size the read-off moves by a bin or two between seeds.

```python
sim = oisim.simulate(oisim.Scenario("cochrane", "5-15", tau2=0.15, rrr=0.0, n_meta=500), seed=1)
for row in oisim.required_table(sim, bin_rule="interval"):
    pat = [oisim.format_required(row[f"patients_{l}"], 50000) for l in (10, 5, 1)]
    ev = [oisim.format_required(row[f"events_{l}"], 5000) for l in (10, 5, 1)]
    print(f"RRR > {row['threshold']:.0%}: patients {'/'.join(pat)}, events {'/'.join(ev)}")
```

```text
RRR > 30%: patients 1500/2500/6500, events 150/200/600
RRR > 20%: patients 3500/6500/13000, events 400/650/950
```

## 7. Your own data

- **Trials** (`oisim cumulative`, `read_trials`): a CSV with columns `trial`, `events_treatment`, `n_treatment`, `events_control`, `n_control`, one row per trial in publication order. The output has, after each trial, `cum_patients`, `cum_events`, the pooled `rr` and `rrr` and `tau2`. `--zero correct_all` keeps trials with no events in either arm (with the 0.5 correction) instead of leaving them out.
- **OIS** (`oisim ois`, `ois`): `--pc` control-group risk and `--rrr` the effect to detect, both as proportions; `--i2` the heterogeneity correction; `--alpha` (two-sided) and `--beta`. Events are patients times the mean of the two arms' risks.
- **Simulation** (`oisim simulate`, `simulate`): `--sizes cochrane` or `common`, `--pc` one of `1-5`, `5-15`, `15-40`, `40-80`, `--tau2`, `--rrr` the true effect, `--n-meta` meta-analyses of 100 trials each. Use 20,000 for the paper's precision.

## 8. The reproduction

The full simulation of the paper's 36 scenarios, its tables and figures compared with the published ones, and the results page: https://github.com/jeonglab-bcm/fossil/tree/main/PMC3196500
