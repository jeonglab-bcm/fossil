function k=kurtosis(v,flag)
% Stand-in for the kurtosis LIMPIC 1.1 expects. find_intervals.m keeps blocks with
% kurtosis(block,0) < 1. MATLAB's and Octave's own kurtosis is 3 for Gaussian noise and
% never below 1, so with it no block passes and rem_baseline.m fails. The authors' run
% used an excess kurtosis (0 for Gaussian noise): with it, single_spectrum.m returns the
% 16 peaks of Figs 7 and 8 at the published positions and heights.
% Normalized excess kurtosis, biased estimator; flag is ignored.
v=v(:)-mean(v);
k=mean(v.^4)/mean(v.^2)^2-3;
