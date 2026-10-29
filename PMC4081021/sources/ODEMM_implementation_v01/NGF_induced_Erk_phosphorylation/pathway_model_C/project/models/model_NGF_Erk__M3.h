#ifndef _MY_model_NGF_Erk__M3
#define _MY_model_NGF_Erk__M3

#include <cvodes/cvodes.h>
#include <cvodes/cvodes_dense.h>
#include <nvector/nvector_serial.h>
#include <sundials/sundials_types.h>
#include <sundials/sundials_math.h>
#include <udata.h>
#include <math.h>
#include <mex.h>

             void fu_model_NGF_Erk__M3(void *user_data, double t);
             void fsu_model_NGF_Erk__M3(void *user_data, double t);
             void fv_model_NGF_Erk__M3(realtype t, N_Vector x, void *user_data);
             void dvdx_model_NGF_Erk__M3(realtype t, N_Vector x, void *user_data);
             void dvdu_model_NGF_Erk__M3(realtype t, N_Vector x, void *user_data);
             void dvdp_model_NGF_Erk__M3(realtype t, N_Vector x, void *user_data);
             int fx_model_model_NGF_Erk__M3(realtype t, N_Vector x, N_Vector xdot, void *user_data);
             void fxdouble_model_NGF_Erk__M3(realtype t, N_Vector x, double *xdot_tmp, void *user_data);
             void fx0_model_NGF_Erk__M3(N_Vector x0, void *user_data);
             int dfxdx_model_NGF_Erk__M3(long int N, realtype t, N_Vector x,N_Vector fx, DlsMat J, void *user_data,N_Vector tmp1, N_Vector tmp2, N_Vector tmp3);
             int fsx_model_NGF_Erk__M3(int Ns, realtype t, N_Vector x, N_Vector xdot,int ip, N_Vector sx, N_Vector sxdot, void *user_data,N_Vector tmp1, N_Vector tmp2);
             void fsx0_model_NGF_Erk__M3(int ip, N_Vector sx0, void *user_data);
             void dfxdp_model_NGF_Erk__M3(realtype t, N_Vector x, double *dfxdp, void *user_data);
             void fy_model_NGF_Erk__M3(double t, int nt, int it, double *y, double *p, double *u, double *x);
             void fsy_model_NGF_Erk__M3(double t, int nt, int it, double *sy, double *p, double *u, double *x, double *su, double *sx);


#endif /* _MY_model_NGF_Erk__M3 */
