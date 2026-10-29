% Fluorescence data possess an experiment dependent unknown scaling factor.
% In general this scaling factor is elimiated by scaling the mean of the
% contol for the individual experiments to one. This yields a zero variance
% for this point and artificially increases the variance at the other
% point.
% This routine improves the scaling factor calculation by minimizing the
% mean square differences between the dataset (instead od setting the
% difference to zero for one particular point).

clear all;
close all;
clc;

%% Kinetic
ExpC = load_NGF_kinetic;
D(1).name = 'NGF kinetic';
D(1).type = 'kinetic';
D(1).measurand = 'relative pErk conc.';
D(1).t = [0,5,15,30,60];
D(1).u = 1;
D(1).y = nan(length(D(1).t),6000);
D(1).Ey = nan(length(D(1).t),10);
r = 3;
for k = 1:length(D(1).t)
    n0 = 0;
    for r = 1:length(ExpC(k).experiment)
        nx = size(ExpC(k).experiment(r).data,1);
        D(1).y(k,n0+1:n0+nx) = ExpC(k).experiment(r).data(1:nx,1)';
        D(1).Ey(k,r) = mean(ExpC(k).experiment(r).data(1:nx,1)');
        n0 = n0 + nx;
    end
end
D(1).y = D(1).y(:,1:find(sum(isnan(D(1).y))==length(D(1).t),1,'first')-1);
D(1).Ey = D(1).Ey(:,1:find(sum(isnan(D(1).Ey))==length(D(1).t),1,'first')-1);

% Computation of optimal scaling
A = D(1).Ey; d = size(A,2);
J = @(s) sum(sum(bsxfun(@minus,A*diag(d*s/sum(s)),A*(s/sum(s))).^2));

log_s = fminunc(@(log_s) J(exp(log_s)),zeros(d,1));
s = d*exp(log_s)/sum(exp(log_s))

As = A*diag(s);

% Variance comparison
varA  = std(A')'
varAs = std(As')'


%% Dose response
ExpC = load_NGF_dose_response;
D(2).name = 'NGF dose response';
D(2).type = 'dose response';
D(2).measurand = 'relative pErk conc.';
D(2).t = [30];
D(2).u = [0,0.001,0.01,0.1,1,10];
D(2).y = nan(length(D(2).u),10000);
D(2).Ey = nan(length(D(2).u),10);
r = 3;
for d = 1:length(D(2).u)
    n0 = 0;
    for r = 1:length(ExpC(d).experiment)
        nx = size(ExpC(d).experiment(r).data,1);
        D(2).y(d,n0+1:n0+nx) = ExpC(d).experiment(r).data(1:nx,1)';
        D(2).Ey(d,r) = mean(ExpC(d).experiment(r).data(1:nx,1)');
        n0 = n0 + nx;
    end
end
D(2).y = D(2).y(:,1:find(sum(isnan(D(2).y))==length(D(2).u),1,'first')-1);
D(2).Ey = D(2).Ey(:,1:find(sum(isnan(D(2).Ey))==length(D(2).u),1,'first')-1);

% Computation of optimal scaling
A = D(2).Ey; d = size(A,2);
J = @(s) sum(sum(bsxfun(@minus,A*diag(d*s/sum(s)),A*(s/sum(s))).^2));

log_s = fminunc(@(log_s) J(exp(log_s)),zeros(d,1));
s = d*exp(log_s)/sum(exp(log_s))

As = A*diag(s);

% Variance comparison
varA  = std(A')'
varAs = std(As')'

%% Dose response
ExpC = load_NGF_correlation;
D_corr.name = 'NGF correlation';
D_corr.type = 'correlation';
D_corr.measurand = {'relative Erk conc.','relative pErk conc.'};
D_corr.t = [30];
D_corr.u = [0,1];
D_corr.Ey_Erk  = [mean(ExpCondition(1).experiment(1).data(:,1)),mean(ExpCondition(1).experiment(2).data(:,1)),mean(ExpCondition(1).experiment(3).data(:,1))
                  mean(ExpCondition(2).experiment(1).data(:,1)),mean(ExpCondition(2).experiment(2).data(:,1)),mean(ExpCondition(2).experiment(3).data(:,1))];
D_corr.Ey_pErk = [mean(ExpCondition(1).experiment(1).data(:,2)),mean(ExpCondition(1).experiment(2).data(:,2)),mean(ExpCondition(1).experiment(3).data(:,2))
                  mean(ExpCondition(2).experiment(1).data(:,2)),mean(ExpCondition(2).experiment(2).data(:,2)),mean(ExpCondition(2).experiment(3).data(:,2))];
              
% Computation of optimal scaling
A = D_corr.Ey_Erk; d = size(A,2);
J = @(s) sum(sum(bsxfun(@minus,A*diag(d*s/sum(s)),A*(s/sum(s))).^2));

log_s = fminunc(@(log_s) J(exp(log_s)),zeros(d,1));
s_Erk = d*exp(log_s)/sum(exp(log_s))
s_Erk = s_Erk*(d/sum(s_Erk.*A(1,:)'))
% s_Erk = s_Erk/mean([s_Erk(1)*ExpCondition(1).experiment(1).data(:,1)
%                     s_Erk(2)*ExpCondition(1).experiment(2).data(:,1)
%                     s_Erk(3)*ExpCondition(1).experiment(3).data(:,1)]);


As = A*diag(s_Erk);
D_corr.Ey_Erk = D_corr.Ey_Erk*diag(s_Erk);

% Variance comparison
varA  = std(A')'
varAs = std(As')'

% Computation of optimal scaling
A = D_corr.Ey_pErk; d = size(A,2);
J = @(s) sum(sum(bsxfun(@minus,A*diag(d*s/sum(s)),A*(s/sum(s))).^2));

log_s = fminunc(@(log_s) J(exp(log_s)),zeros(d,1));
s_pErk = d*exp(log_s)/sum(exp(log_s))
s_pErk = s_pErk*(d/sum(s_pErk.*A(1,:)'))
% s_pErk = s_pErk/mean([s_pErk(1)*ExpCondition(1).experiment(1).data(:,2)
%                       s_pErk(2)*ExpCondition(1).experiment(2).data(:,2)
%                       s_pErk(3)*ExpCondition(1).experiment(3).data(:,2)]);

As = A*diag(s_pErk);
D_corr.Ey_pErk = D_corr.Ey_pErk*diag(s_pErk);

% Variance comparison
varA  = std(A')'
varAs = std(As')'

% Pooled, scaled data
D_corr.y_control = [s_Erk(1)*ExpCondition(1).experiment(1).data(:,1),s_pErk(1)*ExpCondition(1).experiment(1).data(:,2),ExpCondition(1).experiment(1).data(:,3)
                    s_Erk(2)*ExpCondition(1).experiment(2).data(:,1),s_pErk(2)*ExpCondition(1).experiment(2).data(:,2),ExpCondition(1).experiment(2).data(:,3)
                    s_Erk(3)*ExpCondition(1).experiment(3).data(:,1),s_pErk(3)*ExpCondition(1).experiment(3).data(:,2),ExpCondition(1).experiment(3).data(:,3)];

D_corr.y_stimulated = [s_Erk(1)*ExpCondition(2).experiment(1).data(:,1),s_pErk(1)*ExpCondition(2).experiment(1).data(:,2),ExpCondition(2).experiment(1).data(:,3)
                       s_Erk(2)*ExpCondition(2).experiment(2).data(:,1),s_pErk(2)*ExpCondition(2).experiment(2).data(:,2),ExpCondition(2).experiment(2).data(:,3)
                       s_Erk(3)*ExpCondition(2).experiment(3).data(:,1),s_pErk(3)*ExpCondition(2).experiment(3).data(:,2),ExpCondition(2).experiment(3).data(:,3)];

save('correlation_data','D_corr');