clear all;
close all;
clc;

%% ODE
% R1: A -> B, w = k10+k1*u*[A]
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
options_MS.n_starts = 200;

options_PL.fmincon = optimset('GradObj','off','display','iter','MaxIter',100);
options_PL.parameter_index = 1;
options_PL.P_next_step.min = 1e-3;

%% Measurement data
load('./project/data/data');

% Visualization (linear)
options_plot.boundaries(1).y_min = 0; options_plot.boundaries(1).y_max = 0.8;
options_plot.boundaries(2).y_min = 0; options_plot.boundaries(2).y_max = 0.8;
options_plot.x_scale = 'lin';
fh = plotODEMix(D,[],[],options_plot);
% Save plot
saveas(fh,['./project/results/data__kinetic__distribution_lin']);

% Visualization (logarithmic)
options_plot.boundaries(1).y_min = 0.1; options_plot.boundaries(1).y_max = 1;
options_plot.boundaries(2).y_min = 0.1; options_plot.boundaries(2).y_max = 1;
options_plot.x_scale = 'log';
fh = plotODEMix(D,[],[],options_plot);
% Save plot
saveas(fh,['./project/results/data__kinetic__distribution_log']);

%% Measurement data used for statistical analysis
% unstimulated
y0 = D.y(1,:);

% stimulated
y = D.y(end,:);

%% Mixture modelling - log-normal
% log-likelihood
logLikelihood_MM_logn = @(xi) sum(log(     xi(1) *pdf('logn',y,xi(2),10^xi(4))...
                                      + (1-xi(1))*pdf('logn',y,xi(3),10^xi(5))));

% Parameter struct
parameters.min = [0;-2.5*ones(4,1)];
parameters.max = [1; 2.5*ones(4,1)];
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
parameters.min = [0;-2.5*ones(4,1)];
parameters.max = [1; 2.5*ones(4,1)];
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
ymin = min(min(y0),min(y))/2;
ymax = max(max(y0),max(y))*2;
y_grid = linspace(ymin,ymax,1e4);

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
