#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split, cross_validate
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    roc_auc_score, roc_curve, f1_score,
    brier_score_loss, confusion_matrix
)
from sklearn.calibration import calibration_curve

ROLE_MAP = {
    1: 'Vanguard',
    2: 'Duelist',
    3: 'Strategist'
}


def analyze_role(df_role, role_name):
    print(f"\n=== Análisis para rol: {role_name} ===")
    total_rows = df_role.shape[0]
    unique_rows = df_role.drop_duplicates().shape[0]
    dup_rows = total_rows - unique_rows
    print(f"Total filas (contando duplicados): {total_rows}")
    print(f"Filas únicas: {unique_rows}")
    print(f"Filas duplicadas (que también se cuentan): {dup_rows}")

    # Estadísticas descriptivas
    stats = df_role[['kills','deaths','assists','damage','dmg_taken','healing']].describe().T
    stats['median'] = df_role[['kills','deaths','assists','damage','dmg_taken','healing']].median()
    print("\nEstadísticas descriptivas:\n", stats)

    # Valores faltantes
    missing = df_role.isnull().sum()
    print("\nValores faltantes por columna:\n", missing)

    # Correlaciones y multicolinealidad
    corr = df_role[['kills','deaths','assists','damage','dmg_taken','healing']].corr()
    print("\nMatriz de correlaciones:\n", corr)
    high_corr = [
        (i, j, corr.loc[i,j])
        for i in corr.columns for j in corr.index
        if i != j and abs(corr.loc[i,j]) > 0.8
    ]
    print("\nPares con |ρ| > 0.8:\n", high_corr)

    # Preparación para el modelo
    features = ['kills','deaths','assists','damage','dmg_taken','healing']
    X = df_role[features]
    y = df_role['mvp']

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.3, random_state=42, stratify=y
    )

    # Entrenamiento
    model = LogisticRegression(
        penalty='l2', class_weight='balanced',
        solver='liblinear', random_state=42
    )
    cross_validate(model, X_train, y_train, cv=5, scoring='roc_auc')
    model.fit(X_train, y_train)

    intercept = model.intercept_[0]
    coefs = model.coef_[0]
    print(f"\nIntercepto: {intercept:.3f}")
    print("Coeficientes:")
    for var, coef in zip(features, coefs):
        print(f"  {var}: {coef:.3f}")

    # Evaluación
    y_prob = model.predict_proba(X_test)[:,1]
    y_pred = model.predict(X_test)

    roc_auc = roc_auc_score(y_test, y_prob)
    fpr, tpr, _ = roc_curve(y_test, y_prob)
    ks_stat = np.max(np.abs(tpr - fpr))
    f1 = f1_score(y_test, y_pred)
    brier = brier_score_loss(y_test, y_prob)
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
    sens = tp / (tp + fn)
    spec = tn / (tn + fp)

    print("\nMétricas de evaluación:")
    print(f"  ROC-AUC     : {roc_auc:.3f}")
    print(f"  KS          : {ks_stat:.3f}")
    print(f"  F1-Score    : {f1:.3f}")
    print(f"  Brier Score : {brier:.3f}")
    print(f"  Sensibilidad: {sens:.3f}")
    print(f"  Especificidad: {spec:.3f}")

    # Gráficas ROC y calibración
    plt.figure()
    plt.plot(fpr, tpr, label=f'ROC (AUC={roc_auc:.2f})')
    plt.plot([0,1],[0,1],'--', label='Aleatorio')
    plt.title(f'Curva ROC - {role_name}')
    plt.xlabel('FPR'); plt.ylabel('TPR'); plt.legend(); plt.show()

    prob_true, prob_pred = calibration_curve(y_test, y_prob, n_bins=10)
    plt.figure()
    plt.plot(prob_pred, prob_true, marker='o', label='Calibración')
    plt.plot([0,1],[0,1],'--', label='Perfecta')
    plt.title(f'Curva de Calibración - {role_name}')
    plt.xlabel('Prob. predicha'); plt.ylabel('Prob. observada'); plt.legend(); plt.show()

    # Ecuación
    equation = (
        f"log(p/(1-p)) = {intercept:.3f} + " +
        " + ".join(f"{coef:.3f}*{var}" for coef,var in zip(coefs, features))
    )
    print("\nEcuación del modelo:\n", equation)


def main():
    # 1. Carga y preprocesado global
    df = pd.read_csv('rivals_data.csv')
    # Imputar faltantes con mediana
    # Imputar faltantes con mediana solo en columnas numéricas
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())

    # 2. Ejecutar análisis por cada rol
    for code, name in ROLE_MAP.items():
        df_role = df[df['role'] == code]
        if df_role.empty:
            print(f"\n--- No hay datos para rol: {name} ---")
            continue
        analyze_role(df_role, name)

if __name__ == "__main__":
    main()
