function D = dist(W)
% Shim for the Neural Network Toolbox function dist(W): Euclidean distances between the columns
% of W (the authors call dist(Loc') to get the distances between nodes).
  X = W';
  sq = sum(X.^2, 2);
  D = sqrt(max(bsxfun(@plus, sq, sq') - 2 * (X * X'), 0));
end
