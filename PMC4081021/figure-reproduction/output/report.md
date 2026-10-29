# PMC4081021 reproduction check

## Likelihood port

Python log-likelihood at the authors' 51 saved optima: max |difference| 8.8e-04 (required < 1e-2): PASS

## Tables

| Table | Fit | Rows | Fields matching | Exceptions (paper errors) |
| --- | --- | --- | --- | --- |
| table1_cr1 | saved | 12 | 59/60 | H3,1 logL |
| table1_cr1 | refit | 12 | 59/60 | H3,1 logL |
| table1_cr2 | saved | 12 | 57/60 | H1,1 rank, H1,2 rank, H1,3 rank |
| table1_cr2 | refit | 12 | 57/60 | H1,1 rank, H1,2 rank, H1,3 rank |
| table2 | saved | 9 | 45/45 | - |
| supp_table1_ngfA | saved | 9 | 45/45 | - |
| supp_table1_ngfB | saved | 9 | 45/45 | - |
| supp_table1_ngfC | saved | 9 | 45/45 | - |

## Figures (pixels within 4 px)

| Fit | Figure | Panel | Colour | Published matched | Ours matched | Required | |
| --- | --- | --- | --- | --- | --- | --- | --- |
| saved | fig2 | B | all_traces | 1.000 | 1.000 | 0.95 / 0.95 | PASS |
| saved | fig2 | B | (0.0, 0.0, 0.0) | 1.000 | 1.000 | 0.95 / 0.95 | PASS |
| saved | fig2 | C:0 | all_traces | 1.000 | 0.999 | 0.95 / 0.95 | PASS |
| saved | fig2 | C:0 | (0.7, 0.7, 0.7) | 0.940 | 0.992 | 0.9 / 0.95 | PASS |
| saved | fig2 | C:1 | all_traces | 1.000 | 1.000 | 0.95 / 0.95 | PASS |
| saved | fig2 | C:1 | (0.7, 0.7, 0.7) | 0.932 | 0.998 | 0.9 / 0.95 | PASS |
| saved | fig2 | C:2 | all_traces | 1.000 | 1.000 | 0.95 / 0.95 | PASS |
| saved | fig2 | C:2 | (0.7, 0.7, 0.7) | 0.927 | 0.991 | 0.9 / 0.95 | PASS |
| saved | fig2 | C:3 | all_traces | 1.000 | 1.000 | 0.95 / 0.95 | PASS |
| saved | fig2 | C:3 | (0.7, 0.7, 0.7) | 0.920 | 0.992 | 0.9 / 0.95 | PASS |
| saved | fig2 | C:4 | all_traces | 1.000 | 1.000 | 0.95 / 0.95 | PASS |
| saved | fig2 | C:4 | (0.7, 0.7, 0.7) | 0.914 | 0.996 | 0.9 / 0.95 | PASS |
| saved | fig2 | C:5 | all_traces | 1.000 | 1.000 | 0.95 / 0.95 | PASS |
| saved | fig2 | C:5 | (0.7, 0.7, 0.7) | 0.920 | 0.997 | 0.9 / 0.95 | PASS |
| saved | fig2 | D:k1_density | all_traces | 1.000 | 1.000 | 0.95 / 0.95 | PASS |
| saved | fig2 | D:k1_s1_estimate | (0.0, 0.0, 0.0) | 0.997 | 1.000 | 0.95 / 0.9 | PASS |
| saved | fig2 | D:k1_s2_estimate | (0.0, 0.0, 0.0) | 0.992 | 1.000 | 0.95 / 0.9 | PASS |
| saved | fig2 | D:k2_density | all_traces | 1.000 | 0.995 | 0.95 / 0.95 | PASS |
| saved | fig2 | D:k2_estimate | (0.0, 0.0, 0.0) | 1.000 | 0.992 | 0.95 / 0.9 | PASS |
| saved | fig2 | D:k3_density | all_traces | 1.000 | 0.992 | 0.95 / 0.95 | PASS |
| saved | fig2 | D:k3_estimate | (0.0, 0.0, 0.0) | 1.000 | 1.000 | 0.95 / 0.9 | PASS |
| saved | fig2 | D:w1_density | (0.0, 0.0, 0.0) | 0.958 | 1.000 | 0.95 / 0.95 | PASS |
| saved | fig2 | D:w1_estimate | (0.0, 0.0, 0.0) | 1.000 | 1.000 | 0.95 / 0.9 | PASS |
| saved | fig2 | E | all_traces | 0.982 | 0.888 | 0.95 / 0.85 | PASS |
| saved | fig2 | E | (0.0, 0.0, 0.0) | 1.000 | 1.000 | 0.95 / 0.95 | PASS |
| saved | fig2 | F:0 | all_traces | 1.000 | 1.000 | 0.95 / 0.95 | PASS |
| saved | fig2 | F:0 | (0.7, 0.7, 0.7) | 0.967 | 1.000 | 0.9 / 0.95 | PASS |
| saved | fig2 | F:1 | all_traces | 1.000 | 1.000 | 0.95 / 0.95 | PASS |
| saved | fig2 | F:1 | (0.7, 0.7, 0.7) | 0.967 | 0.999 | 0.9 / 0.95 | PASS |
| saved | fig2 | F:2 | all_traces | 1.000 | 1.000 | 0.95 / 0.95 | PASS |
| saved | fig2 | F:2 | (0.7, 0.7, 0.7) | 0.965 | 0.999 | 0.9 / 0.95 | PASS |
| saved | fig2 | F:3 | all_traces | 1.000 | 1.000 | 0.95 / 0.95 | PASS |
| saved | fig2 | F:3 | (0.7, 0.7, 0.7) | 0.967 | 0.999 | 0.9 / 0.95 | PASS |
| saved | fig2 | F:4 | all_traces | 1.000 | 1.000 | 0.95 / 0.95 | PASS |
| saved | fig2 | F:4 | (0.7, 0.7, 0.7) | 0.962 | 1.000 | 0.9 / 0.95 | PASS |
| saved | fig2 | F:5 | all_traces | 1.000 | 1.000 | 0.95 / 0.95 | PASS |
| saved | fig2 | F:5 | (0.7, 0.7, 0.7) | 0.969 | 1.000 | 0.9 / 0.95 | PASS |
| saved | fig2 | G:k1_density | all_traces | 1.000 | 1.000 | 0.95 / 0.95 | PASS |
| saved | fig2 | G:k1_s1_estimate | (0.0, 0.0, 0.0) | 0.998 | 1.000 | 0.95 / 0.9 | PASS |
| saved | fig2 | G:k1_s2_estimate | (0.0, 0.0, 0.0) | 0.999 | 0.957 | 0.95 / 0.9 | PASS |
| saved | fig2 | G:k2_density | all_traces | 1.000 | 1.000 | 0.95 / 0.95 | PASS |
| saved | fig2 | G:k2_estimate | (0.0, 0.0, 0.0) | 0.999 | 0.988 | 0.95 / 0.9 | PASS |
| saved | fig2 | G:k3_density | all_traces | 1.000 | 1.000 | 0.95 / 0.95 | PASS |
| saved | fig2 | G:k3_estimate | (0.0, 0.0, 0.0) | 1.000 | 1.000 | 0.95 / 0.9 | PASS |
| saved | fig2 | G:w1_density | (0.0, 0.0, 0.0) | 0.955 | 1.000 | 0.95 / 0.95 | PASS |
| saved | fig2 | G:w1_estimate | (0.0, 0.0, 0.0) | 0.999 | 0.910 | 0.95 / 0.9 | PASS |
| saved | fig3 | B:kinetic_0 | all_traces | 1.000 | 0.998 | 0.95 / 0.95 | PASS |
| saved | fig3 | B:kinetic_0 | (0.0, 0.0, 0.0) | 0.998 | 1.000 | 0.95 / 0.95 | PASS |
| saved | fig3 | B:kinetic_1 | all_traces | 1.000 | 0.999 | 0.95 / 0.95 | PASS |
| saved | fig3 | B:kinetic_1 | (0.0, 0.0, 0.0) | 0.999 | 1.000 | 0.95 / 0.95 | PASS |
| saved | fig3 | B:dose_0 | all_traces | 1.000 | 1.000 | 0.95 / 0.95 | PASS |
| saved | fig3 | B:dose_0 | (0.0, 0.0, 0.0) | 0.999 | 0.998 | 0.95 / 0.95 | PASS |
| saved | fig3 | B:dose_1 | all_traces | 1.000 | 0.998 | 0.95 / 0.95 | PASS |
| saved | fig3 | B:dose_1 | (0.0, 0.0, 0.0) | 0.999 | 1.000 | 0.95 / 0.95 | PASS |
| saved | fig3 | D:rates | (0.0, 0.0, 0.0) | 0.986 | 0.921 | 0.9 / 0.9 | PASS |
| saved | fig3 | C:kinetic_0 | all_traces | 1.000 | 0.999 | 0.85 / 0.95 | PASS |
| saved | fig3 | C:kinetic_0 | (0.7, 0.7, 0.7) | 0.921 | 1.000 | 0.8 / 0.95 | PASS |
| saved | fig3 | C:kinetic_1 | all_traces | 1.000 | 0.999 | 0.85 / 0.95 | PASS |
| saved | fig3 | C:kinetic_1 | (0.7, 0.7, 0.7) | 0.900 | 0.999 | 0.8 / 0.95 | PASS |
| saved | fig3 | C:kinetic_2 | all_traces | 1.000 | 0.998 | 0.85 / 0.95 | PASS |
| saved | fig3 | C:kinetic_2 | (0.7, 0.7, 0.7) | 0.894 | 1.000 | 0.8 / 0.95 | PASS |
| saved | fig3 | C:kinetic_3 | all_traces | 1.000 | 0.997 | 0.85 / 0.95 | PASS |
| saved | fig3 | C:kinetic_3 | (0.7, 0.7, 0.7) | 0.908 | 1.000 | 0.8 / 0.95 | PASS |
| saved | fig3 | C:kinetic_4 | all_traces | 1.000 | 0.997 | 0.85 / 0.95 | PASS |
| saved | fig3 | C:kinetic_4 | (0.7, 0.7, 0.7) | 0.886 | 1.000 | 0.8 / 0.95 | PASS |
| saved | fig3 | C:dose_0 | all_traces | 1.000 | 1.000 | 0.85 / 0.95 | PASS |
| saved | fig3 | C:dose_0 | (0.7, 0.7, 0.7) | 0.876 | 0.997 | 0.8 / 0.95 | PASS |
| saved | fig3 | C:dose_1 | all_traces | 1.000 | 1.000 | 0.85 / 0.95 | PASS |
| saved | fig3 | C:dose_1 | (0.7, 0.7, 0.7) | 0.852 | 0.995 | 0.8 / 0.95 | PASS |
| saved | fig3 | C:dose_2 | all_traces | 1.000 | 0.998 | 0.85 / 0.95 | PASS |
| saved | fig3 | C:dose_2 | (0.7, 0.7, 0.7) | 0.861 | 0.999 | 0.8 / 0.95 | PASS |
| saved | fig3 | C:dose_3 | all_traces | 1.000 | 0.990 | 0.85 / 0.95 | PASS |
| saved | fig3 | C:dose_3 | (0.7, 0.7, 0.7) | 0.843 | 1.000 | 0.8 / 0.95 | PASS |
| saved | fig3 | C:dose_4 | all_traces | 1.000 | 0.995 | 0.85 / 0.95 | PASS |
| saved | fig3 | C:dose_4 | (0.7, 0.7, 0.7) | 0.860 | 1.000 | 0.8 / 0.95 | PASS |
| saved | fig3 | C:dose_5 | all_traces | 1.000 | 0.998 | 0.85 / 0.95 | PASS |
| saved | fig3 | C:dose_5 | (0.7, 0.7, 0.7) | 0.857 | 0.999 | 0.8 / 0.95 | PASS |
| saved | fig4 | B:kinetic_0 | all_traces | 0.865 | 1.000 | 0.8 / 0.95 | PASS |
| saved | fig4 | B:kinetic_0 | (0.0, 0.0, 0.0) | 0.996 | 1.000 | 0.95 / 0.95 | PASS |
| saved | fig4 | B:kinetic_1 | all_traces | 0.863 | 1.000 | 0.8 / 0.95 | PASS |
| saved | fig4 | B:kinetic_1 | (0.0, 0.0, 0.0) | 0.995 | 1.000 | 0.95 / 0.95 | PASS |
| saved | fig4 | B:dose_0 | all_traces | 0.814 | 0.998 | 0.8 / 0.95 | PASS |
| saved | fig4 | B:dose_0 | (0.0, 0.0, 0.0) | 1.000 | 1.000 | 0.95 / 0.95 | PASS |
| saved | fig4 | B:dose_1 | all_traces | 0.821 | 0.999 | 0.8 / 0.95 | PASS |
| saved | fig4 | B:dose_1 | (0.0, 0.0, 0.0) | 0.999 | 1.000 | 0.95 / 0.95 | PASS |
| saved | fig4 | D:rates | (0.0, 0.0, 0.0) | 0.994 | 0.953 | 0.9 / 0.9 | PASS |
| saved | fig4 | D:w1 | (0.0, 0.0, 0.0) | 1.000 | 0.957 | 0.9 / 0.9 | PASS |
| saved | fig4 | C:kinetic_0 | all_traces | 0.983 | 1.000 | 0.85 / 0.95 | PASS |
| saved | fig4 | C:kinetic_0 | (0.7, 0.7, 0.7) | 0.906 | 0.999 | 0.8 / 0.95 | PASS |
| saved | fig4 | C:kinetic_1 | all_traces | 0.978 | 0.999 | 0.85 / 0.95 | PASS |
| saved | fig4 | C:kinetic_1 | (0.7, 0.7, 0.7) | 0.922 | 0.998 | 0.8 / 0.95 | PASS |
| saved | fig4 | C:kinetic_2 | all_traces | 0.956 | 1.000 | 0.85 / 0.95 | PASS |
| saved | fig4 | C:kinetic_2 | (0.7, 0.7, 0.7) | 0.889 | 0.998 | 0.8 / 0.95 | PASS |
| saved | fig4 | C:kinetic_3 | all_traces | 0.953 | 0.999 | 0.85 / 0.95 | PASS |
| saved | fig4 | C:kinetic_3 | (0.7, 0.7, 0.7) | 0.906 | 0.999 | 0.8 / 0.95 | PASS |
| saved | fig4 | C:kinetic_4 | all_traces | 0.951 | 1.000 | 0.85 / 0.95 | PASS |
| saved | fig4 | C:kinetic_4 | (0.7, 0.7, 0.7) | 0.891 | 0.999 | 0.8 / 0.95 | PASS |
| saved | fig4 | C:dose_0 | all_traces | 0.923 | 1.000 | 0.85 / 0.95 | PASS |
| saved | fig4 | C:dose_0 | (0.7, 0.7, 0.7) | 0.845 | 0.998 | 0.8 / 0.95 | PASS |
| saved | fig4 | C:dose_1 | all_traces | 0.921 | 1.000 | 0.85 / 0.95 | PASS |
| saved | fig4 | C:dose_1 | (0.7, 0.7, 0.7) | 0.820 | 0.999 | 0.8 / 0.95 | PASS |
| saved | fig4 | C:dose_2 | all_traces | 0.917 | 1.000 | 0.85 / 0.95 | PASS |
| saved | fig4 | C:dose_2 | (0.7, 0.7, 0.7) | 0.840 | 0.998 | 0.8 / 0.95 | PASS |
| saved | fig4 | C:dose_3 | all_traces | 0.916 | 0.998 | 0.85 / 0.95 | PASS |
| saved | fig4 | C:dose_3 | (0.7, 0.7, 0.7) | 0.866 | 0.996 | 0.8 / 0.95 | PASS |
| saved | fig4 | C:dose_4 | all_traces | 0.917 | 1.000 | 0.85 / 0.95 | PASS |
| saved | fig4 | C:dose_4 | (0.7, 0.7, 0.7) | 0.870 | 0.998 | 0.8 / 0.95 | PASS |
| saved | fig4 | C:dose_5 | all_traces | 0.898 | 1.000 | 0.85 / 0.95 | PASS |
| saved | fig4 | C:dose_5 | (0.7, 0.7, 0.7) | 0.852 | 0.995 | 0.8 / 0.95 | PASS |
| saved | fig5 | B | all_traces | 0.955 | 1.000 | 0.95 / 0.95 | PASS |
| saved | fig5 | B | (0.0, 0.0, 0.0) | 1.000 | 0.964 | 0.95 / 0.95 | PASS |
| saved | fig6 | A:scatter | (0.0, 0.0, 0.0) | 1.000 | 0.999 | 0.95 / 0.95 | PASS |
| saved | fig6 | B:scatter | (0.0, 0.0, 0.0) | 1.000 | 0.996 | 0.95 / 0.95 | PASS |
| saved | fig6 | B:scatter | all_traces | 1.000 | 1.000 | 0.95 / 0.95 | PASS |
| saved | fig6 | A:pErk_hist | (0.7, 0.7, 0.7) | 0.995 | 1.000 | 0.95 / 0.95 | PASS |
| saved | fig6 | A:Erk_hist | (0.7, 0.7, 0.7) | 0.994 | 0.999 | 0.95 / 0.95 | PASS |
| saved | fig6 | B:pErk_hist | all_traces | 1.000 | 1.000 | 0.95 / 0.95 | PASS |
| saved | fig6 | B:Erk_hist | all_traces | 1.000 | 1.000 | 0.95 / 0.95 | PASS |
| refit | fig2 | B | all_traces | 1.000 | 1.000 | 0.95 / 0.95 | PASS |
| refit | fig2 | B | (0.0, 0.0, 0.0) | 1.000 | 1.000 | 0.95 / 0.95 | PASS |
| refit | fig2 | C:0 | all_traces | 1.000 | 0.999 | 0.95 / 0.95 | PASS |
| refit | fig2 | C:0 | (0.7, 0.7, 0.7) | 0.940 | 0.992 | 0.9 / 0.95 | PASS |
| refit | fig2 | C:1 | all_traces | 1.000 | 1.000 | 0.95 / 0.95 | PASS |
| refit | fig2 | C:1 | (0.7, 0.7, 0.7) | 0.932 | 0.998 | 0.9 / 0.95 | PASS |
| refit | fig2 | C:2 | all_traces | 1.000 | 1.000 | 0.95 / 0.95 | PASS |
| refit | fig2 | C:2 | (0.7, 0.7, 0.7) | 0.927 | 0.991 | 0.9 / 0.95 | PASS |
| refit | fig2 | C:3 | all_traces | 1.000 | 1.000 | 0.95 / 0.95 | PASS |
| refit | fig2 | C:3 | (0.7, 0.7, 0.7) | 0.920 | 0.992 | 0.9 / 0.95 | PASS |
| refit | fig2 | C:4 | all_traces | 1.000 | 1.000 | 0.95 / 0.95 | PASS |
| refit | fig2 | C:4 | (0.7, 0.7, 0.7) | 0.914 | 0.996 | 0.9 / 0.95 | PASS |
| refit | fig2 | C:5 | all_traces | 1.000 | 1.000 | 0.95 / 0.95 | PASS |
| refit | fig2 | C:5 | (0.7, 0.7, 0.7) | 0.920 | 0.997 | 0.9 / 0.95 | PASS |
| refit | fig2 | D:k1_density | all_traces | 1.000 | 1.000 | 0.95 / 0.95 | PASS |
| refit | fig2 | D:k2_density | all_traces | 1.000 | 0.995 | 0.95 / 0.95 | PASS |
| refit | fig2 | D:k3_density | all_traces | 1.000 | 0.992 | 0.95 / 0.95 | PASS |
| refit | fig2 | D:w1_density | (0.0, 0.0, 0.0) | 0.958 | 1.000 | 0.95 / 0.95 | PASS |
| refit | fig2 | E | all_traces | 0.982 | 0.888 | 0.95 / 0.85 | PASS |
| refit | fig2 | E | (0.0, 0.0, 0.0) | 1.000 | 1.000 | 0.95 / 0.95 | PASS |
| refit | fig2 | F:0 | all_traces | 1.000 | 1.000 | 0.95 / 0.95 | PASS |
| refit | fig2 | F:0 | (0.7, 0.7, 0.7) | 0.967 | 1.000 | 0.9 / 0.95 | PASS |
| refit | fig2 | F:1 | all_traces | 1.000 | 1.000 | 0.95 / 0.95 | PASS |
| refit | fig2 | F:1 | (0.7, 0.7, 0.7) | 0.967 | 0.999 | 0.9 / 0.95 | PASS |
| refit | fig2 | F:2 | all_traces | 1.000 | 1.000 | 0.95 / 0.95 | PASS |
| refit | fig2 | F:2 | (0.7, 0.7, 0.7) | 0.965 | 0.999 | 0.9 / 0.95 | PASS |
| refit | fig2 | F:3 | all_traces | 1.000 | 1.000 | 0.95 / 0.95 | PASS |
| refit | fig2 | F:3 | (0.7, 0.7, 0.7) | 0.967 | 0.999 | 0.9 / 0.95 | PASS |
| refit | fig2 | F:4 | all_traces | 1.000 | 1.000 | 0.95 / 0.95 | PASS |
| refit | fig2 | F:4 | (0.7, 0.7, 0.7) | 0.962 | 1.000 | 0.9 / 0.95 | PASS |
| refit | fig2 | F:5 | all_traces | 1.000 | 1.000 | 0.95 / 0.95 | PASS |
| refit | fig2 | F:5 | (0.7, 0.7, 0.7) | 0.969 | 1.000 | 0.9 / 0.95 | PASS |
| refit | fig2 | G:k1_density | all_traces | 1.000 | 1.000 | 0.95 / 0.95 | PASS |
| refit | fig2 | G:k2_density | all_traces | 1.000 | 1.000 | 0.95 / 0.95 | PASS |
| refit | fig2 | G:k3_density | all_traces | 1.000 | 1.000 | 0.95 / 0.95 | PASS |
| refit | fig2 | G:w1_density | (0.0, 0.0, 0.0) | 0.955 | 1.000 | 0.95 / 0.95 | PASS |

## Numbers

- Fig. 5C, w1 of M_H3,3 (A, B, C): [68.8, 69.8, 70.0] % against published [68.8, 71.5, 70.0] %. A and C must match: PASS. B does not match any saved fit of pathway model B (M_H3,3 gives 69.8 %).
- Fig. 6: rho 0.895 and 0.696, mixture weights [68.04, 31.96] % (published 0.895, 0.696, 68.0 / 32.0 %): PASS

## Saved optima

49 of 51 saved optima checked with exact gradients; the largest gain of a local L-BFGS-B run started at a saved optimum is 5.9e-05 in log-likelihood.

**Overall: PASS**
