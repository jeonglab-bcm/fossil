clear all;
close all;
clc;

%% Definition of model
model_name = '1logn_mean';

M.N_subpop = 1;
M.model = @(T,theta,u) simulate_model_NGF_Erk__M3_modified(T,theta,u);

% Subpopulation 1
M.subind{1} = [1:14];
M.theta{1} = @(xi) 10.^xi([1:14]);
M.dthetadxi{1} = @(xi) [diag(10.^xi(1:14)),zeros(14,11)]*log(10);
   % Experiment 1
M.mu{1,1} = @(t,x,xi,d) log(x(:,5)) - 10.^(2*xi(15:19))/2;
M.dmudxi{1,1} = @(t,x,dxdxi,xi,d) bsxfun(@plus,bsxfun(@rdivide,permute(dxdxi(5,:,:),[3,2,1]),x(:,5)),...
                                          [zeros(5,14),-diag(10.^(2*xi(15:19))*log(10)),zeros(5,6)]);

M.sigma{1,1} = @(t,x,xi,d) 10.^xi(15:19);
M.dsigmadxi{1,1} = @(t,x,dxdxi,xi,d) [zeros(5,14),diag(10.^xi(15:19)*log(10)),zeros(5,6)];
   % Experiment 2
M.mu{1,2} = @(t,x,xi,d) log(x(:,5)) - (d==0)    *10.^(2*xi(20))/2 ...
                                    - (d==0.001)*10.^(2*xi(21))/2 ...
                                    - (d==0.01) *10.^(2*xi(22))/2 ...
                                    - (d==0.1)  *10.^(2*xi(23))/2 ...
                                    - (d==1)    *10.^(2*xi(24))/2 ...
                                    - (d==10)   *10.^(2*xi(25))/2;
M.dmudxi{1,2} = @(t,x,dxdxi,xi,d) bsxfun(@plus,bsxfun(@rdivide,permute(dxdxi(5,:,:),[3,2,1]),x(:,5)),...
                        (d==0)    *[zeros(1,19),-10.^(2*xi(20))*log(10),zeros(1, 5)] ...
                      + (d==0.001)*[zeros(1,20),-10.^(2*xi(21))*log(10),zeros(1, 4)] ...
                      + (d==0.01) *[zeros(1,21),-10.^(2*xi(22))*log(10),zeros(1, 3)] ...
                      + (d==0.1)  *[zeros(1,22),-10.^(2*xi(23))*log(10),zeros(1, 2)] ...
                      + (d==1)    *[zeros(1,23),-10.^(2*xi(24))*log(10),zeros(1, 1)] ...
                      + (d==10)   *[zeros(1,24),-10.^(2*xi(25))*log(10)]);
M.sigma{1,2} = @(t,x,xi,d)   (d ==  0    )*10.^xi(20) ...
                           + (d ==  0.001)*10.^xi(21) ...
                           + (d ==  0.01 )*10.^xi(22) ...
                           + (d ==  0.1  )*10.^xi(23) ...
                           + (d ==  1    )*10.^xi(24) ...
                           + (d == 10    )*10.^xi(25);
M.dsigmadxi{1,2} = @(t,x,dxdxi,xi,d)   (d ==  0    )*[zeros(1,19),10^xi(20)*log(10),zeros(1, 5)] ...
                                     + (d ==  0.001)*[zeros(1,20),10^xi(21)*log(10),zeros(1, 4)] ...
                                     + (d ==  0.01 )*[zeros(1,21),10^xi(22)*log(10),zeros(1, 3)] ...
                                     + (d ==  0.1  )*[zeros(1,22),10^xi(23)*log(10),zeros(1, 2)] ...
                                     + (d ==  1    )*[zeros(1,23),10^xi(24)*log(10),zeros(1, 1)] ...
                                     + (d == 10    )*[zeros(1,24),10^xi(25)*log(10),zeros(1, 0)];
   % Weights
M.w{1} = @(xi) 1;
M.dwdxi{1} = @(x,xi) zeros(1,25);
M.distribution{1} = 'logn';

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

