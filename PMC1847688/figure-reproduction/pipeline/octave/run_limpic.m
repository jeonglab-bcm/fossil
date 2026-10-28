% Run LIMPIC 1.1 (Additional File 1) on Additional Files 2 and 3.
% Usage: octave-cli run_limpic.m <limpic_dir> <invitro_dir> <plasma_dir> <outdir>
args=argv(); limpic=args{1}; invitro=args{2}; plasma=args{3}; out=args{4};
here=fileparts(mfilename('fullpath'));
addpath(limpic); addpath(here); addpath(fullfile(here,'shim'));   % shim shadows read_txt and kurtosis
warning('off','all');
global LIMPIC_FILES LIMPIC_NEXT

function write_classes(f,lv,la)
  fid=fopen(f,'w'); fprintf(fid,'mz,n'); fprintf(fid,',s%d',1:rows(la)); fprintf(fid,'\n');
  fprintf(fid,[repmat('%.6f,',1,1) '%d' repmat(',%.6f',1,rows(la)) '\n'],[lv; sum(la>0,1); la]);
  fclose(fid);
end

% Plasma: multiple_spectra.m on P_1..P_30, ppm 300, PDR 0.5 (the authors' function, unmodified).
LIMPIC_FILES=arrayfun(@(i) sprintf('%s/P_%d.txt',plasma,i),1:30,'UniformOutput',false); LIMPIC_NEXT=1;
[lv,la,sel]=multiple_spectra(30,300,0.5);
write_classes(fullfile(out,'plasma_classes.csv'),lv,la);

% Plasma: per-spectrum peaks with their SNR (Eq. 4 against LIMPIC's noise level).
fid=fopen(fullfile(out,'plasma_peaks.csv'),'w'); fprintf(fid,'spectrum,mz,intensity,noise,sigma\n');
for i=1:30
  r=limpic_spectrum(LIMPIC_FILES{i});
  sigma=r.norm_factor*interp1([r.xr(1) r.x_int r.xr(end)],[r.s_int(1) r.s_int 0],r.xr);
  p=r.peak_point;
  fprintf(fid,'%d,%.2f,%.6f,%.6f,%.6f\n',[i*ones(1,numel(p)); r.xr(p); r.wxrbn(p); r.noise_lev(p); sigma(p)]);
  if i==15
    % The example spectrum of Figs 2 to 8.
    s=r; m=numel(s.xr);
    dlmwrite(fullfile(out,'p15_raw.csv'),[s.x' s.w' s.wx'],'precision','%.6f');
    dlmwrite(fullfile(out,'p15_processed.csv'),[s.xr' s.wxr' s.baseline' s.wxrbn' s.noise_lev'],'precision','%.6f');
    dlmwrite(fullfile(out,'p15_blocks.csv'),[s.x_int' s.m_int' s.v_int' s.s_int'],'precision','%.6f');
    dlmwrite(fullfile(out,'p15_norm.csv'),s.norm_factor,'precision','%.10f');
    sm=[];
    for f=[10 20 30 40]
      sm=[sm prepro(s.w,f)'];
    end
    dlmwrite(fullfile(out,'p15_smooth.csv'),[s.x' sm],'precision','%.6f');
  end
end
fclose(fid);

% In vitro: each concentration (5 replicates) separately, as in Tables 1 to 3.
conc={'2.5','5','7.5','10','25','50'};
fid=fopen(fullfile(out,'invitro_peaks.csv'),'w'); fprintf(fid,'conc,replicate,file,mz,intensity\n');
for c=1:numel(conc)
  d=dir(fullfile(invitro,['SOL_' conc{c} '_TXT'],'*.txt')); files=sort({d.name});
  paths=cellfun(@(f) fullfile(invitro,['SOL_' conc{c} '_TXT'],f),files,'UniformOutput',false);
  for i=1:numel(paths)
    r=limpic_spectrum(paths{i}); p=r.peak_point;
    for j=1:numel(p), fprintf(fid,'%s,%d,%s,%.2f,%.6f\n',conc{c},i,files{i},r.xr(p(j)),r.wxrbn(p(j))); end
  end
  LIMPIC_FILES=paths; LIMPIC_NEXT=1;
  [lv,la,sel]=multiple_spectra(numel(paths),300,0.5);
  write_classes(fullfile(out,sprintf('invitro_%s_classes.csv',conc{c})),lv,la);
end
fclose(fid);
printf('done\n');
