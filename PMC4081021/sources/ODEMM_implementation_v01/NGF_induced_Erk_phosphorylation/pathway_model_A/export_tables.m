clc

model_specification = {'1norm'             ,'$\\mathcal{M}_{\\text{H1,1}}$','    normal','mean  ','     -      ';...
                       '1logn_mean'        ,'$\\mathcal{M}_{\\text{H1,2}}$','log-normal','mean  ','     -      ';...
                       '1logn_median'      ,'$\\mathcal{M}_{\\text{H1,3}}$','log-normal','median','     -      ';...
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

%% Generate string - Model comparison
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
disp(' ');
disp(' ');


%% Generate string - Parameter confidence intervals
% Table 1
str = ['\\hline \n' ...
       '& \\multicolumn{2}{c|}{weights $w$} & $\\log_{10}(k_1)$ & $\\log_{10}(k_2)$ & $\\log_{10}(k_4)$ \\\\ \\hline  \n' ...
       '& $w_{1}$ & $w_{2} (= 1 - w_{1})$ &  &  & \\\\ \\hline \\hline \n'];

for model_ind = 1:length(model_specification)
    % Load results
    load(['./project/results/' model_specification{model_ind,1} '_all']);
    
    % Write model name
    str = [str model_specification{model_ind,2} ' & '];
    
    % log_10(w_i)
    if ~isempty(strfind(model_specification{model_ind,1},'TrkA'))
        if parameters.MS.MAP.par(5) < parameters.MS.MAP.par(6) 
            w1 = parameters.MS.MAP.par(8);
            w2 = 1 - parameters.MS.MAP.par(8);
            lb_w1 = parameters.CI.PL(8,1);
            ub_w1 = parameters.CI.PL(8,2);
            lb_w2 = 1-parameters.CI.PL(8,2);
            ub_w2 = 1-parameters.CI.PL(8,1);
        else
            w1 = 1 - parameters.MS.MAP.par(8);
            w2 = parameters.MS.MAP.par(8);
            lb_w1 = 1-parameters.CI.PL(8,2);
            ub_w1 = 1-parameters.CI.PL(8,1);
            lb_w2 = parameters.CI.PL(8,1);
            ub_w2 = parameters.CI.PL(8,2);
        end
        %
        str = [str '$' num2str_sign(w1,'%.3f')  '$ $('];
        str = [str num2str_sign(lb_w1,'%.3f')  ','];
        str = [str num2str_sign(ub_w1,'%.3f')  ')$'];
        str = [str ' & '];
        %
        str = [str '$' num2str_sign(w2,'%.3f')  '$ $('];
        str = [str num2str_sign(lb_w2,'%.3f')  ','];
        str = [str num2str_sign(ub_w2,'%.3f')  ')$'];
        str = [str ' & '];

    elseif ~isempty(strfind(model_specification{model_ind,1},'Erk0'))
        if parameters.MS.MAP.par(6) < parameters.MS.MAP.par(7)  
            w1 = parameters.MS.MAP.par(8);
            w2 = 1 - parameters.MS.MAP.par(8);
            lb_w1 = parameters.CI.PL(8,1);
            ub_w1 = parameters.CI.PL(8,2);
            lb_w2 = 1-parameters.CI.PL(8,2);
            ub_w2 = 1-parameters.CI.PL(8,1);
        else
            w1 = 1 - parameters.MS.MAP.par(8);
            w2 = parameters.MS.MAP.par(8);
            lb_w1 = 1-parameters.CI.PL(8,2);
            ub_w1 = 1-parameters.CI.PL(8,1);
            lb_w2 = parameters.CI.PL(8,1);
            ub_w2 = parameters.CI.PL(8,2);
        end
        %
        str = [str '$' num2str_sign(w1,'%.3f')  '$ $('];
        str = [str num2str_sign(lb_w1,'%.3f')  ','];
        str = [str num2str_sign(ub_w1,'%.3f')  ')$'];
        str = [str ' & '];
        %
        str = [str '$' num2str_sign(w2,'%.3f')  '$ $('];
        str = [str num2str_sign(lb_w2,'%.3f')  ','];
        str = [str num2str_sign(ub_w2,'%.3f')  ')$'];
        str = [str ' & '];
    else
        str = [str '\\multicolumn{2}{c|}{$1$}                                & '];
    end
    
    % log_10(k_1)
    i = 1;
    str = [str '$' num2str_sign(parameters.MS.MAP.par(i),'%.3f')  '$ $('];
    if parameters.CI.PL(i,1) > -6
        str = [str num2str_sign(parameters.CI.PL(i,1),'%.3f')  ','];
    else
        str = [str '<-6.0 ,'];
    end
    if parameters.CI.PL(i,2) < +6
        str = [str num2str_sign(parameters.CI.PL(i,2),'%.3f')  ')$'];
    else
        str = [str '>+6.0 )$'];
    end
    str = [str ' & '];
        
    % log_10(k_2)
    i = 2;
    str = [str '$' num2str_sign(parameters.MS.MAP.par(i),'%.3f')  '$ $('];
    if parameters.CI.PL(i,1) > -6
        str = [str num2str_sign(parameters.CI.PL(i,1),'%.3f')  ','];
    else
        str = [str '<-6.0 ,'];
    end
    if parameters.CI.PL(i,2) < +6
        str = [str num2str_sign(parameters.CI.PL(i,2),'%.3f')  ')$'];
    else
        str = [str '>+6.0 )$'];
    end
    str = [str ' & '];
        
    % log_10(k_4)
    i = 3;
    str = [str '$' num2str_sign(parameters.MS.MAP.par(i),'%.3f')  '$ $('];
    if parameters.CI.PL(i,1) > -6
        str = [str num2str_sign(parameters.CI.PL(i,1),'%.3f')  ','];
    else
        str = [str '<-6.0 ,'];
    end
    if parameters.CI.PL(i,2) < +6
        str = [str num2str_sign(parameters.CI.PL(i,2),'%.3f')  ')$'];
    else
        str = [str '>+6.0 )$'];
    end
    
    str = [str ' \\\\ \\hline '];
    
    % Line break
    if (mod(model_ind,3) == 0) && (model_ind ~= length(model_specification))
        str = [str ' \\hline \n'];
    else
        str = [str ' \n'];
    end
end

% Print to screen
fprintf(str);
disp(' ');
disp(' ');


% Table 2
str = ['\\hline \n' ...
       '& \\multicolumn{2}{c|}{$\\log_{10}(k_3 [\\TrkA]_{0})$} & $\\log_{10}(k_5)$ & \\multicolumn{2}{c|}{$\\log_{10}(s [\\Erk]_{0})$} \\\\ \\hline \n' ...
       '& $\\log_{10}(k_3 [\\TrkA]_{0,1})$ & $\\log_{10}(k_3 [\\TrkA]_{0,2})$ & & $\\log_{10}(s [\\Erk]_{0,1})$ & $\\log_{10}(s [\\Erk]_{0,2})$ \\\\ \\hline \\hline \n'];

for model_ind = 1:length(model_specification)
    % Load results
    load(['./project/results/' model_specification{model_ind,1} '_all']);
    
    % Write model name
    str = [str model_specification{model_ind,2} ' & '];
    
    % 
    if ~isempty(strfind(model_specification{model_ind,1},'TrkA'))
        % log_10(k_3*TrkA_0)
        if parameters.MS.MAP.par(5) < parameters.MS.MAP.par(6) 
            i1 = 5;
            i2 = 6;
        else
            i1 = 6;
            i2 = 5;
        end

        %
        i = i1;
        str = [str '$' num2str_sign(parameters.MS.MAP.par(i),'%.3f')  '$ $('];
        if parameters.CI.PL(i,1) > -6
            str = [str num2str_sign(parameters.CI.PL(i,1),'%.3f')  ','];
        else
            str = [str '<-6.0 ,'];
        end
        if parameters.CI.PL(i,2) < +6
            str = [str num2str_sign(parameters.CI.PL(i,2),'%.3f')  ')$'];
        else
            str = [str '>+6.0 )$'];
        end
        str = [str ' & '];
        %
        i = i2;
        str = [str '$' num2str_sign(parameters.MS.MAP.par(i),'%.3f')  '$ $('];
        if parameters.CI.PL(i,1) > -6
            str = [str num2str_sign(parameters.CI.PL(i,1),'%.3f')  ','];
        else
            str = [str '<-6.0 ,'];
        end
        if parameters.CI.PL(i,2) < +6
            str = [str num2str_sign(parameters.CI.PL(i,2),'%.3f')  ')$'];
        else
            str = [str '>+6.0 )$'];
        end
        str = [str ' & '];

        % log_10(k_5)
        i = 4;
        str = [str '$' num2str_sign(parameters.MS.MAP.par(i),'%.3f')  '$ $('];
        if parameters.CI.PL(i,1) > -6
            str = [str num2str_sign(parameters.CI.PL(i,1),'%.3f')  ','];
        else
            str = [str '<-6.0 ,'];
        end
        if parameters.CI.PL(i,2) < +6
            str = [str num2str_sign(parameters.CI.PL(i,2),'%.3f')  ')$'];
        else
            str = [str '>+6.0 )$'];
        end
        str = [str ' & '];
          
        % log_10(s*Erk_0)
        i = 7;
        str = [str '\\multicolumn{2}{c|}{$' num2str_sign(parameters.MS.MAP.par(i),'%.3f')  '$ $('];
        if parameters.CI.PL(i,1) > -6
            str = [str num2str_sign(parameters.CI.PL(i,1),'%.3f')  ','];
        else
            str = [str '<-6.0 ,'];
        end
        if parameters.CI.PL(i,2) < +6
            str = [str num2str_sign(parameters.CI.PL(i,2),'%.3f')  ')$}        '];
        else
            str = [str '>+6.0 )$}        '];
        end

    elseif ~isempty(strfind(model_specification{model_ind,1},'Erk0'))
        % log_10(k_3*TrkA_0)
        i = 5;
        str = [str '\\multicolumn{2}{c|}{$' num2str_sign(parameters.MS.MAP.par(i),'%.3f')  '$ $('];
        if parameters.CI.PL(i,1) > -6
            str = [str num2str_sign(parameters.CI.PL(i,1),'%.3f')  ','];
        else
            str = [str '<-6.0 ,'];
        end
        if parameters.CI.PL(i,2) < +6
            str = [str num2str_sign(parameters.CI.PL(i,2),'%.3f')  ')$}        '];
        else
            str = [str '>+6.0 )$}        '];
        end
        str = [str ' & '];
        
        % log_10(k_5)
        i = 4;
        str = [str '$' num2str_sign(parameters.MS.MAP.par(i),'%.3f')  '$ $('];
        if parameters.CI.PL(i,1) > -6
            str = [str num2str_sign(parameters.CI.PL(i,1),'%.3f')  ','];
        else
            str = [str '<-6.0 ,'];
        end
        if parameters.CI.PL(i,2) < +6
            str = [str num2str_sign(parameters.CI.PL(i,2),'%.3f')  ')$'];
        else
            str = [str '>+6.0 )$'];
        end
        str = [str ' & '];
        
        % log_10(s*Erk_0)
        if parameters.MS.MAP.par(6) < parameters.MS.MAP.par(7) 
            i1 = 6;
            i2 = 7;
        else
            i1 = 7;
            i2 = 6;
        end
        %
        i = i1;
        str = [str '$' num2str_sign(parameters.MS.MAP.par(i),'%.3f')  '$ $('];
        if parameters.CI.PL(i,1) > -6
            str = [str num2str_sign(parameters.CI.PL(i,1),'%.3f')  ','];
        else
            str = [str '<-6.0 ,'];
        end
        if parameters.CI.PL(i,2) < +6
            str = [str num2str_sign(parameters.CI.PL(i,2),'%.3f')  ')$'];
        else
            str = [str '>+6.0 )$'];
        end
        str = [str ' & '];
        %
        i = i2;
        str = [str '$' num2str_sign(parameters.MS.MAP.par(i),'%.3f')  '$ $('];
        if parameters.CI.PL(i,1) > -6
            str = [str num2str_sign(parameters.CI.PL(i,1),'%.3f')  ','];
        else
            str = [str '<-6.0 ,'];
        end
        if parameters.CI.PL(i,2) < +6
            str = [str num2str_sign(parameters.CI.PL(i,2),'%.3f')  ')$'];
        else
            str = [str '>+6.0 )$'];
        end
        
    else
        % log_10(k_3*TrkA_0)
        i = 5;
        str = [str '\\multicolumn{2}{c|}{$' num2str_sign(parameters.MS.MAP.par(i),'%.3f')  '$ $('];
        if parameters.CI.PL(i,1) > -6
            str = [str num2str_sign(parameters.CI.PL(i,1),'%.3f')  ','];
        else
            str = [str '<-6.0 ,'];
        end
        if parameters.CI.PL(i,2) < +6
            str = [str num2str_sign(parameters.CI.PL(i,2),'%.3f')  ')$}        '];
        else
            str = [str '>+6.0 )$}        '];
        end
        str = [str ' & '];
        
        % log_10(k_5)
        i = 4;
        str = [str '$' num2str_sign(parameters.MS.MAP.par(i),'%.3f')  '$ $('];
        if parameters.CI.PL(i,1) > -6
            str = [str num2str_sign(parameters.CI.PL(i,1),'%.3f')  ','];
        else
            str = [str '<-6.0 ,'];
        end
        if parameters.CI.PL(i,2) < +6
            str = [str num2str_sign(parameters.CI.PL(i,2),'%.3f')  ')$'];
        else
            str = [str '>+6.0 )$'];
        end
        str = [str ' & '];
        
        % log_10(s*Erk_0)
        i = 6;
        str = [str '\\multicolumn{2}{c|}{$' num2str_sign(parameters.MS.MAP.par(i),'%.3f')  '$ $('];
        if parameters.CI.PL(i,1) > -6
            str = [str num2str_sign(parameters.CI.PL(i,1),'%.3f')  ','];
        else
            str = [str '<-6.0 ,'];
        end
        if parameters.CI.PL(i,2) < +6
            str = [str num2str_sign(parameters.CI.PL(i,2),'%.3f')  ')$}        '];
        else
            str = [str '>+6.0 )$}        '];
        end
    end
    str = [str ' \\\\ \\hline '];
    
    % Line break
    if (mod(model_ind,3) == 0) && (model_ind ~= length(model_specification))
        str = [str ' \\hline \n'];
    else
        str = [str ' \n'];
    end
end

% Print to screen
fprintf(str)
disp(' ');
disp(' ');


% Table 3
offset = [7;7;7;9;9;9;9;9;9];

str_t{1} = ['\\hline \n' ...
            '& $\\log_{10}(\\sigma_{1,t=0\\,\\text{min}})$ & $\\log_{10}(\\sigma_{1,t=5\\,\\text{min}})$ & $\\log_{10}(\\sigma_{1,t=15\\,\\text{min}})$ & $\\log_{10}(\\sigma_{1,t=30\\,\\text{min}})$ & $\\log_{10}(\\sigma_{1,t=60\\,\\text{min}})$ \\\\ \\hline \\hline\n'];

str_t{2} = ['\\hline \n' ...
            '& $\\log_{10}(\\sigma_{2,t=0\\,\\text{min}})$ & $\\log_{10}(\\sigma_{2,t=5\\,\\text{min}})$ & $\\log_{10}(\\sigma_{2,t=15\\,\\text{min}})$ & $\\log_{10}(\\sigma_{2,t=30\\,\\text{min}})$ & $\\log_{10}(\\sigma_{2,t=60\\,\\text{min}})$ \\\\ \\hline \\hline\n'];

for model_ind = 1:length(model_specification)
    % Load results
    load(['./project/results/' model_specification{model_ind,1} '_all']);
    
    % Write model name
    str_t{1} = [str_t{1} model_specification{model_ind,2} ' & '];
    str_t{2} = [str_t{2} model_specification{model_ind,2} ' & '];
    
    o = offset(model_ind);
    % 
    if ~isempty(strfind(model_specification{model_ind,1},'TrkA'))
        if parameters.MS.MAP.par(5) < parameters.MS.MAP.par(6) 
            i1 = 1;
            i2 = 2;
        else
            i1 = 2;
            i2 = 1;
        end

        %
        str_t{i1} = [str_t{i1} ...
            '$' num2str_sign(parameters.MS.MAP.par(o+   0),'%.3f')  '$ $(' num2str_sign(parameters.CI.PL(o+   0,1),'%.3f') ',' num2str_sign(parameters.CI.PL(o+   0,2),'%.3f') ')$ & ' ...
            '$' num2str_sign(parameters.MS.MAP.par(o+   1),'%.3f')  '$ $(' num2str_sign(parameters.CI.PL(o+   1,1),'%.3f') ',' num2str_sign(parameters.CI.PL(o+   1,2),'%.3f') ')$ & ' ...
            '$' num2str_sign(parameters.MS.MAP.par(o+   2),'%.3f')  '$ $(' num2str_sign(parameters.CI.PL(o+   2,1),'%.3f') ',' num2str_sign(parameters.CI.PL(o+   2,2),'%.3f') ')$ & ' ...
            '$' num2str_sign(parameters.MS.MAP.par(o+   3),'%.3f')  '$ $(' num2str_sign(parameters.CI.PL(o+   3,1),'%.3f') ',' num2str_sign(parameters.CI.PL(o+   3,2),'%.3f') ')$ & ' ...
            '$' num2str_sign(parameters.MS.MAP.par(o+   4),'%.3f')  '$ $(' num2str_sign(parameters.CI.PL(o+   4,1),'%.3f') ',' num2str_sign(parameters.CI.PL(o+   4,2),'%.3f') ')$ ' ...
            ];
        %
        str_t{i2} = [str_t{i2} ...
            '$' num2str_sign(parameters.MS.MAP.par(o+ 5+0),'%.3f')  '$ $(' num2str_sign(parameters.CI.PL(o+ 5+0,1),'%.3f') ',' num2str_sign(parameters.CI.PL(o+ 5+0,2),'%.3f') ')$ & ' ...
            '$' num2str_sign(parameters.MS.MAP.par(o+ 5+1),'%.3f')  '$ $(' num2str_sign(parameters.CI.PL(o+ 5+1,1),'%.3f') ',' num2str_sign(parameters.CI.PL(o+ 5+1,2),'%.3f') ')$ & ' ...
            '$' num2str_sign(parameters.MS.MAP.par(o+ 5+2),'%.3f')  '$ $(' num2str_sign(parameters.CI.PL(o+ 5+2,1),'%.3f') ',' num2str_sign(parameters.CI.PL(o+ 5+2,2),'%.3f') ')$ & ' ...
            '$' num2str_sign(parameters.MS.MAP.par(o+ 5+3),'%.3f')  '$ $(' num2str_sign(parameters.CI.PL(o+ 5+3,1),'%.3f') ',' num2str_sign(parameters.CI.PL(o+ 5+3,2),'%.3f') ')$ & ' ...
            '$' num2str_sign(parameters.MS.MAP.par(o+ 5+4),'%.3f')  '$ $(' num2str_sign(parameters.CI.PL(o+ 5+4,1),'%.3f') ',' num2str_sign(parameters.CI.PL(o+ 5+4,2),'%.3f') ')$ ' ...
            ];

    elseif ~isempty(strfind(model_specification{model_ind,1},'Erk0'))
        if parameters.MS.MAP.par(6) < parameters.MS.MAP.par(7) 
            i1 = 1;
            i2 = 2;
        else
            i1 = 2;
            i2 = 1;
        end

        %
        str_t{i1} = [str_t{i1} ...
            '$' num2str_sign(parameters.MS.MAP.par(o+   0),'%.3f')  '$ $(' num2str_sign(parameters.CI.PL(o+   0,1),'%.3f') ',' num2str_sign(parameters.CI.PL(o+   0,2),'%.3f') ')$ & ' ...
            '$' num2str_sign(parameters.MS.MAP.par(o+   1),'%.3f')  '$ $(' num2str_sign(parameters.CI.PL(o+   1,1),'%.3f') ',' num2str_sign(parameters.CI.PL(o+   1,2),'%.3f') ')$ & ' ...
            '$' num2str_sign(parameters.MS.MAP.par(o+   2),'%.3f')  '$ $(' num2str_sign(parameters.CI.PL(o+   2,1),'%.3f') ',' num2str_sign(parameters.CI.PL(o+   2,2),'%.3f') ')$ & ' ...
            '$' num2str_sign(parameters.MS.MAP.par(o+   3),'%.3f')  '$ $(' num2str_sign(parameters.CI.PL(o+   3,1),'%.3f') ',' num2str_sign(parameters.CI.PL(o+   3,2),'%.3f') ')$ & ' ...
            '$' num2str_sign(parameters.MS.MAP.par(o+   4),'%.3f')  '$ $(' num2str_sign(parameters.CI.PL(o+   4,1),'%.3f') ',' num2str_sign(parameters.CI.PL(o+   4,2),'%.3f') ')$ ' ...
            ];
        %
        str_t{i2} = [str_t{i2} ...
            '$' num2str_sign(parameters.MS.MAP.par(o+ 5+0),'%.3f')  '$ $(' num2str_sign(parameters.CI.PL(o+ 5+0,1),'%.3f') ',' num2str_sign(parameters.CI.PL(o+ 5+0,2),'%.3f') ')$ & ' ...
            '$' num2str_sign(parameters.MS.MAP.par(o+ 5+1),'%.3f')  '$ $(' num2str_sign(parameters.CI.PL(o+ 5+1,1),'%.3f') ',' num2str_sign(parameters.CI.PL(o+ 5+1,2),'%.3f') ')$ & ' ...
            '$' num2str_sign(parameters.MS.MAP.par(o+ 5+2),'%.3f')  '$ $(' num2str_sign(parameters.CI.PL(o+ 5+2,1),'%.3f') ',' num2str_sign(parameters.CI.PL(o+ 5+2,2),'%.3f') ')$ & ' ...
            '$' num2str_sign(parameters.MS.MAP.par(o+ 5+3),'%.3f')  '$ $(' num2str_sign(parameters.CI.PL(o+ 5+3,1),'%.3f') ',' num2str_sign(parameters.CI.PL(o+ 5+3,2),'%.3f') ')$ & ' ...
            '$' num2str_sign(parameters.MS.MAP.par(o+ 5+4),'%.3f')  '$ $(' num2str_sign(parameters.CI.PL(o+ 5+4,1),'%.3f') ',' num2str_sign(parameters.CI.PL(o+ 5+4,2),'%.3f') ')$ ' ...
            ];

    else

        %
        str_t{1} = [str_t{1} ...
            '$' num2str_sign(parameters.MS.MAP.par(o+   0),'%.3f')  '$ $(' num2str_sign(parameters.CI.PL(o+   0,1),'%.3f') ',' num2str_sign(parameters.CI.PL(o+   0,2),'%.3f') ')$ & ' ...
            '$' num2str_sign(parameters.MS.MAP.par(o+   1),'%.3f')  '$ $(' num2str_sign(parameters.CI.PL(o+   1,1),'%.3f') ',' num2str_sign(parameters.CI.PL(o+   1,2),'%.3f') ')$ & ' ...
            '$' num2str_sign(parameters.MS.MAP.par(o+   2),'%.3f')  '$ $(' num2str_sign(parameters.CI.PL(o+   2,1),'%.3f') ',' num2str_sign(parameters.CI.PL(o+   2,2),'%.3f') ')$ & ' ...
            '$' num2str_sign(parameters.MS.MAP.par(o+   3),'%.3f')  '$ $(' num2str_sign(parameters.CI.PL(o+   3,1),'%.3f') ',' num2str_sign(parameters.CI.PL(o+   3,2),'%.3f') ')$ & ' ...
            '$' num2str_sign(parameters.MS.MAP.par(o+   4),'%.3f')  '$ $(' num2str_sign(parameters.CI.PL(o+   4,1),'%.3f') ',' num2str_sign(parameters.CI.PL(o+   4,2),'%.3f') ')$ ' ...
            ];
        %
        str_t{2} = [str_t{2} ...
            '$-$                        & ' ...
            '$-$                        & ' ...
            '$-$                        & ' ...
            '$-$                        & ' ...
            '$-$                        ' ...
            ];

    end
    
    str_t{1} = [str_t{1} ' \\\\ \\hline '];
    str_t{2} = [str_t{2} ' \\\\ \\hline '];
    
    % Line break
    if (mod(model_ind,3) == 0) && (model_ind ~= length(model_specification))
        str_t{1} = [str_t{1} ' \\hline \n'];
        str_t{2} = [str_t{2} ' \\hline \n'];
    else
        str_t{1} = [str_t{1} ' \n'];
        str_t{2} = [str_t{2} ' \n'];
    end
end

% Print to screen
fprintf([...
    '\\centering \n'...
    '\\begin{tabular}{|c||c|c|c|c|c|} \n'...
    '\\multicolumn{6}{c}{\\bf Subpopulation 1} \\\\[1ex] \n'...
    str_t{1} ...
    '\\end{tabular} \n'...
    '%% \n'...
    '\\\\[3ex] \n'...
    '%% \n'...
    '\\begin{tabular}{|c||c|c|c|c|c|} \n'...
    '\\multicolumn{6}{c}{\\bf Subpopulation 2} \\\\[1ex] \n'...
    str_t{2} ...
    '\\end{tabular} \n' ...
    '\\end{table*} \n \n \n'
    ]);


% Table 4
offset = [7+5;7+5;7+5;9+10;9+10;9+10;9+10;9+10;9+10];

str_t{1} = ['\\hline \n' ...
            '& $\\log_{10}(\\sigma_{1,[\\NGF]_0=0\\,\\text{nM}})$ & $\\log_{10}(\\sigma_{1,[\\NGF]_0=0.001\\,\\text{nM}})$ & $\\log_{10}(\\sigma_{1,[\\NGF]_0=0.01\\,\\text{nM}})$ & $\\log_{10}(\\sigma_{1,[\\NGF]_0=0.1\\,\\text{nM}})$ & $\\log_{10}(\\sigma_{1,[\\NGF]_0=1\\,\\text{nM}})$ & $\\log_{10}(\\sigma_{1,[\\NGF]_0=10\\,\\text{nM}})$ \\\\ \\hline \\hline\n'];

str_t{2} = ['\\hline \n' ...
            '& $\\log_{10}(\\sigma_{2,[\\NGF]_0=0\\,\\text{nM}})$ & $\\log_{10}(\\sigma_{2,[\\NGF]_0=0.001\\,\\text{nM}})$ & $\\log_{10}(\\sigma_{2,[\\NGF]_0=0.01\\,\\text{nM}})$ & $\\log_{10}(\\sigma_{2,[\\NGF]_0=0.1\\,\\text{nM}})$ & $\\log_{10}(\\sigma_{2,[\\NGF]_0=1\\,\\text{nM}})$ & $\\log_{10}(\\sigma_{2,[\\NGF]_0=10\\,\\text{nM}})$ \\\\ \\hline \\hline\n'];

for model_ind = 1:length(model_specification)
    % Load results
    load(['./project/results/' model_specification{model_ind,1} '_all']);
    
    % Write model name
    str_t{1} = [str_t{1} model_specification{model_ind,2} ' & '];
    str_t{2} = [str_t{2} model_specification{model_ind,2} ' & '];
    
    o = offset(model_ind);
    % 
    if ~isempty(strfind(model_specification{model_ind,1},'TrkA'))
        if parameters.MS.MAP.par(5) < parameters.MS.MAP.par(6) 
            i1 = 1;
            i2 = 2;
        else
            i1 = 2;
            i2 = 1;
        end

        %
        str_t{i1} = [str_t{i1} ...
            '$' num2str_sign(parameters.MS.MAP.par(o+   0),'%.3f')  '$ $(' num2str_sign(parameters.CI.PL(o+   0,1),'%.3f') ',' num2str_sign(parameters.CI.PL(o+   0,2),'%.3f') ')$ & ' ...
            '$' num2str_sign(parameters.MS.MAP.par(o+   1),'%.3f')  '$ $(' num2str_sign(parameters.CI.PL(o+   1,1),'%.3f') ',' num2str_sign(parameters.CI.PL(o+   1,2),'%.3f') ')$ & ' ...
            '$' num2str_sign(parameters.MS.MAP.par(o+   2),'%.3f')  '$ $(' num2str_sign(parameters.CI.PL(o+   2,1),'%.3f') ',' num2str_sign(parameters.CI.PL(o+   2,2),'%.3f') ')$ & ' ...
            '$' num2str_sign(parameters.MS.MAP.par(o+   3),'%.3f')  '$ $(' num2str_sign(parameters.CI.PL(o+   3,1),'%.3f') ',' num2str_sign(parameters.CI.PL(o+   3,2),'%.3f') ')$ & ' ...
            '$' num2str_sign(parameters.MS.MAP.par(o+   4),'%.3f')  '$ $(' num2str_sign(parameters.CI.PL(o+   4,1),'%.3f') ',' num2str_sign(parameters.CI.PL(o+   4,2),'%.3f') ')$ & ' ...
            '$' num2str_sign(parameters.MS.MAP.par(o+   5),'%.3f')  '$ $(' num2str_sign(parameters.CI.PL(o+   5,1),'%.3f') ',' num2str_sign(parameters.CI.PL(o+   5,2),'%.3f') ')$ ' ...
            ];
        %
        str_t{i2} = [str_t{i2} ...
            '$' num2str_sign(parameters.MS.MAP.par(o+ 6+0),'%.3f')  '$ $(' num2str_sign(parameters.CI.PL(o+ 6+0,1),'%.3f') ',' num2str_sign(parameters.CI.PL(o+ 6+0,2),'%.3f') ')$ & ' ...
            '$' num2str_sign(parameters.MS.MAP.par(o+ 6+1),'%.3f')  '$ $(' num2str_sign(parameters.CI.PL(o+ 6+1,1),'%.3f') ',' num2str_sign(parameters.CI.PL(o+ 6+1,2),'%.3f') ')$ & ' ...
            '$' num2str_sign(parameters.MS.MAP.par(o+ 6+2),'%.3f')  '$ $(' num2str_sign(parameters.CI.PL(o+ 6+2,1),'%.3f') ',' num2str_sign(parameters.CI.PL(o+ 6+2,2),'%.3f') ')$ & ' ...
            '$' num2str_sign(parameters.MS.MAP.par(o+ 6+3),'%.3f')  '$ $(' num2str_sign(parameters.CI.PL(o+ 6+3,1),'%.3f') ',' num2str_sign(parameters.CI.PL(o+ 6+3,2),'%.3f') ')$ & ' ...
            '$' num2str_sign(parameters.MS.MAP.par(o+ 6+4),'%.3f')  '$ $(' num2str_sign(parameters.CI.PL(o+ 6+4,1),'%.3f') ',' num2str_sign(parameters.CI.PL(o+ 6+4,2),'%.3f') ')$ & ' ...
            '$' num2str_sign(parameters.MS.MAP.par(o+ 6+5),'%.3f')  '$ $(' num2str_sign(parameters.CI.PL(o+ 6+5,1),'%.3f') ',' num2str_sign(parameters.CI.PL(o+ 6+5,2),'%.3f') ')$ ' ...
            ];

    elseif ~isempty(strfind(model_specification{model_ind,1},'Erk0'))
        if parameters.MS.MAP.par(6) < parameters.MS.MAP.par(7) 
            i1 = 1;
            i2 = 2;
        else
            i1 = 2;
            i2 = 1;
        end

        %
        str_t{i1} = [str_t{i1} ...
            '$' num2str_sign(parameters.MS.MAP.par(o+   0),'%.3f')  '$ $(' num2str_sign(parameters.CI.PL(o+   0,1),'%.3f') ',' num2str_sign(parameters.CI.PL(o+   0,2),'%.3f') ')$ & ' ...
            '$' num2str_sign(parameters.MS.MAP.par(o+   1),'%.3f')  '$ $(' num2str_sign(parameters.CI.PL(o+   1,1),'%.3f') ',' num2str_sign(parameters.CI.PL(o+   1,2),'%.3f') ')$ & ' ...
            '$' num2str_sign(parameters.MS.MAP.par(o+   2),'%.3f')  '$ $(' num2str_sign(parameters.CI.PL(o+   2,1),'%.3f') ',' num2str_sign(parameters.CI.PL(o+   2,2),'%.3f') ')$ & ' ...
            '$' num2str_sign(parameters.MS.MAP.par(o+   3),'%.3f')  '$ $(' num2str_sign(parameters.CI.PL(o+   3,1),'%.3f') ',' num2str_sign(parameters.CI.PL(o+   3,2),'%.3f') ')$ & ' ...
            '$' num2str_sign(parameters.MS.MAP.par(o+   4),'%.3f')  '$ $(' num2str_sign(parameters.CI.PL(o+   4,1),'%.3f') ',' num2str_sign(parameters.CI.PL(o+   4,2),'%.3f') ')$ & ' ...
            '$' num2str_sign(parameters.MS.MAP.par(o+   5),'%.3f')  '$ $(' num2str_sign(parameters.CI.PL(o+   5,1),'%.3f') ',' num2str_sign(parameters.CI.PL(o+   5,2),'%.3f') ')$ ' ...
            ];
        %
        str_t{i2} = [str_t{i2} ...
            '$' num2str_sign(parameters.MS.MAP.par(o+ 6+0),'%.3f')  '$ $(' num2str_sign(parameters.CI.PL(o+ 6+0,1),'%.3f') ',' num2str_sign(parameters.CI.PL(o+ 6+0,2),'%.3f') ')$ & ' ...
            '$' num2str_sign(parameters.MS.MAP.par(o+ 6+1),'%.3f')  '$ $(' num2str_sign(parameters.CI.PL(o+ 6+1,1),'%.3f') ',' num2str_sign(parameters.CI.PL(o+ 6+1,2),'%.3f') ')$ & ' ...
            '$' num2str_sign(parameters.MS.MAP.par(o+ 6+2),'%.3f')  '$ $(' num2str_sign(parameters.CI.PL(o+ 6+2,1),'%.3f') ',' num2str_sign(parameters.CI.PL(o+ 6+2,2),'%.3f') ')$ & ' ...
            '$' num2str_sign(parameters.MS.MAP.par(o+ 6+3),'%.3f')  '$ $(' num2str_sign(parameters.CI.PL(o+ 6+3,1),'%.3f') ',' num2str_sign(parameters.CI.PL(o+ 6+3,2),'%.3f') ')$ & ' ...
            '$' num2str_sign(parameters.MS.MAP.par(o+ 6+4),'%.3f')  '$ $(' num2str_sign(parameters.CI.PL(o+ 6+4,1),'%.3f') ',' num2str_sign(parameters.CI.PL(o+ 6+4,2),'%.3f') ')$ & ' ...
            '$' num2str_sign(parameters.MS.MAP.par(o+ 6+5),'%.3f')  '$ $(' num2str_sign(parameters.CI.PL(o+ 6+5,1),'%.3f') ',' num2str_sign(parameters.CI.PL(o+ 6+5,2),'%.3f') ')$ ' ...
            ];

    else

        %
        str_t{1} = [str_t{1} ...
            '$' num2str_sign(parameters.MS.MAP.par(o+   0),'%.3f')  '$ $(' num2str_sign(parameters.CI.PL(o+   0,1),'%.3f') ',' num2str_sign(parameters.CI.PL(o+   0,2),'%.3f') ')$ & ' ...
            '$' num2str_sign(parameters.MS.MAP.par(o+   1),'%.3f')  '$ $(' num2str_sign(parameters.CI.PL(o+   1,1),'%.3f') ',' num2str_sign(parameters.CI.PL(o+   1,2),'%.3f') ')$ & ' ...
            '$' num2str_sign(parameters.MS.MAP.par(o+   2),'%.3f')  '$ $(' num2str_sign(parameters.CI.PL(o+   2,1),'%.3f') ',' num2str_sign(parameters.CI.PL(o+   2,2),'%.3f') ')$ & ' ...
            '$' num2str_sign(parameters.MS.MAP.par(o+   3),'%.3f')  '$ $(' num2str_sign(parameters.CI.PL(o+   3,1),'%.3f') ',' num2str_sign(parameters.CI.PL(o+   3,2),'%.3f') ')$ & ' ...
            '$' num2str_sign(parameters.MS.MAP.par(o+   4),'%.3f')  '$ $(' num2str_sign(parameters.CI.PL(o+   4,1),'%.3f') ',' num2str_sign(parameters.CI.PL(o+   4,2),'%.3f') ')$ & ' ...
            '$' num2str_sign(parameters.MS.MAP.par(o+   5),'%.3f')  '$ $(' num2str_sign(parameters.CI.PL(o+   5,1),'%.3f') ',' num2str_sign(parameters.CI.PL(o+   5,2),'%.3f') ')$ ' ...
            ];
        %
        str_t{2} = [str_t{2} ...
            '$-$                        & ' ...
            '$-$                        & ' ...
            '$-$                        & ' ...
            '$-$                        & ' ...
            '$-$                        & ' ...
            '$-$                        ' ...
            ];

    end
    
    str_t{1} = [str_t{1} ' \\\\ \\hline '];
    str_t{2} = [str_t{2} ' \\\\ \\hline '];
    
    % Line break
    if (mod(model_ind,3) == 0) && (model_ind ~= length(model_specification))
        str_t{1} = [str_t{1} ' \\hline \n'];
        str_t{2} = [str_t{2} ' \\hline \n'];
    else
        str_t{1} = [str_t{1} ' \n'];
        str_t{2} = [str_t{2} ' \n'];
    end
end

% Print to screen
fprintf([...
    '\\centering \n'...
    '\\begin{tabular}{|c||c|c|c|c|c|c|} \n'...
    '\\multicolumn{7}{c}{\\bf Subpopulation 1} \\\\[1ex] \n'...
    str_t{1} ...
    '\\end{tabular} \n'...
    '%% \n'...
    '\\\\[3ex] \n'...
    '%% \n'...
    '\\begin{tabular}{|c||c|c|c|c|c|c|} \n'...
    '\\multicolumn{7}{c}{\\bf Subpopulation 2} \\\\[1ex] \n'...
    str_t{2} ...
    '\\end{tabular} \n' ...
    '\\end{table*} \n \n \n'
    ]);
