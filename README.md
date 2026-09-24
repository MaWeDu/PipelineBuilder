# 🤖 ML Pipeline Builder & Evaluator

Eine interaktive Streamlit-App zum Erstellen, Trainieren und Bewerten
von Machine-Learning-Pipelines für CSV- und Excel-Daten.

Die App unterstützt sowohl **Klassifikation** als auch **Regression**
und kombiniert Datenvorverarbeitung, Modelltraining, Cross-Validation,
Hyperparameter-Suche, Modellvergleich und Feature Importance in einer
Oberfläche.

## Funktionen

-   Upload von **CSV-, XLSX- und XLS-Dateien**
-   Auswahl von Excel-Tabellenblättern
-   Automatische Erkennung auffälliger Header
-   Automatische Erkennung möglicher ID-Spalten
-   Auswahl von Target und Features
-   Automatische Erkennung von Klassifikation oder Regression
-   Train/Test-Split mit konfigurierbarer Testgröße
-   Optionaler stratified Split bei Klassifikation
-   Behandlung fehlender Werte mit Mean- oder Median-Imputation
-   Skalierung mit:
    -   StandardScaler
    -   RobustScaler
    -   MinMaxScaler
-   One-Hot-Encoding für kategoriale Features

## Unterstützte Modelle

### Klassifikation

-   Logistic Regression
-   K-Nearest Neighbors (KNN)
-   Decision Tree
-   Random Forest

### Regression

-   Linear Regression
-   Ridge Regression
-   Random Forest Regressor

## Modellbewertung

### Klassifikation

Die App berechnet unter anderem:

-   Accuracy
-   Balanced Accuracy
-   Precision
-   Recall
-   F1-Score
-   Classification Report
-   Confusion Matrix

### Regression

Die App berechnet:

-   R²
-   MAE
-   MSE
-   RMSE
-   MAPE, sofern sinnvoll berechenbar
-   Actual-vs.-Predicted-Plot
-   Residual Plot

## Cross-Validation

Optional kann eine Cross-Validation durchgeführt werden.

Unterstützt werden:

-   3 Folds
-   5 Folds
-   10 Folds
-   Repeated Cross-Validation

Für Klassifikationsprobleme wird eine stratified Cross-Validation
verwendet. Die App zeigt Mittelwert, Standardabweichung, Minimum und
Maximum der Scores sowie die einzelnen Fold-Ergebnisse grafisch und
tabellarisch an.

## Modellvergleich

Mehrere geeignete Modelle können automatisch mit derselben
Cross-Validation verglichen werden.

Für Klassifikation werden standardmäßig Logistic Regression, KNN,
Decision Tree und Random Forest verglichen.

Für Regression werden Linear Regression, Ridge Regression und Random
Forest Regressor verglichen.

## Hyperparameter-Suche

Die App unterstützt:

-   Grid Search
-   Randomized Search

Die Suche wird auf der vollständigen Scikit-Learn-Pipeline ausgeführt.
Dadurch bleiben Imputation, Skalierung und Encoding innerhalb der
jeweiligen Trainingsschritte.

## Feature Importance

Die App kann eine modellübergreifende **Permutation Feature Importance**
berechnen und die wichtigsten Features tabellarisch und grafisch
darstellen.

## Installation

### 1. Repository klonen

``` bash
git clone <DEIN-REPOSITORY>
cd PipelineBuilder
```

### 2. Abhängigkeiten installieren

``` bash
pip install -r requirements.txt
```

Die verwendeten Abhängigkeiten sind:

``` text
streamlit
pandas>=2.2,<3.0
numpy>=2.2,<2.4
matplotlib>=3.8,<=3.10
scikit-learn
openpyxl
xlrd
setuptools<81
```

## App lokal starten

``` bash
streamlit run streamlit_app.py
```

Alternativ:

``` bash
python -m streamlit run streamlit_app.py
```

Danach ist die App standardmäßig unter folgender lokalen Adresse
erreichbar:

``` text
http://localhost:8501
```

## Verwendung

1.  CSV- oder Excel-Datei hochladen.
2.  Bei Excel-Dateien das gewünschte Tabellenblatt auswählen.
3.  Target-Spalte festlegen.
4.  Gewünschte Features auswählen.
5.  Klassifikation, Regression oder Auto-Detect auswählen.
6.  Testgröße, Random Seed, Scaler und Imputer konfigurieren.
7.  Modell und gegebenenfalls Hyperparameter auswählen.
8.  Optional Cross-Validation, Modellvergleich, Feature Importance oder
    Hyperparameter-Suche aktivieren.
9.  **Train Pipeline & Evaluate** anklicken.
10. Ergebnisse, Metriken und Diagramme auswerten.

## Streamlit Community Cloud

Die App kann direkt über Streamlit Community Cloud veröffentlicht
werden.

Dafür sollten sich mindestens diese Dateien im GitHub-Repository
befinden:

``` text
streamlit_app.py
requirements.txt
README.md
```

Beim Deployment:

``` text
Branch: main
Main file path: streamlit_app.py
```

Streamlit installiert anschließend automatisch die Pakete aus
`requirements.txt`.

## Projektstruktur

``` text
PipelineBuilder/
├── streamlit_app.py
├── requirements.txt
├── README.md
└── LICENSE
```

## Hinweise

Die automatische Task-Erkennung dient als Unterstützung. Bei einem
numerischen Target mit vielen unterschiedlichen Werten wird
standardmäßig Regression angenommen; ansonsten Klassifikation.

ID-Spalten werden nach heuristischen Regeln erkannt und standardmäßig
nicht als Features ausgewählt. Die Auswahl kann in der Oberfläche
angepasst werden.

Bei kleinen oder stark unausgeglichenen Datensätzen können
Cross-Validation oder Stratification fehlschlagen, wenn einzelne Klassen
nicht genügend Beobachtungen enthalten.

MAPE ist bei tatsächlichen Zielwerten von `0` nicht sinnvoll definiert.
In diesem Fall zeigt die App für MAPE keinen Wert an.

Grid Search und Randomized Search können je nach Datenmenge, Modell und
Suchraum deutlich mehr Rechenzeit benötigen.

## Technologie

-   Python
-   Streamlit
-   pandas
-   NumPy
-   Matplotlib
-   scikit-learn
-   openpyxl
-   xlrd

## Lizenz

Siehe `LICENSE` im Repository.
