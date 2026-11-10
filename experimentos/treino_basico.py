"""Experimento exploratório: regras (Pandas) + Random Forest básico nas 300 fichas.

Rodar a partir da raiz do repositório:
    .venv/Scripts/python.exe <este arquivo>

Não grava nada no repositório. Usa as extrações prontas em entregas/.
"""

import json
import sys
import time

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict

sys.path.insert(0, ".")
from ia.entrada.planilha import ler_planilha  # noqa: E402

PROTOCOLO = {  # aba Criterios da planilha da Bárbara (D6 + D15)
    "idade_min": 30, "idade_max": 70,
    "hba1c_min": 7.0, "hba1c_max": 10.5,
    "imc_min": 25, "imc_max": 45,
    "creatinina_max": 1.5,
}
NUM = ["idade", "hba1c", "creatinina", "glicemia_jejum", "imc"]
CAMPOS = ["neoplasia_ativa", "gestacao", "uso_metformina"]


def juntar(planilha, extracoes):
    pac = ler_planilha(planilha) if "Base_ficticia" in planilha else pd.read_excel(planilha, "pacientes")
    ext = json.load(open(extracoes, encoding="utf-8"))
    linhas = []
    for e in ext:
        r = {"id_paciente": e["id_paciente"]}
        for c in NUM:
            r[f"txt_{c}"] = (e.get("dados_lidos", {}).get(c) or {}).get("valor")
        r["txt_sexo"] = (e.get("dados_lidos", {}).get("sexo") or {}).get("valor")
        for c in CAMPOS:
            f = e["campos"][c]
            r[f"{c}_status"] = f["status"]
            r[f"{c}_conf"] = f["confianca"]
            r[f"{c}_problemas"] = "; ".join(f.get("problemas") or [])
            r[f"{c}_evid"] = f.get("evidencia")
        linhas.append(r)
    return pac.merge(pd.DataFrame(linhas), on="id_paciente", how="left")


def avaliar(r, pref="txt_", status=None):
    """Camada 1. Retorna (resultado, atendidos, limitantes, revisar)."""
    P = PROTOCOLO
    at, lim, rev = [], [], []

    def faixa(nome, rot, unid, lo=None, hi=None):
        v = r[f"{pref}{nome}"]
        if v is None or pd.isna(v):
            rev.append(f"{rot}: não encontrado no texto")
            return
        if lo is not None and v < lo:
            lim.append(f"{rot} {v:g}{unid} abaixo do mínimo de {lo:g}{unid}")
        elif hi is not None and v > hi:
            lim.append(f"{rot} {v:g}{unid} acima do máximo de {hi:g}{unid}")
        else:
            at.append(f"{rot} {v:g}{unid}")

    faixa("idade", "Idade", " anos", P["idade_min"], P["idade_max"])
    faixa("hba1c", "HbA1c", "%", P["hba1c_min"], P["hba1c_max"])
    faixa("imc", "IMC", "", P["imc_min"], P["imc_max"])
    faixa("creatinina", "Creatinina", " mg/dL", None, P["creatinina_max"])

    st = status or (lambda c: r[f"{c}_status"])
    conf = (lambda c: "alta") if status else (lambda c: r[f"{c}_conf"])
    for c, rot in [("neoplasia_ativa", "Neoplasia ativa"), ("gestacao", "Gestação")]:  # exclusão
        s = st(c)
        if s == "afirmado":
            lim.append(f"{rot} presente")
        elif s == "incerto" or conf(c) == "baixa":
            rev.append(f"{rot}: {r.get(f'{c}_problemas') or s}")
        else:
            at.append(f"Sem {rot.lower()}")
    s = st("uso_metformina")  # inclusão
    if s == "afirmado" and conf("uso_metformina") != "baixa":
        at.append("Usa metformina")
    elif s == "negado" and conf("uso_metformina") != "baixa":
        lim.append("Não usa metformina")
    else:
        rev.append(f"Metformina: {r.get('uso_metformina_problemas') or s}")

    res = "NÃO ELEGÍVEL" if lim else ("REVISAR" if rev else "ELEGÍVEL")
    return res, at, lim, rev


