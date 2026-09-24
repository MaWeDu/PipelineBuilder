import io
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, LogisticRegression, Ridge
from sklearn.metrics import classification_report, confusion_matrix, mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder, RobustScaler, StandardScaler
from sklearn.tree import DecisionTreeClassifier

st.set_page_config(page_title="ML Pipeline Builder", page_icon="🤖", layout="wide")
st.title("🤖 ML Pipeline Builder & Evaluator")
st.caption("CSV-/Excel-Upload, ID-Spaltenerkennung, Train/Test-Split, Scikit-Learn-Pipelines und visuelle Evaluation.")

def looks_like_bad_header(columns):
    columns = [str(col).strip() for col in columns]
    if not columns:
        return False
    suspicious = sum(
        1 for col in columns
        if col.lower().startswith("unnamed:")
        or re.fullmatch(r"column[_ ]?\d+", col.lower())
        or re.fullmatch(r"\d+", col.lower())
        or col.lower() in {"", "nan", "none", "null"}
    )
    return suspicious / len(columns) >= 0.8

def fix_misplaced_header(df):
    if looks_like_bad_header(df.columns) and not df.empty:
        first_row = df.iloc[0].astype(str).str.strip().tolist()
        if all(first_row) and len(first_row) == len(set(first_row)):
            df = df.iloc[1:].copy()
            df.columns = first_row
            df.reset_index(drop=True, inplace=True)
    return df

def detect_id_columns(df):
    id_cols = []
    for col in df.columns:
        name = str(col).lower()
        if name == "id" or name.endswith("_id") or name.startswith("id_") or "uuid" in name:
            id_cols.append(col)
        elif df[col].nunique(dropna=True) / max(len(df), 1) >= 0.98 and not pd.api.types.is_numeric_dtype(df[col]):
            id_cols.append(col)
    return id_cols

@st.cache_data(show_spinner=False)
def get_sheet_names(data):
    return pd.ExcelFile(io.BytesIO(data)).sheet_names

