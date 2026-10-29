clear all;
close all;
clc;

%%
fs = [6,7];
%fs = [12,14];
TextSizes.DefaultAxesFontSize = fs(2);
TextSizes.DefaultTextFontSize = fs(2);
set(0,TextSizes);
ms = 3;

%% Load necessary information
load('./project/results/1norm_all');               parameters_1norm_all = parameters;
load('./project/results/1logn_mean_all');          parameters_1logn_mean_all = parameters;         M_1logn_mean_all = M;
load('./project/results/1logn_median_all');        parameters_1logn_median_all = parameters;       M_1logn_median_all = M;
load('./project/results/2norm_Erk0_all');          parameters_2norm_Erk0_all = parameters;
load('./project/results/2logn_mean_Erk0_all');     parameters_2logn_mean_Erk0_all = parameters;
load('./project/results/2logn_median_Erk0_all');   parameters_2logn_median_Erk0_all = parameters;
load('./project/results/2norm_TrkA0_all');         parameters_2norm_TrkA0_all = parameters;
load('./project/results/2logn_mean_TrkA0_all');    parameters_2logn_mean_TrkA0_all = parameters;   M_2logn_mean_TrkA0_all = M;
load('./project/results/2logn_median_TrkA0_all');  parameters_2logn_median_TrkA0_all = parameters; M_2logn_median_TrkA0_all = M;

% %% Plot model selection
% delta = 0.3;
% col = [0.9,0.9,0.9;
%        0.7,0.7,0.7;
%        0.5,0.5,0.5];
% col_best = [1,0,0];
% 
% % log-likelihood
% figure;
% 
% bar(0+0*delta,parameters_1norm_all.MS.MAP.BIC,'facecolor',col(1,:)); hold on;
% bar(1+0*delta,parameters_1logn_mean_all.MS.MAP.BIC,'facecolor',col(1,:));
% bar(2+0*delta,parameters_1logn_median_all.MS.MAP.BIC,'facecolor',col(1,:));
% bar(3+1*delta,parameters_2norm_Erk0_all.MS.MAP.BIC,'facecolor',col(2,:));
% bar(4+1*delta,parameters_2logn_mean_Erk0_all.MS.MAP.BIC,'facecolor',col(2,:));
% bar(5+1*delta,parameters_2logn_median_Erk0_all.MS.MAP.BIC,'facecolor',col(2,:));
% bar(6+2*delta,parameters_2norm_TrkA0_all.MS.MAP.BIC,'facecolor',col(3,:));
% bar(7+2*delta,parameters_2logn_mean_TrkA0_all.MS.MAP.BIC,'facecolor',col(3,:));
% bar(8+2*delta,parameters_2logn_median_TrkA0_all.MS.MAP.BIC,'facecolor',col(3,:));
% 
% plot([0-0.7,8+2*delta+0.7],parameters_2logn_median_TrkA0_all.MS.MAP.BIC*[1,1],'-','color',[0,0,1]);
% plot([0-0.7,8+2*delta+0.7],parameters_2logn_median_TrkA0_all.MS.MAP.BIC*[1,1]+4,'-','color',[0.2,0.2,1]);
% plot([0-0.7,8+2*delta+0.7],parameters_2logn_median_TrkA0_all.MS.MAP.BIC*[1,1]+10,'-','color',[0.4,0.4,1]);
% 
% set(gca,'ylim',[7e4,11e4],'xlim',[0-0.7,8+2*delta+0.7]);

%% Plot parameter uncertainty
% Setting
alpha = [0.99,0.95,0.9,0.8];

delta = 0.5;
epsilon1 = 1e-2;
epsilon2 = 2e-3;

% H1
col_H3_2 = [1,0.90,0.90;
            1,0.75,0.75;
            1,0.60,0.60;
            1,0.45,0.45;
            1,0.10,0.10];
col_H3_3 = [0.90,0.90,1;
            0.75,0.75,1;
            0.60,0.60,1;
            0.45,0.45,1;
            0.10,0.10,1];

order1 = [1,2,3,4,6,5];
xl1 = {'k_1','k_2','k_4','k_5','s [Erk]_{ 0}','k_3 [TrkA]_{ 0}'};

figure;
lh = [];
xi_min = -2.5;
xi_max =  1.5;

% Loops
for i = 1:length(order1)
    for j = 1:length(alpha)
        % Confidence intervals
        pars_H1_2 = getConfidenceIntervals(parameters_1logn_mean_all,alpha(j));
        pars_H1_3 = getConfidenceIntervals(parameters_1logn_median_all,alpha(j));
        pars_H1_2.CI.PL = max(min(pars_H1_2.CI.PL,xi_max),xi_min);
        pars_H1_3.CI.PL = max(min(pars_H1_3.CI.PL,xi_max),xi_min);
        % Plot - Uncertainty
        fill(10.^pars_H1_2.CI.PL(order1(i),[1,2,2,1]),(i*(-2-delta)+0)+(0.1+j*0.05)*[+1,+1,-1,-1],'b','facecolor',col_H3_2(j,:)); hold on;
        fill(10.^pars_H1_3.CI.PL(order1(i),[1,2,2,1]),(i*(-2-delta)-1)+(0.1+j*0.05)*[+1,+1,-1,-1],'b','facecolor',col_H3_3(j,:)); hold on;
    end
    % Plot - Optimum
    lh(1) = fill(10.^(pars_H1_2.MS.MAP.par(order1(i))+epsilon1*[-1,+1,+1,-1]),(i*(-2-delta)+0)+0.4*[+1,+1,-1,-1],'b','facecolor',col_H3_2(end,:)); hold on;
    lh(2) = fill(10.^(pars_H1_3.MS.MAP.par(order1(i))+epsilon1*[-1,+1,+1,-1]),(i*(-2-delta)-1)+0.4*[+1,+1,-1,-1],'b','facecolor',col_H3_3(end,:)); hold on;
    % Seperation line
    if i < length(order1)
        plot(10.^[-6,6],((i*(-2-delta)-1)+((i+1)*(-2-delta)+0))/2*[1,1],'-','color',0.8*[1,1,1]);
    end
    % Label
    text(10^-2.55,i*(-2-delta)-0.5,xl1{i},'HorizontalAlignment','Right','FontSize',fs(2))
end
% Formatting
legend(lh,{'M_{H1,2}','M_{H1,3}'},'position',[0.75,0.58,0.1,0.05]);
set(gca,'xscale','log',...
        'xlim',10.^[-2.5,1.5],...
        'xtick',[0.003:0.001:0.009,0.01:0.01:0.09,0.1:0.1:0.9,1:1:9,10:10:30],...
        'xticklabel',{'','','','','','','','0.01','','','','','','','','','0.1','','','','','','','','','1','','','','','','','','','10','',''},...
        'ylim',[length(order1)*(-2-delta)-1-0.5-delta/2,1*(-2-delta)+0.5+delta/2],...
        'ytick',10.^[-2:1],...
        'ytick',[],...
        'yticklabel',{});
