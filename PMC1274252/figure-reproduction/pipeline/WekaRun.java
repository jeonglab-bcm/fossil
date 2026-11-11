// Runs Weka 3.4's ADTree the way the PROSPECTR download page describes
// (-B 15 -E -1, trained and tested on omim_trainingset.arff, then applied to the test sets)
// and writes everything the reproduction compares: the tree, the additive score of every
// instance, the Explorer-style 10-fold cross-validation (seed 1) and Weka's own statistics.
//
// usage: java -cp weka.jar:. WekaRun OUTDIR B E KEEP train.arff [name=test.arff ...]
//   KEEP is "all" or a comma-separated list of attribute names to keep (plus the class).
import java.io.*;
import java.util.*;
import weka.core.*;
import weka.classifiers.Evaluation;
import weka.classifiers.trees.ADTree;
import weka.classifiers.evaluation.*;
import weka.filters.Filter;
import weka.filters.unsupervised.attribute.Remove;

public class WekaRun {
  static class ScoringADTree extends ADTree {
    double score(Instance inst) { return predictionValueForInstance(inst, m_root, 0.0); }
  }

  static Instances load(String path, String keep) throws Exception {
    Instances d = new Instances(new BufferedReader(new FileReader(path)));
    d.setClassIndex(d.numAttributes() - 1);
    if (keep.equals("all")) return d;
    Set names = new HashSet(Arrays.asList(keep.split(",")));
    StringBuffer idx = new StringBuffer();
    for (int i = 0; i < d.numAttributes(); i++)
      if (i == d.classIndex() || names.contains(d.attribute(i).name()))
        idx.append(idx.length() == 0 ? "" : ",").append(i + 1);
    Remove r = new Remove();
    r.setAttributeIndices(idx.toString());
    r.setInvertSelection(true);
    r.setInputFormat(d);
    Instances out = Filter.useFilter(d, r);
    out.setClassIndex(out.numAttributes() - 1);
    return out;
  }

  static String num(double v) { return Double.toString(v); }

  // writes per-instance scores and returns a JSON object of Weka's statistics
  static String evaluate(ScoringADTree model, Instances train, Instances test, int[] index,
                         int[] fold, PrintWriter rows) throws Exception {
    Evaluation ev = new Evaluation(train);
    FastVector preds = new FastVector();
    for (int i = 0; i < test.numInstances(); i++) {
      Instance inst = test.instance(i);
      double[] dist = model.distributionForInstance(inst);
      ev.evaluateModelOnce(dist, inst);
      preds.addElement(new NominalPrediction(inst.classValue(), dist, inst.weight()));
      rows.println((index == null ? i : index[i]) + "\t" + (fold == null ? -1 : fold[i]) + "\t"
                   + test.classAttribute().value((int) inst.classValue()) + "\t" + num(model.score(inst)));
    }
    return stats(ev, preds);
  }

  static String stats(Evaluation ev, FastVector preds) throws Exception {
    ThresholdCurve tc = new ThresholdCurve();
    Instances curve = tc.getCurve(preds, 0);
    StringBuffer roc = new StringBuffer();
    int fpr = curve.attribute(ThresholdCurve.FP_RATE_NAME).index();
    int tpr = curve.attribute(ThresholdCurve.TP_RATE_NAME).index();
    int thr = curve.attribute(ThresholdCurve.THRESHOLD_NAME).index();
    for (int i = 0; i < curve.numInstances(); i++)
      roc.append(i == 0 ? "" : ",").append("[" + num(curve.instance(i).value(fpr)) + ","
                 + num(curve.instance(i).value(tpr)) + "," + num(curve.instance(i).value(thr)) + "]");
    double[][] cm = ev.confusionMatrix();
    return "{\"n\": " + num(ev.numInstances()) + ", \"pct_correct\": " + num(ev.pctCorrect())
      + ", \"kappa\": " + num(ev.kappa()) + ", \"precision_disease\": " + num(ev.precision(0))
      + ", \"recall_disease\": " + num(ev.recall(0)) + ", \"fp_rate_disease\": " + num(ev.falsePositiveRate(0))
      + ", \"auc_disease\": " + num(ThresholdCurve.getROCArea(curve))
      + ", \"confusion\": [[" + num(cm[0][0]) + "," + num(cm[0][1]) + "],[" + num(cm[1][0]) + "," + num(cm[1][1]) + "]]"
      + ", \"roc\": [" + roc + "]}";
  }

