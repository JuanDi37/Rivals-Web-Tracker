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

def main():
    # 1. Carga y preprocesado (CONTEO DE DUPLICADOS INCLUIDOS)
    df = pd.read_csv('rivals_data.csv')
    total_rows = df.shape[0]
    unique_rows = df.drop_duplicates().shape[0]
    dup_rows = total_rows - unique_rows
    print(f"Total filas (contando duplicados): {total_rows}")
    print(f"Filas únicas: {unique_rows}")
    print(f"Filas duplicadas (que también se cuentan): {dup_rows}")

    # Estadísticas descriptivas (incluyen duplicados)
    stats = df[['kills','deaths','assists','damage','dmg_taken','healing']].describe().T
    stats['median'] = df[['kills','deaths','assists','damage','dmg_taken','healing']].median()
    print("\nEstadísticas descriptivas (duplicados incluidos):\n", stats)

    # Valores faltantes
    missing = df.isnull().sum()
    print("\nValores faltantes por columna:\n", missing)

    # Imputar faltantes con la mediana (no drop de filas)
    df.fillna(df.median(), inplace=True)

    # 2. Análisis exploratorio
    corr = df[['kills','deaths','assists','damage','dmg_taken','healing']].corr()
    print("\nMatriz de correlaciones:\n", corr)

    # Multicolinealidad fuerte
    high_corr = [
        (i, j, corr.loc[i,j])
        for i in corr.columns for j in corr.index
        if i != j and abs(corr.loc[i,j]) > 0.8
    ]
    print("\nPares con |ρ| > 0.8:\n", high_corr)

    # Visualizar matriz de correlaciones
    plt.figure(figsize=(6,5))
    plt.imshow(corr, cmap='coolwarm', vmin=-1, vmax=1)
    plt.colorbar(label='Correlación')
    plt.xticks(range(len(corr)), corr.columns, rotation=45)
    plt.yticks(range(len(corr)), corr.index)
    plt.title('Matriz de Correlaciones')
    plt.tight_layout()
    plt.show()

    # 3. Preparación de datos para el modelo
    features = ['kills','deaths','assists','damage','dmg_taken','healing']
    X = df[features]  # duplicados incluidos
    y = df['mvp']

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.3, random_state=42, stratify=y
    )

    # 4. Entrenamiento del modelo
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

    # 5. Evaluación
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

    # Curva ROC
    plt.figure()
    plt.plot(fpr, tpr, label=f'ROC (AUC={roc_auc:.2f})')
    plt.plot([0,1],[0,1],'--', label='Aleatorio')
    plt.xlabel('FPR'); plt.ylabel('TPR')
    plt.title('Curva ROC')
    plt.legend()
    plt.show()

    # Curva de calibración
    prob_true, prob_pred = calibration_curve(y_test, y_prob, n_bins=10)
    plt.figure()
    plt.plot(prob_pred, prob_true, marker='o', label='Calibración')
    plt.plot([0,1],[0,1],'--', label='Perfecta')
    plt.xlabel('Prob. predicha'); plt.ylabel('Prob. observada')
    plt.title('Curva de Calibración')
    plt.legend()
    plt.show()

    # 6. Ecuación del modelo
    equation = (
        f"log(p/(1-p)) = {intercept:.3f} + " +
        " + ".join(f"{coef:.3f}*{var}" for coef,var in zip(coefs, features))
    )
    print("\nEcuación del modelo:\n ", equation)

if __name__ == "__main__":
    main()
