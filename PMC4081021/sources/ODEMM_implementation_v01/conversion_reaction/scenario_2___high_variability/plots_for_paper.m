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
load('./project/results/1norm_all');              parameters_1norm_all = parameters;              M_1norm_all = M;
load('./project/results/1logn_mean_all');         parameters_1logn_mean_all = parameters;         M_1logn_mean_all = M;
load('./project/results/1logn_median_all');       parameters_1logn_median_all = parameters;       M_1logn_median_all = M;
load('./project/results/2norm_k1a_all');          parameters_2norm_all = parameters;              M_2norm_all = M;
load('./project/results/2logn_mean_k1a_all');     parameters_2logn_mean_all = parameters;         M_2logn_mean_all = M;
load('./project/results/2logn_median_k1a_all');   parameters_2logn_median_all = parameters;       M_2logn_median_all = M;

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

xi_true = [log10(0.5),log10(1.5),log10(0.75),log10(0.1),0.5];
sigma_par_true = 0.1;

%% Plot parameter uncertainty
% Setting
alpha = [0.99,0.95,0.9,0.8];

delta = 0.5;
epsilon1 = 1e-2;
epsilon2 = 2e-3;


col_2 = [1,0.90,0.90;
         1,0.75,0.75;
         1,0.60,0.60;
         1,0.45,0.45;
         1,0.10,0.10];
col_3 = [0.90,0.90,1;
         0.75,0.75,1;
         0.60,0.60,1;
         0.45,0.45,1;
         0.10,0.10,1];

xl1 = {'k_1','k_{-1}','k_{2,b}','k_{-2}','s [Erk]_0','k_{2,a} [TrkA]_{ 0,1}','k_{2,a} [TrkA]_{ 0,2}'};
xl2 = {'w_1'};

xi = linspace(-1.5,1,100);

figure;
lh = [];


% Parameter 1
subplot('Position',[0.1,0.48+3*0.05+0.06,0.35,0.26]);
% fill(10.^xi([1,1:end,end]),[0,0.5*pdf('norm',xi,xi_true(3),0.1)+0.5*pdf('norm',xi,xi_true(4),0.1),0],0.9*[1,1,1]);
fill(10.^xi([1,1:end,end]),[0,0.5*pdf('norm',xi,xi_true(3),0.1),0],[0,0.8,0]); hold on;
fill(10.^xi([1,1:end,end]),[0,0.5*pdf('norm',xi,xi_true(4),0.1),0],[0.6,0,0.6]);
set(gca,'xscale','log','xlim',10.^xi([1,end]),'ylim',[0,2.2],'ytick',[],...
        'xtick',[0.03:0.01:0.09,0.1:0.1:0.9,1:1:10],...
        'xticklabel',{});

% Legend / Label
ylabel({'probability','density'},'fontsize',fs(2));

% MM - parameter 1.1
subplot('Position',[0.1,0.48+2*0.05+0.06,0.35,0.04]);
i = 3;
for j = 1:length(alpha)
    pars = getConfidenceIntervals(parameters_2logn_mean_all,alpha(j));
    fill(10.^pars.CI.PL(i,[1,2,2,1]),(0.1+j*0.05)*[+1,+1,-1,-1],'b','facecolor',col_2(j,:)); hold on;
end
fill(10.^(pars.MS.MAP.par(i)+epsilon1*[-1,+1,+1,-1]),0.4*[+1,+1,-1,-1],'b','facecolor',col_2(end,:)); hold on;
set(gca,'xscale','log','xlim',10.^xi([1,end]),'ylim',[-0.5,0.5],'ytick',[],...
        'xtick',[0.03:0.01:0.09,0.1:0.1:0.9,1:1:10],...
        'xticklabel',{});

% MM - parameter 1.2
subplot('Position',[0.1,0.48+1*0.05+0.06,0.35,0.04]);
i = 4;
for j = 1:length(alpha)
    pars = getConfidenceIntervals(parameters_2logn_mean_all,alpha(j));
    fill(10.^pars.CI.PL(i,[1,2,2,1]),(0.1+j*0.05)*[+1,+1,-1,-1],'b','facecolor',col_2(j,:)); hold on;
