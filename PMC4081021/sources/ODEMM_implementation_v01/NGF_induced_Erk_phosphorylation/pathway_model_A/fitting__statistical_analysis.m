clear all;
close all;
clc;

%% ODE
% R1: A -> B, w = k1*u*[A]
% R2: B -> A, w = k2*[B]
% with [A](0) = 1 and [B](0) = 0.
%
% ODE model:
% d[B]/dt = (k10+k1*u)*(A_tot-[B]) - k2*[B],       [B](0) = 0
%         = (k10+k1*u)*A_tot - (k10+k1*u+k2)*[B],  [B](0) = 0
% Measurement:
% y = [B]
%
% Parameter:
% xi = (log10(k10),log10(k2),log10(k1_s1),log10(k1_s2),w_1)

options_MS.fmincon = optimset('GradObj','off','display','iter');
options_MS.n_starts = 20;

options_PL.fmincon = optimset('GradObj','off','display','iter','MaxIter',100);
options_PL.parameter_index = 1;
options_PL.P_next_step.min = 1e-3;

%% Measurement data
% Load data and asign to struct
ExpC = load_NGF_kinetic;
D(1).name = 'NGF kinetic';
D(1).type = 'kinetic';
D(1).measurand = 'relative pErk concentration';
D(1).t = [0,5,15,30,60];
D(1).u = 1;
D(1).y = nan(length(D(1).t),6000);
D(1).Ey = nan(length(D(1).t),10);
s = [0.7978,0.9586,1.1317,1.1119]; % scaling computed in data_scaling.m
for k = 1:length(D(1).t)
    n0 = 0;
    for r = 1:length(ExpC(k).experiment)
        nx = size(ExpC(k).experiment(r).data,1);
        D(1).y(k,n0+1:n0+nx) = s(r)*ExpC(k).experiment(r).data(1:nx,1)';
        D(1).Ey(k,r) = s(r)*mean(ExpC(k).experiment(r).data(1:nx,1)');
        n0 = n0 + nx;
    end
end
D(1).y = D(1).y(:,1:find(sum(isnan(D(1).y))==length(D(1).t),1,'first')-1);
D(1).Ey = D(1).Ey(:,1:find(sum(isnan(D(1).Ey))==length(D(1).t),1,'first')-1);

% Load data and asign to struct
ExpC = load_NGF_dose_response;
D(2).name = 'NGF dose response';
D(2).type = 'dose response';
D(2).measurand = 'relative pErk conc.';
D(2).t = [30];
D(2).u = [0,0.001,0.01,0.1,1,10];
D(2).y = nan(length(D(2).u),10000);
D(2).Ey = nan(length(D(2).u),10);
s = [0.6795,1.1002,0.8158,1.1120,1.2926]; % scaling computed in data_scaling.m
for d = 1:length(D(2).u)
    n0 = 0;
    for r = 1:length(ExpC(d).experiment)
        nx = size(ExpC(d).experiment(r).data,1);
        D(2).y(d,n0+1:n0+nx) = s(r)*ExpC(d).experiment(r).data(1:nx,1)';
        D(2).Ey(d,r) = s(r)*mean(ExpC(d).experiment(r).data(1:nx,1)');
        n0 = n0 + nx;
    end
end
D(2).y = D(2).y(:,1:find(sum(isnan(D(2).y))==length(D(2).u),1,'first')-1);
D(2).Ey = D(2).Ey(:,1:find(sum(isnan(D(2).Ey))==length(D(2).u),1,'first')-1);

%% Measurement data used for statistical analysis
% unstimulated
e = 2;
k = 1;
ind = find(~isnan(D(e).y(k,:)));
y0 = D(e).y(k,ind);

% stimulated
e = 2;
k = 6;
ind = find(~isnan(D(e).y(k,:)));
y = D(e).y(k,ind);

%% Mixture modelling - log-normal
% log-likelihood
logLikelihood_MM_logn = @(xi) sum(log(     xi(1) *pdf('logn',y,xi(2),10^xi(4))...
                                      + (1-xi(1))*pdf('logn',y,xi(3),10^xi(5))));

% Parameter struct
parameters.min = [0;-2*ones(4,1)];
parameters.max = [1; 2*ones(4,1)];
parameters.number = length(parameters.max);
parameters.name = {'w_1','\mu_{1}','\mu_{2}',...
                         'log_{10}(\sigma_{1})','log_{10}(\sigma_{2})'};

% Multi-start optimization
[parameters] = optimizeMultiStart(parameters,@(xi,op) -logLikelihood_MM_logn(xi),options_MS);
saveas(gcf,'./project/results/mixture_model_2logn__multi_start');

% Profile likelihood calculation
[parameters] = computeProfiles(parameters,@(xi,op) -logLikelihood_MM_logn(xi),options_PL);
parameters = getConfidenceIntervals(parameters,0.99);
saveas(gcf,'./project/results/mixture_model_2logn__profile');

% Save results
save('./project/results/mixture_model_2logn__all','parameters');

clear parameters;

%% Mixture modelling - normal
% log-likelihood
logLikelihood_MM_norm = @(xi) sum(log(     xi(1) *pdf('norm',y,10^xi(2),10^xi(4))...
                                      + (1-xi(1))*pdf('norm',y,10^xi(3),10^xi(5))));

% Parameter struct
parameters.min = [0;-2*ones(4,1)];
parameters.max = [1; 2*ones(4,1)];
parameters.number = length(parameters.max);
parameters.name = {'w_1','\mu_{1}','\mu_{2}',...
                         'log_{10}(\sigma_{1})','log_{10}(\sigma_{2})'};

% Multi-start optimization
[parameters] = optimizeMultiStart(parameters,@(xi,op) -logLikelihood_MM_norm(xi),options_MS);
saveas(gcf,'./project/results/mixture_model_2norm__multi_start');

% Profile likelihood calculation
[parameters] = computeProfiles(parameters,@(xi,op) -logLikelihood_MM_norm(xi),options_PL);
parameters = getConfidenceIntervals(parameters,0.99);
saveas(gcf,'./project/results/mixture_model_2norm__profile');

% Save results
save('./project/results/mixture_model_2norm__all','parameters');

%% KDE subtraction
y_grid = linspace(1e-5,1e2,1e4);

% log-normal
options_kde.kernel = 'log-normal';
p0 = kde_simple(y0,y_grid,[],options_kde);
p  = kde_simple(y ,y_grid,[],options_kde);
dp = abs(p-p0);
w_kde_logn = trapz(y_grid,dp)/2;

% normal
options_kde.kernel = 'normal';
p0 = kde_simple(y0,y_grid,[],options_kde);
p  = kde_simple(y ,y_grid,[],options_kde);
dp = abs(p-p0);
w_kde_norm = trapz(y_grid,dp)/2;

% Save results
save('./project/results/kde_subtraction','w_kde_logn','w_kde_norm');
