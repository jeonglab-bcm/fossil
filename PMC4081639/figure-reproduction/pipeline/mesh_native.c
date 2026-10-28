#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define M 20
#define DELTA 0.2
#define MIN_ALPHA (1.0 / DELTA + 1.0)
static double PHI[M + 1][M + 1];
static void init(void) {
    double B[M + 1], a[M + 1];  /* Akiyama-Tanigawa in doubles is exact enough? use rationals via long double */
    long double A[M + 1];
    for (int m = 0; m <= M; m++) {
        A[m] = 1.0L / (m + 1);
        for (int j = m; j > 0; j--) A[j - 1] = j * (A[j - 1] - A[j]);
        B[m] = (double)A[0];
    }
    if (B[1] > 0) B[1] = -B[1];
    (void)a;
    for (int n = 2; n <= M; n++) {
        double c = 1;  /* comb(n,k) */
        for (int k = 0; k < n; k++) { PHI[n][n - k] = c * B[k]; c = c * (n - k) / (k + 1); }
    }
}
static double d_m(double x, double y) {
    double t = x * y, total = 0, tp[M + 1], xp[M + 1];
    tp[0] = xp[0] = 1;
    for (int i = 1; i <= M; i++) { tp[i] = tp[i - 1] * t; xp[i] = xp[i - 1] * x; }
    for (int n = 2; n <= M; n++) {
        double term = tp[n - 1] * y;
        for (int j = n - 1; j >= 1; j--) term += PHI[n][j] * tp[j] * xp[n - 1 - j];
        total += ((n % 2) ? -1.0 : 1.0) * term / (n * (n - 1));
    }
    return total;
}
static double ll_bern(const double *x, const double *p, double psi, int K) {
    double s = 0, N = 0;
    for (int k = 0; k < K; k++) { N += x[k]; if (x[k]) s += x[k] * log(p[k]) + d_m(psi / p[k], x[k]); }
    return s - d_m(psi, N);
}
static double ll_vgam_exact(const double *x, const double *p, double psi, int K) {
    double total = 0; long j = 0;
    for (int k = 0; k < K; k++) for (long r = 0; r < (long)x[k]; r++, j++)
        total += psi >= 1 ? log(p[k] / psi + r) - log(j + 1.0 / psi) : log(r * psi + p[k]) - log(j * psi + 1.0);
    return total;
}
static void next(double *p, double *psi, const double *x, int K) {
    double n = 0; for (int k = 0; k < K; k++) n += x[k];
    double denom = *psi * n + 1.0, psi2 = *psi < 1.0 ? *psi / denom : 1.0 / (1.0 / *psi + n);
    for (int k = 0; k < K; k++) p[k] = p[k] / denom + x[k] * psi2;
    *psi = psi2;
}
double ll_mesh(const double *counts, const double *p0, double psi, int K) {
    double n[16], p[16], x[16], a[16], total = 0; int any = 0, warm = 0;
    for (int k = 0; k < K; k++) { n[k] = counts[k]; p[k] = p0[k]; any |= n[k] != 0; }
    if (!any) return 0;
    if (psi == 0) { for (int k = 0; k < K; k++) if (n[k]) total += n[k] * log(p[k]); return total; }
    for (int k = 0; k < K; k++) { a[k] = p[k] / psi; x[k] = (n[k] && a[k] < MIN_ALPHA) ? fmin(n[k], ceil(MIN_ALPHA - a[k])) : 0; warm |= n[k] && a[k] < MIN_ALPHA; }
    if (warm) { total += ll_vgam_exact(x, p, psi, K); next(p, &psi, x, K); for (int k = 0; k < K; k++) n[k] -= x[k]; }
    for (;;) {
        any = 0; for (int k = 0; k < K; k++) any |= n[k] != 0;
        if (!any) break;
        for (int k = 0; k < K; k++) { a[k] = p[k] / psi; x[k] = n[k] ? (a[k] * DELTA >= n[k] ? n[k] : floor(a[k] * DELTA)) : 0; }
        total += ll_bern(x, p, psi, K); next(p, &psi, x, K);
        for (int k = 0; k < K; k++) n[k] -= x[k];
    }
    return total;
}
int main(int argc, char **argv) {
    init();
    if (argc > 1) {  /* check mode: same stdin format as lldmn_driver */
        int k; double psi;
        while (scanf("%d %lf", &k, &psi) == 2) {
            double n[16], p[16];
            for (int i = 0; i < k; i++) scanf("%lf", &n[i]);
            for (int i = 0; i < k; i++) scanf("%lf", &p[i]);
            printf("%.17g\n", ll_mesh(n, p, psi, k));
        }
        return 0;
    }
    double p[3] = {1.0 / 6, 1.0 / 3, 1.0 / 2}, psi = 1.0 / 60, sink = 0;
    printf("n,method,runtime_us\n");
    for (double n = 100; n <= 1e7; n *= 10) {
        double x[3] = {n, 2 * n, 3 * n};
        for (int w = 0; w < 50; w++) sink += ll_mesh(x, p, psi, 3);
        for (int r = 0; r < 100; r++) {
            struct timespec t0, t1; clock_gettime(CLOCK_MONOTONIC_RAW, &t0);
            sink += ll_mesh(x, p, psi, 3);
            clock_gettime(CLOCK_MONOTONIC_RAW, &t1);
            printf("%.0f,mesh,%.4f\n", n, (t1.tv_sec - t0.tv_sec) * 1e6 + (t1.tv_nsec - t0.tv_nsec) / 1e3);
        }
    }
    fprintf(stderr, "sink %g\n", sink);
    return 0;
}