%% Estimation
parameters.min = [-3*ones(14,1);-1*ones(11,1)];
parameters.max = [ 3*ones(14,1); 1*ones(11,1)];
parameters.number = length(parameters.max);
parameters.name = {'log_{10}(k_1)','log_{10}(k_2)','log_{10}(k_4)',...
                   'log_{10}(k_5)','log_{10}(k_7)','log_{10}(k_9)',...
                   'log_{10}(k_{11})',...
                   'log_{10}(k_3 [TrkA]_{0})',...
                   'log_{10}(k_6 [Ras]_0)',...
                   'log_{10}(k_8 [Raf]_0)',...
                   'log_{10}(k_{10} [Mek]_0)',...
                   'log_{10}(s [Erk]_{0})',...
                   'log_{10}(s K)','log_{10}(n)',...
                   'log_{10}(\sigma(t=0))','log_{10}(\sigma(t=5))','log_{10}(\sigma(t=15))','log_{10}(\sigma(t=30))','log_{10}(\sigma(t=60))',...
                   'log_{10}(\sigma(u=0))','log_{10}(\sigma(u=0.001))','log_{10}(\sigma(u=0.01))','log_{10}(\sigma(u=0.1))','log_{10}(\sigma(u=1))','log_{10}(\sigma(u=10))'};

% Multi-start optimization
options_MS.fmincon = optimset('GradObj','on','display','iter');
options_MS.n_starts = 200;
[parameters] = optimizeMultiStart(parameters,@(xi,op) logLikelihood(xi,M,D,op),options_MS);

%% Filter of parameters which cause oszillations

% Simulation
e = 1;
t = linspace(D(e).t(1),D(e).t(end),10000);

% Maximum number of allowed peaks
n_peaks_max = 5;

% Index of accepted parameters
I_acc = [];

