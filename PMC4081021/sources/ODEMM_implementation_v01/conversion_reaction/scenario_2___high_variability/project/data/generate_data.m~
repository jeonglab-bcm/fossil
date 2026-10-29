clear all;
close all;
clc;


%% Model
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
%xi_true = [log10(0.5),log10(1.8),log10(0.8),log10(0.08),0.4];
xi_true = [log10(0.5),log10(1.5),log10(0.75),log10(0.1),0.5];
% xi_true = [log10(0.6),log10(1.8),log10(1),log10(0.1),0.4];

%% Definition of model
M.N_subpop = 2;
M.model = @(T,theta,u) simConversionReaction(T,theta,u);

% Subpopulation 1
M.subind{1} = [1,2,3];
M.theta{1} = @(xi) 10.^xi([1,2,3]);
M.w{1} = @(xi) xi(5);

% Subpopulation 2
M.subind{2} = [1,2,4];
M.theta{2} = @(xi) 10.^xi([1,2,4]);
M.w{2} = @(xi) 1 - xi(5);

%% Generation of measurement data
% Number of measured cells
N = 1000;

% Variability of parameters
sigma_par = 0.1;

% Simulation mean (kinetic)
% Stimulus
u  = 1;
% Time points
T_kinetic = [0,0.1,0.2,0.3,0.5,1];
% Sampling
Y_r_kinetic  = zeros(length(T_kinetic),N);
Y_nr_kinetic = zeros(length(T_kinetic),N);
Y_kinetic= zeros(length(T_kinetic),N);
for k = 1:length(T_kinetic)
    for j = 1:N
        % Parameter sampling
        if rand < M.w{1}(xi_true)
            theta_k = 10.^(xi_true(M.subind{1}) + sigma_par*randn(1,3));
        else
            theta_k = 10.^(xi_true(M.subind{2}) + sigma_par*randn(1,3));
        end
        % Simulation
        X  = M.model(T_kinetic,theta_k,u);
        Y_kinetic(k,j) = X(k);
    end
end
% Assign to struct
D(1).type = 'kinetic';
D(1).t = T_kinetic;
D(1).u = u;
D(1).y = Y_kinetic;
D(1).name = 'time response';
D(1).measurand = '[B]';

%% Visualization of data
options_plot.boundaries(1).y_min = 0.1;
options_plot.boundaries(1).y_max = 1;
options_plot.x_scale = 'log';
options_plot.data.bins  = 30;
fhd = plotODEMix(D,[],[],options_plot);

%% Save artifical data
save('data','D')
