% function fh = plotODEMix_2_paper(D,M1,M2,xi,options)
function fh = plotODEMix_2_paper(varargin)

%% Assign inputs
D = varargin{1};
if nargin >= 3
    M = varargin{2};
    xi = varargin{3};
else
    M = [];
    xi = [];
end

% Set defaults
options.type = 'kde';
options.model.col = {'r','b'};
options.model.col_s{1}{1} = [1.0,0.5,0.5];
options.model.col_s{1}{2} = [0.5,0.0,0.0];
options.model.col_s{2}{1} = [0.5,0.5,1.0];
options.model.col_s{2}{2} = [0.0,0.0,0.5];
options.model.ls = {'-','--'};
options.model.lw  = 2;
options.model.lw_s  = 0.5;
options.model.points = 100;
options.model.plot = 'continuous'; % 'hist'
options.data.plot = 'filled'; %'empty'
options.data.col  = 'b';
options.data.fill_col = 0.7*[1,1,1];
options.data.lw   = 2;
options.data.bins = 100;
options.x_scale = 'lin';
options.fs = [12 14];
for e = 1:length(D)
    options.boundaries(e).y_min = [];
    options.boundaries(e).y_max = [];
    options.ylabel{e} = 'frequency';
    options.z_max{e} = [];
end
if nargin == 4
    options = setdefault(varargin{4},options);
end

%% Introduction
if ~isempty(M)
    for m = 1:length(M)
        for s = 1:M{m}.N_subpop
            theta{m}{s} = M{m}.theta{s}(xi{m});
            dthetadxi{m}{s} = M{m}.dthetadxi{s}(xi{m});
            w{m}{s} = M{m}.w{s}(xi{m});
            dwdxi{m}{s} = M{m}.dwdxi{s}(xi{m});
        end
    end
end

%% Visualization
% Open figure
fh = figure;
% Loop: Experimental conditions
for e = 1:length(D)
    % Plot
    switch D(e).type
        % Time response
        case 'kinetic'
            % Simulation
            if ~isempty(M)
                for m = 1:length(M)
                    for s = 1:M{m}.N_subpop
                        [X,dXdtheta] = M{m}.model(D(e).t,theta{m}{s},D(e).u);
                        mu{m}{s} = M{m}.mu{s,e}(D(e).t,X,xi{m},D(e).u);
                        sigma{m}{s} = M{m}.sigma{s,e,1}(D(e).t,X,xi{m},D(e).u);
                    end
                end
            end
            % Boundaries
            if isempty(options.boundaries(e).y_min) || isempty(options.boundaries(e).y_max)
                y_min{e} =  inf;
                y_max{e} = -inf;
                for k = 1:length(D(e).t)
                    y = D(e).y(k,:)';
                    y = y(~isnan(y));
                    y_min{e} = min(y_min{e},min(y));
                    y_max{e} = max(y_max{e},max(y));
                end
            else
                y_min{e} = options.boundaries(e).y_min;
                y_max{e} = options.boundaries(e).y_max;
            end
            switch options.x_scale
                case 'lin'
                    y_hist = linspace(y_min{e},y_max{e},options.data.bins+1)';
                    d_y_hist = y_hist(2)-y_hist(1);
                    y_grid = linspace(y_min{e},y_max{e},options.model.points+1)';
                    d_y_grid = y_grid(2)-y_grid(1);
                case 'log'
                    z_hist = linspace(log10(y_min{e}),log10(y_max{e}),options.data.bins+1)';
                    d_y_hist = (z_hist(2)-z_hist(1));
                    y_hist = 10.^z_hist;
                    z_grid = linspace(log10(y_min{e}),log10(y_max{e}),options.model.points+1)';
                    d_y_grid = (z_grid(2)-z_grid(1));
                    y_grid = 10.^z_grid;
            end
            % Evaluation of probability density
            for k = 1:length(D(e).t)
                %subplot(6,length(D),(k-1)*length(D)+e);