set(gca,'Position',[0.2,0.15,0.75,0.83])
xlabel('parameter values','fontsize',fs(2));

% Print
set(gcf,'Position',[200 200 240 155]);
set(gcf,'PaperPositionMode','auto');
print('-depsc2','figures/H1_parameter_uncertainty');

% H3
col_H3_2 = [1,0.90,0.90;
            1,0.75,0.75;
            1,0.60,0.60;
            1,0.45,0.45;
            1,0.10,0.10];
col_H3_3 = [0.90,0.90,1;
            0.75,0.75,1;
            0.60,0.60,1;
            0.45,0.45,1;
            0.10,0.10,1];

order1 = [1,2,3,4,7,5,6];
order2 = [8];
xl1 = {'k_1','k_2','k_4','k_5','s [Erk]_0','k_3 [TrkA]_{ 0,1}','k_3 [TrkA]_{ 0,2}'};
xl2 = {'w_1'};

figure;
lh = [];

subplot(9,1,1:7);
% Loops
for i = 1:length(order1)
    for j = 1:length(alpha)
        % Confidence intervals
        pars_H3_2 = getConfidenceIntervals(parameters_2logn_mean_TrkA0_all,alpha(j));
        pars_H3_3 = getConfidenceIntervals(parameters_2logn_median_TrkA0_all,alpha(j));
        % Plot - Uncertainty
        fill(10.^pars_H3_2.CI.PL(order1(i),[1,2,2,1]),(i*(-2-delta)+0)+(0.1+j*0.05)*[+1,+1,-1,-1],'b','facecolor',col_H3_2(j,:)); hold on;
        fill(10.^pars_H3_3.CI.PL(order1(i),[1,2,2,1]),(i*(-2-delta)-1)+(0.1+j*0.05)*[+1,+1,-1,-1],'b','facecolor',col_H3_3(j,:)); hold on;
    end
    % Plot - Optimum
    lh(1) = fill(10.^(pars_H3_2.MS.MAP.par(order1(i))+epsilon1*[-1,+1,+1,-1]),(i*(-2-delta)+0)+0.4*[+1,+1,-1,-1],'b','facecolor',col_H3_2(end,:)); hold on;
    lh(2) = fill(10.^(pars_H3_3.MS.MAP.par(order1(i))+epsilon1*[-1,+1,+1,-1]),(i*(-2-delta)-1)+0.4*[+1,+1,-1,-1],'b','facecolor',col_H3_3(end,:)); hold on;
    % Seperation line
    if i < length(order1)
        plot(10.^[-6,6],((i*(-2-delta)-1)+((i+1)*(-2-delta)+0))/2*[1,1],'-','color',0.8*[1,1,1]);
    end
    % Label
    text(10^-2.55,i*(-2-delta)-0.5,xl1{i},'HorizontalAlignment','Right','FontSize',fs(2))
end
% Formatting
legend(lh,{'M_{H3,2}','M_{H3,3}'});
set(gca,'xscale','log',...
        'xlim',10.^[-2.5,1.5],...
        'xtick',[0.003:0.001:0.009,0.01:0.01:0.09,0.1:0.1:0.9,1:1:9,10:10:30],...
        'xticklabel',{'','','','','','','','0.01','','','','','','','','','0.1','','','','','','','','','1','','','','','','','','','10','',''},...
        'ylim',[length(order1)*(-2-delta)-1-0.5-delta/2,1*(-2-delta)+0.5+delta/2],...
        'ytick',10.^[-2:1],...
        'ytick',[],...
        'yticklabel',{});
set(gca,'Position',[0.2,0.29,0.75,0.7])

subplot(9,1,9);
% Loops
for i = 1:length(order2)
    for j = 1:length(alpha)
        % Confidence intervals
        pars_H3_2 = getConfidenceIntervals(parameters_2logn_mean_TrkA0_all,alpha(j));
        pars_H3_3 = getConfidenceIntervals(parameters_2logn_median_TrkA0_all,alpha(j));
        % Plot - Uncertainty
        fill(pars_H3_2.CI.PL(order2(i),[1,2,2,1]),(i*(-2-delta)+0)+(0.1+j*0.05)*[+1,+1,-1,-1],'b','facecolor',col_H3_2(j,:)); hold on;
        fill(pars_H3_3.CI.PL(order2(i),[1,2,2,1]),(i*(-2-delta)-1)+(0.1+j*0.05)*[+1,+1,-1,-1],'b','facecolor',col_H3_3(j,:)); hold on;
    end
    % Plot - Optimum
    fill((pars_H3_2.MS.MAP.par(order2(i))+epsilon2*[-1,+1,+1,-1]),(i*(-2-delta)+0)+0.4*[+1,+1,-1,-1],'b','facecolor',col_H3_2(end,:)); hold on;
    fill((pars_H3_3.MS.MAP.par(order2(i))+epsilon2*[-1,+1,+1,-1]),(i*(-2-delta)-1)+0.4*[+1,+1,-1,-1],'b','facecolor',col_H3_3(end,:)); hold on;
    % Label
    text(-0.02,i*(-2-delta)-0.5,xl2{i},'HorizontalAlignment','Right','Fontsize',fs(2))
end
% Formatting
set(gca,'xlim',[0,1],...
        'ylim',[length(order2)*(-2-delta)-1-0.5-delta/2,1*(-2-delta)+0.5+delta/2],...
        'ytick',[],...
        'yticklabel',{});
set(gca,'Position',[0.2,0.1,0.75,0.1])
xlabel('parameter values','fontsize',fs(2));

% Print
set(gcf,'Position',[200 200 240 215]);
set(gcf,'PaperPositionMode','auto');
print('-depsc2','figures/H3_parameter_uncertainty');

%% Model-data comparison

% H1
D(1).measurand = 'pErk level [UI]';
D(2).measurand = 'pErk level [UI]';
options_plot.fs = fs([1,1]);
options_plot.z_max{1} = 0.06;
options_plot.z_max{2} = 0.06;
options_plot.data.bins = 200;
options_plot.model.points = 200;
options_plot.boundaries(1).y_min = 0.1; options_plot.boundaries(1).y_max = 100;
options_plot.boundaries(2).y_min = 0.1; options_plot.boundaries(2).y_max = 100;
options_plot.x_scale = 'log';
options_plot.data.lw   = 1;
options_plot.model.lw   = 1;
options_plot.model.ls = {'-','-'};
options_plot.legend = {'data','M_{H1,2}','M_{H1,3}'};
fh = plotODEMix_1_paper(D,{M_1logn_mean_all,...
                           M_1logn_median_all},...
                          {parameters_1logn_mean_all.MS.MAP.par,...
                           parameters_1logn_median_all.MS.MAP.par},...
                           options_plot);