end
fill(10.^(pars.MS.MAP.par(i)+epsilon1*[-1,+1,+1,-1]),0.4*[+1,+1,-1,-1],'b','facecolor',col_2(end,:)); hold on;
set(gca,'xscale','log','xlim',10.^xi([1,end]),'ylim',[-0.5,0.5],'ytick',[],...
        'xtick',[0.03:0.01:0.09,0.1:0.1:0.9,1:1:10],...
        'xticklabel',{'','','','','','','','0.1','','','','','','','','','1','','','','','','','','','10'});

% Legend / Label
ylabel({'      ODE-MM','      estimate'},'fontsize',fs(2));

% Legend / Label
xlabel('k_1','fontsize',fs(2));


% Parameter 2
subplot('Position',[0.1+0.5,0.48+3*0.05+0.06,0.35,0.26]);
%fill(10.^xi([1,1:end,end]),[0,pdf('norm',xi,xi_true(1),0.1),0],0.9*[1,1,1]); hold on;
fill(10.^xi([1,1:end,end]),[0,pdf('norm',xi,xi_true(1),0.1),0],[0,0.8,0]); hold on;
fill(10.^xi([1,1:end,end]),0.5*[0,pdf('norm',xi,xi_true(1),0.1),0],[0.6,0,0.6]); hold on;
set(gca,'xscale','log','xlim',10.^xi([1,end]),'ylim',[0,4.4],'ytick',[],...
        'xtick',[0.03:0.01:0.09,0.1:0.1:0.9,1:1:10],...
        'xticklabel',{});

% Legend / Label
ylabel({'probability','density'},'fontsize',fs(2));

% MM - parameter 2
subplot('Position',[0.1+0.5,0.48+1*0.05+0.06,0.35,0.09]);
i = 1;
for j = 1:length(alpha)
    pars = getConfidenceIntervals(parameters_2logn_mean_all,alpha(j));
    fill(10.^pars.CI.PL(i,[1,2,2,1]),(0.1+j*0.05)*[+1,+1,-1,-1],'b','facecolor',col_2(j,:)); hold on;
end
fill(10.^(pars.MS.MAP.par(i)+epsilon1*[-1,+1,+1,-1]),0.4*[+1,+1,-1,-1],'b','facecolor',col_2(end,:)); hold on;
set(gca,'xscale','log','xlim',10.^xi([1,end]),'ylim',[-0.5,0.5],'ytick',[],...
        'xtick',[0.03:0.01:0.09,0.1:0.1:0.9,1:1:10],...
        'xticklabel',{'','','','','','','','0.1','','','','','','','','','1','','','','','','','','','10'});

% Legend / Label
xlabel('k_2','fontsize',fs(2));
ylabel({'ODE-MM','estimate'},'fontsize',fs(2));


% Parameter 3
subplot('Position',[0.1,3*0.05+0.06,0.35,0.26]);
% fill(10.^xi([1,1:end,end]),[0,pdf('norm',xi,xi_true(2),0.1),0],0.9*[1,1,1]);
fill(10.^xi([1,1:end,end]),[0,pdf('norm',xi,xi_true(2),0.1),0],[0,0.8,0]); hold on;
fill(10.^xi([1,1:end,end]),0.5*[0,pdf('norm',xi,xi_true(2),0.1),0],[0.6,0,0.6]);
set(gca,'xscale','log','xlim',10.^xi([1,end]),'ylim',[0,4.4],'ytick',[],...
        'xtick',[0.03:0.01:0.09,0.1:0.1:0.9,1:1:10],...
        'xticklabel',{});

% Legend / Label
ylabel({'probability','density'},'fontsize',fs(2));

% MM - parameter 3
subplot('Position',[0.1,1*0.05+0.06,0.35,0.09]);
i = 2;
for j = 1:length(alpha)
    pars = getConfidenceIntervals(parameters_2logn_mean_all,alpha(j));
    fill(10.^pars.CI.PL(i,[1,2,2,1]),(0.1+j*0.05)*[+1,+1,-1,-1],'b','facecolor',col_2(j,:)); hold on;
