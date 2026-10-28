#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
typedef struct { void *b, *e, *c; } vec;
double ll_mesh(vec *n, vec *p, double psi) __asm__("__ZN9loglikdmn22loglikdirmultinom_meshESt6vectorIjSaIjEES0_IdSaIdEEd");
static vec make(const void *src, size_t bytes) { vec v; v.b = malloc(bytes); memcpy(v.b, src, bytes); v.e = v.c = (char *)v.b + bytes; return v; }
int main(void) {
    double p[3] = {1.0/6, 1.0/3, 1.0/2}, psi = 1.0/60, sink = 0;
    printf("n,method,runtime_us\n");
    for (unsigned n = 100; n <= 10000000; n *= 10) {
        unsigned x[3] = {n, 2*n, 3*n};
        for (int w = 0; w < 20; w++) { vec a = make(x, sizeof x), b = make(p, sizeof p); sink += ll_mesh(&a, &b, psi); free(a.b); free(b.b); }
        for (int r = 0; r < 100; r++) {
            vec a = make(x, sizeof x), b = make(p, sizeof p);
            struct timespec t0, t1; clock_gettime(CLOCK_MONOTONIC_RAW, &t0);
            sink += ll_mesh(&a, &b, psi);
            clock_gettime(CLOCK_MONOTONIC_RAW, &t1);
            printf("%u,mesh,%.4f\n", n, (t1.tv_sec - t0.tv_sec) * 1e6 + (t1.tv_nsec - t0.tv_nsec) / 1e3);
            free(a.b); free(b.b);
        }
    }
    fprintf(stderr, "sink %g\n", sink);
    return 0;
}
