# Document classifier report

Trained at 2026-11-13T08:30:53+00:00 on 1350 documents, 9 classes.

## Held-out templates

The test set uses one template per class that the model never saw during training.

- Accuracy: **1.000**
- Macro F1: **1.000**

| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| acordao | 1.00 | 1.00 | 1.00 | 30 |
| calculos | 1.00 | 1.00 | 1.00 | 25 |
| certidao_obito | 1.00 | 1.00 | 1.00 | 30 |
| certidao_transito_julgado | 1.00 | 1.00 | 1.00 | 25 |
| despacho | 1.00 | 1.00 | 1.00 | 25 |
| peticao | 1.00 | 1.00 | 1.00 | 25 |
| procuracao | 1.00 | 1.00 | 1.00 | 30 |
| sentenca | 1.00 | 1.00 | 1.00 | 25 |
| substabelecimento | 1.00 | 1.00 | 1.00 | 30 |

## 5-fold cross-validation (grouped by template)

- Accuracy: **0.866** ± 0.064
- Macro F1: **0.847** ± 0.073

## Confusion matrix (held-out templates)

Rows are true classes, columns are predicted classes.

| | acordao | calculos | certidao_obito | certidao_transito_julgado | despacho | peticao | procuracao | sentenca | substabelecimento |
|---|---|---|---|---|---|---|---|---|---|
| **acordao** | 30 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **calculos** | 0 | 25 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **certidao_obito** | 0 | 0 | 30 | 0 | 0 | 0 | 0 | 0 | 0 |
| **certidao_transito_julgado** | 0 | 0 | 0 | 25 | 0 | 0 | 0 | 0 | 0 |
| **despacho** | 0 | 0 | 0 | 0 | 25 | 0 | 0 | 0 | 0 |
| **peticao** | 0 | 0 | 0 | 0 | 0 | 25 | 0 | 0 | 0 |
| **procuracao** | 0 | 0 | 0 | 0 | 0 | 0 | 30 | 0 | 0 |
| **sentenca** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 25 | 0 |
| **substabelecimento** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 30 |