end
fill(10.^(pars.MS.MAP.par(i)+epsilon1*[-1,+1,+1,-1]),0.4*[+1,+1,-1,-1],'b','facecolor',col_2(end,:)); hold on;
set(gca,'xscale','log','xlim',10.^xi([1,end]),'ylim',[-0.5,0.5],'ytick',[],...
        'xtick',[0.03:0.01:0.09,0.1:0.1:0.9,1:1:10],...
        'xticklabel',{'','','','','','','','0.1','','','','','','','','','1','','','','','','','','','10'});

% Legend / Label
xlabel('k_3','fontsize',fs(2));
ylabel({'ODE-MM','estimate'},'fontsize',fs(2));


% Parameter 4
subplot('Position',[0.1+0.5,3*0.05+0.06,0.35,0.26]);
plot((0:1000)/1000,pdf('poiss',0:1000,xi_true(5)*1000)/1000,'k-'); hold on;
lh = plot(0.5,0,'ko','markersize',4);
set(gca,'xlim',[0,1],'ytick',[],'xtick',[0:0.2:1],'xticklabel',{},'ylim',[0,0.00003]);

% Legend / Label
ylabel({'sampling','density'},'fontsize',fs(2));
legend(lh,{'true parameter'}); legend('boxoff');

% MM - parameter 4
subplot('Position',[0.1+0.5,1*0.05+0.06,0.35,0.09]);
i = 5;
for j = 1:length(alpha)
    pars = getConfidenceIntervals(parameters_2logn_mean_all,alpha(j));
    fill(pars.CI.PL(i,[1,2,2,1]),(0.1+j*0.05)*[+1,+1,-1,-1],'b','facecolor',col_2(j,:)); hold on;
end
fill(pars.MS.MAP.par(i)+epsilon1/2*[-1,+1,+1,-1],0.4*[+1,+1,-1,-1],'b','facecolor',col_2(end,:)); hold on;
set(gca,'xlim',[0,1],'ytick',[],'xtick',[0:0.2:1]);

% Legend / Label
xlabel('w_1','fontsize',fs(2));
ylabel({'ODE-MM','estimate'},'fontsize',fs(2));


% Print
set(gcf,'Position',[200 200 270 215]);
set(gcf,'PaperPositionMode','auto');
print('-depsc2','figures/parameter_uncertainties');


