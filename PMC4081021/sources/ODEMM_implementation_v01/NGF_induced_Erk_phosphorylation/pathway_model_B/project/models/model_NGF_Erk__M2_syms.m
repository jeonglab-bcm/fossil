function [model] = model_NGF_Erk__M2_syms()

%% CVODES OPTIONS

% absolute tolerance
model.atol = 1e-8;
% relative tolerance
model.rtol = 1e-8;
% maximal number of steps
model.maxsteps = 1e4;

%% STATES

syms TrkA_NGF RasGTP pRaf pMek pErk

x = [TrkA_NGF,RasGTP,pRaf,pMek,pErk];

%% PARAMETERS
syms k_1 k_2 k_4 k_5 k_7 k_9 k_11 k_3__TrkA_0 k_6__Ras_0 k_8__Raf_0 k_10__Mek_0 s__Erk_0 NGF_0
p = [k_1,k_2,k_4,k_5,k_7,k_9,k_11,k_3__TrkA_0,k_6__Ras_0,k_8__Raf_0,k_10__Mek_0,s__Erk_0,NGF_0];

%% INPUT 
u = sym.empty(0,0);

%% SYSTEM EQUATIONS
xdot = sym(zeros(size(x)));

xdot(1) =  k_1*NGF_0 *( k_3__TrkA_0 - TrkA_NGF) -  k_2*TrkA_NGF;
xdot(2) = (TrkA_NGF + k_4)*( k_6__Ras_0 - RasGTP) -  k_5*RasGTP;
xdot(3) =  RasGTP*( k_8__Raf_0  - pRaf) -  k_7*pRaf;
xdot(4) =  pRaf  *(k_10__Mek_0  - pMek) -  k_9*pMek;
xdot(5) =  pMek  *(   s__Erk_0  - pErk) - k_11*pErk;
       
%% INITIAL CONDITIONS
x_10 = 0;
x_20 = k_4*(k_6__Ras_0)/(k_4+k_5);
x_30 = (x_20*k_8__Raf_0)/(x_20+k_7); 
x_40 = (x_30*k_10__Mek_0)/(x_30+k_9);
x_50 = (x_40*s__Erk_0)/(x_40+k_11);

x0 = [x_10;x_20;x_30;x_40;x_50];

%% OBSERVABLES
y = pErk;

%% SYSTEM STRUCT
model.sym.x = x;
model.sym.u = u;
model.sym.xdot = xdot;
model.sym.p = p;
model.sym.x0 = x0;
model.sym.y = y;

end