  public static void main(String[] a) throws Exception {
    File out = new File(a[0]); out.mkdirs();
    String[] opts = {"-B", a[1], "-E", a[2]};
    String keep = a[3];
    Instances train = load(a[4], keep);
    StringBuffer json = new StringBuffer("{\"options\": \"-B " + a[1] + " -E " + a[2] + "\"");

    ScoringADTree model = new ScoringADTree();
    model.setOptions((String[]) opts.clone());
    model.buildClassifier(train);
    PrintWriter tree = new PrintWriter(new FileWriter(new File(out, "tree.txt")));
    tree.println(model.toString()); tree.close();

    PrintWriter rows = new PrintWriter(new FileWriter(new File(out, "scores_training.tsv")));
    rows.println("index\tfold\tclass\tscore");
    json.append(", \"training\": " + evaluate(model, train, train, null, null, rows));
    rows.close();

    for (int t = 5; t < a.length; t++) {
      String[] nv = a[t].split("=", 2);
      Instances test = load(nv[1], keep);
      rows = new PrintWriter(new FileWriter(new File(out, "scores_" + nv[0] + ".tsv")));
      rows.println("index\tfold\tclass\tscore");
      json.append(", \"" + nv[0] + "\": " + evaluate(model, train, test, null, null, rows));
      rows.close();
    }

    // 10-fold cross-validation exactly as Evaluation.crossValidateModel with new Random(1),
    // keeping each instance's original row number and fold
    int folds = 10;
    Random random = new Random(1);
    Instances data = new Instances(train);
    IdentityHashMap orig = new IdentityHashMap();
    for (int i = 0; i < data.numInstances(); i++) orig.put(data.instance(i), new Integer(i));
    data.randomize(random);
    data.stratify(folds);
    int[] pos = new int[data.numInstances()];
    for (int i = 0; i < data.numInstances(); i++) pos[i] = ((Integer) orig.get(data.instance(i))).intValue();
    Evaluation cv = new Evaluation(data);
    FastVector preds = new FastVector();
    rows = new PrintWriter(new FileWriter(new File(out, "scores_cv.tsv")));
    rows.println("index\tfold\tclass\tscore");
    StringBuffer foldTrees = new StringBuffer();
    for (int f = 0; f < folds; f++) {
      Instances tr = data.trainCV(folds, f, random);
      Instances te = data.testCV(folds, f);
      ScoringADTree m = new ScoringADTree();
      m.setOptions((String[]) opts.clone());
      m.buildClassifier(tr);
      int n = data.numInstances() / folds, offset = data.numInstances() % folds;
      int first = f * n + (f < offset ? f : offset);
      for (int i = 0; i < te.numInstances(); i++) {
        Instance inst = te.instance(i);
        double[] dist = m.distributionForInstance(inst);
        cv.evaluateModelOnce(dist, inst);
        preds.addElement(new NominalPrediction(inst.classValue(), dist, inst.weight()));
        rows.println(pos[first + i] + "\t" + f + "\t" + te.classAttribute().value((int) inst.classValue()) + "\t" + num(m.score(inst)));
      }
    }
    rows.close();
    json.append(", \"cv10\": " + stats(cv, preds) + "}");
    PrintWriter js = new PrintWriter(new FileWriter(new File(out, "weka.json")));
    js.println(json); js.close();
  }
}