% %% Sample trajectories
% % Number of simulated cells
% N = 1000;
% N_plot = 100;
% u  = 1;
% t = linspace(0,1.05,15);
% 
% % Sample simulation
% X1 = zeros(length(t),N); nj1 = 0;
% X2 = zeros(length(t),N); nj2 = 0;
% for j = 1:N
%     % Parameter sampling
%     if rand < M_2logn_mean_all.w{1}(xi_true)
%         theta_k = 10.^(xi_true(M_2logn_mean_all.subind{1}) + sigma_par_true*randn(1,3));
%         X = M_2logn_mean_all.model(t,theta_k,u);
%         X1(:,nj1+1) = X; nj1 = nj1 + 1;
%     else
%         theta_k = 10.^(xi_true(M_2logn_mean_all.subind{2}) + sigma_par_true*randn(1,3));
%         X = M_2logn_mean_all.model(t,theta_k,u);
%         X2(:,nj2+1) = X; nj2 = nj2 + 1;
%     end
% end
% 
% % Average
% X1_mean = mean(X1(:,1:nj1),2);
% X2_mean = mean(X2(:,1:nj2),2);
% 
% % Estimated subpopulations
% X_ODEMM1 = M_2logn_mean_all.model(t,10.^parameters_2logn_mean_all.MS.MAP.par(M_2logn_mean_all.subind{1}),u);
% X_ODEMM2 = M_2logn_mean_all.model(t,10.^parameters_2logn_mean_all.MS.MAP.par(M_2logn_mean_all.subind{2}),u);
% 
% % Visualization
% lh = [];
% 
% figure;
% subplot('Position',[0.15,0.58+0.1,0.82,0.3]);
% for j = 1:N_plot
%     lh(1) = plot([-0.05,t([1:end])],1-X1([1,1:end],j),'-','color',min([0.6,0,0.6]+0.7,1),'linewidth',0.5); hold on;
%     plot([-0.05,t([1:end])],1-X2([1,1:end],j),'-','color',min([0,0.8,0]+0.7,1),'linewidth',0.5); hold on;
% end
% lh(2) = plot([-0.05,t([1:end])],1-X1_mean([1,1:end]),'--','color',[0.6,0,0.6],'linewidth',1.5);
% plot([-0.05,t([1:end])],1-X2_mean([1,1:end]),'--','color',[0,0.8,0],'linewidth',1.5);
% plot([-0.05,t([1:end])],1-X_ODEMM1([1,1:end]),'-','color',[0,0.8,0],'linewidth',1.5);
% lh(3) = plot([-0.05,t([1:end])],1-X_ODEMM2([1,1:end]),'-','color',[0.6,0,0.6],'linewidth',1.5);
% 
% set(gca,'xlim',[-0.05,1.05],'ylim',[0,1],...
%         'xtick',0:0.2:1,'xticklabel',{},'ytick',0:0.2:1);
% ylabel('concentration of A [nM]','fontsize',fs(2));
% subplot('Position',[0.15,0.15+0.2,0.82,0.3]);
% for j = 1:N_plot
%     lh(4) = plot([-0.05,t([1:end])],X1([1,1:end],j),'-','color',min([0.6,0,0.6]+0.7,1),'linewidth',0.5); hold on;
%     lh(1) = plot([-0.05,t([1:end])],X2([1,1:end],j),'-','color',min([0,0.8,0]+0.7,1),'linewidth',0.5); hold on;
% end
% lh(5) = plot([-0.05,t([1:end])],X1_mean([1,1:end]),'--','color',[0.6,0,0.6],'linewidth',1.5);
% lh(2) = plot([-0.05,t([1:end])],X2_mean([1,1:end]),'--','color',[0,0.8,0],'linewidth',1.5);
% lh(3) = plot([-0.05,t([1:end])],X_ODEMM1([1,1:end]),'-','color',[0,0.8,0],'linewidth',1.5);
% lh(6) = plot([-0.05,t([1:end])],X_ODEMM2([1,1:end]),'-','color',[0.6,0,0.6],'linewidth',1.5);
% 
% set(gca,'xlim',[-0.05,1.05],'ylim',[0,1],...
%         'xtick',0:0.2:1,'ytick',0:0.2:1);
% xlabel('time [min]','fontsize',fs(2));
% ylabel('concentration of B [nM]','fontsize',fs(2));
% legend(lh,{'supopulation 1: sample trajectory',...
%            'supopulation 1: mean',...
%            'supopulation 1: mean by ODE-MM',...
%            'supopulation 2: sample trajectory',...
%            'supopulation 2: mean',...
%            'supopulation 2: mean by ODE-MM'},...
%            'Position',[0.49,0.03,0.6,0.2]); legend('boxoff');
% 
% % Print
% set(gcf,'Position',[200 200 270 320]);
% set(gcf,'PaperPositionMode','auto');
% print('-depsc2','figures/sample_trajectories');

%% Sample trajectories
% Number of simulated cells
N = 500;
N_plot = 20;
u  = 1;
t = linspace(0,1.05,15);

% Sample simulation
X1 = zeros(length(t),N); nj1 = 0;
X2 = zeros(length(t),N); nj2 = 0;
for j = 1:N
    % Parameter sampling
    if rand < M_2logn_mean_all.w{1}(xi_true)
        theta_k = 10.^(xi_true(M_2logn_mean_all.subind{1}) + sigma_par_true*randn(1,3));
        X = M_2logn_mean_all.model(t,theta_k,u);
        X1(:,nj1+1) = X; nj1 = nj1 + 1;
    else
        theta_k = 10.^(xi_true(M_2logn_mean_all.subind{2}) + sigma_par_true*randn(1,3));
        X = M_2logn_mean_all.model(t,theta_k,u);
        X2(:,nj2+1) = X; nj2 = nj2 + 1;
    end
end

% Average
X1_mean = mean(X1(:,1:nj1),2);
X2_mean = mean(X2(:,1:nj2),2);

