function r=limpic_spectrum(file,factor)
% The steps of LIMPIC 1.1 single_spectrum.m, calling the authors' functions with their
% settings, but returning every intermediate signal for the figures.
if nargin < 2, factor=20; end
data=load_spectrum(file);
r.x=data(51:end,1)'; r.w=data(51:end,2)';           % read_txt.m: first 50 points dropped
r.wx=prepro(r.w,factor);                             % "Kaiser" smoothing
[r.wxr,r.xr]=resample_sig(r.wx,r.x,0.25);
[r.int,r.x_int,r.v_int,r.m_int,r.s_int]=find_intervals(r.wxr,r.xr,round(100/0.25));
[r.wxrb,r.baseline]=rem_baseline(r.wxr,r.xr,r.m_int,r.x_int);
[r.wxrbn,r.norm_factor]=normalize(r.wxrb,r.xr,16952.25);
r.noise_lev=estimate_noise(r.xr,r.s_int,(r.v_int-r.m_int),r.x_int,3,r.norm_factor);
r.peak_point=find_peaks(r.wxrbn,r.noise_lev,ceil(0.5/0.25));
