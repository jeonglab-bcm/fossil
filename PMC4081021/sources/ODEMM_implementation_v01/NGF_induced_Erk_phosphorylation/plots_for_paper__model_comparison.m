clear all;
close all;
clc;

%%
fs = [6,7];
%fs = [12,14];
TextSizes.DefaultAxesFontSize = fs(2);
TextSizes.DefaultTextFontSize = fs(2);
set(0,TextSizes);

%% Load necessary information
for j = 1:3
    if j == 1
        str_p = 'A';
    elseif j == 2
        str_p = 'B';
    else
        str_p = 'C';
    end
    i = 1; load(['./pathway_model_' str_p '/project/results/1norm_all'],'parameters');               BIC_all(i,j) = parameters.MS.MAP.BIC; AIC_all(i,j) = parameters.MS.MAP.AIC; logL_all(i,j) = parameters.MS.MAP.logPost;
    i = 2; load(['./pathway_model_' str_p '/project/results/1logn_mean_all'],'parameters');          BIC_all(i,j) = parameters.MS.MAP.BIC; AIC_all(i,j) = parameters.MS.MAP.AIC; logL_all(i,j) = parameters.MS.MAP.logPost;
    i = 3; load(['./pathway_model_' str_p '/project/results/1logn_median_all'],'parameters');        BIC_all(i,j) = parameters.MS.MAP.BIC; AIC_all(i,j) = parameters.MS.MAP.AIC; logL_all(i,j) = parameters.MS.MAP.logPost;
    i = 4; load(['./pathway_model_' str_p '/project/results/2norm_Erk0_all'],'parameters');          BIC_all(i,j) = parameters.MS.MAP.BIC; AIC_all(i,j) = parameters.MS.MAP.AIC; logL_all(i,j) = parameters.MS.MAP.logPost;
    i = 5; load(['./pathway_model_' str_p '/project/results/2logn_mean_Erk0_all'],'parameters');     BIC_all(i,j) = parameters.MS.MAP.BIC; AIC_all(i,j) = parameters.MS.MAP.AIC; logL_all(i,j) = parameters.MS.MAP.logPost;
    i = 6; load(['./pathway_model_' str_p '/project/results/2logn_median_Erk0_all'],'parameters');   BIC_all(i,j) = parameters.MS.MAP.BIC; AIC_all(i,j) = parameters.MS.MAP.AIC; logL_all(i,j) = parameters.MS.MAP.logPost;
    i = 7; load(['./pathway_model_' str_p '/project/results/2norm_TrkA0_all'],'parameters');         BIC_all(i,j) = parameters.MS.MAP.BIC; AIC_all(i,j) = parameters.MS.MAP.AIC; logL_all(i,j) = parameters.MS.MAP.logPost;
    i = 8; load(['./pathway_model_' str_p '/project/results/2logn_mean_TrkA0_all'],'parameters');    BIC_all(i,j) = parameters.MS.MAP.BIC; AIC_all(i,j) = parameters.MS.MAP.AIC; logL_all(i,j) = parameters.MS.MAP.logPost;
    i = 9; load(['./pathway_model_' str_p '/project/results/2logn_median_TrkA0_all'],'parameters');  BIC_all(i,j) = parameters.MS.MAP.BIC; AIC_all(i,j) = parameters.MS.MAP.AIC; logL_all(i,j) = parameters.MS.MAP.logPost;
end

%% Visualization
figure;
axes('Position',[0.13,0.27,0.82,0.65],'Box','on')

% Bar plot
bar((BIC_all)); hold on; 
%colormap autumn
colormap([1,0,0;
          1,0.35,0;
          1,0.7,0])

% Seperation of hypothesis
yl = exp([11.15,11.65]);
plot(3.5*[1,1],yl,'k-');
plot(6.5*[1,1],yl,'k-');

set(gca,'xtick',1:9,'xticklabel',{' ',' ',' ',' ',' ',' ',' ',' ',' '});
name = {'M_{H1,1}','M_{H1,2}','M_{H1,3}',...
        'M_{H2,1}','M_{H2,2}','M_{H2,3}',...
        'M_{H3,1}','M_{H3,2}','M_{H3,3}'};
name_1 = {'normal','log-normal','log-normal',...
          'normal','log-normal','log-normal',...
          'normal','log-normal','log-normal'};
name_2 = {'mean','mean','median',...
          'mean','mean','median',...
          'mean','mean','median'};
text(-0.5,yl(1)*0.90,'Distribution:','fontsize',fs(2));
text(-0.5,yl(1)*0.86,'ODE-const.:','fontsize',fs(2));
for i = 1:9
    text(i+0.05,yl(1)*0.95,name{i},'fontsize',fs(2)+2,'HorizontalAlignment','center');
    text(i,yl(1)*0.90,name_1{i},'fontsize',fs(2),'HorizontalAlignment','center');
    text(i,yl(1)*0.86,name_2{i},'fontsize',fs(2),'HorizontalAlignment','center');
%     text(i,yl(1)*0.9,['(' name_1{i} ','],'fontsize',fs(2),'HorizontalAlignment','center');
%     text(i,yl(1)*0.86,[name_2{i} ')'],'fontsize',fs(2),'HorizontalAlignment','center');
end
set(gca,'fontsize',fs(2));

xlim([0.5,9.5]);
ylim(yl);

text(4.15,yl(1)*0.78,'model hypothesis','fontsize',fs(2)+2);
%xlabel('model hypothesis','fontsize',fs(2)+4);
ylabel('Bayesian information criterion, BIC','fontsize',fs(2)+2);

% Print
set(gcf,'Position',[200 200 440 210]);
set(gcf,'PaperPositionMode','auto');
print('-depsc2','pathway_model_comparison');

% %% Correlation
% PathM = [1,2,3;
%          1,2,3;
%          1,2,3;
%          1,2,3;
%          1,2,3;
%          1,2,3;
%          1,2,3;
%          1,2,3;
%          1,2,3];
% 
% Dis = [1,1,1;
%        2,2,2;
%        3,3,3;
%        1,1,1;
%        2,2,2;
%        3,3,3;
%        1,1,1;
%        2,2,2;
%        3,3,3];
% 
% Het = [1,1,1;
%        1,1,1;
%        1,1,1;
%        2,2,2;
%        2,2,2;
%        2,2,2;
%        3,3,3;
%        3,3,3;
%        3,3,3];
%    
% [rho,pval] = corr(BIC_all(:),PathM(:),'type','Spearman')
% [rho,pval] = corr(BIC_all(:),Dis(:),'type','Spearman')
% [rho,pval] = corr(BIC_all(:),Het(:),'type','Spearman')
