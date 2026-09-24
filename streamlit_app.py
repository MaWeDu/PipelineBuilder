import io
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LinearRegression, LogisticRegression, Ridge
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_absolute_percentage_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
)
from sklearn.model_selection import (
    GridSearchCV,
    KFold,
    RandomizedSearchCV,
    RepeatedKFold,
    RepeatedStratifiedKFold,
    StratifiedKFold,
    cross_val_score,
    train_test_split,
)
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder, RobustScaler, StandardScaler
from sklearn.tree import DecisionTreeClassifier


st.set_page_config(page_title="ML Pipeline Builder", page_icon="🤖", layout="wide")
st.title("🤖 ML Pipeline Builder & Evaluator")
st.caption(
    "CSV-/Excel-Upload · Preprocessing · Train/Test · Cross-Validation · "
    "Modellvergleich · Hyperparameter-Suche · Feature Importance"
)


def looks_like_bad_header(columns):
    columns = [str(c).strip() for c in columns]
    if not columns:
        return False
    suspicious = sum(
        c.lower().startswith("unnamed:")
        or bool(re.fullmatch(r"column[_ ]?\d+", c.lower()))
        or bool(re.fullmatch(r"\d+", c.lower()))
        or c.lower() in {"", "nan", "none", "null"}
        for c in columns
    )
    return suspicious / len(columns) >= 0.8


def fix_misplaced_header(df):
    if looks_like_bad_header(df.columns) and not df.empty:
        row = df.iloc[0].astype(str).str.strip().tolist()
        if all(row) and len(row) == len(set(row)):
            df = df.iloc[1:].copy()
            df.columns = row
            df.reset_index(drop=True, inplace=True)
    return df


def detect_id_columns(df):
    result = []
    for col in df.columns:
        name = str(col).strip().lower()
        if name == "id" or name.endswith("_id") or name.startswith("id_") or "uuid" in name:
            result.append(col)
            continue
        unique_ratio = df[col].nunique(dropna=True) / max(len(df), 1)
        if unique_ratio >= 0.98 and not pd.api.types.is_numeric_dtype(df[col]):
            result.append(col)
    return result


@st.cache_data(show_spinner=False)
def get_sheet_names(data):
    return pd.ExcelFile(io.BytesIO(data)).sheet_names


