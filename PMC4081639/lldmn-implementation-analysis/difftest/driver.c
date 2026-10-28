/* Calls the authors' compiled lldmn functions. Input lines: K psi n_1..n_K p_1..p_K
   Output: mesh vgam bern_approx (%.17g). Vectors use the libstdc++ layout {begin, end, cap}. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct { void *b, *e, *c; } vec;

double ll_mesh(vec *n, vec *p, double psi) __asm__("__ZN9loglikdmn22loglikdirmultinom_meshESt6vectorIjSaIjEES0_IdSaIdEEd");
double ll_vgam(const vec *n, const vec *p, double psi) __asm__("__ZN9loglikdmn22loglikdirmultinom_vgamERKSt6vectorIjSaIjEERKS0_IdSaIdEEd");
double ll_bern(const vec *n, const vec *p, double psi) __asm__("__ZN9loglikdmn29loglikdirmultinom_bern_approxERKSt6vectorIjSaIjEERKS0_IdSaIdEEd");

static vec make(const void *src, size_t bytes) {
    vec v; v.b = malloc(bytes ? bytes : 1); memcpy(v.b, src, bytes);
    v.e = v.c = (char *)v.b + bytes; return v;
}

int main(void) {
    int k; double psi;
    while (scanf("%d %lf", &k, &psi) == 2) {
        unsigned *n = malloc(sizeof(unsigned) * k); double *p = malloc(sizeof(double) * k);
        for (int i = 0; i < k; i++) scanf("%u", &n[i]);
        for (int i = 0; i < k; i++) scanf("%lf", &p[i]);
        vec vn = make(n, sizeof(unsigned) * k), vp = make(p, sizeof(double) * k);
        double vg = ll_vgam(&vn, &vp, psi), be = ll_bern(&vn, &vp, psi);
        double me = ll_mesh(&vn, &vp, psi);   /* by-value temporaries: callee may reassign them */
        printf("%.17g %.17g %.17g\n", me, vg, be);
        free(vn.b); free(vp.b); free(n); free(p);
    }
    return 0;
}
