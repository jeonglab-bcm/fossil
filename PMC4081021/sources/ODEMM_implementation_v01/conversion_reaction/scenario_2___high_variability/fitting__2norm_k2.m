% clear all;
close all;
clc;

%% ODE
% R1: A -> B, w = k1b+k1a*u*[A]
% R2: B -> A, w = k2*[B]
% with [A](0) = 1 and [B](0) = 0.
%
% ODE model:
% d[B]/dt = (k1b+k1a*u)*(A_tot-[B]) - k2*[B],       [B](0) = 0
%         = (k1b+k1a*u)*A_tot - (k1b+k1a*u+k2)*[B],  [B](0) = 0
% Measurement:
% y = [B]
%
% Parameter:
% xi = (log10(k1a),log10(k2),log10(k1b_s1),log10(k1b_s2),w_1)

model_name = '2norm_k2';

%% Definition of model
M.N_subpop = 2;
M.model = @(T,theta,u) simConversionReaction(T,theta,u);

% Subpopulation 1
M.subind{1} = [1,3,2];
M.theta{1} = @(xi) 10.^xi([1,3,2]);
M.dthetadxi{1} = @(xi) [10.^xi(1),0,0,0,zeros(1,13);...
                        0,0,10.^xi(3),0,zeros(1,13);...
                        0,10.^xi(2),0,0,zeros(1,13)]*log(10);
   % Experiment 1
M.mu{1,1} = @(t,x,xi,d) x;
M.dmudxi{1,1} = @(t,x,dxdxi,xi,d) permute(dxdxi(1,:,:),[3,2,1]);
M.sigma{1,1} = @(t,x,xi,d) 10.^xi(6:11);
M.dsigmadxi{1,1} = @(t,x,dxdxi,xi,d) [zeros(6,5),diag(10.^xi(6:11)*log(10)),zeros(6,6)];
   % Weights
M.w{1} = @(xi) xi(5);
M.dwdxi{1} = @(x,xi) [zeros(1,4),1,zeros(1,12)];
M.distribution{1} = 'norm';

% Subpopulation 2
M.subind{2} = [1,4,2];
M.theta{2} = @(xi) 10.^xi([1,4,2]);
M.dthetadxi{2} = @(xi) [10.^xi(1),0,0,0,zeros(1,13);...
                        0,0,0,10.^xi(4),zeros(1,13);...
                        0,10.^xi(2),0,0,zeros(1,13)]*log(10);
   % Experiment 1
M.mu{2,1} = @(t,x,xi,d) x;
M.dmudxi{2,1} = @(t,x,dxdxi,xi,d) permute(dxdxi(1,:,:),[3,2,1]);
M.sigma{2,1} = @(t,x,xi,d) 10.^xi(12:17);
M.dsigmadxi{2,1} = @(t,x,dxdxi,xi,d) [zeros(6,11),diag(10.^xi(12:17)*log(10))];
   % Weights
M.w{2} = @(xi) 1 - xi(5);
M.dwdxi{2} = @(x,xi) -[zeros(1,4),1,zeros(1,12)];
M.distribution{2} = 'norm';

%% Measurement data
load('./project/data/data');

%% Estimation
% Parameter struct
parameters.min = [-6*ones(4,1);0;-2*ones(12,1)];
parameters.max = [ 4*ones(4,1);1; 3*ones(12,1)];
parameters.number = length(parameters.max);
parameters.name = {'log_{10}(k_{1,b})','log_{10}(k_{1,a})',...
                   'log_{10}(k_{2,s1})','log_{10}(k_{2,s2})','w',...
                   'log_{10}(\sigma_{s1}(t_1))','log_{10}(\sigma_{s1}(t_2))','log_{10}(\sigma_{s1}(t_3))','log_{10}(\sigma_{s1}(t_4))','log_{10}(\sigma_{s1}(t_5))','log_{10}(\sigma_{s1}(t_6))',...
                   'log_{10}(\sigma_{s2}(t_1))','log_{10}(\sigma_{s2}(t_2))','log_{10}(\sigma_{s2}(t_3))','log_{10}(\sigma_{s2}(t_4))','log_{10}(\sigma_{s2}(t_5))','log_{10}(\sigma_{s2}(t_6))'};

% Multi-start optimization
options_MS.fmincon = optimset('GradObj','on','display','iter');
options_MS.n_starts = 40;
[parameters] = optimizeMultiStart(parameters,@(xi,op) logLikelihood(xi,M,D,op),options_MS);

% Parameter assignment
xi = parameters.MS.MAP.par;

% Model selection criteria
parameters.MS.MAP.AIC = -2*parameters.MS.MAP.logPost + 2*parameters.number;
parameters.MS.MAP.BIC = -2*parameters.MS.MAP.logPost + log(sum(~isnan(D(1).y(:))))*parameters.number;

% Save plot
saveas(gcf,['./project/results/' model_name '__multi_start']);

% Save results
save(['./project/results/' model_name]);

%% Visualization - Fit (linear)
options_plot.boundaries(1).y_min = 0; options_plot.boundaries(1).y_max = 0.8;
options_plot.boundaries(2).y_min = 0; options_plot.boundaries(2).y_max = 0.8;
options_plot.x_scale = 'lin';
fh = plotODEMix(D,M,xi,options_plot);
% Save plot
saveas(fh,['./project/results/' model_name '__kinetic__distribution_lin']);

%% Visualization - Fit (logarithmic)
options_plot.boundaries(1).y_min = 0.1; options_plot.boundaries(1).y_max = 1;
options_plot.boundaries(2).y_min = 0.1; options_plot.boundaries(2).y_max = 1;
options_plot.x_scale = 'log';
fh = plotODEMix(D,M,xi,options_plot);
% Save plot
saveas(fh,['./project/results/' model_name '__kinetic__distribution_log']);

% %% Profile likelihood calculation
% options_PL.fmincon = optimset('GradObj','on','display','iter','MaxIter',100);
% options_PL.parameter_index = 1:5;
% options_PL.P_next_step.min = 1e-2;
% [parameters] = computeProfiles(parameters,@(xi,op) logLikelihood(xi,M,D,op),options_PL);
% parameters = getConfidenceIntervals(parameters,0.99);
% % Save plot
% saveas(gcf,['./project/results/' model_name '__profile']);

%% Save results
save(['./project/results/' model_name '_all']);
