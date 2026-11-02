// Run RPISeq's two classifiers in Weka 3.7 as the paper's Methods set them.
//
//   RPISeq-RF:  RandomForest, 20 trees, 10 features per node (Weka's default seed 1).
//   RPISeq-SVM: SMO, normalized polykernel of order 2, C = 1.0, tolerance 0.001,
//               epsilon 1.0E-12, logistic models fitted to the outputs.
//
// Usage:
//   java RpiWeka cv    rf|svm DATA.arff FOLDS SEED OUT_PREFIX
//       Weka's stratified cross-validation (Evaluation.crossValidateModel). Writes
//       OUT_PREFIX.predictions.csv (row in DATA, fold, actual, P(interact)) and
//       OUT_PREFIX.summary.json (counts, accuracy, precision, recall, F-measure, AUC).
//   java RpiWeka train rf|svm TRAIN.arff TEST.arff OUT.csv
//       Train on all of TRAIN and write P(interact) for each row of TEST.
import java.io.*;
import java.util.*;
import weka.classifiers.AbstractClassifier;
import weka.classifiers.Classifier;
import weka.classifiers.Evaluation;
import weka.classifiers.meta.FilteredClassifier;
import weka.core.*;
import weka.filters.unsupervised.attribute.Remove;

public class RpiWeka {
    static Classifier make(String which) throws Exception {
        if (which.equals("rf"))
            return AbstractClassifier.forName("weka.classifiers.trees.RandomForest",
                Utils.splitOptions("-I 20 -K 10 -S 1"));
        if (which.equals("svm"))
            return AbstractClassifier.forName("weka.classifiers.functions.SMO",
                Utils.splitOptions("-C 1.0 -L 0.001 -P 1.0E-12 -N 0 -M -V -1 -W 1 -K "
                    + "\"weka.classifiers.functions.supportVector.NormalizedPolyKernel -C 250007 -E 2.0\""));
        throw new IllegalArgumentException(which);
    }

    static Instances load(String path) throws Exception {
        Instances d = new Instances(new BufferedReader(new FileReader(path)));
        d.setClassIndex(d.numAttributes() - 1);
        return d;
    }

    public static void main(String[] a) throws Exception {
        if (a[0].equals("cv")) cv(a[1], load(a[2]), Integer.parseInt(a[3]), Integer.parseInt(a[4]), a[5]);
        else if (a[0].equals("train")) train(a[1], load(a[2]), load(a[3]), a[4]);
        else throw new IllegalArgumentException(a[0]);
    }

    static void cv(String which, Instances data, int folds, int seed, String out) throws Exception {
        // Tag each row with its index as a first attribute that a Remove filter hides from the
        // classifier, so each prediction maps back to its row. The steps below are those of
        // Evaluation.crossValidateModel (randomize, stratify, trainCV with the same Random).
        Instances d = new Instances(data);
        d.insertAttributeAt(new Attribute("row"), 0);
        for (int i = 0; i < d.numInstances(); i++) d.instance(i).setValue(0, i);
        d.setClassIndex(d.numAttributes() - 1);
        Random random = new Random(seed);
        d.randomize(random);
        d.stratify(folds);
        Evaluation eval = new Evaluation(d);
        PrintWriter pw = new PrintWriter(new FileWriter(out + ".predictions.csv"));
        pw.println("row,fold,actual,p_interact");
        for (int f = 0; f < folds; f++) {
            Instances train = d.trainCV(folds, f, random);
            eval.setPriors(train);
            FilteredClassifier c = new FilteredClassifier();
            Remove rm = new Remove();
            rm.setAttributeIndices("1");
            c.setFilter(rm);
            c.setClassifier(make(which));
            c.buildClassifier(train);
            Instances test = d.testCV(folds, f);
            for (int i = 0; i < test.numInstances(); i++) {
                Instance inst = test.instance(i);
                double[] dist = c.distributionForInstance(inst);
                eval.evaluateModelOnceAndRecordPrediction(dist, inst);
                pw.printf(Locale.ROOT, "%d,%d,%d,%.17g%n", (int) inst.value(0), f, (int) inst.classValue(), dist[1]);
            }
        }
        pw.close();
        summary(eval, out + ".summary.json");
    }

    static void summary(Evaluation e, String path) throws Exception {
        PrintWriter pw = new PrintWriter(new FileWriter(path));
        pw.println("{");
        pw.printf(Locale.ROOT, "  \"weka\": \"%s\",%n", weka.core.Version.VERSION);
        pw.printf(Locale.ROOT, "  \"n\": %d,%n", (int) e.numInstances());
        pw.printf(Locale.ROOT, "  \"tp\": %d, \"fn\": %d, \"fp\": %d, \"tn\": %d,%n",
            (int) e.numTruePositives(1), (int) e.numFalseNegatives(1),
            (int) e.numFalsePositives(1), (int) e.numTrueNegatives(1));
        pw.printf(Locale.ROOT, "  \"accuracy\": %.17g,%n", e.pctCorrect());
        pw.printf(Locale.ROOT, "  \"precision\": %.17g, \"recall\": %.17g, \"f_measure\": %.17g,%n",
            e.precision(1), e.recall(1), e.fMeasure(1));
        pw.printf(Locale.ROOT, "  \"weighted_precision\": %.17g, \"weighted_recall\": %.17g, \"weighted_f_measure\": %.17g,%n",
            e.weightedPrecision(), e.weightedRecall(), e.weightedFMeasure());
        pw.printf(Locale.ROOT, "  \"auc\": %.17g%n", e.areaUnderROC(1));
        pw.println("}");
        pw.close();
    }

    static void train(String which, Instances train, Instances test, String out) throws Exception {
        Classifier c = make(which);
        c.buildClassifier(train);
        PrintWriter pw = new PrintWriter(new FileWriter(out));
        pw.println("row,p_interact");
        for (int i = 0; i < test.numInstances(); i++)
            pw.printf(Locale.ROOT, "%d,%.17g%n", i, c.distributionForInstance(test.instance(i))[1]);
        pw.close();
    }
}