% Print
set(gcf,'Position',[200 200 240 300]);
set(gcf,'PaperPositionMode','auto');
print('-depsc2','figures/H1_model_data_comparison');

%% H3
options_plot.legend = {'data','M_{H3,2}','M_{H3,3}'};
fh = plotODEMix_2_paper(D,{M_2logn_mean_TrkA0_all,...
                           M_2logn_median_TrkA0_all},...
                          {parameters_2logn_mean_TrkA0_all.MS.MAP.par,...
                           parameters_2logn_median_TrkA0_all.MS.MAP.par},...
                           options_plot);
% Print
set(gcf,'Position',[200 200 240 358]);
set(gcf,'PaperPositionMode','auto');
print('-depsc2','figures/H3_model_data_comparison');

%% Data

fh = plotODEMix_paper(D,[],...
                        {parameters_2logn_mean_TrkA0_all.MS.MAP.par,...
                         parameters_2logn_median_TrkA0_all.MS.MAP.par},...
                         options_plot);
% Print
set(gcf,'Position',[200 200 240 300]);
set(gcf,'PaperPositionMode','auto');
print('-depsc2','figures/data');

%% Kinetic and dose response

% H1
% Simulation - Kinetic
e = 1;
t = linspace(D(e).t(1),D(e).t(end),100);
for s = 1:M_1logn_mean_all.N_subpop
    X = M_1logn_mean_all.model(t,M_1logn_mean_all.theta{s}(parameters_1logn_mean_all.MS.MAP.par),D(e).u);
    MEAN_K{1}{s} = X(:,2);
    SIGMA_K{1}{s} = 10.^interp1(D(e).t,log10(M_1logn_mean_all.sigma{s,1}(D(e).t,X,parameters_1logn_mean_all.MS.MAP.par,D(e).u)),t,'cubic')';
    MEDIAN_K{1}{s} = exp(log(X(:,2))-(SIGMA_K{1}{s}.^2)/2);

    X = M_1logn_median_all.model(t,M_1logn_median_all.theta{s}(parameters_1logn_median_all.MS.MAP.par),D(e).u);
    MEDIAN_K{2}{s} = exp(M_1logn_median_all.mu{s,e}(t,X,parameters_1logn_median_all.MS.MAP.par,D(e).u));
    SIGMA_K{2}{s} = 10.^interp1(D(e).t,log10(M_1logn_median_all.sigma{s,1}(D(e).t,X,parameters_1logn_median_all.MS.MAP.par,D(e).u)),t,'cubic')';
    MEAN_K{2}{s} = MEDIAN_K{2}{s}.*exp((SIGMA_K{2}{s}.^2)/2);
end

indt = [1,1:length(t),length(t)];
t_indt = [-3,t,t(end)+3];