% Estimated subpopulations
X_ODEMM1 = M_2logn_mean_all.model(t,10.^parameters_2logn_mean_all.MS.MAP.par(M_2logn_mean_all.subind{1}),u);
X_ODEMM2 = M_2logn_mean_all.model(t,10.^parameters_2logn_mean_all.MS.MAP.par(M_2logn_mean_all.subind{2}),u);
X_ODEMM =   M_2logn_mean_all.w{1}(parameters_2logn_mean_all.MS.MAP.par)*X_ODEMM1 ...
          + M_2logn_mean_all.w{2}(parameters_2logn_mean_all.MS.MAP.par)*X_ODEMM2;

% Visualization
lh = [];

figure;
% subplot('Position',[0.15,0.58+0.1,0.82,0.3]);
% for j = 1:N_plot
%     lh(1) = plot([-0.05,t([1:end])],1-X1([1,1:end],j),'-','color',min([0,0.8,0]+0.7,1),'linewidth',0.5); hold on;
%     plot([-0.05,t([1:end])],1-X2([1,1:end],j),'-','color',min([0.6,0,0.6]+0.7,1),'linewidth',0.5); hold on;
% end
% lh(2) = plot([-0.05,t([1:end])],1-X1_mean([1,1:end]),'--','color',[0,0.8,0],'linewidth',1.5);
% plot([-0.05,t([1:end])],1-X2_mean([1,1:end]),'--','color',[0.6,0,0.6],'linewidth',1.5);
% plot([-0.05,t([1:end])],1-X_ODEMM1([1,1:end]),'-','color',[0,0.8,0],'linewidth',1.5);
% lh(3) = plot([-0.05,t([1:end])],1-X_ODEMM2([1,1:end]),'-','color',[0.6,0,0.6],'linewidth',1.5);

set(gca,'xlim',[-0.05,1.05],'ylim',[0,1],...
        'xtick',0:0.2:1,'xticklabel',{},'ytick',0:0.2:1);
ylabel('concentration of A [nM]','fontsize',fs(2));
subplot('Position',[0.15,0.2,0.4,0.75]);
for j = 1:N_plot
%     lh(9) = plot([-0.05,t([1:end])],X1([1,1:end],j),'-','color',min([0,0,0]+0.7,1),'linewidth',0.5); hold on;
%     lh(4) = plot([-0.05,t([1:end])],X2([1,1:end],j),'-','color',min([0,0,0]+0.7,1),'linewidth',0.5); hold on;
%     lh(9) = patch([-0.05,t([1:end])],X1([1,1:end],j), '-','EdgeColor',[0,0.8,0],'EdgeAlpha',0.05,'FaceColor','none'); hold on;
%     lh(4) = patch([-0.05,t([1:end])],X2([1,1:end],j), '-','EdgeColor',[0.6,0,0.6],'EdgeAlpha',0.05,'FaceColor','none');
    lh(8) = plot([-0.05,t([1:end])],X1([1,1:end],j),'-','color',min([0,0.8,0]+0.7,1),'linewidth',0.5); hold on;
    lh(4) = plot([-0.05,t([1:end])],X2([1,1:end],j),'-','color',min([0.6,0,0.6]+0.7,1),'linewidth',0.5); hold on;
end
lh(9) = plot([-0.05,t([1:end])],X1_mean([1,1:end]),'--','color',[0,0.8,0],'linewidth',1.5);
lh(5) = plot([-0.05,t([1:end])],X2_mean([1,1:end]),'--','color',[0.6,0,0.6],'linewidth',1.5);
lh(10) = plot([-0.05,t([1:end])],X_ODEMM1([1,1:end]),'-','color',[0,0.8,0],'linewidth',1.5);
lh(6) = plot([-0.05,t([1:end])],X_ODEMM2([1,1:end]),'-','color',[0.6,0,0.6],'linewidth',1.5);
lh(2) = plot([-0.05,t([1:end])],X_ODEMM([1,1:end]),'-','color',[1,0,0],'linewidth',1.5);
lh(1) = plot(D.t([1:end]),mean(D.y,2),'.','color',[0,0,0],'linewidth',6,'markersize',8);

