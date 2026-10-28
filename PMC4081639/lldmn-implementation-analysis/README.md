# lldmn implementation analysis (Yu & Shaw 2014, Bioinformatics 30:1547)

The supplementary `lldmn` R package ships the mesh algorithm only as precompiled static libraries
(`libloglikdmn-linux.a`, sha256 `416d978f…911a30`; `libloglikdmn-mac.a`, x86_64, sha256
`31fcd321…7a484`). Its `DESCRIPTION` declares `License: GPL-2`. No C++ source for the algorithm is
included. This folder records what the compiled code does.

## Method

- Split the Linux archive (GCC 4.6.1, Ubuntu; symbols not stripped, no DWARF) into its 8 objects and
  decompiled every function with REA 6.8.0 (`rea decompile-all --provider ghidra`) on Ghidra 12.1.4 / JDK 21.
  Output: `decompiled-ghidra/<object>/<address>.c` (Ghidra pseudocode, not original source; kept local,
  not in this repository).
- Ran the authors' macOS x86_64 library under Rosetta through a C driver (`difftest/driver.c`;
  `difftest/stubs.c` supplies `operator new/delete` and aborts on any other C++ runtime call).
- Compared, over 324 inputs (paper Figs 2/4/5/6 settings, the vignette example, 300 random K=21 cases
  with counts up to 1e5 and psi in {0} ∪ [1e-8, 10]): the binary, a Python reimplementation written from
  the decompiled logic (`difftest/difftest.py`), and exact Eq. (6) via mpmath at 50 digits.

## Results

| Comparison | Max relative difference |
| --- | --- |
| Reimplementation vs authors' binary | 3.9e-16 |
| Authors' binary vs exact Eq. (6) | 4.0e-16 |

Vignette example `lldmn(c(3,5,7), c(.2,.3,.5), .01)` = -15.838047564592856.

## Recovered algorithm (R entry point → `loglikdmn::loglikdirmultinom_mesh(n, p, psi)`)

```
if all n == 0: return 0
alpha = p / psi                                   # psi_and_p2alpha; psi = 0 gives inf
min_alpha = 1/delta + 1 = 6                       # vgam::_min_alpha, delta = 0.2
# 1. VGAM warm-up (not described in the paper)
if any(n_i > 0 and alpha_i < 6):
    x_i = min(n_i, ceil(6 - alpha_i)) for those i, else 0
    total += sum_i sum_{r<x_i} log(p_i + r psi) - sum_{j<sum x} log(1 + j psi)   # exact product (Eq. 4/7); 1/psi form when psi >= 1
    (p, psi) <- next(p, psi, x); n <- n - x       # Eqs (27)-(28)
# 2. Bernoulli mesh steps (paper Eqs 20, 29-32)
while any(n > 0):
    x_i = min(n_i, floor(0.2 * alpha_i))          # Eq. (30) with the Eq. (32) cap
    total += sum_{x_k>0} [x_k log p_k + D_20(psi/p_k, x_k)] - D_20(psi, sum x)   # Eq. (20)
    (p, psi) <- next(p, psi, x); n <- n - x
return total

next: N = sum x; psi' = psi/(1+psi N) if psi < 1 else 1/(1/psi + N); p' = p/(1+psi N) + x psi'
D_20(x, y) = sum_{n=2}^{20} (-1)^n phi_n(y) x^(n-1) / (n(n-1)),  phi_n = B_n(y) - B_n,
             each phi_n(y) x^(n-1) hand-expanded in old_bern_poly_power02..20 (factored in t = x*y)
```

## Differences from the paper

1. **Undocumented exact warm-up.** Before any Bernoulli step, every category with alpha_i = p_i/psi < 6
   gets up to ceil(6 - alpha_i) counts evaluated with the exact VGAM-style product. The paper's mesh
   rule, Eq. (30) x_i = floor(alpha_i delta), is 0 whenever alpha_i < 5. Implemented exactly as
   written, it would never advance such a category. The warm-up is what makes the algorithm terminate.
   It adds at most 6 terms per category, so the runtime claims are unaffected.
2. **For larger psi, the result is entirely the exact product.** In the Fig. 2/4 setting
   (x = (2,3,1), p = (.2,.3,.5)), psi >= 0.1 gives zero Bernoulli steps. The value reported as the
   "mesh algorithm" there is the VGAM-style product, written in psi rather than rho.
3. **Fixed constants.** m = 20 and delta = 0.2, as stated in the paper. psi < 1 and psi >= 1 use
   different but algebraically equal update formulas, matching Eqs (27)-(28).
4. **Unpublished extras.** The library also contains `loglikdirmultinom_diff_{mesh,vgam,bern_approx}`
   (log-likelihood differences for a second p vector). These are not exposed by the R wrapper.

## Reproduce

```
uv run --with mpmath==1.3.0 python -I difftest/difftest.py <x86_64 driver built from driver.c + stubs.c + libloglikdmn-mac.a>
clang -arch x86_64 -mmacosx-version-min=10.13 -w driver.c stubs.c libloglikdmn-mac.a -o lldmn_driver
```