% Simulation - Dose response
e = 2;
u = [0,10.^linspace(-3.1,1.1,21)];
u_plot = [10^-4,10.^linspace(-3.1,1.1,21)];
u_plot_data = 10.^[-4:1];
for s = 1:M_1logn_mean_all.N_subpop
    for d = 1:length(u)
        X = M_1logn_mean_all.model(t,M_1logn_mean_all.theta{s}(parameters_1logn_mean_all.MS.MAP.par),u(d));
        MEAN_DR{1}{s}(d) = X(end,2);
        SIGMA_DR{1}{s}(d) = 10.^interp1(D(e).u',log10(M_1logn_mean_all.sigma{s,2}(D(e).t,X,parameters_1logn_mean_all.MS.MAP.par,D(e).u)),u(d),'cubic');
        MEDIAN_DR{1}{s}(d) = exp(log(X(end,2))-(SIGMA_DR{1}{s}(d).^2)/2);
    
        X = M_2logn_median_TrkA0_all.model(t,M_1logn_median_all.theta{s}(parameters_1logn_median_all.MS.MAP.par),u(d));
        MEDIAN_DR{2}{s}(d) = exp(M_1logn_median_all.mu{s}(t,X(end,:),parameters_1logn_median_all.MS.MAP.par,u(d)));
        SIGMA_DR{2}{s}(d) = 10.^interp1(D(e).u,log10(M_1logn_median_all.sigma{s,2}(D(e).t,X,parameters_1logn_median_all.MS.MAP.par,D(e).u)),u(d),'cubic')';
        MEAN_DR{2}{s}(d) = MEDIAN_DR{2}{s}(d)*exp((SIGMA_DR{2}{s}(d).^2)/2);
    end
end

%
figure;
lh = [];

% Kinetic
% Plot - M_{H1,2}
subplot('Position',[0.1,0.62,0.43,0.29]);
indt = [1,1:length(t),length(t)];
t_indt = [-3,t,t(end)+3];
plot(t_indt,MEAN_K{1}{1}(indt),'r-','linewidth',2); hold on;
lh(1) = plot(D(1).t,nanmean(D(1).Ey,2),'ko','markersize',ms,'linewidth',1);
for k = 1:length(D(1).t)
    plot(D(1).t(k)*[1,1],nanmean(D(1).Ey(k,:)) + nanstd(D(1).Ey(k,:))*[-1,1],'k-','linewidth',1);
    plot(D(1).t(k)+[0.7,-0.7],nanmean(D(1).Ey(k,:)) + nanstd(D(1).Ey(k,:))*[1,1],'k-','linewidth',1);
    plot(D(1).t(k)+[0.7,-0.7],nanmean(D(1).Ey(k,:)) - nanstd(D(1).Ey(k,:))*[1,1],'k-','linewidth',1);
end
% Limits / Label
%legend(lh,{'measurement: mean'}); legend('boxoff');
ylabel('pErk level [U]');
set(gca,'xlim',t_indt([1,end]),'ylim',[0,4],'yscale','lin','xtick',[0:15:60],'xticklabel',[]);
text(28,6.45*2/3,['\bf Kinetic for [NGF]_0 = 1 nM'],'fontsize',fs(2)+1,'HorizontalAlignment','center');

% Plot - M_{H1,3}
subplot('Position',[0.1,0.3,0.43,0.29]);
indt = [1,1:length(t),length(t)];
t_indt = [-3,t,t(end)+3];
plot(t_indt,MEAN_K{2}{1}(indt),'b-','linewidth',2); hold on;
plot(D(1).t,nanmean(D(1).Ey,2),'ko','markersize',ms,'linewidth',1);
for k = 1:length(D(1).t)
    plot(D(1).t(k)*[1,1],nanmean(D(1).Ey(k,:)) + nanstd(D(1).Ey(k,:))*[-1,1],'k-','linewidth',1);
    plot(D(1).t(k)+[0.7,-0.7],nanmean(D(1).Ey(k,:)) + nanstd(D(1).Ey(k,:))*[1,1],'k-','linewidth',1);
    plot(D(1).t(k)+[0.7,-0.7],nanmean(D(1).Ey(k,:)) - nanstd(D(1).Ey(k,:))*[1,1],'k-','linewidth',1);
end
% Limits / Label
xlabel('time, t [min]');
ylabel('pErk level [UI]');
set(gca,'xlim',t_indt([1,end]),'ylim',[0,4],'yscale','lin','xtick',[0:15:60]);

% Dose response
% Plot - M_{H1,2}
subplot('Position',[0.55,0.62,0.43,0.29]);
plot(u_plot(1)*[1/1.5,1.5],MEAN_DR{1}{1}(1)*[1,1],'r-','linewidth',2); hold on;
plot(u_plot_data(1),nanmean(D(2).Ey(1,:),2),'ko','markersize',ms,'linewidth',1);
lh(1) = plot(u_plot(2:end),MEAN_DR{1}{1}(2:end),'r-','linewidth',2);
plot(u_plot_data(2:end),nanmean(D(2).Ey(2:end,:),2),'ko','markersize',ms,'linewidth',1);
plot(u_plot_data([1,2]).*[2.5,1/2],1.12*[1,1],'k:','markersize',ms,'linewidth',1);
for d = 1:length(D(2).u)
    plot(u_plot_data(d)*[1,1],nanmean(D(2).Ey(d,:),2) + nanstd(D(2).Ey(d,:))*[-1,1],'k-','linewidth',1);
    plot(u_plot_data(d)*[1/1.12,1.12],nanmean(D(2).Ey(d,:),2) + nanstd(D(2).Ey(d,:))*[1,1],'k-','linewidth',1);
    plot(u_plot_data(d)*[1/1.12,1.12],nanmean(D(2).Ey(d,:),2) - nanstd(D(2).Ey(d,:))*[1,1],'k-','linewidth',1);
end
xlim([u_plot(1)/1.5,u_plot(end)]);
% Legend / Label
% legend(lh,{'M_{H1,2}: mean'}); legend('boxoff');
plot(0.001,3.5,'ko','markersize',ms,'linewidth',1); text(0.001*7,3.5,'data','HorizontalAlignment','left')
plot(0.001*[1/3,3],3.0*[1,1],'r-','linewidth',2); text(0.001*7,2.9,'M_{H1,2}','HorizontalAlignment','left')
plot(0.001*[1/3,3],2.5*[1,1],'b-','linewidth',2); text(0.001*7,2.4,'M_{H1,3}','HorizontalAlignment','left')
set(gca,'xscale','log','xtick',10.^[-4:1],'xticklabel',[],'ytick',0:4,'yticklabel',[],'ylim',[0,4],'yscale','lin');
text(0.025,6.68*2/3,['\bf Dose response for t = 30 min'],'fontsize',fs(2)+1,'HorizontalAlignment','center');

% Plot - M_{H1,3}
subplot('Position',[0.55,0.3,0.43,0.29]);
plot(u_plot(1)*[1/1.5,1.5],MEAN_DR{2}{1}(1)*[1,1],'b-','linewidth',2); hold on;
plot(u_plot_data(1),nanmean(D(e).Ey(1,:),2),'ko','markersize',ms,'linewidth',1);
lh(1) = plot(u_plot(2:end),MEAN_DR{2}{1}(2:end),'b-','linewidth',2);
plot(u_plot_data(2:end),nanmean(D(e).Ey(2:end,:),2),'ko','markersize',ms,'linewidth',1);
plot(u_plot_data([1,2]).*[2.5,1/2],1.12*[1,1],'k:','markersize',ms,'linewidth',1);
for d = 1:length(D(e).u)
    plot(u_plot_data(d)*[1,1],nanmean(D(e).Ey(d,:),2) + nanstd(D(e).Ey(d,:))*[-1,1],'k-','linewidth',1);
    plot(u_plot_data(d)*[1/1.12,1.12],nanmean(D(2).Ey(d,:),2) + nanstd(D(2).Ey(d,:))*[1,1],'k-','linewidth',1);
    plot(u_plot_data(d)*[1/1.12,1.12],nanmean(D(2).Ey(d,:),2) - nanstd(D(2).Ey(d,:))*[1,1],'k-','linewidth',1);
end
xlim([u_plot(1)/1.5,u_plot(end)]);
% Legend / Label
%legend(lh,{'M_{H1,3}: mean'}); legend('boxoff');
text(0.03,-1.5*0.63,['NGF concentration, [NGF]_0 [nM]'],'fontsize',fs(2),'HorizontalAlignment','center');

set(gca,'xscale','log','xtick',10.^[-4:1],'xticklabel',[0,0.001,0.01,0.1,1,10],'ytick',0:4,'yticklabel',[],'ylim',[0,4],'yscale','lin');

% Print
set(gcf,'Position',[200 200 240 300]);
set(gcf,'PaperPositionMode','auto');
print('-depsc2','figures/H1_model_data_comparison_mean');

% H3
% Simulation - Kinetic
e = 1;
t = linspace(D(e).t(1),D(e).t(end),100);
for s = 1:2
    X = M_2logn_mean_TrkA0_all.model(t,M_2logn_mean_TrkA0_all.theta{s}(parameters_2logn_mean_TrkA0_all.MS.MAP.par),D(e).u);
    MEAN_K{1}{s} = X(:,2);
    SIGMA_K{1}{s} = 10.^interp1(D(e).t,log10(M_2logn_mean_TrkA0_all.sigma{s,1}(D(e).t,X,parameters_2logn_mean_TrkA0_all.MS.MAP.par,D(e).u)),t,'cubic')';
    MEDIAN_K{1}{s} = exp(log(X(:,2))-(SIGMA_K{1}{s}.^2)/2);

    X = M_2logn_median_TrkA0_all.model(t,M_2logn_median_TrkA0_all.theta{s}(parameters_2logn_median_TrkA0_all.MS.MAP.par),D(e).u);
    MEDIAN_K{2}{s} = exp(M_2logn_median_TrkA0_all.mu{s,e}(t,X,parameters_2logn_median_TrkA0_all.MS.MAP.par,D(e).u));
    SIGMA_K{2}{s} = 10.^interp1(D(e).t,log10(M_2logn_median_TrkA0_all.sigma{s,1}(D(e).t,X,parameters_2logn_median_TrkA0_all.MS.MAP.par,D(e).u)),t,'cubic')';
    MEAN_K{2}{s} = MEDIAN_K{2}{s}.*exp((SIGMA_K{2}{s}.^2)/2);
end
W_K{1}{1} = M_2logn_mean_TrkA0_all.w{1}(parameters_2logn_mean_TrkA0_all.MS.MAP.par);
W_K{1}{2} = M_2logn_mean_TrkA0_all.w{2}(parameters_2logn_mean_TrkA0_all.MS.MAP.par);
W_K{2}{1} = M_2logn_median_TrkA0_all.w{1}(parameters_2logn_median_TrkA0_all.MS.MAP.par);
W_K{2}{2} = M_2logn_median_TrkA0_all.w{2}(parameters_2logn_median_TrkA0_all.MS.MAP.par);

indt = [1,1:length(t),length(t)];
t_indt = [-3,t,t(end)+3];

% Simulation - Dose response
e = 2;
u = [0,10.^linspace(-3.1,1.1,21)];
u_plot = [10^-4,10.^linspace(-3.1,1.1,21)];
u_plot_data = 10.^[-4:1];
for s = 1:M.N_subpop
    for d = 1:length(u)
        X = M_2logn_mean_TrkA0_all.model(t,M_2logn_mean_TrkA0_all.theta{s}(parameters_2logn_mean_TrkA0_all.MS.MAP.par),u(d));
        MEAN_DR{1}{s}(d) = X(end,2);
        SIGMA_DR{1}{s}(d) = 10.^interp1(D(e).u',log10(M_2logn_mean_TrkA0_all.sigma{s,2}(D(e).t,X,parameters_2logn_mean_TrkA0_all.MS.MAP.par,D(e).u)),u(d),'cubic');
        MEDIAN_DR{1}{s}(d) = exp(log(X(end,2))-(SIGMA_DR{1}{s}(d).^2)/2);
    
        X = M_2logn_median_TrkA0_all.model(t,M_2logn_median_TrkA0_all.theta{s}(parameters_2logn_median_TrkA0_all.MS.MAP.par),u(d));
        MEDIAN_DR{2}{s}(d) = exp(M_2logn_median_TrkA0_all.mu{s}(t,X(end,:),parameters_2logn_median_TrkA0_all.MS.MAP.par,u(d)));
        SIGMA_DR{2}{s}(d) = 10.^interp1(D(e).u,log10(M_2logn_median_TrkA0_all.sigma{s,2}(D(e).t,X,parameters_2logn_median_TrkA0_all.MS.MAP.par,D(e).u)),u(d),'cubic')';
        MEAN_DR{2}{s}(d) = MEDIAN_DR{2}{s}(d)*exp((SIGMA_DR{2}{s}(d).^2)/2);
    end
end
W_DR{1}{1} = M_2logn_mean_TrkA0_all.w{1}(parameters_2logn_mean_TrkA0_all.MS.MAP.par);
W_DR{1}{2} = M_2logn_mean_TrkA0_all.w{2}(parameters_2logn_mean_TrkA0_all.MS.MAP.par);
W_DR{2}{1} = M_2logn_median_TrkA0_all.w{1}(parameters_2logn_median_TrkA0_all.MS.MAP.par);
W_DR{2}{2} = M_2logn_median_TrkA0_all.w{2}(parameters_2logn_median_TrkA0_all.MS.MAP.par);

%
figure;
lh = [];

% Kinetic
% Plot - M_{H3,2}
subplot('Position',[0.1,0.62,0.43,0.29]);
indt = [1,1:length(t),length(t)];
t_indt = [-3,t,t(end)+3];
plot(t_indt,MEAN_K{1}{1}(indt),'-','color',[1.0,0.5,0.5],'linewidth',1); hold on;
plot(t_indt,MEAN_K{1}{2}(indt),'-','color',[0.5,0.0,0.0],'linewidth',1);
plot(t_indt,W_K{1}{1}*MEAN_K{1}{1}(indt)+W_K{1}{2}*MEAN_K{1}{2}(indt),'r-','linewidth',2);
lh(1) = plot(D(1).t,nanmean(D(1).Ey,2),'ko','markersize',ms,'linewidth',1);
for k = 1:length(D(1).t)
    plot(D(1).t(k)*[1,1],nanmean(D(1).Ey(k,:)) + nanstd(D(1).Ey(k,:))*[-1,1],'k-','linewidth',1);
    plot(D(1).t(k)+[0.7,-0.7],nanmean(D(1).Ey(k,:)) + nanstd(D(1).Ey(k,:))*[1,1],'k-','linewidth',1);
    plot(D(1).t(k)+[0.7,-0.7],nanmean(D(1).Ey(k,:)) - nanstd(D(1).Ey(k,:))*[1,1],'k-','linewidth',1);
end
% Limits / Label
legend(lh,{'overall mean'},'Position',[0.095,0.147,0.1,0.05]); legend('boxoff');
ylabel('pErk level [U]');
set(gca,'xlim',t_indt([1,end]),'ylim',[0,6],'yscale','lin','xtick',[0:15:60],'xticklabel',[]);
text(t_indt(end)-25,MEAN_K{1}{1}(end)-0.7,'w_1 = 69.7 %','color',[1.0,0.5,0.5]);
text(t_indt(end)-25,MEAN_K{1}{2}(end)+0.5,'w_2 = 30.3 %','color',[0.5,0.0,0.0]);
text(28,6.45,['\bf Kinetic for [NGF]_0 = 1 nM'],'fontsize',fs(2)+1,'HorizontalAlignment','center');

%annotation('doublearrow',[0.36,0.36],[0.68,0.83],'HeadWidth',3,'HeadLength',4);
%text(39,2.6,'\Delta_{12} = 3.1');


% Plot - M_{H3,3}
subplot('Position',[0.1,0.3,0.43,0.29]);
indt = [1,1:length(t),length(t)];
t_indt = [-3,t,t(end)+3];
plot(t_indt,MEAN_K{2}{1}(indt),'-','color',[0.5,0.5,1.0],'linewidth',1); hold on;
plot(t_indt,MEAN_K{2}{2}(indt),'-','color',[0.0,0.0,0.5],'linewidth',1);
plot(t_indt,W_K{2}{1}*MEAN_K{2}{1}(indt)+W_K{2}{2}*MEAN_K{2}{2}(indt),'b-','linewidth',2);
plot(D(1).t,nanmean(D(1).Ey,2),'ko','markersize',ms,'linewidth',1);
for k = 1:length(D(1).t)
    plot(D(1).t(k)*[1,1],nanmean(D(1).Ey(k,:)) + nanstd(D(1).Ey(k,:))*[-1,1],'k-','linewidth',1);
    plot(D(1).t(k)+[0.7,-0.7],nanmean(D(1).Ey(k,:)) + nanstd(D(1).Ey(k,:))*[1,1],'k-','linewidth',1);
    plot(D(1).t(k)+[0.7,-0.7],nanmean(D(1).Ey(k,:)) - nanstd(D(1).Ey(k,:))*[1,1],'k-','linewidth',1);
end
% Limits / Label
text(-11.8,-3.6,'\bf Model M_{H3,2}:');
text(-11.8,-2,'\bf Measurement data:');
xlabel('time, t [min]');
ylabel('pErk level [UI]');
set(gca,'xlim',t_indt([1,end]),'ylim',[0,6],'yscale','lin','xtick',[0:15:60]);
text(t_indt(end)-25,MEAN_K{2}{1}(end)-0.7,'w_1 = 68.8 %','color',[0.5,0.5,1.0]);
text(t_indt(end)-25,MEAN_K{2}{2}(end)+0.5,'w_2 = 31.2 %','color',[0.0,0.0,0.5]);

% Dose response
% Plot - M_{H3,3}
subplot('Position',[0.55,0.62,0.43,0.29]);
plot(u_plot(1)*[1/1.5,1.5],MEAN_DR{1}{1}(1)*[1,1],'-','color',[1.0,0.5,0.5],'linewidth',1); hold on;
plot(u_plot(1)*[1/1.5,1.5],MEAN_DR{1}{2}(1)*[1,1],'-','color',[0.5,0.0,0.0],'linewidth',1);
plot(u_plot(1)*[1/1.5,1.5],(W_DR{1}{1}*MEAN_DR{1}{1}(1)+W_DR{1}{2}*MEAN_DR{1}{2}(1))*[1,1],'r-','linewidth',2);
plot(u_plot_data(1),nanmean(D(2).Ey(1,:),2),'ko','markersize',ms,'linewidth',1);
lh(2) = plot(u_plot(2:end),MEAN_DR{1}{1}(2:end),'-','color',[1.0,0.5,0.5],'linewidth',1); hold on;
lh(3) = plot(u_plot(2:end),MEAN_DR{1}{2}(2:end),'-','color',[0.5,0.0,0.0],'linewidth',1);
lh(1) = plot(u_plot(2:end),W_DR{1}{1}*MEAN_DR{1}{1}(2:end)+W_DR{1}{2}*MEAN_DR{1}{2}(2:end),'r-','linewidth',2);
plot(u_plot_data(2:end),nanmean(D(2).Ey(2:end,:),2),'ko','markersize',ms,'linewidth',1);
plot(u_plot_data([1,2]).*[2.5,1/2],1.12*[1,1],'k:','markersize',ms,'linewidth',1);
for d = 1:length(D(2).u)
    plot(u_plot_data(d)*[1,1],nanmean(D(2).Ey(d,:),2) + nanstd(D(2).Ey(d,:))*[-1,1],'k-','linewidth',1);
    plot(u_plot_data(d)*[1/1.12,1.12],nanmean(D(2).Ey(d,:),2) + nanstd(D(2).Ey(d,:))*[1,1],'k-','linewidth',1);
    plot(u_plot_data(d)*[1/1.12,1.12],nanmean(D(2).Ey(d,:),2) - nanstd(D(2).Ey(d,:))*[1,1],'k-','linewidth',1);
end
xlim([u_plot(1)/1.5,u_plot(end)]);
% Legend / Label
legend(lh,{'overall mean','mean of subpopulation 1','mean of subpopulation 2'},'Position',[0.2,0.01,0.1,0.1]); legend('boxoff');
set(gca,'xscale','log','xtick',10.^[-4:1],'xticklabel',[],'ytick',0:6,'yticklabel',[],'ylim',[0,6],'yscale','lin');
text(0.15,MEAN_K{2}{1}(end)-0.7,'w_1 = 69.7 %','color',[1.0,0.5,0.5]);
text(0.15,MEAN_K{2}{2}(end)+0.5,'w_2 = 30.3 %','color',[0.5,0.0,0.0]);
text(0.025,6.68,['\bf Dose response for t = 30 min'],'fontsize',fs(2)+1,'HorizontalAlignment','center');

% Plot - M_{H3,3}
subplot('Position',[0.55,0.3,0.43,0.29]);
plot(u_plot(1)*[1/1.5,1.5],MEAN_DR{2}{1}(1)*[1,1],'-','color',[0.5,0.5,1.0],'linewidth',1); hold on;
plot(u_plot(1)*[1/1.5,1.5],MEAN_DR{2}{2}(1)*[1,1],'-','color',[0.0,0.0,0.5],'linewidth',1);
plot(u_plot(1)*[1/1.5,1.5],(W_DR{2}{1}*MEAN_DR{2}{1}(1)+W_DR{2}{2}*MEAN_DR{2}{2}(1))*[1,1],'b-','linewidth',2);
plot(u_plot_data(1),nanmean(D(e).Ey(1,:),2),'ko','markersize',ms,'linewidth',1);
lh(2) = plot(u_plot(2:end),MEAN_DR{2}{1}(2:end),'-','color',[0.5,0.5,1.0],'linewidth',1); hold on;
lh(3) = plot(u_plot(2:end),MEAN_DR{2}{2}(2:end),'-','color',[0.0,0.0,0.5],'linewidth',1);
lh(1) = plot(u_plot(2:end),W_DR{2}{1}*MEAN_DR{2}{1}(2:end)+W_DR{2}{2}*MEAN_DR{2}{2}(2:end),'b-','linewidth',2);
plot(u_plot_data(2:end),nanmean(D(e).Ey(2:end,:),2),'ko','markersize',ms,'linewidth',1);
plot(u_plot_data([1,2]).*[2.5,1/2],1.12*[1,1],'k:','markersize',ms,'linewidth',1);
for d = 1:length(D(e).u)
    plot(u_plot_data(d)*[1,1],nanmean(D(e).Ey(d,:),2) + nanstd(D(e).Ey(d,:))*[-1,1],'k-','linewidth',1);
    plot(u_plot_data(d)*[1/1.12,1.12],nanmean(D(2).Ey(d,:),2) + nanstd(D(2).Ey(d,:))*[1,1],'k-','linewidth',1);
    plot(u_plot_data(d)*[1/1.12,1.12],nanmean(D(2).Ey(d,:),2) - nanstd(D(2).Ey(d,:))*[1,1],'k-','linewidth',1);
end
xlim([u_plot(1)/1.5,u_plot(end)]);
% Legend / Label
text(0.00005,-3.6,'\bf Model M_{H3,3}:');
legend(lh,{'overall mean','mean of subpopulation 1','mean of subpopulation 2'},'Position',[0.7,0.01,0.1,0.1]); legend('boxoff');
%xlabel('     NGF concentration, [NGF]_0 [nM]');
text(0.03,-1.47,['NGF concentration, [NGF]_0 [nM]'],'fontsize',fs(2),'HorizontalAlignment','center');

set(gca,'xscale','log','xtick',10.^[-4:1],'xticklabel',[0,0.001,0.01,0.1,1,10],'ytick',0:6,'yticklabel',[],'ylim',[0,6],'yscale','lin');
text(0.15,MEAN_K{2}{1}(end)-0.7,'w_1 = 68.8 %','color',[0.5,0.5,1.0]);
text(0.15,MEAN_K{2}{2}(end)+0.5,'w_2 = 31.2 %','color',[0.0,0.0,0.5]);

% Print
set(gcf,'Position',[200 200 240 300]);
set(gcf,'PaperPositionMode','auto');
print('-depsc2','figures/H3_model_data_comparison_mean');

%% Correlation data
lh = [];

% Load data
load correlation_data;
I = 1:1500;

% Limits
Erk_lim = [0.1,10];
pErk_lim = [0.1,10];

% Mixture modeling of simulated data
gm = gmdistribution.fit(log10([D_corr.y_stimulated(I,1),D_corr.y_stimulated(I,2)]),2);

[~,order] = sort(gm.mu(:,2));

sgm = struct(gm);
sgm.mu = sgm.mu(order,:);
sgm.Sigma = sgm.Sigma(:,:,order);
sgm.PComponents = sgm.PComponents(order);
gm = struct(sgm);

% Assignment of samples to individual groups
P1 = mvnpdf(log10([D_corr.y_stimulated(I,1),D_corr.y_stimulated(I,2)]),gm.mu(1,:),gm.Sigma(:,:,1))*gm.PComponents(1);
P2 = mvnpdf(log10([D_corr.y_stimulated(I,1),D_corr.y_stimulated(I,2)]),gm.mu(2,:),gm.Sigma(:,:,2))*gm.PComponents(1);

ind1 = find(P1 > P2);
ind2 = find(P2 > P1);

% Evaluation of histograms
y_hist = linspace(log10(pErk_lim(1)),log10(pErk_lim(2)),40);
n = length(I);

h12_Erk_control = histc(log10(D_corr.y_control([ind1;ind2],1)),y_hist); 
h12_Erk_control = h12_Erk_control(1:end-1)/n;

h12_pErk_control = histc(log10(D_corr.y_control([ind1;ind2],2)),y_hist); 
h12_pErk_control = h12_pErk_control(1:end-1)/n;

h12_Erk_stimulated = histc(log10(D_corr.y_stimulated([ind1;ind2],1)),y_hist);
h12_Erk_stimulated = h12_Erk_stimulated(1:end-1)/n;
h2_Erk_stimulated = histc(log10(D_corr.y_stimulated(ind2,1)),y_hist);
h2_Erk_stimulated = h2_Erk_stimulated(1:end-1)/n;

h12_pErk_stimulated = histc(log10(D_corr.y_stimulated([ind1;ind2],2)),y_hist);
h12_pErk_stimulated = h12_pErk_stimulated(1:end-1)/n;
h2_pErk_stimulated = histc(log10(D_corr.y_stimulated(ind2,2)),y_hist);
h2_pErk_stimulated = h2_pErk_stimulated(1:end-1)/n;

% Evaluation of distribution for contour plot
[X1,X2] = meshgrid(linspace(log10(Erk_lim(1)),log10(Erk_lim(2)),1000),...
                   linspace(log10(pErk_lim(1)),log10(pErk_lim(2)),1000));
P1 = reshape(mvnpdf([X1(:),X2(:)],gm.mu(1,:),gm.Sigma(:,:,1)),size(X1));
P2 = reshape(mvnpdf([X1(:),X2(:)],gm.mu(2,:),gm.Sigma(:,:,2)),size(X1));

% Pearson correlation
[rho_control,pvalue_control] = corr(log10(D_corr.y_control(I,1)),log10(D_corr.y_control(I,2)));
[rho_stimulated,pvalue_stimulated] = corr(log10(D_corr.y_stimulated(I,1)),log10(D_corr.y_stimulated(I,2)));

% Plot: 2D control
figure;
subplot('Position',[0.2,0.4,0.25,0.5]);
plot(log10(D_corr.y_control(I,1)),log10(D_corr.y_control(I,2)),'k.','markersize',1.5); hold on;
set(gca,'xscale','lin','yscale','lin',...
    'xtick',log10([0.1:0.1:0.9,1:10]),'xticklabel',{'','','','','','','','','','','','','','','','','','',''},...
    'ytick',log10([0.1:0.1:0.9,1:10]),'yticklabel',{'','','','','','','','','','','','','','','','','','',''});
set(gca,'xlim',log10(Erk_lim),'ylim',log10(pErk_lim));
text(log10(0.1*3),log10(10/1.3),['\rho = ' num2str(rho_control,'%.3f')],'fontsize',fs(2),'HorizontalAlignment','center');
text(log10(0.1*3),log10(10/1.8),'(p < 0.001***)','fontsize',fs(1),'HorizontalAlignment','center');
text(log10(1),log10(23),'\bf Control','fontsize',fs(2)+1,'HorizontalAlignment','center');
text(log10(1),log10(14),'(t = 30 min, [NGF]_0 = 0 nM)','fontsize',fs(2),'HorizontalAlignment','center');
axis square;

% Plot: pErk histogram
subplot('Position',[0.1,0.4,0.08,0.5]);
fill([0;h12_pErk_control(round(0.5:0.5:length(h12_pErk_control)));0],y_hist(round(0.5:0.5:length(y_hist))),[0.7,0.7,0.7]); hold on;
set(gca,'xscale','lin','yscale','lin',...
    'ytick',log10([0.1:0.1:0.9,1:10]),'yticklabel',{'0.1','','','','','','','','','1','','','','','','','','','10'},...
    'xlim',[0,1.1*max(h12_pErk_control)],'xtick',[]);
ylabel('pErk level [UI]');

% Plot: Erk histogram
subplot('Position',[0.2,0.22,0.25,0.14]);
fill(y_hist(round(0.5:0.5:length(y_hist))),[0;h12_Erk_control(round(0.5:0.5:length(h12_Erk_control)));0],[0.7,0.7,0.7]); hold on;
set(gca,'xscale','lin','yscale','lin',...
    'xtick',log10([0.1:0.1:0.9,1:10]),'xticklabel',{'0.1','','','','','','','','','1','','','','','','','','','10'},...
    'ylim',[0,1.1*max(h12_pErk_control)],'ytick',[]);
xlabel('total Erk level [UI]');


% Plot: 2D 30 min, 1 nM NGF
subplot('Position',[0.2,0.4,0.25,0.5]+[0.5,0,0,0]);
plot(log10(D_corr.y_control(I,1)),log10(D_corr.y_control(I,2)),'k.','markersize',1.5); hold on;
plot(log10(D_corr.y_stimulated(I,1)),log10(D_corr.y_stimulated(I,2)),'k.','markersize',1.5); hold on;
[~,lh(1)] = contour(X1,X2,P1/max(P1(:)),exp(-1/2*(2)^2)*[1,1],'color',[0,0.8,0]);
[~,lh(2)] = contour(X1,X2,P2/max(P2(:)),exp(-1/2*(2)^2)*[1,1],'color',[0.6,0,0.6]);
set(gca,'xscale','lin','yscale','lin',...
    'xtick',log10([0.1:0.1:0.9,1:10]),'xticklabel',{'','','','','','','','','','','','','','','','','','',''},...
    'ytick',log10([0.1:0.1:0.9,1:10]),'yticklabel',{'','','','','','','','','','','','','','','','','','',''});
set(gca,'xlim',log10(Erk_lim),'ylim',log10(pErk_lim));
text(log10(10/3.5),log10(1),[num2str(gm.PComponents(1)*100,'%.1f') ' %'],'fontsize',fs(2),'HorizontalAlignment','center','color',[0,0.8,0]);
text(log10(10/3.5),log10(6),[num2str(gm.PComponents(2)*100,'%.1f') ' %'],'fontsize',fs(2),'HorizontalAlignment','center','color',[0.6,0,0.6]);
text(log10(0.1*3),log10(10/1.3),['\rho = ' num2str(rho_stimulated,'%.3f')],'fontsize',fs(2),'HorizontalAlignment','center');
text(log10(0.1*3),log10(10/1.8),'(p < 0.001***)','fontsize',fs(1),'HorizontalAlignment','center');
text(log10(1),log10(23),'\bf Stimulation','fontsize',fs(2)+1,'HorizontalAlignment','center');
text(log10(1),log10(14),'(t = 30 min, [NGF]_0 = 1 nM)','fontsize',fs(2),'HorizontalAlignment','center');
legend(lh,{['subpopulation 1'],...
           ['subpopulation 2']},...
           'location','SouthEast'); legend('boxoff');
axis square;

% Plot: pErk histogram
subplot('Position',[0.1,0.4,0.08,0.5]+[0.5,0,0,0]);
fill([0;h12_pErk_stimulated(round(0.5:0.5:length(h12_pErk_stimulated)));0],y_hist(round(0.5:0.5:length(y_hist))),[0,0.8,0]); hold on;
fill([0;h2_pErk_stimulated(round(0.5:0.5:length(h2_pErk_stimulated)));0],y_hist(round(0.5:0.5:length(y_hist))),[0.6,0,0.6]);
set(gca,'xscale','lin','yscale','lin',...
    'ytick',log10([0.1:0.1:0.9,1:10]),'yticklabel',{'0.1','','','','','','','','','1','','','','','','','','','10'},...
    'xlim',[0,1.1*max(h12_pErk_control)],'xtick',[]);
ylabel('pErk level [UI]');

% Plot: Erk histogram
subplot('Position',[0.2,0.22,0.25,0.14]+[0.5,0,0,0]);
fill(y_hist(round(0.5:0.5:length(y_hist))),[0;h12_Erk_stimulated(round(0.5:0.5:length(h12_Erk_stimulated)));0],[0,0.8,0]); hold on;
fill(y_hist(round(0.5:0.5:length(y_hist))),[0;h2_Erk_stimulated(round(0.5:0.5:length(h2_Erk_stimulated)));0],[0.6,0,0.6]);
set(gca,'xscale','lin','yscale','lin',...
    'xtick',log10([0.1:0.1:0.9,1:10]),'xticklabel',{'0.1','','','','','','','','','1','','','','','','','','','10'},...
    'ylim',[0,1.1*max(h12_pErk_control)],'ytick',[]);
xlabel('total Erk level [UI]');

% Print
set(gcf,'Position',[200 200 480 240]);
set(gcf,'PaperPositionMode','auto');
print('-depsc2','figures/correlation_analysis');

%% Profiles
close all;
par_name = {'log_{10}(k_1)','log_{10}(k_{2})','log_{10}(k_{4})',...
            'log_{10}(k_{5})','log_{10}(k_{3} [TrkA]_{0,1})','log_{10}(k_{3} [TrkA]_{0,2})',...
            'log_{10}(s [Erk]_0)','w_1',...
            'log_{10}(\sigma_{1,t=0min})','log_{10}(\sigma_{1,t=5min})','log_{10}(\sigma_{1,t=15min})','log_{10}(\sigma_{1,t=30min})','log_{10}(\sigma_{1,t=60min})',...
            'log_{10}(\sigma_{2,t=0min})','log_{10}(\sigma_{2,t=5min})','log_{10}(\sigma_{2,t=15min})','log_{10}(\sigma_{2,t=30min})','log_{10}(\sigma_{2,t=60min})',...
            'log_{10}(\sigma_{1,[NGF]_0=0nM})','log_{10}(\sigma_{1,[NGF]_0=0.001nM})','log_{10}(\sigma_{1,[NGF]_0=0.01nM})','log_{10}(\sigma_{1,[NGF]_0=0.1nM})','log_{10}(\sigma_{1,[NGF]_0=1nM})','log_{10}(\sigma_{1,[NGF]_0=10nM})',...
            'log_{10}(\sigma_{2,[NGF]_0=0nM})','log_{10}(\sigma_{2,[NGF]_0=0.001nM})','log_{10}(\sigma_{2,[NGF]_0=0.01nM})','log_{10}(\sigma_{2,[NGF]_0=0.1nM})','log_{10}(\sigma_{2,[NGF]_0=1nM})','log_{10}(\sigma_{2,[NGF]_0=10nM})'};

% Print
parameters_2logn_mean_TrkA0_all.name = par_name;
plotP_paper(parameters_2logn_mean_TrkA0_all);
set(gcf,'Position',[200 200 550 600]);
set(gcf,'PaperPositionMode','auto');
print('-depsc2','figures/profile_2logn_mean_TrkA0');

% Print
parameters_2logn_median_TrkA0_all.name = par_name;
plotP_paper(parameters_2logn_median_TrkA0_all);
set(gcf,'Position',[200 200 550 600]);
set(gcf,'PaperPositionMode','auto');
print('-depsc2','figures/profile_2logn_median_TrkA0');
