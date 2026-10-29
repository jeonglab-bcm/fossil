clc;

xi = parameters.MS.MAP.par%+0.0001*rand(size(parameters.MS.MAP.par));
%xi = (parameters.max+parameters.min)/2;

[logL,dlogLdxi] = logLikelihood(xi,M,D);

eps = 1e-3;
logLi = zeros(length(xi),1);
for i = 1:length(xi)
    xii = xi; xii(i) = xi(i) + eps;
    [logLi(i)] = logLikelihood(xii,M,D);
end

S = [(logLi - logL)/eps,dlogLdxi,(logLi - logL)/eps-dlogLdxi]

