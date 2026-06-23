import argparse
from pathlib import Path

try:
    import pandas as pd
except ImportError as exc:
    raise SystemExit(
        "Dependencia ausente: pandas.\n"
        "Instale no WSL com: python3 -m pip install -r requirements.txt"
    ) from exc


def main() -> None:
    parser = argparse.ArgumentParser(description="Analisa tempos dos algoritmos da mochila 0-1 com duas restricoes.")
    parser.add_argument("csv", help="CSV gerado por run_experiments")
    parser.add_argument("--out-dir", default="results/analysis", help="Diretorio de saida")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.csv)
    summary = (
        df.groupby(["n", "W", "V", "algorithm"])["time_seconds"]
        .agg(["count", "mean", "median", "std", "min", "max"])
        .reset_index()
    )
    summary.to_csv(out_dir / "summary.csv", index=False)

    try:
        from scipy.stats import friedmanchisquare, wilcoxon

        tests = []
        for (n, w, v), group in df.groupby(["n", "W", "V"]):
            pivot = group.pivot_table(index="rep", columns="algorithm", values="time_seconds", aggfunc="mean")
            required = [col for col in ["dp", "bt", "bb"] if col in pivot.columns]
            pivot = pivot.dropna(subset=required)
            if len(required) == 3 and len(pivot) >= 2:
                stat, pvalue = friedmanchisquare(pivot["dp"], pivot["bt"], pivot["bb"])
                tests.append({
                    "n": n,
                    "W": w,
                    "V": v,
                    "test": "friedman",
                    "comparison": "dp_vs_bt_vs_bb",
                    "statistic": stat,
                    "p_value": pvalue,
                })
                for a, b in [("dp", "bt"), ("dp", "bb"), ("bt", "bb")]:
                    stat, pvalue = wilcoxon(pivot[a], pivot[b], zero_method="zsplit")
                    tests.append({
                        "n": n,
                        "W": w,
                        "V": v,
                        "test": "wilcoxon",
                        "comparison": f"{a}_vs_{b}",
                        "statistic": stat,
                        "p_value": pvalue,
                    })

        pd.DataFrame(tests).to_csv(out_dir / "statistical_tests.csv", index=False)
    except ImportError:
        (out_dir / "statistical_tests.txt").write_text(
            "scipy nao esta instalado. Instale com: python -m pip install scipy\n",
            encoding="utf-8",
        )

    try:
        import matplotlib.pyplot as plt
        import seaborn as sns

        sns.set_theme(style="whitegrid")
        for (w, v), group in df.groupby(["W", "V"]):
            plt.figure(figsize=(9, 5))
            sns.lineplot(data=group, x="n", y="time_seconds", hue="algorithm", marker="o", estimator="mean")
            plt.title(f"Tempo medio por quantidade de itens (W={w}, V={v})")
            plt.xlabel("Quantidade de itens")
            plt.ylabel("Tempo medio (s)")
            plt.tight_layout()
            plt.savefig(out_dir / f"time_by_n_W{w}_V{v}.png", dpi=160)
            plt.close()

        for n, group in df.groupby("n"):
            plt.figure(figsize=(9, 5))
            sns.barplot(data=group, x="algorithm", y="time_seconds", hue="algorithm", errorbar="sd")
            plt.title(f"Distribuicao dos tempos por algoritmo (n={n})")
            plt.xlabel("Algoritmo")
            plt.ylabel("Tempo (s)")
            plt.tight_layout()
            plt.savefig(out_dir / f"time_by_algorithm_n{n}.png", dpi=160)
            plt.close()
    except ImportError:
        (out_dir / "plots.txt").write_text(
            "matplotlib/seaborn nao estao instalados. Instale com: python -m pip install matplotlib seaborn\n",
            encoding="utf-8",
        )

    print(f"Analise salva em: {out_dir}")


if __name__ == "__main__":
    main()
