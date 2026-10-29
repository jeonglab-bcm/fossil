function [status,t,x,y,sx,sy] = simulate_model_NGF_Erk__M2(tout,theta)

persistent old_theta old_tout
persistent ncount
persistent old_status old_t old_x old_y old_sx old_sy

try
        if(and(all(tout==old_tout),all(theta==old_theta)))
                        status = old_status;
        t = old_t;
        x = old_x;
        y = old_y;
        sx = old_sx;
        sy = old_sy;
        ncount = ncount + 1;
    if ncount > 5
                status = -1;
    end
        return
    end
    
catch
end

ncount = 0;
options_cvode.cvodes_atol = 1e-08;
options_cvode.cvodes_rtol = 1e-08;
options_cvode.cvodes_maxsteps = 10000;

options_cvode.xs = ones(5,1);
options_cvode.ys = ones(1,1);
options_cvode.ps = ones(1,13);
options_cvode.tstart = 0;

options_cvode.qPositiveX = zeros(size(options_cvode.xs));
options_cvode.uNum = zeros(1,0);
options_cvode.vNum = zeros(1,5);
options_cvode.dvdxNum = zeros(5,5);
options_cvode.dvduNum = zeros(5,0);
options_cvode.dvdpNum = zeros(5,13);
options_cvode.suNum = zeros(0,13);
options_cvode.svNum = zeros(1,5);

[status,t,x,y,sx,sy] = model_NGF_Erk__M2(tout,theta,options_cvode);
old_status = status;
old_t = t;
old_x = x;
old_y = y;
old_sx = sx;
old_sy = sy;
old_theta = theta;
old_tout = tout;
end