%                subplot('Position',[0.11,(6-k)*0.149+0.08,0.36,0.13]+[0.015,0,0,0]);
                subplot('Position',[0.11,(6-k)*0.125+0.2,0.36,0.125*0.125/0.149]+[0.015,0,0,0]);
                % Data
                y = D(e).y(k,:)';
                y = y(~isnan(y));
                h = hist(y,y_hist);
                h = (h(1:end-1)'/sum(h(1:end-1)));
                % Density calculation
                if ~isempty(M)
                    for m = 1:length(M)
                        p{m} = zeros(size(y_grid));
                        cp{m} = zeros(size(y_grid));
                        for s = 1:M{m}.N_subpop
                            p{m} = p{m} + w{m}{s}*pdf(M{m}.distribution{s},y_grid,mu{m}{s}(k),sigma{m}{s}(k));
                            cp{m} = cp{m} + w{m}{s}*cdf(M{m}.distribution{s},y_grid,mu{m}{s}(k),sigma{m}{s}(k));
                            p_s{m}{s} = w{m}{s}*pdf(M{m}.distribution{s},y_grid,mu{m}{s}(k),sigma{m}{s}(k));
                            cp_s{m}{s} = w{m}{s}*cdf(M{m}.distribution{s},y_grid,mu{m}{s}(k),sigma{m}{s}(k));
                        end
                    end
                end
                % Plot
                switch options.data.plot
                    case 'filled'
                        lh(1) = fill(y_hist(round(0.5:0.5:length(y_hist))),[0;h(round(0.5:0.5:length(h)));0],options.data.fill_col); hold on;
                    case 'empty'
                        lh(1) = plot(y_hist(round(0.5:0.5:length(y_hist))),[0;h(round(0.5:0.5:length(h)));0],...
                            '-','color',options.data.col,'linewidth',options.data.lw); hold on;
                end
                if ~isempty(M)
                    for m = 1:length(M)
                        switch options.model.plot
                            case 'continuous'
                                switch options.x_scale
                                    case 'lin'
                                        for s = 1:M{m}.N_subpop
                                            lh(3*(m-1)+s+2) = plot(y_grid,p_s{m}{s}*d_y_hist,options.model.ls{m},'color',options.model.col_s{m}{s},'linewidth',options.model.lw_s);
                                        end
                                        lh(3*(m-1)+2) = plot(y_grid,p{m}*d_y_hist,options.model.ls{m},'color',options.model.col{m},'linewidth',options.model.lw);
                                    case 'log'
                                        for s = 1:M{m}.N_subpop
                                            lh(3*(m-1)+s+2) = plot(y_grid,p_s{m}{s}.*y_grid*d_y_hist*log(10),options.model.ls{m},'color',options.model.col_s{m}{s},'linewidth',options.model.lw_s);
                                        end
                                        lh(3*(m-1)+2) = plot(y_grid,p{m}.*y_grid*d_y_hist*log(10),options.model.ls{m},'color',options.model.col{m},'linewidth',options.model.lw);
                                end
                            case 'hist'
                                h_sim = diff(cp{m})*d_y_hist/d_y_grid;
                                plot(y_grid(round(0.5:0.5:length(y_hist))),[0;h_sim(round(0.5:0.5:length(h_sim)));0],...
                                     options.model.ls{m},'color',options.model.col{m},'linewidth',options.model.lw); hold on;
                        end
                    end
                end
                % Label
                ylabel(options.ylabel{e});
                xlim([y_min{e},y_max{e}]);
                if ~isempty(options.z_max{e})
                    ylim([0,options.z_max{e}]);
                end
                text(0.12,0.05,['\bf t = ' num2str(D(e).t(k)) ' min'],'fontsize',options.fs(2),'HorizontalAlignment','left');
                set(gca,'xscale',options.x_scale);
                set(gca,'xtick',[0.1:0.1:0.9,1:1:9,10:10:100]);
                set(gca,'ytick',0:0.02:0.06);
                if k == 1
                    text(3,0.0719,['\bf Kinetic for [NGF]_0 = 1 nM'],'fontsize',options.fs(2)+1,'HorizontalAlignment','center');
                end
                if k ~= length(D(e).t)
                    set(gca,'xticklabel',[]);
                else
                    set(gca,'xticklabel',{'0.1','','','','','','','','','1','','','','','','','','','10','','','','','','','','','100'});
                    xlabel(D(e).measurand);
                end
                
%                 % Data
%                 if (e == 1) && (k == 1)
%                     if isempty(M)
%                         %legend('data')
%                     else
%                         legend(options.legend,'Position',[0.28,0.03,0.1,0.10]); legend('boxoff');
%                     end
%                 end
                  if k == 1
                    text(0.07,-0.408,'\bf Model M_{H3,2}:');
                    legend(lh(2:4),{'overall','subpopulation 1','subpopulation 2'},'Position',[0.2,0.01,0.1,0.1]); legend('boxoff');
                  elseif k == 2
                    text(1050,-0.335,'\bf Model M_{H3,3}:');
                    legend(lh(5:7),{'overall','subpopulation 1','subpopulation 2'},'Position',[0.7,0.01,0.1,0.1]); legend('boxoff');
                  elseif k == 3
                    text(0.07,-0.212,'\bf Measurement data:');
                    legend(lh(1),{'overall'},'Position',[0.14,0.16,0.1,0.03]); legend('boxoff');
                  end
            end

        % Dose response
        case 'dose response'
            % Boundaries
            if isempty(options.boundaries(e).y_min) || isempty(options.boundaries(e).y_max)
                y_min{e} =  inf;
                y_max{e} = -inf;
                for d = 1:length(D(e).u)
                    y = D(e).y(k,:)';
                    y = y(~isnan(y));
                    h = hist(y,y_hist);
                    h = (h(1:end-1)'/sum(h(1:end-1)));
                end
            else
                y_min{e} = options.boundaries(e).y_min;
                y_max{e} = options.boundaries(e).y_max;
            end
            y_grid = linspace(y_min{e},y_max{e},options.model.points)';
            switch options.x_scale
                case 'lin'
                    y_hist = linspace(y_min{e},y_max{e},options.data.bins+1)';
                    d_y_hist = y_hist(2)-y_hist(1);
                    y_grid = linspace(y_min{e},y_max{e},options.model.points+1)';
                    d_y_grid = y_grid(2)-y_grid(1);
                case 'log'
                    z_hist = linspace(log10(y_min{e}),log10(y_max{e}),options.data.bins+1)';
                    d_y_hist = (z_hist(2)-z_hist(1));
                    y_hist = 10.^z_hist;
                    z_grid = linspace(log10(y_min{e}),log10(y_max{e}),options.model.points+1)';
                    d_y_grid = (z_grid(2)-z_grid(1));
                    y_grid = 10.^z_grid;
            end
            % Loop: Doses
            for d = 1:length(D(e).u)
                %subplot(6,length(D),(d-1)*length(D)+e);
                %subplot('Position',[0.61,(6-d)*0.149+0.08,0.36,0.13]+[0.015,0,0,0]);
                subplot('Position',[0.61,(6-d)*0.125+0.2,0.36,0.125*0.125/0.149]+[0.015,0,0,0]);
                % Data
                y = D(e).y(d,:)';
                y = y(~isnan(y));
                h = hist(y,y_hist);
                h = (h(1:end-1)'/sum(h(1:end-1)));
                % Density calculation
                if ~isempty(M)
                    for m = 1:length(M)
                        p{m} = zeros(size(y_grid));
                        cp{m} = zeros(size(y_grid));
                        for s = 1:M{m}.N_subpop
                            % Simulation
                            [X,dXdtheta] = M{m}.model(D(e).t,theta{m}{s},D(e).u(d));
                            mu{m}{s} = M{m}.mu{s,e}(D(e).t,X,xi{m},D(e).u(d));
                            sigma{m}{s} = M{m}.sigma{s,e}(D(e).t,X,xi{m},D(e).u(d));
                            % Evaluation of probability density
                            p{m} = p{m} + w{m}{s}*pdf(M{m}.distribution{s},y_grid,mu{m}{s},sigma{m}{s});
                            cp{m} = cp{m} + w{m}{s}*cdf(M{m}.distribution{s},y_grid,mu{m}{s},sigma{m}{s});
                            p_s{m}{s} = w{m}{s}*pdf(M{m}.distribution{s},y_grid,mu{m}{s},sigma{m}{s});
                            cp_s{m}{s} = w{m}{s}*cdf(M{m}.distribution{s},y_grid,mu{m}{s},sigma{m}{s});
                        end
                    end
                end
                % Plot
                switch options.data.plot
                    case 'filled'
                        fill(y_hist(round(0.5:0.5:length(y_hist))),[0;h(round(0.5:0.5:length(h)));0],options.data.fill_col); hold on;
                    case 'empty'
                        plot(y_hist(round(0.5:0.5:length(y_hist))),[0;h(round(0.5:0.5:length(h)));0],...
                            '-','color',options.data.col,'linewidth',options.data.lw); hold on;
                end
                if ~isempty(M)
                    for m = 1:length(M)
                        switch options.model.plot
                            case 'continuous'
                                switch options.x_scale
                                    case 'lin'
                                        for s = 1:M{m}.N_subpop
                                            plot(y_grid,p_s{m}{s}*d_y_hist,options.model.ls{m},'color',options.model.col_s{m}{s},'linewidth',options.model.lw_s);
                                        end
                                        plot(y_grid,p{m}*d_y_hist,options.model.ls{m},'color',options.model.col{m},'linewidth',options.model.lw);
                                    case 'log'
                                        for s = 1:M{m}.N_subpop
                                            plot(y_grid,p_s{m}{s}.*y_grid*d_y_hist*log(10),options.model.ls{m},'color',options.model.col_s{m}{s},'linewidth',options.model.lw_s);
                                        end
                                        plot(y_grid,p{m}.*y_grid*d_y_hist*log(10),options.model.ls{m},'color',options.model.col{m},'linewidth',options.model.lw);
                                end
                            case 'hist'
                                h_sim = diff(cp{m})*d_y_hist/d_y_grid;
                                plot(y_grid(round(0.5:0.5:length(y_hist))),[0;h_sim(round(0.5:0.5:length(h_sim)));0],...
                                     options.model.ls{m},'color',options.model.col{m},'linewidth',options.model.lw); hold on;
                        end
                    end
                end
                % Label
                ylabel(options.ylabel{e});
                xlim([y_min{e},y_max{e}]);
                if ~isempty(options.z_max{e})
                    ylim([0,options.z_max{e}]);
                end
                text(0.12,0.046,['\bf [NGF]_0 = ' num2str(D(e).u(d)) ' nM'],'fontsize',options.fs(2),'HorizontalAlignment','left');
                set(gca,'xscale',options.x_scale);
                set(gca,'xtick',[0.1:0.1:0.9,1:1:9,10:10:100]);
                set(gca,'ytick',0:0.02:0.06);
                if d == 1
                    text(3,0.078,['\bf Dose response for t = 30 min'],'fontsize',options.fs(2)+1,'HorizontalAlignment','center');
                end
                if d ~= length(D(e).u)
                    set(gca,'xticklabel',[]);
                else
                    xlabel(D(e).measurand);
                    set(gca,'xticklabel',{'0.1','','','','','','','','','1','','','','','','','','','10','','','','','','','','','100'});
                end
                % Data
                if (e == 1) && (d == 1)
                    if isempty(M)
                        %legend('data')
                    else
                        legend('data','model')
                    end
                end
           end
    end
end