% Loop: Parameter estimates
for i = 1:size(parameters.MS.MAP_list.par,2)
    % No oszillations
    n_peaks = 0;
    
    % Parameter assignment
    xi = parameters.MS.MAP_list.par(:,i);
    
    % Loop: Subpopulations
    for s = 1:M.N_subpop
        % Simulation
        X = M.model(t,M.theta{s}(xi),D(e).u);
        y_sim = X(:,5);
        % Peak detection
        [maxtab,mintab] = peakdet(y_sim,0.01,t');
        % Plot
        figure(100); hold off;
        plot(t,y_sim,'k-'); hold on;
        if ~isempty(maxtab)
            plot(maxtab(:,1), maxtab(:,2), 'b*');
            n_peaks = max([n_peaks,size(maxtab,1)]);
        end
        if ~isempty(mintab)
            plot(mintab(:,1), mintab(:,2), 'r*');
        end        
    end
    % Check peak constraint
    if n_peaks <= n_peaks_max
        I_acc(end+1) = i;
    end
end

% Parameter reassignment
parameters_full = parameters;

parameters.MS.MAP_list.par = parameters.MS.MAP_list.par(:,I_acc);
parameters.MS.MAP_list.logPost = parameters.MS.MAP_list.logPost(I_acc);
parameters.MS.MAP_list.gradient = parameters.MS.MAP_list.gradient(:,I_acc);
parameters.MS.MAP_list.hessian = parameters.MS.MAP_list.hessian(:,:,I_acc);
parameters.MS.MAP_list.nonzero = parameters.MS.MAP_list.nonzero;

parameters.MS.MAP.par = parameters.MS.MAP_list.par(:,1);
parameters.MS.MAP.logPost = parameters.MS.MAP_list.logPost(1);
parameters.MS.MAP.gradient = parameters.MS.MAP_list.gradient(:,1);
parameters.MS.MAP.hessian = parameters.MS.MAP_list.hessian(:,:,1);
parameters.MS.MAP.AIC = -2*parameters.MS.MAP.logPost + 2*parameters.number;
parameters.MS.MAP.BIC = -2*parameters.MS.MAP.logPost + log(sum(~isnan(D(1).y(:)))+sum(~isnan(D(2).y(:))))*parameters.number;

xi = parameters.MS.MAP.par;

% Save plot
plotMS(parameters)
saveas(gcf,['./project/results/' model_name '__multi_start']);

% Save results
save(['./project/results/' model_name]);

%% Visualization - Fit (linear)
options_plot.boundaries(1).y_min = 0; options_plot.boundaries(1).y_max = 10;
options_plot.boundaries(2).y_min = 0; options_plot.boundaries(2).y_max = 10;
options_plot.x_scale = 'lin';
options_plot.data.bins = 200;
options_plot.model.points = 200;
fh = plotODEMix(D,M,xi,options_plot);
% Save plot
saveas(fh(1),['./project/results/' model_name '__kinetic__distribution_lin']);
saveas(fh(2),['./project/results/' model_name '__dose_response__distribution_lin']);

%% Visualization - Fit (logarithmic)
options_plot.boundaries(1).y_min = 0.1; options_plot.boundaries(1).y_max = 100;
options_plot.boundaries(2).y_min = 0.1; options_plot.boundaries(2).y_max = 100;
options_plot.x_scale = 'log';
fh = plotODEMix(D,M,xi,options_plot);
% Save plot
saveas(fh(1),['./project/results/' model_name '__kinetic__distribution_log']);
saveas(fh(2),['./project/results/' model_name '__dose_response__distribution_log']);

%% Visualization -  kinetic
e = 1;
% Simulation
t = linspace(D(e).t(1),D(e).t(end),100);
for s = 1:M.N_subpop
    X = M.model(t,M.theta{s}(xi),D(e).u);
    mu{s} = X(:,5);
end
% Plot
figure('name','NGF kinetic - mean');
indt = [1,1:length(t),length(t)];
t_indt = [-3,t,t(end)+3];
lh(1) = plot(t_indt, M.w{1}(xi)*mu{1}(indt),'k-','linewidth',2); hold on;
lh(2) = plot(D(e).t,nanmean(D(e).Ey,2),'ko','linewidth',2);
for k = 1:length(D(e).t)
    plot(D(e).t(k)*[1,1],nanmean(D(e).Ey(k,:)) + nanstd(D(e).Ey(k,:))*[-1,1],'k-','linewidth',2);
end
% Legend / Label
legend(lh,{'model: mean','data: mean'},'location','Northwest');
xlabel('time {\itt} [min]');
ylabel(D(1).measurand);
xlim(t_indt([1,end]));
% Save plot
saveas(gcf,['./project/results/' model_name '__kinetic__mean']);

%% Visualization -  dose response
e = 2;
% Simulation
u = [0,10.^linspace(-3.1,1.1,21)];
u_plot = [10^-4,10.^linspace(-3.1,1.1,21)];
u_plot_data = 10.^[-4:1];
for s = 1:M.N_subpop
    for d = 1:length(u)
        X = M.model(D(e).t,M.theta{s}(xi),u(d));
        MU(d,s) = X(end,5);
    end
end
% Plot
figure('name','NGF dose response - mean');
plot(u_plot(1)*[1/1.5,1.5],M.w{1}(xi)*MU(1,1)*[1,1],'k-','linewidth',2); hold on;
plot(u_plot_data(1),nanmean(D(e).Ey(1,:),2),'ko','linewidth',2);
lh(1) = plot(u_plot(2:end),M.w{1}(xi)*MU(2:end,1),'k-','linewidth',2);
lh(2) = plot(u_plot_data(2:end),nanmean(D(e).Ey(2:end,:),2),'ko','linewidth',2);
plot(u_plot_data([1,2]).*[2.5,1/2],1.2*[1,1],'k:','markersize',8,'linewidth',1.5);
for d = 1:length(D(e).u)
    plot(u_plot_data(d)*[1,1],nanmean(D(e).Ey(d,:),2) + nanstd(D(e).Ey(d,:))*[-1,1],'k-','linewidth',2);
end
xlim([u_plot(1)/1.5,u_plot(end)]);
% Legend / Label
legend(lh,{'model: mean','data: mean'},'location','Northwest');
xlabel('NGF concentration');
ylabel(D(1).measurand);
set(gca,'xscale','log','xtick',10.^[-4:1],'xticklabel',[0,0.001,0.01,0.1,1,10]);
% Save plot
saveas(gcf,['./project/results/' model_name '__dose_response__mean']);

% %% Profile likelihood calculation
% options_PL.fmincon = optimset('GradObj','on','display','off','MaxIter',100);
% options_PL.parameter_index = 1:6;
% options_PL.P_next_step.min = 1e-2;
% [parameters] = computeProfiles(parameters,@(xi,op) logLikelihood(xi,M,D,op),options_PL);
% parameters = getConfidenceIntervals(parameters,0.99);
% % Save plot
% saveas(gcf,['./project/results/' model_name '__profile']);

%% Save results
save(['./project/results/' model_name '_all']);
