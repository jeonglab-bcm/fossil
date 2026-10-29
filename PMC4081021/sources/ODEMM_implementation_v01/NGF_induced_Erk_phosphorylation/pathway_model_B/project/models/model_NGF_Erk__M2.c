#include "model_NGF_Erk__M2.h"
#include <cvodes/cvodes.h>
#include <cvodes/cvodes_dense.h>
#include <nvector/nvector_serial.h>
#include <sundials/sundials_types.h>
#include <sundials/sundials_math.h>
#include <udata.h>
#include <math.h>
#include <mex.h>



 void fu_model_NGF_Erk__M2(void *user_data, double t)
{

  return;
}


 void fsu_model_NGF_Erk__M2(void *user_data, double t)
{

  return;
}


 void fv_model_NGF_Erk__M2(realtype t, N_Vector x, void *user_data)
{
  UserData data = (UserData) user_data;
  double *p = data->p;
  double *u = data->u;
  double *x_tmp = N_VGetArrayPointer(x);
  data->v[0] = -p[1]*x_tmp[0]+(p[7]-x_tmp[0])*p[0]*p[12];
  data->v[1] = -p[3]*x_tmp[1]+(p[2]+x_tmp[0])*(p[8]-x_tmp[1]);
  data->v[2] = -p[4]*x_tmp[2]+(p[9]-x_tmp[2])*x_tmp[1];
  data->v[3] = -p[5]*x_tmp[3]+(p[10]-x_tmp[3])*x_tmp[2];
  data->v[4] = -p[6]*x_tmp[4]+(p[11]-x_tmp[4])*x_tmp[3];  

  return;
}


 void dvdx_model_NGF_Erk__M2(realtype t, N_Vector x, void *user_data)
{
  UserData data = (UserData) user_data;
  double *p = data->p;
  double *u = data->u;
  double *x_tmp = N_VGetArrayPointer(x);
  data->dvdx[0] = -p[1]-p[0]*p[12];
  data->dvdx[1] = p[8]-x_tmp[1];
  data->dvdx[6] = -p[2]-p[3]-x_tmp[0];
  data->dvdx[7] = p[9]-x_tmp[2];
  data->dvdx[12] = -p[4]-x_tmp[1];
  data->dvdx[13] = p[10]-x_tmp[3];
  data->dvdx[18] = -p[5]-x_tmp[2];
  data->dvdx[19] = p[11]-x_tmp[4];
  data->dvdx[24] = -p[6]-x_tmp[3];  

  return;
}


 void dvdu_model_NGF_Erk__M2(realtype t, N_Vector x, void *user_data)
{

  return;
}


 void dvdp_model_NGF_Erk__M2(realtype t, N_Vector x, void *user_data)
{
  UserData data = (UserData) user_data;
  double *p = data->p;
  double *u = data->u;
  double *x_tmp = N_VGetArrayPointer(x);
  data->dvdp[0] = (p[7]-x_tmp[0])*p[12];
  data->dvdp[5] = -x_tmp[0];
  data->dvdp[11] = p[8]-x_tmp[1];
  data->dvdp[16] = -x_tmp[1];
  data->dvdp[22] = -x_tmp[2];
  data->dvdp[28] = -x_tmp[3];
  data->dvdp[34] = -x_tmp[4];
  data->dvdp[35] = p[0]*p[12];
  data->dvdp[41] = p[2]+x_tmp[0];
  data->dvdp[47] = x_tmp[1];
  data->dvdp[53] = x_tmp[2];
  data->dvdp[59] = x_tmp[3];
  data->dvdp[60] = (p[7]-x_tmp[0])*p[0];  
  
  return;
}


 int fx_model_NGF_Erk__M2(realtype t, N_Vector x, N_Vector xdot, void *user_data)
{
  int is;
  UserData data = (UserData) user_data;
  double *qpositivex = data->qpositivex;
  double *p = data->p;
  double *u = data->u;
  double *v = data->v;
  double *x_tmp = N_VGetArrayPointer(x);
  double *xdot_tmp = N_VGetArrayPointer(xdot);
  fu_model_NGF_Erk__M2(data, t);
  fv_model_NGF_Erk__M2(t, x, data);
  xdot_tmp[0] = v[0];
  xdot_tmp[1] = v[1];
  xdot_tmp[2] = v[2];
  xdot_tmp[3] = v[3];
  xdot_tmp[4] = v[4];
  for (is=0; is<5; is++) {
    if(mxIsNaN(xdot_tmp[is])) xdot_tmp[is] = 0.0;
    if(qpositivex[is]>0.5 && x_tmp[is]<0.0 && xdot_tmp[is]<0.0) xdot_tmp[is] = -xdot_tmp[is];
  }

  return(0);
}


 void fxdouble_model_NGF_Erk__M2(realtype t, N_Vector x, double *xdot_tmp, void *user_data)
{
  int is;
  UserData data = (UserData) user_data;
  double *p = data->p;
  double *u = data->u;
  double *v = data->v;
  fu_model_NGF_Erk__M2(data, t);
  fv_model_NGF_Erk__M2(t, x, data);
  xdot_tmp[0] = v[0];
  xdot_tmp[1] = v[1];
  xdot_tmp[2] = v[2];
  xdot_tmp[3] = v[3];
  xdot_tmp[4] = v[4];
  for (is=0; is<5; is++) {
    if(mxIsNaN(xdot_tmp[is])) xdot_tmp[is] = 0.0;
  }

  return;
}


 void fx0_model_NGF_Erk__M2(N_Vector x0, void *user_data)
{
  UserData data = (UserData) user_data;
  double *p = data->p;
  double *u = data->u;
  double *x0_tmp = N_VGetArrayPointer(x0);
  x0_tmp[1] = (p[2]*p[8])/(p[2]+p[3]);
  x0_tmp[2] = (p[2]*p[8]*p[9])/((p[4]+(p[2]*p[8])/(p[2]+p[3]))*(p[2]+p[3]));
  x0_tmp[3] = (p[2]*p[8]*p[9]*p[10])/((p[5]+(p[2]*p[8]*p[9])/((p[4]+(p[2]*p[8])/(p[2]+p[3]))*(p[2]+p[3])))*(p[4]+(p[2]*p[8])/(p[2]+p[3]))*(p[2]+p[3]));
  x0_tmp[4] = (p[2]*p[8]*p[9]*p[10]*p[11])/((p[5]+(p[2]*p[8]*p[9])/((p[4]+(p[2]*p[8])/(p[2]+p[3]))*(p[2]+p[3])))*(p[4]+(p[2]*p[8])/(p[2]+p[3]))*(p[6]+(p[2]*p[8]*p[9]*p[10])/((p[5]+(p[2]*p[8]*p[9])/((p[4]+(p[2]*p[8])/(p[2]+p[3]))*(p[2]+p[3])))*(p[4]+(p[2]*p[8])/(p[2]+p[3]))*(p[2]+p[3])))*(p[2]+p[3]));  
  
  return;
}


 int dfxdx_model_NGF_Erk__M2(long int N, realtype t, N_Vector x,
  	N_Vector fx, DlsMat J, void *user_data, 
  	N_Vector tmp1, N_Vector tmp2, N_Vector tmp3)
{
  int is;
  UserData data = (UserData) user_data;
  double *p = data->p;
  double *u = data->u;
  double *dvdx = data->dvdx;
  dvdx_model_NGF_Erk__M2(t, x, data);
  J->data[0] = dvdx[0];
  J->data[1] = dvdx[1];
  J->data[6] = dvdx[6];
  J->data[7] = dvdx[7];
  J->data[12] = dvdx[12];
  J->data[13] = dvdx[13];
  J->data[18] = dvdx[18];
  J->data[19] = dvdx[19];
  J->data[24] = dvdx[24];
  J->data[2] = 0.0;
  J->data[3] = 0.0;
  J->data[4] = 0.0;
  J->data[5] = 0.0;
  J->data[8] = 0.0;
  J->data[9] = 0.0;
  J->data[10] = 0.0;
  J->data[11] = 0.0;
  J->data[14] = 0.0;
  J->data[15] = 0.0;
  J->data[16] = 0.0;
  J->data[17] = 0.0;
  J->data[20] = 0.0;
  J->data[21] = 0.0;
  J->data[22] = 0.0;
  J->data[23] = 0.0;
  for (is=0; is<25; is++) {
    if(mxIsNaN(J->data[is])) J->data[is] = 0.0;
  }

  return(0);
}


 int fsx_model_NGF_Erk__M2(int Ns, realtype t, N_Vector x, N_Vector xdot,
  	int ip, N_Vector sx, N_Vector sxdot, void *user_data, 
  	N_Vector tmp1, N_Vector tmp2)
{
  int is;
  UserData data = (UserData) user_data;
  double *p = data->p;
  double *u = data->u;
  double *sv = data->sv;
  double *dvdx = data->dvdx;
  double *dvdu = data->dvdu;
  double *dvdp = data->dvdp;
  double *su = data->su;
  double *sx_tmp = N_VGetArrayPointer(sx);
  double *sxdot_tmp = N_VGetArrayPointer(sxdot);
  switch (ip) {
  case 0: {
  fsu_model_NGF_Erk__M2(data, t);
  dvdx_model_NGF_Erk__M2(t, x, data);
  dvdu_model_NGF_Erk__M2(t, x, data);
  dvdp_model_NGF_Erk__M2(t, x, data);
  sv[0] = dvdp[0]+dvdx[0]*sx_tmp[0];
  sv[1] = dvdx[1]*sx_tmp[0]+dvdx[6]*sx_tmp[1];
  sv[2] = dvdx[7]*sx_tmp[1]+dvdx[12]*sx_tmp[2];
  sv[3] = dvdx[13]*sx_tmp[2]+dvdx[18]*sx_tmp[3];
  sv[4] = dvdx[19]*sx_tmp[3]+dvdx[24]*sx_tmp[4];
  sxdot_tmp[0] = sv[0];
  sxdot_tmp[1] = sv[1];
  sxdot_tmp[2] = sv[2];
  sxdot_tmp[3] = sv[3];
  sxdot_tmp[4] = sv[4];
  } break;

  case 1: {
  sv[0] = dvdp[5]+dvdx[0]*sx_tmp[0];
  sv[1] = dvdx[1]*sx_tmp[0]+dvdx[6]*sx_tmp[1];
  sv[2] = dvdx[7]*sx_tmp[1]+dvdx[12]*sx_tmp[2];
  sv[3] = dvdx[13]*sx_tmp[2]+dvdx[18]*sx_tmp[3];
  sv[4] = dvdx[19]*sx_tmp[3]+dvdx[24]*sx_tmp[4];
  sxdot_tmp[0] = sv[0];
  sxdot_tmp[1] = sv[1];
  sxdot_tmp[2] = sv[2];
  sxdot_tmp[3] = sv[3];
  sxdot_tmp[4] = sv[4];
  } break;

  case 2: {
  sv[0] = dvdx[0]*sx_tmp[0];
  sv[1] = dvdp[11]+dvdx[1]*sx_tmp[0]+dvdx[6]*sx_tmp[1];
  sv[2] = dvdx[7]*sx_tmp[1]+dvdx[12]*sx_tmp[2];
  sv[3] = dvdx[13]*sx_tmp[2]+dvdx[18]*sx_tmp[3];
  sv[4] = dvdx[19]*sx_tmp[3]+dvdx[24]*sx_tmp[4];
  sxdot_tmp[0] = sv[0];
  sxdot_tmp[1] = sv[1];
  sxdot_tmp[2] = sv[2];
  sxdot_tmp[3] = sv[3];
  sxdot_tmp[4] = sv[4];
  } break;

  case 3: {
  sv[0] = dvdx[0]*sx_tmp[0];
  sv[1] = dvdp[16]+dvdx[1]*sx_tmp[0]+dvdx[6]*sx_tmp[1];
  sv[2] = dvdx[7]*sx_tmp[1]+dvdx[12]*sx_tmp[2];
  sv[3] = dvdx[13]*sx_tmp[2]+dvdx[18]*sx_tmp[3];
  sv[4] = dvdx[19]*sx_tmp[3]+dvdx[24]*sx_tmp[4];
  sxdot_tmp[0] = sv[0];
  sxdot_tmp[1] = sv[1];
  sxdot_tmp[2] = sv[2];
  sxdot_tmp[3] = sv[3];
  sxdot_tmp[4] = sv[4];
  } break;

  case 4: {
  sv[0] = dvdx[0]*sx_tmp[0];
  sv[1] = dvdx[1]*sx_tmp[0]+dvdx[6]*sx_tmp[1];
  sv[2] = dvdp[22]+dvdx[7]*sx_tmp[1]+dvdx[12]*sx_tmp[2];
  sv[3] = dvdx[13]*sx_tmp[2]+dvdx[18]*sx_tmp[3];
  sv[4] = dvdx[19]*sx_tmp[3]+dvdx[24]*sx_tmp[4];
  sxdot_tmp[0] = sv[0];
  sxdot_tmp[1] = sv[1];
  sxdot_tmp[2] = sv[2];
  sxdot_tmp[3] = sv[3];
  sxdot_tmp[4] = sv[4];
  } break;

  case 5: {
  sv[0] = dvdx[0]*sx_tmp[0];
  sv[1] = dvdx[1]*sx_tmp[0]+dvdx[6]*sx_tmp[1];
  sv[2] = dvdx[7]*sx_tmp[1]+dvdx[12]*sx_tmp[2];
  sv[3] = dvdp[28]+dvdx[13]*sx_tmp[2]+dvdx[18]*sx_tmp[3];
  sv[4] = dvdx[19]*sx_tmp[3]+dvdx[24]*sx_tmp[4];
  sxdot_tmp[0] = sv[0];
  sxdot_tmp[1] = sv[1];
  sxdot_tmp[2] = sv[2];
  sxdot_tmp[3] = sv[3];
  sxdot_tmp[4] = sv[4];
  } break;

  case 6: {
  sv[0] = dvdx[0]*sx_tmp[0];
  sv[1] = dvdx[1]*sx_tmp[0]+dvdx[6]*sx_tmp[1];
  sv[2] = dvdx[7]*sx_tmp[1]+dvdx[12]*sx_tmp[2];
  sv[3] = dvdx[13]*sx_tmp[2]+dvdx[18]*sx_tmp[3];
  sv[4] = dvdp[34]+dvdx[19]*sx_tmp[3]+dvdx[24]*sx_tmp[4];
  sxdot_tmp[0] = sv[0];
  sxdot_tmp[1] = sv[1];
  sxdot_tmp[2] = sv[2];
  sxdot_tmp[3] = sv[3];
  sxdot_tmp[4] = sv[4];
  } break;

  case 7: {
  sv[0] = dvdp[35]+dvdx[0]*sx_tmp[0];
  sv[1] = dvdx[1]*sx_tmp[0]+dvdx[6]*sx_tmp[1];
  sv[2] = dvdx[7]*sx_tmp[1]+dvdx[12]*sx_tmp[2];
  sv[3] = dvdx[13]*sx_tmp[2]+dvdx[18]*sx_tmp[3];
  sv[4] = dvdx[19]*sx_tmp[3]+dvdx[24]*sx_tmp[4];
  sxdot_tmp[0] = sv[0];
  sxdot_tmp[1] = sv[1];
  sxdot_tmp[2] = sv[2];
  sxdot_tmp[3] = sv[3];
  sxdot_tmp[4] = sv[4];
  } break;

  case 8: {
  sv[0] = dvdx[0]*sx_tmp[0];
  sv[1] = dvdp[41]+dvdx[1]*sx_tmp[0]+dvdx[6]*sx_tmp[1];
  sv[2] = dvdx[7]*sx_tmp[1]+dvdx[12]*sx_tmp[2];
  sv[3] = dvdx[13]*sx_tmp[2]+dvdx[18]*sx_tmp[3];
  sv[4] = dvdx[19]*sx_tmp[3]+dvdx[24]*sx_tmp[4];
  sxdot_tmp[0] = sv[0];
  sxdot_tmp[1] = sv[1];
  sxdot_tmp[2] = sv[2];
  sxdot_tmp[3] = sv[3];
  sxdot_tmp[4] = sv[4];
  } break;

  case 9: {
  sv[0] = dvdx[0]*sx_tmp[0];
  sv[1] = dvdx[1]*sx_tmp[0]+dvdx[6]*sx_tmp[1];
  sv[2] = dvdp[47]+dvdx[7]*sx_tmp[1]+dvdx[12]*sx_tmp[2];
  sv[3] = dvdx[13]*sx_tmp[2]+dvdx[18]*sx_tmp[3];
  sv[4] = dvdx[19]*sx_tmp[3]+dvdx[24]*sx_tmp[4];
  sxdot_tmp[0] = sv[0];
  sxdot_tmp[1] = sv[1];
  sxdot_tmp[2] = sv[2];
  sxdot_tmp[3] = sv[3];
  sxdot_tmp[4] = sv[4];
  } break;

  case 10: {
  sv[0] = dvdx[0]*sx_tmp[0];
  sv[1] = dvdx[1]*sx_tmp[0]+dvdx[6]*sx_tmp[1];
  sv[2] = dvdx[7]*sx_tmp[1]+dvdx[12]*sx_tmp[2];
  sv[3] = dvdp[53]+dvdx[13]*sx_tmp[2]+dvdx[18]*sx_tmp[3];
  sv[4] = dvdx[19]*sx_tmp[3]+dvdx[24]*sx_tmp[4];
  sxdot_tmp[0] = sv[0];
  sxdot_tmp[1] = sv[1];
  sxdot_tmp[2] = sv[2];
  sxdot_tmp[3] = sv[3];
  sxdot_tmp[4] = sv[4];
  } break;

  case 11: {
  sv[0] = dvdx[0]*sx_tmp[0];
  sv[1] = dvdx[1]*sx_tmp[0]+dvdx[6]*sx_tmp[1];
  sv[2] = dvdx[7]*sx_tmp[1]+dvdx[12]*sx_tmp[2];
  sv[3] = dvdx[13]*sx_tmp[2]+dvdx[18]*sx_tmp[3];
  sv[4] = dvdp[59]+dvdx[19]*sx_tmp[3]+dvdx[24]*sx_tmp[4];
  sxdot_tmp[0] = sv[0];
  sxdot_tmp[1] = sv[1];
  sxdot_tmp[2] = sv[2];
  sxdot_tmp[3] = sv[3];
  sxdot_tmp[4] = sv[4];
  } break;

  case 12: {
  sv[0] = dvdp[60]+dvdx[0]*sx_tmp[0];
  sv[1] = dvdx[1]*sx_tmp[0]+dvdx[6]*sx_tmp[1];
  sv[2] = dvdx[7]*sx_tmp[1]+dvdx[12]*sx_tmp[2];
  sv[3] = dvdx[13]*sx_tmp[2]+dvdx[18]*sx_tmp[3];
  sv[4] = dvdx[19]*sx_tmp[3]+dvdx[24]*sx_tmp[4];
  sxdot_tmp[0] = sv[0];
  sxdot_tmp[1] = sv[1];
  sxdot_tmp[2] = sv[2];
  sxdot_tmp[3] = sv[3];
  sxdot_tmp[4] = sv[4];
  } break;

  }
  for (is=0; is<5; is++) {
    if(mxIsNaN(sxdot_tmp[is])) sxdot_tmp[is] = 0.0;
  }

  return(0);
}


 void fsx0_model_NGF_Erk__M2(int ip, N_Vector sx0, void *user_data)
{
  UserData data = (UserData) user_data;
  double *p = data->p;
  double *u = data->u;
  double *sx0_tmp = N_VGetArrayPointer(sx0);
  switch (ip) {
  case 0: {

  } break;

  case 1: {

  } break;

  case 2: {
  sx0_tmp[1] = p[3]*p[8]*1.0/pow(p[2]+p[3],2.0);
  sx0_tmp[2] = p[3]*p[4]*p[8]*p[9]*1.0/pow(p[2]*p[4]+p[3]*p[4]+p[2]*p[8],2.0);
  sx0_tmp[3] = p[3]*p[4]*p[5]*p[8]*p[9]*p[10]*1.0/pow(p[2]*p[4]*p[5]+p[3]*p[4]*p[5]+p[2]*p[5]*p[8]+p[2]*p[8]*p[9],2.0);
  sx0_tmp[4] = p[3]*p[4]*p[5]*p[6]*p[8]*p[9]*p[10]*p[11]*1.0/pow(p[2]*p[4]*p[5]*p[6]+p[3]*p[4]*p[5]*p[6]+p[2]*p[5]*p[6]*p[8]+p[2]*p[6]*p[8]*p[9]+p[2]*p[8]*p[9]*p[10],2.0);
  } break;

  case 3: {
  sx0_tmp[1] = -p[2]*p[8]*1.0/pow(p[2]+p[3],2.0);
  sx0_tmp[2] = -p[2]*p[4]*p[8]*p[9]*1.0/pow(p[2]*p[4]+p[3]*p[4]+p[2]*p[8],2.0);
  sx0_tmp[3] = -p[2]*p[4]*p[5]*p[8]*p[9]*p[10]*1.0/pow(p[2]*p[4]*p[5]+p[3]*p[4]*p[5]+p[2]*p[5]*p[8]+p[2]*p[8]*p[9],2.0);
  sx0_tmp[4] = -p[2]*p[4]*p[5]*p[6]*p[8]*p[9]*p[10]*p[11]*1.0/pow(p[2]*p[4]*p[5]*p[6]+p[3]*p[4]*p[5]*p[6]+p[2]*p[5]*p[6]*p[8]+p[2]*p[6]*p[8]*p[9]+p[2]*p[8]*p[9]*p[10],2.0);
  } break;

  case 4: {
  sx0_tmp[2] = -p[2]*p[8]*p[9]*(p[2]+p[3])*1.0/pow(p[2]*p[4]+p[3]*p[4]+p[2]*p[8],2.0);
  sx0_tmp[3] = -p[2]*p[5]*p[8]*p[9]*p[10]*(p[2]+p[3])*1.0/pow(p[2]*p[4]*p[5]+p[3]*p[4]*p[5]+p[2]*p[5]*p[8]+p[2]*p[8]*p[9],2.0);
  sx0_tmp[4] = -p[2]*p[5]*p[6]*p[8]*p[9]*p[10]*p[11]*(p[2]+p[3])*1.0/pow(p[2]*p[4]*p[5]*p[6]+p[3]*p[4]*p[5]*p[6]+p[2]*p[5]*p[6]*p[8]+p[2]*p[6]*p[8]*p[9]+p[2]*p[8]*p[9]*p[10],2.0);
  } break;

  case 5: {
  sx0_tmp[3] = -p[2]*p[8]*p[9]*p[10]*(p[2]*p[4]+p[3]*p[4]+p[2]*p[8])*1.0/pow(p[2]*p[4]*p[5]+p[3]*p[4]*p[5]+p[2]*p[5]*p[8]+p[2]*p[8]*p[9],2.0);
  sx0_tmp[4] = -p[2]*p[6]*p[8]*p[9]*p[10]*p[11]*(p[2]*p[4]+p[3]*p[4]+p[2]*p[8])*1.0/pow(p[2]*p[4]*p[5]*p[6]+p[3]*p[4]*p[5]*p[6]+p[2]*p[5]*p[6]*p[8]+p[2]*p[6]*p[8]*p[9]+p[2]*p[8]*p[9]*p[10],2.0);
  } break;

  case 6: {
  sx0_tmp[4] = -p[2]*p[8]*p[9]*p[10]*p[11]*(p[2]*p[4]*p[5]+p[3]*p[4]*p[5]+p[2]*p[5]*p[8]+p[2]*p[8]*p[9])*1.0/pow(p[2]*p[4]*p[5]*p[6]+p[3]*p[4]*p[5]*p[6]+p[2]*p[5]*p[6]*p[8]+p[2]*p[6]*p[8]*p[9]+p[2]*p[8]*p[9]*p[10],2.0);
  } break;

  case 7: {

  } break;

  case 8: {
  sx0_tmp[1] = p[2]/(p[2]+p[3]);
  sx0_tmp[2] = p[2]*p[4]*p[9]*(p[2]+p[3])*1.0/pow(p[2]*p[4]+p[3]*p[4]+p[2]*p[8],2.0);
  sx0_tmp[3] = p[2]*p[4]*p[5]*p[9]*p[10]*(p[2]+p[3])*1.0/pow(p[2]*p[4]*p[5]+p[3]*p[4]*p[5]+p[2]*p[5]*p[8]+p[2]*p[8]*p[9],2.0);
  sx0_tmp[4] = p[2]*p[4]*p[5]*p[6]*p[9]*p[10]*p[11]*(p[2]+p[3])*1.0/pow(p[2]*p[4]*p[5]*p[6]+p[3]*p[4]*p[5]*p[6]+p[2]*p[5]*p[6]*p[8]+p[2]*p[6]*p[8]*p[9]+p[2]*p[8]*p[9]*p[10],2.0);
  } break;

  case 9: {
  sx0_tmp[2] = (p[2]*p[8])/(p[2]*p[4]+p[3]*p[4]+p[2]*p[8]);
  sx0_tmp[3] = p[2]*p[5]*p[8]*p[10]*(p[2]*p[4]+p[3]*p[4]+p[2]*p[8])*1.0/pow(p[2]*p[4]*p[5]+p[3]*p[4]*p[5]+p[2]*p[5]*p[8]+p[2]*p[8]*p[9],2.0);
  sx0_tmp[4] = p[2]*p[5]*p[6]*p[8]*p[10]*p[11]*(p[2]*p[4]+p[3]*p[4]+p[2]*p[8])*1.0/pow(p[2]*p[4]*p[5]*p[6]+p[3]*p[4]*p[5]*p[6]+p[2]*p[5]*p[6]*p[8]+p[2]*p[6]*p[8]*p[9]+p[2]*p[8]*p[9]*p[10],2.0);
  } break;

  case 10: {
  sx0_tmp[3] = (p[2]*p[8]*p[9])/(p[2]*p[4]*p[5]+p[3]*p[4]*p[5]+p[2]*p[5]*p[8]+p[2]*p[8]*p[9]);
  sx0_tmp[4] = p[2]*p[6]*p[8]*p[9]*p[11]*(p[2]*p[4]*p[5]+p[3]*p[4]*p[5]+p[2]*p[5]*p[8]+p[2]*p[8]*p[9])*1.0/pow(p[2]*p[4]*p[5]*p[6]+p[3]*p[4]*p[5]*p[6]+p[2]*p[5]*p[6]*p[8]+p[2]*p[6]*p[8]*p[9]+p[2]*p[8]*p[9]*p[10],2.0);
  } break;

  case 11: {
  sx0_tmp[4] = (p[2]*p[8]*p[9]*p[10])/(p[2]*p[4]*p[5]*p[6]+p[3]*p[4]*p[5]*p[6]+p[2]*p[5]*p[6]*p[8]+p[2]*p[6]*p[8]*p[9]+p[2]*p[8]*p[9]*p[10]);
  } break;

  case 12: {

  } break;

  }

  return;
}


 void dfxdp_model_NGF_Erk__M2(realtype t, N_Vector x, double *dfxdp, void *user_data)
{
  int is;
  UserData data = (UserData) user_data;
  double *p = data->p;
  double *u = data->u;
  double *dvdp = data->dvdp;
  double *dvdx = data->dvdx;
  double *dvdu = data->dvdu;
  double *x_tmp = N_VGetArrayPointer(x);
  dfxdp[0] = dvdp[0];
  dfxdp[5] = dvdp[5];
  dfxdp[11] = dvdp[11]+dvdx[6]*p[3]*p[8]*1.0/pow(p[2]+p[3],2.0);
  dfxdp[12] = dvdx[7]*p[3]*p[8]*1.0/pow(p[2]+p[3],2.0)+dvdx[12]*p[3]*p[4]*p[8]*p[9]*1.0/pow(p[2]*p[4]+p[3]*p[4]+p[2]*p[8],2.0);
  dfxdp[13] = dvdx[13]*p[3]*p[4]*p[8]*p[9]*1.0/pow(p[2]*p[4]+p[3]*p[4]+p[2]*p[8],2.0)+dvdx[18]*p[3]*p[4]*p[5]*p[8]*p[9]*p[10]*1.0/pow(p[2]*p[4]*p[5]+p[3]*p[4]*p[5]+p[2]*p[5]*p[8]+p[2]*p[8]*p[9],2.0);
  dfxdp[14] = dvdx[19]*p[3]*p[4]*p[5]*p[8]*p[9]*p[10]*1.0/pow(p[2]*p[4]*p[5]+p[3]*p[4]*p[5]+p[2]*p[5]*p[8]+p[2]*p[8]*p[9],2.0)+dvdx[24]*p[3]*p[4]*p[5]*p[6]*p[8]*p[9]*p[10]*p[11]*1.0/pow(p[2]*p[4]*p[5]*p[6]+p[3]*p[4]*p[5]*p[6]+p[2]*p[5]*p[6]*p[8]+p[2]*p[6]*p[8]*p[9]+p[2]*p[8]*p[9]*p[10],2.0);
  dfxdp[16] = dvdp[16]-dvdx[6]*p[2]*p[8]*1.0/pow(p[2]+p[3],2.0);
  dfxdp[17] = -dvdx[7]*p[2]*p[8]*1.0/pow(p[2]+p[3],2.0)-dvdx[12]*p[2]*p[4]*p[8]*p[9]*1.0/pow(p[2]*p[4]+p[3]*p[4]+p[2]*p[8],2.0);
  dfxdp[18] = -dvdx[13]*p[2]*p[4]*p[8]*p[9]*1.0/pow(p[2]*p[4]+p[3]*p[4]+p[2]*p[8],2.0)-dvdx[18]*p[2]*p[4]*p[5]*p[8]*p[9]*p[10]*1.0/pow(p[2]*p[4]*p[5]+p[3]*p[4]*p[5]+p[2]*p[5]*p[8]+p[2]*p[8]*p[9],2.0);
  dfxdp[19] = -dvdx[19]*p[2]*p[4]*p[5]*p[8]*p[9]*p[10]*1.0/pow(p[2]*p[4]*p[5]+p[3]*p[4]*p[5]+p[2]*p[5]*p[8]+p[2]*p[8]*p[9],2.0)-dvdx[24]*p[2]*p[4]*p[5]*p[6]*p[8]*p[9]*p[10]*p[11]*1.0/pow(p[2]*p[4]*p[5]*p[6]+p[3]*p[4]*p[5]*p[6]+p[2]*p[5]*p[6]*p[8]+p[2]*p[6]*p[8]*p[9]+p[2]*p[8]*p[9]*p[10],2.0);
  dfxdp[22] = dvdp[22]-dvdx[12]*p[2]*p[8]*p[9]*(p[2]+p[3])*1.0/pow(p[2]*p[4]+p[3]*p[4]+p[2]*p[8],2.0);
  dfxdp[23] = -dvdx[13]*p[2]*p[8]*p[9]*(p[2]+p[3])*1.0/pow(p[2]*p[4]+p[3]*p[4]+p[2]*p[8],2.0)-dvdx[18]*p[2]*p[5]*p[8]*p[9]*p[10]*(p[2]+p[3])*1.0/pow(p[2]*p[4]*p[5]+p[3]*p[4]*p[5]+p[2]*p[5]*p[8]+p[2]*p[8]*p[9],2.0);
  dfxdp[24] = -dvdx[19]*p[2]*p[5]*p[8]*p[9]*p[10]*(p[2]+p[3])*1.0/pow(p[2]*p[4]*p[5]+p[3]*p[4]*p[5]+p[2]*p[5]*p[8]+p[2]*p[8]*p[9],2.0)-dvdx[24]*p[2]*p[5]*p[6]*p[8]*p[9]*p[10]*p[11]*(p[2]+p[3])*1.0/pow(p[2]*p[4]*p[5]*p[6]+p[3]*p[4]*p[5]*p[6]+p[2]*p[5]*p[6]*p[8]+p[2]*p[6]*p[8]*p[9]+p[2]*p[8]*p[9]*p[10],2.0);
  dfxdp[28] = dvdp[28]-dvdx[18]*p[2]*p[8]*p[9]*p[10]*(p[2]*p[4]+p[3]*p[4]+p[2]*p[8])*1.0/pow(p[2]*p[4]*p[5]+p[3]*p[4]*p[5]+p[2]*p[5]*p[8]+p[2]*p[8]*p[9],2.0);
  dfxdp[29] = -dvdx[19]*p[2]*p[8]*p[9]*p[10]*(p[2]*p[4]+p[3]*p[4]+p[2]*p[8])*1.0/pow(p[2]*p[4]*p[5]+p[3]*p[4]*p[5]+p[2]*p[5]*p[8]+p[2]*p[8]*p[9],2.0)-dvdx[24]*p[2]*p[6]*p[8]*p[9]*p[10]*p[11]*(p[2]*p[4]+p[3]*p[4]+p[2]*p[8])*1.0/pow(p[2]*p[4]*p[5]*p[6]+p[3]*p[4]*p[5]*p[6]+p[2]*p[5]*p[6]*p[8]+p[2]*p[6]*p[8]*p[9]+p[2]*p[8]*p[9]*p[10],2.0);
  dfxdp[34] = dvdp[34]-dvdx[24]*p[2]*p[8]*p[9]*p[10]*p[11]*(p[2]*p[4]*p[5]+p[3]*p[4]*p[5]+p[2]*p[5]*p[8]+p[2]*p[8]*p[9])*1.0/pow(p[2]*p[4]*p[5]*p[6]+p[3]*p[4]*p[5]*p[6]+p[2]*p[5]*p[6]*p[8]+p[2]*p[6]*p[8]*p[9]+p[2]*p[8]*p[9]*p[10],2.0);
  dfxdp[35] = dvdp[35];
  dfxdp[41] = dvdp[41]+(dvdx[6]*p[2])/(p[2]+p[3]);
  dfxdp[42] = (dvdx[7]*p[2])/(p[2]+p[3])+dvdx[12]*p[2]*p[4]*p[9]*(p[2]+p[3])*1.0/pow(p[2]*p[4]+p[3]*p[4]+p[2]*p[8],2.0);
  dfxdp[43] = dvdx[13]*p[2]*p[4]*p[9]*(p[2]+p[3])*1.0/pow(p[2]*p[4]+p[3]*p[4]+p[2]*p[8],2.0)+dvdx[18]*p[2]*p[4]*p[5]*p[9]*p[10]*(p[2]+p[3])*1.0/pow(p[2]*p[4]*p[5]+p[3]*p[4]*p[5]+p[2]*p[5]*p[8]+p[2]*p[8]*p[9],2.0);
  dfxdp[44] = dvdx[19]*p[2]*p[4]*p[5]*p[9]*p[10]*(p[2]+p[3])*1.0/pow(p[2]*p[4]*p[5]+p[3]*p[4]*p[5]+p[2]*p[5]*p[8]+p[2]*p[8]*p[9],2.0)+dvdx[24]*p[2]*p[4]*p[5]*p[6]*p[9]*p[10]*p[11]*(p[2]+p[3])*1.0/pow(p[2]*p[4]*p[5]*p[6]+p[3]*p[4]*p[5]*p[6]+p[2]*p[5]*p[6]*p[8]+p[2]*p[6]*p[8]*p[9]+p[2]*p[8]*p[9]*p[10],2.0);
  dfxdp[47] = dvdp[47]+(dvdx[12]*p[2]*p[8])/(p[2]*p[4]+p[3]*p[4]+p[2]*p[8]);
  dfxdp[48] = (dvdx[13]*p[2]*p[8])/(p[2]*p[4]+p[3]*p[4]+p[2]*p[8])+dvdx[18]*p[2]*p[5]*p[8]*p[10]*(p[2]*p[4]+p[3]*p[4]+p[2]*p[8])*1.0/pow(p[2]*p[4]*p[5]+p[3]*p[4]*p[5]+p[2]*p[5]*p[8]+p[2]*p[8]*p[9],2.0);
  dfxdp[49] = dvdx[19]*p[2]*p[5]*p[8]*p[10]*(p[2]*p[4]+p[3]*p[4]+p[2]*p[8])*1.0/pow(p[2]*p[4]*p[5]+p[3]*p[4]*p[5]+p[2]*p[5]*p[8]+p[2]*p[8]*p[9],2.0)+dvdx[24]*p[2]*p[5]*p[6]*p[8]*p[10]*p[11]*(p[2]*p[4]+p[3]*p[4]+p[2]*p[8])*1.0/pow(p[2]*p[4]*p[5]*p[6]+p[3]*p[4]*p[5]*p[6]+p[2]*p[5]*p[6]*p[8]+p[2]*p[6]*p[8]*p[9]+p[2]*p[8]*p[9]*p[10],2.0);
  dfxdp[53] = dvdp[53]+(dvdx[18]*p[2]*p[8]*p[9])/(p[2]*p[4]*p[5]+p[3]*p[4]*p[5]+p[2]*p[5]*p[8]+p[2]*p[8]*p[9]);
  dfxdp[54] = (dvdx[19]*p[2]*p[8]*p[9])/(p[2]*p[4]*p[5]+p[3]*p[4]*p[5]+p[2]*p[5]*p[8]+p[2]*p[8]*p[9])+dvdx[24]*p[2]*p[6]*p[8]*p[9]*p[11]*(p[2]*p[4]*p[5]+p[3]*p[4]*p[5]+p[2]*p[5]*p[8]+p[2]*p[8]*p[9])*1.0/pow(p[2]*p[4]*p[5]*p[6]+p[3]*p[4]*p[5]*p[6]+p[2]*p[5]*p[6]*p[8]+p[2]*p[6]*p[8]*p[9]+p[2]*p[8]*p[9]*p[10],2.0);
  dfxdp[59] = dvdp[59]+(dvdx[24]*p[2]*p[8]*p[9]*p[10])/(p[2]*p[4]*p[5]*p[6]+p[3]*p[4]*p[5]*p[6]+p[2]*p[5]*p[6]*p[8]+p[2]*p[6]*p[8]*p[9]+p[2]*p[8]*p[9]*p[10]);
  dfxdp[60] = dvdp[60];  
  for (is=0; is<65; is++) {
    if(mxIsNaN(dfxdp[is])) dfxdp[is] = 0.0;
  }

  return;
}

void fy_model_NGF_Erk__M2(double t, int nt, int it, double *y, double *p, double *u, double *x){
  y[it+nt*0] = x[it+nt*4];    
    return;
}


void fsy_model_NGF_Erk__M2(double t, int nt, int it, double *sy, double *p, double *u, double *x, double *su, double *sx){
  sy[it+nt*0] = sx[it+nt*4];
  sy[it+nt*1] = sx[it+nt*9];
  sy[it+nt*2] = sx[it+nt*14];
  sy[it+nt*3] = sx[it+nt*19];
  sy[it+nt*4] = sx[it+nt*24];
  sy[it+nt*5] = sx[it+nt*29];
  sy[it+nt*6] = sx[it+nt*34];
  sy[it+nt*7] = sx[it+nt*39];
  sy[it+nt*8] = sx[it+nt*44];
  sy[it+nt*9] = sx[it+nt*49];
  sy[it+nt*10] = sx[it+nt*54];
  sy[it+nt*11] = sx[it+nt*59];
  sy[it+nt*12] = sx[it+nt*64];    
    return;
}