set(gca,'xlim',[-0.05,1.05],'ylim',[0,0.7],...
        'xtick',0:0.2:1,'ytick',0:0.1:0.7);
xlabel('time [min]','fontsize',fs(2));
ylabel('concentration of B [nM]','fontsize',fs(2));

legend(lh,{'measured mean',...
           'mean by ODE-MM',...
           '',...
           'sample trajectory',...
           'mean by sample trajectory',...
           'mean by ODE-MM',...
           '',...
           'sample trajectory',...
           'mean of sample trajectory',...
           'mean by ODE-MM'},...
           'Position',[0.79,0.44,0.01,0.1]); legend('boxoff');
text(1.1,0.68,'\bf Overall population:')
text(1.1,0.45,'\bf Subpopulation 1:')
text(1.1,0.15,'\bf Subpopulation 2:')

% Print
set(gcf,'Position',[200 200 270 130]);
set(gcf,'PaperPositionMode','auto');
print('-depsc2','figures/sample_trajectories');

%% Sample trajectories
% Number of simulated cells
N = 500;
N_plot = 20;
u  = 1;
t = linspace(0,1.05,15);

% Sample simulation
X1 = zeros(length(t),N); nj1 = 0;
X2 = zeros(length(t),N); nj2 = 0;
for j = 1:N
    % Parameter sampling
    if rand < M_2logn_mean_all.w{1}(xi_true)
        theta_k = 10.^(xi_true(M_2logn_mean_all.subind{1}) + sigma_par_true*randn(1,3));
        X = M_2logn_mean_all.model(t,theta_k,u);
        X1(:,nj1+1) = X; nj1 = nj1 + 1;
    else
        theta_k = 10.^(xi_true(M_2logn_mean_all.subind{2}) + sigma_par_true*randn(1,3));
        X = M_2logn_mean_all.model(t,theta_k,u);
        X2(:,nj2+1) = X; nj2 = nj2 + 1;
    end
end

% Average
X1_mean = mean(X1(:,1:nj1),2);
X2_mean = mean(X2(:,1:nj2),2);

% Estimated subpopulations
X_ODEMM1 = M_2logn_mean_all.model(t,10.^parameters_2logn_mean_all.MS.MAP.par(M_2logn_mean_all.subind{1}),u);
X_ODEMM2 = M_2logn_mean_all.model(t,10.^parameters_2logn_mean_all.MS.MAP.par(M_2logn_mean_all.subind{2}),u);
X_ODEMM =   M_2logn_mean_all.w{1}(parameters_2logn_mean_all.MS.MAP.par)*X_ODEMM1 ...
          + M_2logn_mean_all.w{2}(parameters_2logn_mean_all.MS.MAP.par)*X_ODEMM2;

% Visualization
lh = [];

figure;
% subplot('Position',[0.15,0.58+0.1,0.82,0.3]);
% for j = 1:N_plot
%     lh(1) = plot([-0.05,t([1:end])],1-X1([1,1:end],j),'-','color',min([0,0.8,0]+0.7,1),'linewidth',0.5); hold on;
%     plot([-0.05,t([1:end])],1-X2([1,1:end],j),'-','color',min([0.6,0,0.6]+0.7,1),'linewidth',0.5); hold on;
% end
% lh(2) = plot([-0.05,t([1:end])],1-X1_mean([1,1:end]),'--','color',[0,0.8,0],'linewidth',1.5);
% plot([-0.05,t([1:end])],1-X2_mean([1,1:end]),'--','color',[0.6,0,0.6],'linewidth',1.5);
% plot([-0.05,t([1:end])],1-X_ODEMM1([1,1:end]),'-','color',[0,0.8,0],'linewidth',1.5);
% lh(3) = plot([-0.05,t([1:end])],1-X_ODEMM2([1,1:end]),'-','color',[0.6,0,0.6],'linewidth',1.5);

set(gca,'xlim',[-0.05,1.05],'ylim',[0,1],...
        'xtick',0:0.2:1,'xticklabel',{},'ytick',0:0.2:1);