@st.cache_data(show_spinner=False)
def load_file(data, filename, sheet=None):
    ext = Path(filename).suffix.lower()
    if ext == ".csv":
        try:
            df = pd.read_csv(io.BytesIO(data), encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(io.BytesIO(data), encoding="cp1252")
    elif ext in {".xlsx", ".xls"}:
        df = pd.read_excel(io.BytesIO(data), sheet_name=sheet)
    else:
        raise ValueError(f"Nicht unterstütztes Format: {ext}")
    return fix_misplaced_header(df)


def resolve_task(df, target, requested):
    if requested != "Auto-Detect":
        return requested
    y = df[target]
    if pd.api.types.is_numeric_dtype(y) and y.nunique(dropna=True) > 15:
        return "Regression"
    return "Classification"


def make_estimator(name, seed, hp=None):
    hp = hp or {}
    if name == "Logistic Regression":
        return LogisticRegression(C=hp.get("C", 1.0), max_iter=2000, random_state=seed)
    if name == "KNN":
        return KNeighborsClassifier(n_neighbors=hp.get("k", 5))
    if name == "Decision Tree":
        return DecisionTreeClassifier(max_depth=hp.get("max_depth", 10), random_state=seed)
    if name == "Random Forest":
        return RandomForestClassifier(
            n_estimators=hp.get("n_estimators", 100),
            max_depth=hp.get("max_depth", 10),
            random_state=seed,
        )
    if name == "Linear Regression":
        return LinearRegression()
    if name == "Ridge":
        return Ridge(alpha=hp.get("alpha", 1.0))
    if name == "Random Forest Regressor":
        return RandomForestRegressor(
            n_estimators=hp.get("n_estimators", 100),
            max_depth=hp.get("max_depth", 10),
            random_state=seed,
        )
    raise ValueError(f"Unbekanntes Modell: {name}")


def default_models(task, seed):
    if task == "Classification":
        return {
            "Logistic Regression": make_estimator("Logistic Regression", seed),
            "KNN": make_estimator("KNN", seed),
            "Decision Tree": make_estimator("Decision Tree", seed),
            "Random Forest": make_estimator("Random Forest", seed),
        }
    return {
        "Linear Regression": make_estimator("Linear Regression", seed),
        "Ridge": make_estimator("Ridge", seed),
        "Random Forest Regressor": make_estimator("Random Forest Regressor", seed),
    }


def build_preprocessor(X, scaler_name, imputer_strategy):
    numeric = X.select_dtypes(include=[np.number]).columns.tolist()
    categorical = X.select_dtypes(exclude=[np.number]).columns.tolist()

    scaler = {
        "StandardScaler": StandardScaler(),
        "RobustScaler": RobustScaler(),
        "MinMaxScaler": MinMaxScaler(),
    }[scaler_name]

    transformers = []
    if numeric:
        transformers.append(
            ("num", Pipeline([
                ("imputer", SimpleImputer(strategy=imputer_strategy)),
                ("scaler", scaler),
            ]), numeric)
        )
    if categorical:
        transformers.append(
            ("cat", Pipeline([
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("encoder", OneHotEncoder(handle_unknown="ignore")),
            ]), categorical)
        )

    return ColumnTransformer(transformers=transformers), numeric, categorical


def make_cv(task, folds, seed, repeated=False, repeats=2):
    if task == "Classification":
        if repeated:
            return RepeatedStratifiedKFold(
                n_splits=folds, n_repeats=repeats, random_state=seed
            )
        return StratifiedKFold(n_splits=folds, shuffle=True, random_state=seed)
    if repeated:
        return RepeatedKFold(n_splits=folds, n_repeats=repeats, random_state=seed)
    return KFold(n_splits=folds, shuffle=True, random_state=seed)


def search_space(model):
    spaces = {
        "Logistic Regression": {
            "model__C": [0.01, 0.1, 1, 10, 100]
        },
        "KNN": {
            "model__n_neighbors": [3, 5, 7, 9, 11, 15]
        },
        "Decision Tree": {
            "model__max_depth": [3, 5, 10, 20, None],
            "model__min_samples_split": [2, 5, 10],
        },
        "Random Forest": {
            "model__n_estimators": [50, 100, 200],
            "model__max_depth": [5, 10, 20, None],
            "model__min_samples_split": [2, 5],
        },
        "Ridge": {
            "model__alpha": [0.01, 0.1, 1, 10, 100]
        },
        "Random Forest Regressor": {
            "model__n_estimators": [50, 100, 200],
            "model__max_depth": [5, 10, 20, None],
            "model__min_samples_split": [2, 5],
        },
    }
    return spaces.get(model, {})


def class_metrics(y_true, y_pred):
    return {
        "Accuracy": accuracy_score(y_true, y_pred),
        "Balanced Accuracy": balanced_accuracy_score(y_true, y_pred),
        "Precision": precision_score(y_true, y_pred, average="weighted", zero_division=0),
        "Recall": recall_score(y_true, y_pred, average="weighted", zero_division=0),
        "F1": f1_score(y_true, y_pred, average="weighted", zero_division=0),
    }


def reg_metrics(y_true, y_pred):
    mse = mean_squared_error(y_true, y_pred)
    result = {
        "R²": r2_score(y_true, y_pred),
        "MAE": mean_absolute_error(y_true, y_pred),
        "MSE": mse,
        "RMSE": np.sqrt(mse),
    }
    # MAPE is hard to interpret when actual values contain zero.
    result["MAPE"] = (
        np.nan
        if np.any(np.asarray(y_true) == 0)
        else mean_absolute_percentage_error(y_true, y_pred)
    )
    return result


uploaded = st.file_uploader(
    "CSV- oder Excel-Datei hochladen",
    type=["csv", "xlsx", "xls"],
)

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

a, b, c = st.columns(3)
a.metric("Zeilen", len(df_raw))
b.metric("Spalten", len(df_raw.columns))
c.metric("Erkannte ID-Spalten", len(id_cols))

if id_cols:
    st.info("Erkannte ID-Spalten: " + ", ".join(map(str, id_cols)))

with st.expander("Datenvorschau", expanded=True):
    st.dataframe(df_raw.head(50), width="stretch")

st.divider()
st.subheader("1. Pipeline konfigurieren")

left, right = st.columns(2)

with left:
    target = st.selectbox("Target (y)", list(df_raw.columns))
    feature_options = [col for col in df_raw.columns if col != target]
    default_features = [col for col in feature_options if col not in id_cols]
    features = st.multiselect("Features (X)", feature_options, default=default_features)
    task_request = st.selectbox(
        "Task",
        ["Auto-Detect", "Classification", "Regression"],
    )

task = resolve_task(df_raw, target, task_request)

with right:
    test_size = st.slider("Test Size", 0.10, 0.50, 0.20, 0.05)
    seed = int(st.number_input("Random Seed", min_value=0, value=42, step=1))
    stratify_requested = st.checkbox(
        "Stratify Split",
        value=True,
        disabled=task == "Regression",
    )
    scaler_name = st.selectbox(
        "Scaler",
        ["StandardScaler", "RobustScaler", "MinMaxScaler"],
    )
    imputer_strategy = st.selectbox(
        "Numerischer Imputer",
        ["median", "mean"],
    )

models = (
    ["Logistic Regression", "KNN", "Decision Tree", "Random Forest"]
    if task == "Classification"
    else ["Linear Regression", "Ridge", "Random Forest Regressor"]
)

model_name = st.selectbox("Modell", models)

hp = {}
if model_name == "Logistic Regression":
    hp["C"] = st.number_input("C", 0.001, 1000.0, 1.0)
elif model_name == "KNN":
    hp["k"] = st.slider("k", 1, 30, 5)
elif model_name in {"Decision Tree", "Random Forest", "Random Forest Regressor"}:
    hp["max_depth"] = st.slider("Max Depth", 1, 50, 10)
    if "Random Forest" in model_name:
        hp["n_estimators"] = st.slider("Estimators", 10, 300, 100, 10)
elif model_name == "Ridge":
    hp["alpha"] = st.number_input("Alpha", 0.001, 1000.0, 1.0)

st.caption(f"Erkannter Task: **{task}**")

st.subheader("2. Erweiterte Auswertung")
x1, x2, x3 = st.columns(3)

with x1:
    run_cv = st.checkbox("Cross-Validation", value=True)
    folds = st.selectbox("Folds", [3, 5, 10], index=1)

with x2:
    repeated = st.checkbox("Repeated Cross-Validation", value=False, disabled=not run_cv)
    repeats = st.slider("Wiederholungen", 2, 5, 2, disabled=not repeated)

with x3:
    compare = st.checkbox("Modellvergleich", value=True)
    importance = st.checkbox("Feature Importance", value=True)

search_method = st.selectbox(
    "Hyperparameter-Suche",
    ["Keine", "Grid Search", "Randomized Search"],
)
random_iterations = st.slider(
    "Randomized-Search Iterationen",
    5, 30, 10,
    disabled=search_method != "Randomized Search",
)

if st.button("Train Pipeline & Evaluate", type="primary", width="stretch"):
    if not features:
        st.error("Mindestens ein Feature auswählen.")
        st.stop()

    df = df_raw.dropna(subset=[target]).copy()
    X = df[features]
    y = df[target]

    if len(df) < 5:
        st.error("Für die Modellierung sind zu wenige vollständige Target-Werte vorhanden.")
        st.stop()

    if task == "Classification" and y.nunique() < 2:
        st.error("Das Target benötigt mindestens zwei Klassen.")
        st.stop()

    use_stratify = (
        task == "Classification"
        and stratify_requested
        and y.value_counts().min() >= 2
    )

    try:
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=float(test_size),
            random_state=seed,
            stratify=y if use_stratify else None,
        )

        preprocessor, num_cols, cat_cols = build_preprocessor(
            X, scaler_name, imputer_strategy
        )

        estimator = make_estimator(model_name, seed, hp)
        pipeline = Pipeline([
            ("preprocessor", preprocessor),
            ("model", estimator),
        ])

        best_params = None

        with st.spinner("Modell wird trainiert ..."):
            if search_method == "Keine":
                pipeline.fit(X_train, y_train)
            else:
                params = search_space(model_name)
                if not params:
                    st.warning(
                        "Für dieses Modell ist keine Hyperparameter-Suche hinterlegt. "
                        "Das gewählte Modell wird normal trainiert."
                    )
                    pipeline.fit(X_train, y_train)
                else:
                    search_cv = make_cv(task, min(int(folds), 5), seed)
                    scoring = (
                        "balanced_accuracy"
                        if task == "Classification"
                        else "neg_root_mean_squared_error"
                    )

                    if search_method == "Grid Search":
                        search = GridSearchCV(
                            pipeline,
                            params,
                            scoring=scoring,
                            cv=search_cv,
                            n_jobs=-1,
                            refit=True,
                        )
                    else:
                        combinations = int(np.prod([len(v) for v in params.values()]))
                        search = RandomizedSearchCV(
                            pipeline,
                            params,
                            n_iter=min(random_iterations, combinations),
                            scoring=scoring,
                            cv=search_cv,
                            n_jobs=-1,
                            random_state=seed,
                            refit=True,
                        )

                    search.fit(X_train, y_train)
                    pipeline = search.best_estimator_
                    best_params = search.best_params_

            y_pred = pipeline.predict(X_test)

    except Exception as exc:
        st.error(f"Training fehlgeschlagen: {exc}")
        st.stop()

    st.success("Training abgeschlossen.")

    if best_params:
        st.subheader("Beste Hyperparameter")
        st.json(best_params)

    st.subheader("3. Train / Test Split")
    st.dataframe(
        pd.DataFrame([
            {
                "Split": "Train Set",
                "Rows": len(X_train),
                "Features": X_train.shape[1],
                "Share": f"{1-test_size:.0%}",
            },
            {
                "Split": "Test Set",
                "Rows": len(X_test),
                "Features": X_test.shape[1],
                "Share": f"{test_size:.0%}",
            },
        ]),
        hide_index=True,
        width="stretch",
    )
    st.caption(f"Random State: {seed} · Stratified: {use_stratify}")

    st.subheader("4. Modellmetriken")

    if task == "Classification":
        metrics = class_metrics(y_test, y_pred)
        cols = st.columns(len(metrics))
        for widget, (name, value) in zip(cols, metrics.items()):
            widget.metric(name, f"{value:.3f}")

        st.markdown("#### Classification Report")
        report = pd.DataFrame(
            classification_report(
                y_test,
                y_pred,
                output_dict=True,
                zero_division=0,
            )
        ).T
        st.dataframe(report, width="stretch")

        st.markdown("#### Confusion Matrix")
        labels = np.unique(
            np.concatenate([np.asarray(y_test), np.asarray(y_pred)])
        )
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
        metrics = reg_metrics(y_test, y_pred)
        cols = st.columns(len(metrics))

        for widget, (name, value) in zip(cols, metrics.items()):
            widget.metric(
                name,
                "n/a" if pd.isna(value) else f"{value:.3f}",
            )

        st.markdown("#### Actual vs. Predicted")
        actual = np.asarray(y_test, dtype=float)
        predicted = np.asarray(y_pred, dtype=float)

        fig, ax = plt.subplots(figsize=(7, 5))
        ax.scatter(actual, predicted, alpha=0.5)
        low = min(actual.min(), predicted.min())
        high = max(actual.max(), predicted.max())
        ax.plot([low, high], [low, high], linestyle="--")
        ax.set_xlabel("Actual")
        ax.set_ylabel("Predicted")
        ax.set_title("Actual vs. Predicted")
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

        st.markdown("#### Residual Plot")
        residuals = actual - predicted

        fig, ax = plt.subplots(figsize=(7, 4))
        ax.scatter(predicted, residuals, alpha=0.5)
        ax.axhline(0, linestyle="--")
        ax.set_xlabel("Predicted")
        ax.set_ylabel("Residuals")
        ax.set_title("Residual Plot")
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    if run_cv:
        st.subheader("5. Cross-Validation")

        try:
            cv = make_cv(task, int(folds), seed, repeated, int(repeats))
            scoring = "balanced_accuracy" if task == "Classification" else "r2"

            scores = cross_val_score(
                clone(pipeline),
                X,
                y,
                cv=cv,
                scoring=scoring,
                n_jobs=-1,
            )

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Mittelwert", f"{scores.mean():.3f}")
            c2.metric("Std.", f"{scores.std():.3f}")
            c3.metric("Minimum", f"{scores.min():.3f}")
            c4.metric("Maximum", f"{scores.max():.3f}")

            cv_df = pd.DataFrame({
                "Fold": range(1, len(scores) + 1),
                "Score": scores,
            })
            st.dataframe(cv_df, hide_index=True, width="stretch")

            fig, ax = plt.subplots(figsize=(8, 4))
            ax.bar(cv_df["Fold"], cv_df["Score"])
            ax.axhline(scores.mean(), linestyle="--", label="Mittelwert")
            ax.set_xlabel("Fold")
            ax.set_ylabel(scoring)
            ax.set_title("Cross-Validation Scores")
            ax.legend()
            fig.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

        except Exception as exc:
            st.warning(f"Cross-Validation nicht möglich: {exc}")

    if compare:
        st.subheader("6. Modellvergleich")
        rows = []

        try:
            comparison_cv = make_cv(task, int(folds), seed)
            scoring = "balanced_accuracy" if task == "Classification" else "r2"

            for name, model in default_models(task, seed).items():
                comparison_pipeline = Pipeline([
                    ("preprocessor", clone(preprocessor)),
                    ("model", model),
                ])

                try:
                    scores = cross_val_score(
                        comparison_pipeline,
                        X,
                        y,
                        cv=comparison_cv,
                        scoring=scoring,
                        n_jobs=-1,
                    )
                    rows.append({
                        "Modell": name,
                        "CV Mean": scores.mean(),
                        "CV Std": scores.std(),
                        "CV Min": scores.min(),
                        "CV Max": scores.max(),
                    })
                except Exception as model_exc:
                    rows.append({
                        "Modell": name,
                        "CV Mean": np.nan,
                        "CV Std": np.nan,
                        "CV Min": np.nan,
                        "CV Max": np.nan,
                        "Fehler": str(model_exc),
                    })

            comparison_df = pd.DataFrame(rows).sort_values(
                "CV Mean",
                ascending=False,
                na_position="last",
            )

            st.dataframe(
                comparison_df,
                hide_index=True,
                width="stretch",
            )

            valid = comparison_df.dropna(subset=["CV Mean"])
            if not valid.empty:
                fig, ax = plt.subplots(figsize=(8, 4))
                ax.bar(valid["Modell"], valid["CV Mean"])
                ax.set_ylabel(scoring)
                ax.set_title("Modellvergleich")
                ax.tick_params(axis="x", rotation=30)
                fig.tight_layout()
                st.pyplot(fig)
                plt.close(fig)

        except Exception as exc:
            st.warning(f"Modellvergleich nicht möglich: {exc}")

    if importance:
        st.subheader("7. Feature Importance")

        try:
            scoring = "balanced_accuracy" if task == "Classification" else "r2"

            perm = permutation_importance(
                pipeline,
                X_test,
                y_test,
                scoring=scoring,
                n_repeats=10,
                random_state=seed,
                n_jobs=-1,
            )

            importance_df = pd.DataFrame({
                "Feature": features,
                "Importance": perm.importances_mean,
                "Std": perm.importances_std,
            }).sort_values("Importance", ascending=False)

            st.dataframe(
                importance_df,
                hide_index=True,
                width="stretch",
            )

            shown = importance_df.sort_values("Importance").tail(20)

            fig, ax = plt.subplots(
                figsize=(8, max(4, len(shown) * 0.35))
            )
            ax.barh(shown["Feature"], shown["Importance"])
            ax.set_xlabel("Permutation Importance")
            ax.set_title("Feature Importance – Top 20")
            fig.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

        except Exception as exc:
            st.warning(f"Feature Importance nicht möglich: {exc}")

    st.subheader("8. Pipeline-Zusammenfassung")
    st.write(f"**Task:** {task}")
    st.write(f"**Modell:** {model_name}")
    st.write(f"**Target:** {target}")
    st.write(f"**Numerische Features:** {', '.join(map(str, num_cols)) or 'Keine'}")
    st.write(f"**Kategoriale Features:** {', '.join(map(str, cat_cols)) or 'Keine'}")
    st.write(f"**Scaler:** {scaler_name}")
    st.write(f"**Imputer:** {imputer_strategy}")