@st.cache_data(show_spinner=False)
def load_file(data, filename, sheet_name=None):
    ext = Path(filename).suffix.lower()
    if ext == ".csv":
        try:
            df = pd.read_csv(io.BytesIO(data), encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(io.BytesIO(data), encoding="cp1252")
    elif ext in {".xlsx", ".xls"}:
        df = pd.read_excel(io.BytesIO(data), sheet_name=sheet_name)
    else:
        raise ValueError(f"Nicht unterstütztes Format: {ext}")
    return fix_misplaced_header(df)

def resolve_task(df, target_col, requested):
    if requested != "Auto-Detect":
        return requested
    target = df[target_col]
    if pd.api.types.is_numeric_dtype(target) and target.nunique(dropna=True) > 15:
        return "Regression"
    return "Classification"

def make_estimator(model_name, seed, hp):
    if model_name == "Logistic Regression":
        return LogisticRegression(C=hp.get("C", 1.0), max_iter=1000, random_state=seed)
    if model_name == "KNN":
        return KNeighborsClassifier(n_neighbors=hp.get("k", 5))
    if model_name == "Decision Tree":
        return DecisionTreeClassifier(max_depth=hp.get("max_depth", 10), random_state=seed)
    if model_name == "Random Forest":
        return RandomForestClassifier(max_depth=hp.get("max_depth", 10), n_estimators=hp.get("n_estimators", 100), random_state=seed)
    if model_name == "Linear Regression":
        return LinearRegression()
    if model_name == "Ridge":
        return Ridge(alpha=hp.get("alpha", 1.0))
    if model_name == "Random Forest Regressor":
        return RandomForestRegressor(max_depth=hp.get("max_depth", 10), n_estimators=hp.get("n_estimators", 100), random_state=seed)
    raise ValueError("Unbekanntes Modell")

def build_production_code(num_cols, cat_cols, target_col, test_size, seed, use_stratify, scaler_name, imputer_strategy, estimator):
    stratify_text = ", stratify=y" if use_stratify else ""
    lines = [
        "import pandas as pd",
        "from sklearn.pipeline import Pipeline",
        "from sklearn.compose import ColumnTransformer",
        f"from sklearn.preprocessing import {scaler_name}, OneHotEncoder",
        "from sklearn.impute import SimpleImputer",
        "from sklearn.model_selection import train_test_split",
        f"from {estimator.__class__.__module__} import {estimator.__class__.__name__}",
        "",
        f"num_features = {num_cols!r}",
        f"cat_features = {cat_cols!r}",
        f"target = {target_col!r}",
        "",
        "X = df[num_features + cat_features]",
        "y = df[target]",
        f"X_train, X_test, y_train, y_test = train_test_split(X, y, test_size={test_size}, random_state={seed}{stratify_text})",
        "",
        "num_transformer = Pipeline([",
        f"    ('imputer', SimpleImputer(strategy={imputer_strategy!r})),",
        f"    ('scaler', {scaler_name}())",
        "])",
        "cat_transformer = Pipeline([",
        "    ('imputer', SimpleImputer(strategy='most_frequent')),",
        "    ('encoder', OneHotEncoder(handle_unknown='ignore'))",
        "])",
        "",
        "preprocessor = ColumnTransformer(transformers=[",
        "    ('num', num_transformer, num_features),",
        "    ('cat', cat_transformer, cat_features)",
        "])",
        "",
        "pipeline = Pipeline([",
        "    ('preprocessor', preprocessor),",
        f"    ('model', {estimator!r})",
        "])",
        "",
        "pipeline.fit(X_train, y_train)",
        "score = pipeline.score(X_test, y_test)",
    ]
    return "\n".join(lines)

uploaded = st.file_uploader("CSV- oder Excel-Datei hochladen", type=["csv", "xlsx", "xls"])
if uploaded is None:
    st.info("Bitte eine CSV- oder Excel-Datei hochladen.")
    st.stop()

data = uploaded.getvalue()
ext = Path(uploaded.name).suffix.lower()
sheet = None

if ext in {".xlsx", ".xls"}:
    sheet = st.selectbox("Excel-Tabellenblatt", get_sheet_names(data))

try:
    df_raw = load_file(data, uploaded.name, sheet)
except Exception as exc:
    st.error(f"Datei konnte nicht geladen werden: {exc}")
    st.stop()

id_cols = detect_id_columns(df_raw)
m1, m2, m3 = st.columns(3)
m1.metric("Zeilen", len(df_raw))
m2.metric("Spalten", len(df_raw.columns))
m3.metric("Erkannte ID-Spalten", len(id_cols))

if id_cols:
    st.info("Erkannte ID-Spalten: " + ", ".join(map(str, id_cols)))

with st.expander("Datenvorschau", expanded=True):
    st.dataframe(df_raw.head(50), use_container_width=True)

st.divider()
st.subheader("Pipeline konfigurieren")
left, right = st.columns(2)

with left:
    target_col = st.selectbox("Target (y)", list(df_raw.columns))
    feature_options = [c for c in df_raw.columns if c != target_col]
    default_features = [c for c in feature_options if c not in id_cols]
    feature_cols = st.multiselect("Features (X)", feature_options, default=default_features)
    task_request = st.selectbox("Task", ["Auto-Detect", "Classification", "Regression"])

task = resolve_task(df_raw, target_col, task_request)

with right:
    test_size = st.slider("Test Size", 0.10, 0.50, 0.20, 0.05)
    seed = int(st.number_input("Random Seed", min_value=0, value=42, step=1))
    stratify_requested = st.checkbox("Stratify Split (Klassifikation)", value=True, disabled=(task == "Regression"))
    scaler_name = st.selectbox("Scaler", ["StandardScaler", "RobustScaler", "MinMaxScaler"])
    imputer_strategy = st.selectbox("Numerischer Imputer", ["median", "mean"])

models = (
    ["Logistic Regression", "KNN", "Decision Tree", "Random Forest"]
    if task == "Classification"
    else ["Linear Regression", "Ridge", "Random Forest Regressor"]
)
model_name = st.selectbox("Modell", models)

hp = {}
if model_name == "Logistic Regression":
    hp["C"] = st.number_input("C (Regularisierung)", min_value=0.001, max_value=1000.0, value=1.0)
elif model_name == "KNN":
    hp["k"] = st.slider("k (Neighbors)", 1, 30, 5)
elif model_name in {"Decision Tree", "Random Forest", "Random Forest Regressor"}:
    hp["max_depth"] = st.slider("Max Depth", 1, 50, 10)
    if "Random Forest" in model_name:
        hp["n_estimators"] = st.slider("Estimators", 10, 300, 100, 10)
elif model_name == "Ridge":
    hp["alpha"] = st.number_input("Alpha", min_value=0.001, max_value=1000.0, value=1.0)

st.caption(f"Aufgelöster Task: **{task}**")

if st.button("Train Pipeline & Evaluate", type="primary", use_container_width=True):
    if not feature_cols:
        st.error("Mindestens ein Feature muss ausgewählt werden.")
        st.stop()

    df = df_raw.dropna(subset=[target_col]).copy()
    X = df[feature_cols]
    y = df[target_col]

    use_stratify = (
        stratify_requested
        and task == "Classification"
        and not y.value_counts().empty
        and y.value_counts().min() >= 2
    )

    try:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=float(test_size), random_state=seed,
            stratify=y if use_stratify else None
        )

        num_cols = X.select_dtypes(include=[np.number]).columns.tolist()
        cat_cols = X.select_dtypes(exclude=[np.number]).columns.tolist()

        scaler = {
            "StandardScaler": StandardScaler(),
            "RobustScaler": RobustScaler(),
            "MinMaxScaler": MinMaxScaler(),
        }[scaler_name]

        num_pipe = Pipeline([
            ("imputer", SimpleImputer(strategy=imputer_strategy)),
            ("scaler", scaler),
        ])
        cat_pipe = Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ])

        transformers = []
        if num_cols:
            transformers.append(("num", num_pipe, num_cols))
        if cat_cols:
            transformers.append(("cat", cat_pipe, cat_cols))

        preprocessor = ColumnTransformer(transformers=transformers)
        estimator = make_estimator(model_name, seed, hp)
        pipeline = Pipeline([("preprocessor", preprocessor), ("model", estimator)])

        with st.spinner("Pipeline wird trainiert ..."):
            pipeline.fit(X_train, y_train)
            y_pred = pipeline.predict(X_test)
    except Exception as exc:
        st.error(f"Training fehlgeschlagen: {exc}")
        st.stop()

    st.success("Training abgeschlossen.")

    st.subheader("Train / Test Split")
    st.dataframe(pd.DataFrame([
        {"Split": "Train Set", "Rows": len(X_train), "Features": X_train.shape[1], "Share": f"{1-test_size:.0%}"},
        {"Split": "Test Set", "Rows": len(X_test), "Features": X_test.shape[1], "Share": f"{test_size:.0%}"},
    ]), hide_index=True, use_container_width=True)
    st.caption(f"Random State: {seed} · Stratified: {use_stratify}")

    st.subheader(f"Evaluation: {task}")
    st.write(f"**Modell:** {model_name}")
    st.write(f"**Features:** {len(feature_cols)} ({len(num_cols)} numerisch, {len(cat_cols)} kategorial)")

    if task == "Classification":
        report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
        st.dataframe(pd.DataFrame(report).T, use_container_width=True)

        labels = np.unique(np.concatenate([np.asarray(y_test), np.asarray(y_pred)]))
        cm = confusion_matrix(y_test, y_pred, labels=labels)
        fig, ax = plt.subplots(figsize=(6, 5))
        im = ax.imshow(cm)
        ax.set_xticks(range(len(labels)), labels=labels, rotation=45, ha="right")
        ax.set_yticks(range(len(labels)), labels=labels)
        ax.set_xlabel("Predicted")
        ax.set_ylabel("Actual")
        ax.set_title("Confusion Matrix")
        for i in range(cm.shape[0]):
            for j in range(cm.shape[1]):
                ax.text(j, i, str(cm[i, j]), ha="center", va="center")
        fig.colorbar(im, ax=ax)
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
    else:
        metrics = pd.DataFrame([{
            "R² Score": r2_score(y_test, y_pred),
            "MAE": mean_absolute_error(y_test, y_pred),
            "RMSE": np.sqrt(mean_squared_error(y_test, y_pred)),
        }]).round(3)
        st.dataframe(metrics, hide_index=True, use_container_width=True)

        residuals = y_test - y_pred
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.scatter(y_pred, residuals, alpha=0.4)
        ax.axhline(0, linestyle="--")
        ax.set_xlabel("Predicted")
        ax.set_ylabel("Residuals")
        ax.set_title("Residual Plot")
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    code = build_production_code(
        num_cols, cat_cols, target_col, float(test_size), seed,
        use_stratify, scaler_name, imputer_strategy, estimator
    )
    st.subheader("Produktions-Code")
    st.code(code, language="python")
    st.download_button(
        "Produktions-Code herunterladen",
        data=code,
        file_name="trained_pipeline_template.py",
        mime="text/x-python",
    )
