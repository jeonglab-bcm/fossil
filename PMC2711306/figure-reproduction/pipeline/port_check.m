% Run the authors' embed_novi.m (kuchaev.com/Denoising, fetched by fetch_inputs.sh) under Octave on
% a numbered edge list and write the coordinates for each dimension.
% Usage: octave --no-gui port_check.m AUTHORS_DIR SHIMS_DIR EDGES.txt OUT_PREFIX DIMS...
args = argv();
addpath(args{1}); addpath(args{2});
A = dlmread(args{3});
for k = 5:numel(args)
  dimen = str2double(args{k});
  tic; L = embed_novi(A, dimen); t = toc;
  dlmwrite(sprintf('%s_dim%d.txt', args{4}, dimen), L, 'precision', '%.10g');
  printf('dim %d: %d nodes, %.1f s\n', dimen, size(L, 1), t);
end
