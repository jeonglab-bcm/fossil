clc

model_specification = {'1norm'             ,'$\\mathcal{M}_{\\text{H1,1}}$','    normal','mean  ','     -     ';...
                       '1logn_mean'        ,'$\\mathcal{M}_{\\text{H1,2}}$','log-normal','mean  ','     -     ';...
                       '1logn_median'      ,'$\\mathcal{M}_{\\text{H1,3}}$','log-normal','median','     -     ';...
                       '2norm_Erk0'        ,'$\\mathcal{M}_{\\text{H2,1}}$','    normal','mean  ',' $[\\Erk]_0$';...
                       '2logn_mean_Erk0'   ,'$\\mathcal{M}_{\\text{H2,2}}$','log-normal','mean  ',' $[\\Erk]_0$';...
                       '2logn_median_Erk0' ,'$\\mathcal{M}_{\\text{H2,3}}$','log-normal','median',' $[\\Erk]_0$';...
                       '2norm_TrkA0'       ,'$\\mathcal{M}_{\\text{H3,1}}$','    normal','mean  ','$[\\TrkA]_0$';...
                       '2logn_mean_TrkA0'  ,'$\\mathcal{M}_{\\text{H3,2}}$','log-normal','mean  ','$[\\TrkA]_0$';...
                       '2logn_median_TrkA0','$\\mathcal{M}_{\\text{H3,3}}$','log-normal','median','$[\\TrkA]_0$'};

%% Perform comparison 
for model_ind = 1:length(model_specification)
    % Load results
    load(['./project/results/' model_specification{model_ind,1} '_all']);
    
    % Store BIC
    BIC(model_ind) = parameters.MS.MAP.BIC;
end
% Compute Delta_BIC
Delta_BIC = BIC - min(BIC);
% Compute rank
[~,model_rank] = sort(Delta_BIC);

%% Generate string
str = '& $m$ & distribution & ODE const. & variability & $n$ & $\\logL(\\theta^*) (10^4)$ & BIC $(10^4)$ & rank & $\\Delta_{\\text{BIC}} $ & decision \\\\ \\hline \\hline \n';
for model_ind = 1:length(model_specification)
    % Load results
    load(['./project/results/' model_specification{model_ind,1} '_all']);
    
    % Write model name
    str = [str model_specification{model_ind,2} ' & '];
    
    % m
    str = [str num2str(M.N_subpop,'%i') ' & '];
    % distribution
    str = [str model_specification{model_ind,3} ' & '];
    % ODE const.
    str = [str model_specification{model_ind,4} ' & '];
    % variability
    str = [str model_specification{model_ind,5} ' & '];
    % n
    str = [str num2str(parameters.number,'%i') ' & '];
    % logL
    str = [str '$' num2str(parameters.MS.MAP.logPost*1e-4,'%.4f') '$' ' & '];
    % BIC
    str = [str '$' num2str(parameters.MS.MAP.BIC*1e-4,'%.4f') '$' ' & '];
    % rank
    str = [str '$' num2str(find(model_rank==model_ind),'%i') '$' ' & '];
    % Delta_BIC
    if Delta_BIC(model_ind) > 10
        str = [str '$> 10  $' ' & rejected     \\\\ \\hline'];
    elseif Delta_BIC(model_ind) > 0
        str = [str '$' num2str(Delta_BIC(model_ind),'%.3f') '$' ' & not rejected \\\\ \\hline'];
    else
        str = [str '$   0  $' ' & optimal      \\\\ \\hline'];
    end
    
    % Line break
    if (mod(model_ind,3) == 0) && (model_ind ~= length(model_specification))
        str = [str ' \\hline \n'];
    else
        str = [str ' \n'];
    end
end

% Print to screen
fprintf(str)