def margem(r):
    """Score alternativo (6.4): menor folga normalizada até um limite numérico."""
    P = PROTOCOLO
    f = []
    for c, lo, hi in [("idade", P["idade_min"], P["idade_max"]), ("hba1c", P["hba1c_min"], P["hba1c_max"]),
                      ("imc", P["imc_min"], P["imc_max"]), ("creatinina", 0.0, P["creatinina_max"])]:
        v = r[f"txt_{c}"]
        if v is None or pd.isna(v):
            continue
        f.append(min(v - lo, hi - v) / (hi - lo))
    return min(f) if f else np.nan


def main():
    t0 = time.time()
    b1 = juntar("dados/Base_ficticia_DM2_CLINIA.xlsx", "entregas/extracoes_base1.json")
    b2 = juntar("dados/pacientes_ficticios_PAC201-300.xlsx", "entregas/extracoes_base2.json")
    b1["base"], b2["base"] = 1, 2

    # Gabarito de elegibilidade
    b1["gold"] = (b1["elegibilidade_calculada"] == "Elegível").astype(int)
    gab = {"neoplasia_ativa": "gab_neoplasia", "gestacao": "gab_gestacao", "uso_metformina": "gab_metformina"}
    g2 = []
    for _, r in b2.iterrows():  # [HIPÓTESE] regras sobre números da planilha + gab_* (leitura humana)
        rr = r.copy()
        for c in NUM:
            rr[f"pl_{c}"] = r[c]
        res, *_ = avaliar(rr, pref="pl_", status=lambda c, r=r: r[gab[c]])
        g2.append(1 if res == "ELEGÍVEL" else 0)
    b2["gold"] = g2
    df = pd.concat([b1, b2], ignore_index=True)

    # Camada 1 (regras sobre o que a CLINIA leu do texto)
    out = df.apply(lambda r: avaliar(r), axis=1, result_type="expand")
    df[["resultado", "atendidos", "limitantes", "revisar"]] = out
    df["margem"] = df.apply(margem, axis=1)

    print("=" * 70, "\nCAMADA 1 — REGRAS (sobre o texto lido pela CLINIA)\n")
    for b in [1, 2]:
        d = df[df.base == b]
        ct = pd.crosstab(d["gold"].map({1: "elegível", 0: "não eleg."}), d["resultado"])
        print(f"Base {b} ({len(d)} pacientes)\n{ct}\n")
        eleg = d[d.gold == 1]
        enc = (eleg.resultado == "ELEGÍVEL").mean()
        enc_rev = (eleg.resultado != "NÃO ELEGÍVEL").mean()
        marc = d[d.resultado == "ELEGÍVEL"]
        prec = (marc.gold == 1).mean() if len(marc) else float("nan")
        perig = ((d.gold == 0) & (d.resultado == "ELEGÍVEL")).sum()
        perdidos = ((d.gold == 1) & (d.resultado == "NÃO ELEGÍVEL")).sum()
        print(f"  Sensibilidade (ELEGÍVEL direto):          {enc:.0%}")
        print(f"  Sensibilidade (ELEGÍVEL + REVISAR):       {enc_rev:.0%}   <- meta > 80%")
        print(f"  Precisão dos ELEGÍVEL:                    {prec:.0%}")
        print(f"  Não elegível marcado ELEGÍVEL (perigoso): {perig}")
        print(f"  Elegível descartado como NÃO ELEGÍVEL:    {perdidos}")
        if b == 1:
            lim = d[d.grupo_simulacao == "Limítrofe"]
            print(f"  Limítrofes (30): {lim.resultado.value_counts().to_dict()} | "
                  f"acerto binário {((lim.resultado == 'ELEGÍVEL') == (lim.gold == 1)).mean():.0%}")
        print()

    # Camada 2 — Random Forest
    X = pd.DataFrame({f"txt_{c}": df[f"txt_{c}"] for c in NUM})
    X["sexo_F"] = (df["txt_sexo"] == "F").astype(int)
    for c in CAMPOS:
        for s in ["afirmado", "negado", "nao_mencionado", "incerto"]:
            X[f"{c}={s}"] = (df[f"{c}_status"] == s).astype(int)
        X[f"{c}_conf_baixa"] = (df[f"{c}_conf"] == "baixa").astype(int)
    X = X.fillna(-1)  # valor ausente no texto
    y = df["gold"].values

    rf = RandomForestClassifier(n_estimators=300, min_samples_leaf=3, random_state=42, class_weight="balanced")
    cv = StratifiedKFold(5, shuffle=True, random_state=42)
    t1 = time.time()
    proba = cross_val_predict(rf, X, y, cv=cv, method="predict_proba")[:, 1]
    t_cv = time.time() - t1
    df["prob"] = proba
    pred = (proba >= 0.5).astype(int)

    print("=" * 70, "\nCAMADA 2 — RANDOM FOREST (validação cruzada 5 dobras, 300 pacientes)\n")
    print(f"  AUC:        {roc_auc_score(y, proba):.3f}")
    print(f"  Acurácia:   {(pred == y).mean():.1%}")
    tn, fp, fn, tp = confusion_matrix(y, pred).ravel()
    print(f"  Matriz:     VP={tp} FN={fn} FP={fp} VN={tn}  | sensibilidade {tp/(tp+fn):.0%}, precisão {tp/(tp+fp):.0%}")
    print(f"  Tempo CV:   {t_cv:.1f}s")
    bins = [0, .1, .3, .5, .7, .9, 1.0001]
    dist = pd.cut(proba, bins, right=False).value_counts().sort_index()
    print("\n  Distribuição das probabilidades (ponto 6.4):")
    for k, v in dist.items():
        print(f"    {str(k):14s} {v:4d} {'#' * (v // 3)}")
    extremos = ((proba < .1) | (proba > .9)).mean()
    print(f"  -> {extremos:.0%} dos pacientes com prob < 0,1 ou > 0,9")

    # Generalização: treina só na Base 1, testa na Base 2 (texto variado)
    m1 = df.base == 1
    rf.fit(X[m1], y[m1])
    p2 = rf.predict_proba(X[~m1])[:, 1]
    print(f"\n  Treina Base 1 -> testa Base 2: AUC {roc_auc_score(y[~m1], p2):.3f}, "
          f"acurácia {((p2 >= .5) == y[~m1]).mean():.0%}")

    rf.fit(X, y)
    imp = pd.Series(rf.feature_importances_, X.columns).sort_values(ascending=False).head(8)
    print("\n  Importância das features (top 8):")
    for k, v in imp.items():
        print(f"    {k:32s} {v:.3f}")

    # A ordenação dentro de cada resultado agrega?
    print("\n  Ordenação dentro do grupo (prob. RF vs margem até o limite):")
    for res in ["ELEGÍVEL", "REVISAR"]:
        d = df[df.resultado == res]
        print(f"    {res:9s} n={len(d):3d} | prob RF: min {d.prob.min():.2f} mediana {d.prob.median():.2f} "
              f"| valores distintos {d.prob.round(2).nunique()} | corr(prob, margem) {d.prob.corr(d.margem):.2f}")
    rev = df[df.resultado == "REVISAR"]
    if len(rev) and rev.gold.nunique() > 1:
        print(f"    Em REVISAR, a prob. RF separa os elegíveis de verdade? AUC {roc_auc_score(rev.gold, rev.prob):.3f}")

    print(f"\nTempo total: {time.time() - t0:.1f}s")
    df.drop(columns=[c for c in df.columns if c.endswith("_evid")]).to_csv(
        sys.argv[1] if len(sys.argv) > 1 else "resultado_treino_basico.csv", index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