ylabel('concentration of A [nM]','fontsize',fs(2));
subplot('Position',[0.15,0.2,0.4,0.75]);
for j = 1:N_plot
%     lh(9) = plot([-0.05,t([1:end])],X1([1,1:end],j),'-','color',min([0,0,0]+0.7,1),'linewidth',0.5); hold on;
%     lh(4) = plot([-0.05,t([1:end])],X2([1,1:end],j),'-','color',min([0,0,0]+0.7,1),'linewidth',0.5); hold on;
%     lh(9) = patch([-0.05,t([1:end])],X1([1,1:end],j), '-','EdgeColor',[0,0.8,0],'EdgeAlpha',0.05,'FaceColor','none'); hold on;
%     lh(4) = patch([-0.05,t([1:end])],X2([1,1:end],j), '-','EdgeColor',[0.6,0,0.6],'EdgeAlpha',0.05,'FaceColor','none');
    lh(8) = plot([-0.05,t([1:end])],X1([1,1:end],j),'-','color',min([0,0.8,0]+0.7,1),'linewidth',0.5); hold on;
    lh(4) = plot([-0.05,t([1:end])],X2([1,1:end],j),'-','color',min([0.6,0,0.6]+0.7,1),'linewidth',0.5); hold on;
end
lh(9) = plot([-0.05,t([1:end])],X1_mean([1,1:end]),'--','color',[0,0.8,0],'linewidth',1.5);
lh(5) = plot([-0.05,t([1:end])],X2_mean([1,1:end]),'--','color',[0.6,0,0.6],'linewidth',1.5);
%lh(10) = plot([-0.05,t([1:end])],X_ODEMM1([1,1:end]),'-','color',[0,0.8,0],'linewidth',1.5);
%lh(6) = plot([-0.05,t([1:end])],X_ODEMM2([1,1:end]),'-','color',[0.6,0,0.6],'linewidth',1.5);
lh(2) = plot([-0.05,t([1:end])],X_ODEMM([1,1:end]),'-','color',[1,0,0],'linewidth',1.5);
lh(1) = plot(D.t([1:end]),mean(D.y,2),'.','color',[0,0,0],'linewidth',6,'markersize',8);

set(gca,'xlim',[-0.05,1.05],'ylim',[0,0.7],...
        'xtick',0:0.2:1,'ytick',0:0.1:0.7);
xlabel('time [min]','fontsize',fs(2));
ylabel('concentration of B [nM]','fontsize',fs(2));

legend(lh,{'measured mean',...
           'mean by ODE-MM',...
           '',...
           'sample trajectory',...
           'mean by sample trajectory',...
           '',...
           '',...
           'sample trajectory',...
           'mean of sample trajectory',...
           ''},...
           'Position',[0.79,0.44,0.01,0.1]); legend('boxoff');
text(1.1,0.68,'\bf Overall population:')
text(1.1,0.45,'\bf Subpopulation 1:')
text(1.1,0.15,'\bf Subpopulation 2:')

% Print
set(gcf,'Position',[200 200 270 130]);
set(gcf,'PaperPositionMode','auto');
print('-depsc2','figures/sample_trajectories_data');

%% Model-data comparison

% H1
D(1).measurand = 'concentration of B [nM]';
options_plot.fs = fs([1,1]);
options_plot.z_max{1} = 0.1;
options_plot.data.bins = 50;
options_plot.model.points = 200;
options_plot.boundaries(1).y_min = 0.1; options_plot.boundaries(1).y_max = 1;
options_plot.x_scale = 'log';
options_plot.data.lw   = 1;
options_plot.model.lw   = 1;
options_plot.model.ls = {'-','-'};
options_plot.legend = {'data','model'};
fh = plotODEMix_paper(D,{M_2logn_mean_all},...
                        {parameters_2logn_mean_all.MS.MAP.par},...
                        options_plot);
% Print
set(gcf,'Position',[200 200 265 170]);
set(gcf,'PaperPositionMode','auto');
print('-depsc2','figures/model_data_comparison');

%% Data

fh = plotODEMix_paper(D,[],...
                        {parameters_2logn_mean_all.MS.MAP.par},...
                        options_plot);
% Print
set(gcf,'Position',[200 200 265 170]);
set(gcf,'PaperPositionMode','auto');
print('-depsc2','figures/data');
