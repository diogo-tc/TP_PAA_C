import argparse
import base64
import html
import math
from pathlib import Path

try:
    import pandas as pd
except ImportError as exc:
    raise SystemExit(
        "Dependencia ausente: pandas.\n"
        "Instale com: python -m pip install -r requirements.txt"
    ) from exc


ALGORITHM_ORDER = ["dp", "bt", "bb"]
PRESENTATION_ALGORITHM_ORDER = ["bt", "bb", "dp"]
ALGORITHM_NAMES = {
    "dp": "Programacao dinamica",
    "bt": "Backtracking",
    "bb": "Branch-and-bound",
}

ALGORITHM_NAMES_PRESENTATION = {
    "dp": "Dinamica",
    "bt": "Backtracking",
    "bb": "BnB",
}

ALGORITHM_COLORS = {
    "dp": "#b6d7a8",
    "bt": "#a4c2f4",
    "bb": "#f9cb9c",
}

COLUMN_NAMES_PT_BR = {
    "source_csv": "arquivo_csv",
    "n": "quantidade_itens",
    "W": "capacidade_peso",
    "V": "capacidade_volume",
    "rep": "repeticao",
    "algorithm": "algoritmo",
    "runs": "execucoes",
    "mean_time": "tempo_medio",
    "median_time": "tempo_mediano",
    "std_time": "desvio_padrao_tempo",
    "min_time": "tempo_minimo",
    "max_time": "tempo_maximo",
    "mean_profit": "lucro_medio",
    "cv_time": "coeficiente_variacao_tempo",
    "dp": "tempo_medio_dp",
    "bt": "tempo_medio_bt",
    "bb": "tempo_medio_bb",
    "speed_ratio_bt_over_dp": "razao_tempo_bt_sobre_dp",
    "speed_ratio_bb_over_dp": "razao_tempo_bb_sobre_dp",
    "speed_ratio_bb_over_bt": "razao_tempo_bb_sobre_bt",
    "fastest_algorithm": "algoritmo_mais_rapido",
    "fastest_mean_time": "menor_tempo_medio",
    "distinct_profits": "quantidade_lucros_distintos",
    "same_profit_all_algorithms": "mesmo_lucro_todos_algoritmos",
    "test": "teste_estatistico",
    "comparison": "comparacao",
    "statistic": "estatistica",
    "p_value": "valor_p",
    "significant_0_05": "significativo_0_05",
    "message": "mensagem",
}

TIME_COLUMNS = {
    "mean_time",
    "median_time",
    "std_time",
    "min_time",
    "max_time",
    "fastest_mean_time",
    "dp",
    "bt",
    "bb",
}

RATIO_COLUMNS = {
    "cv_time",
    "speed_ratio_bt_over_dp",
    "speed_ratio_bb_over_dp",
    "speed_ratio_bb_over_bt",
}


# Renomeia as colunas de um DataFrame para nomes em portugues do Brasil.
def to_pt_br(df: pd.DataFrame) -> pd.DataFrame:
    return df.rename(columns={col: COLUMN_NAMES_PT_BR.get(str(col), str(col)) for col in df.columns})


# Formata numeros decimais seguindo a regra definida para tempos e razoes.
def format_decimal_pt(value: float) -> str:
    if pd.isna(value):
        return ""

    value = float(value)
    if value == 0:
        return "0"

    if abs(value) >= 1:
        return f"{value:.4f}".replace(".", ",")
    else:
        text = f"{value:.20f}".rstrip("0")
        decimals = text.split(".", 1)[1]
        first_non_zero = next((i for i, char in enumerate(decimals) if char != "0"), None)
        if first_non_zero is None:
            text = "0"
        else:
            decimals_to_keep = first_non_zero + 2
            text = f"{value:.{decimals_to_keep}f}".rstrip("0")

    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text.replace(".", ",")


# Formata valores monetarios em reais no padrao brasileiro.
def format_currency_pt(value: float) -> str:
    text = f"{float(value):,.2f}"
    text = text.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {text}"


# Formata valores em milissegundos para tabelas de apresentacao.
def format_ms_pt(value: float) -> str:
    if pd.isna(value):
        return ""
    value = float(value)
    if value == 0:
        return "0"
    if abs(value) >= 1:
        return f"{value:.2f}".replace(".", ",")
    return format_decimal_pt(value)


# Formata parametros inteiros da instancia sem casas decimais.
def format_instance_size(value: float) -> str:
    if pd.isna(value):
        return ""
    value = float(value)
    if value.is_integer():
        return str(int(value))
    return format_decimal_pt(value)


# Aplica a formatacao decimal apenas nas colunas indicadas para exportacao.
def format_for_export(df: pd.DataFrame, decimal_columns: set[str]) -> pd.DataFrame:
    formatted = df.copy()
    for column in decimal_columns:
        if column in formatted.columns:
            formatted[column] = formatted[column].map(format_decimal_pt)
    return formatted


# Carrega os CSVs, valida colunas obrigatorias e padroniza tipos numericos.
def load_data(paths: list[Path]) -> pd.DataFrame:
    frames = []
    for path in paths:
        df = pd.read_csv(path)
        df["source_csv"] = path.name
        frames.append(df)

    if not frames:
        raise SystemExit("Nenhum CSV encontrado.")

    df = pd.concat(frames, ignore_index=True)
    required = {"n", "W", "V", "rep", "algorithm", "profit", "time_seconds"}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"CSV sem colunas obrigatorias: {sorted(missing)}")

    df["algorithm"] = pd.Categorical(df["algorithm"], categories=ALGORITHM_ORDER, ordered=True)
    df["time_seconds"] = pd.to_numeric(df["time_seconds"], errors="coerce")
    df["profit"] = pd.to_numeric(df["profit"], errors="coerce")
    if "status" in df.columns:
        df = df[df["status"].fillna("ok") == "ok"]
    df = df.dropna(subset=["time_seconds", "profit"])
    return df


# Gera tabelas consolidadas de resumo, razoes, vencedores e consistencia de lucro.
def save_tables(df: pd.DataFrame, out_dir: Path) -> dict[str, Path]:
    tables_dir = out_dir / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)

    summary = (
        df.groupby(["source_csv", "n", "W", "V", "algorithm"], observed=False)
        .agg(
            runs=("time_seconds", "count"),
            mean_time=("time_seconds", "mean"),
            median_time=("time_seconds", "median"),
            std_time=("time_seconds", "std"),
            min_time=("time_seconds", "min"),
            max_time=("time_seconds", "max"),
            mean_profit=("profit", "mean"),
        )
        .reset_index()
    )
    summary["cv_time"] = summary["std_time"] / summary["mean_time"]
    format_for_export(to_pt_br(summary), {
        COLUMN_NAMES_PT_BR[col] for col in (TIME_COLUMNS | RATIO_COLUMNS) if col in COLUMN_NAMES_PT_BR
    }).to_csv(tables_dir / "summary_by_combination.csv", index=False)

    global_summary = (
        df.groupby(["source_csv", "algorithm"], observed=False)
        .agg(
            runs=("time_seconds", "count"),
            mean_time=("time_seconds", "mean"),
            median_time=("time_seconds", "median"),
            std_time=("time_seconds", "std"),
            min_time=("time_seconds", "min"),
            max_time=("time_seconds", "max"),
        )
        .reset_index()
    )
    format_for_export(to_pt_br(global_summary), {
        COLUMN_NAMES_PT_BR[col] for col in TIME_COLUMNS if col in COLUMN_NAMES_PT_BR
    }).to_csv(tables_dir / "summary_global.csv", index=False)

    pivot = (
        summary.pivot_table(
            index=["source_csv", "n", "W", "V"],
            columns="algorithm",
            values="mean_time",
            observed=False,
        )
        .reset_index()
    )
    for a, b in [("bt", "dp"), ("bb", "dp"), ("bb", "bt")]:
        if a in pivot.columns and b in pivot.columns:
            pivot[f"speed_ratio_{a}_over_{b}"] = pivot[a] / pivot[b]
    format_for_export(to_pt_br(pivot), {
        COLUMN_NAMES_PT_BR[col] for col in (TIME_COLUMNS | RATIO_COLUMNS) if col in COLUMN_NAMES_PT_BR
    }).to_csv(tables_dir / "mean_time_ratios.csv", index=False)

    winners = summary.loc[summary.groupby(["source_csv", "n", "W", "V"], observed=False)["mean_time"].idxmin()]
    winners = winners[["source_csv", "n", "W", "V", "algorithm", "mean_time"]].rename(
        columns={"algorithm": "fastest_algorithm", "mean_time": "fastest_mean_time"}
    )
    format_for_export(to_pt_br(winners), {
        COLUMN_NAMES_PT_BR[col] for col in TIME_COLUMNS if col in COLUMN_NAMES_PT_BR
    }).to_csv(tables_dir / "fastest_by_combination.csv", index=False)

    consistency = (
        df.groupby(["source_csv", "n", "W", "V", "rep"], observed=False)
        .agg(distinct_profits=("profit", "nunique"))
        .reset_index()
    )
    consistency["same_profit_all_algorithms"] = consistency["distinct_profits"] == 1
    to_pt_br(consistency).to_csv(tables_dir / "profit_consistency.csv", index=False)

    return {
        "summary": tables_dir / "summary_by_combination.csv",
        "global_summary": tables_dir / "summary_global.csv",
        "ratios": tables_dir / "mean_time_ratios.csv",
        "winners": tables_dir / "fastest_by_combination.csv",
        "consistency": tables_dir / "profit_consistency.csv",
    }


# Gera tabelas resumidas em formato adequado para apresentacao em slides.
def save_presentation_tables(df: pd.DataFrame, out_dir: Path) -> list[Path]:
    presentation_dir = out_dir / "presentation_tables"
    presentation_dir.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []

    for source, source_df in df.groupby("source_csv", observed=False):
        table = (
            source_df.groupby(["n", "W", "V", "algorithm"], observed=False)
            .agg(
                tempo_medio_ms=("time_seconds", lambda values: values.mean() * 1000),
                desvio_ms=("time_seconds", lambda values: values.std(ddof=1) * 1000),
                amostras=("time_seconds", "count"),
            )
            .reset_index()
        )
        table["ic_95_ms"] = table.apply(
            lambda row: 0.0 if pd.isna(row["desvio_ms"]) or row["amostras"] <= 1
            else 1.96 * row["desvio_ms"] / math.sqrt(row["amostras"]),
            axis=1,
        )
        table["algorithm"] = pd.Categorical(table["algorithm"], categories=PRESENTATION_ALGORITHM_ORDER, ordered=True)
        table = table.sort_values(["n", "W", "V", "algorithm"])

        display = pd.DataFrame({
            "N (Itens)": table["n"].map(format_instance_size),
            "Peso (W)": table["W"].map(format_instance_size),
            "Volume (V)": table["V"].map(format_instance_size),
            "Metodo": table["algorithm"].map(ALGORITHM_NAMES_PRESENTATION),
            "Tempo (ms)": table["tempo_medio_ms"].map(format_ms_pt),
            "Desvio (ms)": table["desvio_ms"].map(format_ms_pt),
            "IC 95% (ms)": table["ic_95_ms"].map(format_ms_pt),
        })

        safe_source = Path(str(source)).stem
        csv_path = presentation_dir / f"{safe_source}_tabela_apresentacao.csv"
        svg_path = presentation_dir / f"{safe_source}_tabela_apresentacao.svg"
        html_path = presentation_dir / f"{safe_source}_tabela_apresentacao.html"

        display.to_csv(csv_path, index=False)
        title = f"Tabela - Comparacao por Tamanho da Instancia ({source})"
        svg_path.write_text(presentation_table_svg(display, title), encoding="utf-8")
        html_path.write_text(presentation_table_html(display, title), encoding="utf-8")
        generated.extend([csv_path, svg_path, html_path])

    return generated


# Gera tabelas compactas para slides, resumindo uma dimensao por vez.
def save_compact_presentation_tables(df: pd.DataFrame, out_dir: Path) -> list[Path]:
    presentation_dir = out_dir / "presentation_tables"
    presentation_dir.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []

    dimensions = [
        ("n", "N (Itens)", "por_itens"),
        ("W", "Peso (W)", "por_peso"),
        ("V", "Volume (V)", "por_volume"),
    ]

    for source, source_df in df.groupby("source_csv", observed=False):
        safe_source = Path(str(source)).stem
        for group_col, label, suffix in dimensions:
            table = (
                source_df.groupby([group_col, "algorithm"], observed=False)
                .agg(
                    tempo_medio_ms=("time_seconds", lambda values: values.mean() * 1000),
                    desvio_ms=("time_seconds", lambda values: values.std(ddof=1) * 1000),
                    amostras=("time_seconds", "count"),
                )
                .reset_index()
            )
            table["ic_95_ms"] = table.apply(
                lambda row: 0.0 if pd.isna(row["desvio_ms"]) or row["amostras"] <= 1
                else 1.96 * row["desvio_ms"] / math.sqrt(row["amostras"]),
                axis=1,
            )
            table["algorithm"] = pd.Categorical(table["algorithm"], categories=PRESENTATION_ALGORITHM_ORDER, ordered=True)
            table = table.sort_values([group_col, "algorithm"])

            display = pd.DataFrame({
                label: table[group_col].map(format_instance_size),
                "Metodo": table["algorithm"].map(ALGORITHM_NAMES_PRESENTATION),
                "Tempo (ms)": table["tempo_medio_ms"].map(format_ms_pt),
                "Desvio (ms)": table["desvio_ms"].map(format_ms_pt),
                "IC 95% (ms)": table["ic_95_ms"].map(format_ms_pt),
            })

            csv_path = presentation_dir / f"{safe_source}_tabela_slide_{suffix}.csv"
            svg_path = presentation_dir / f"{safe_source}_tabela_slide_{suffix}.svg"
            html_path = presentation_dir / f"{safe_source}_tabela_slide_{suffix}.html"
            title = f"Tabela - Tempo medio {label} ({source})"

            display.to_csv(csv_path, index=False)
            svg_path.write_text(presentation_table_svg(display, title), encoding="utf-8")
            html_path.write_text(presentation_table_html(display, title), encoding="utf-8")
            generated.extend([csv_path, svg_path, html_path])

    return generated


# Cria uma tabela visual em SVG com cores por metodo para uso em slides.
def presentation_table_svg(table: pd.DataFrame, title: str) -> str:
    columns = list(table.columns)
    default_widths = {
        "N (Itens)": 105,
        "Peso (W)": 115,
        "Volume (V)": 120,
        "Metodo": 155,
        "Tempo (ms)": 135,
        "Desvio (ms)": 135,
        "IC 95% (ms)": 135,
    }
    col_widths = [default_widths.get(col, 130) for col in columns]
    row_h = 34
    header_h = 38
    title_h = 44
    width = sum(col_widths) + 2
    height = title_h + header_h + len(table) * row_h + 2

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="{width / 2}" y="29" text-anchor="middle" font-family="Arial" font-size="22" font-weight="700">{html.escape(title)}</text>',
    ]

    y = title_h
    x = 1
    svg.append(f'<rect x="1" y="{y}" width="{width - 2}" height="{header_h}" fill="#bfbfbf" stroke="#222" stroke-width="1"/>')
    for col, col_w in zip(columns, col_widths):
        svg.append(f'<rect x="{x}" y="{y}" width="{col_w}" height="{header_h}" fill="#bfbfbf" stroke="#222" stroke-width="1"/>')
        svg.append(f'<text x="{x + col_w / 2}" y="{y + 25}" text-anchor="middle" font-family="Arial" font-size="16" font-weight="700">{html.escape(col)}</text>')
        x += col_w

    for row_index, (_, row) in enumerate(table.iterrows()):
        y = title_h + header_h + row_index * row_h
        method = str(row["Metodo"])
        method_key = {"Backtracking": "bt", "BnB": "bb", "Dinamica": "dp"}.get(method, "")
        x = 1
        for col, col_w in zip(columns, col_widths):
            fill = ALGORITHM_COLORS.get(method_key, "white") if col == "Metodo" else "white"
            svg.append(f'<rect x="{x}" y="{y}" width="{col_w}" height="{row_h}" fill="{fill}" stroke="#222" stroke-width="1"/>')
            weight = "700" if col == "Metodo" else "400"
            svg.append(f'<text x="{x + col_w / 2}" y="{y + 22}" text-anchor="middle" font-family="Arial" font-size="15" font-weight="{weight}">{html.escape(str(row[col]))}</text>')
            x += col_w

    svg.append("</svg>")
    return "\n".join(svg)


# Cria uma versao HTML da tabela visual para abrir no navegador ou copiar para slides.
def presentation_table_html(table: pd.DataFrame, title: str) -> str:
    rows = []
    for _, row in table.iterrows():
        method = str(row["Metodo"])
        method_key = {"Backtracking": "bt", "BnB": "bb", "Dinamica": "dp"}.get(method, "")
        cells = []
        for col in table.columns:
            style = ""
            if col == "Metodo":
                style = f' style="background:{ALGORITHM_COLORS.get(method_key, "white")}; font-weight:700;"'
            cells.append(f"<td{style}>{html.escape(str(row[col]))}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")

    headers = "".join(f"<th>{html.escape(col)}</th>" for col in table.columns)
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <title>{html.escape(title)}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; }}
    h1 {{ text-align: center; font-size: 24px; }}
    table {{ border-collapse: collapse; margin: 0 auto; font-size: 16px; }}
    th {{ background: #bfbfbf; font-weight: 700; }}
    th, td {{ border: 1px solid #222; padding: 7px 14px; text-align: center; }}
  </style>
</head>
<body>
  <h1>{html.escape(title)}</h1>
  <table>
    <thead><tr>{headers}</tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
</body>
</html>
"""


# Executa os testes estatisticos de Friedman e Wilcoxon quando o scipy esta disponivel.
def save_stats(df: pd.DataFrame, out_dir: Path) -> Path:
    stats_dir = out_dir / "tables"
    stats_dir.mkdir(parents=True, exist_ok=True)
    out_path = stats_dir / "statistical_tests.csv"

    try:
        from scipy.stats import friedmanchisquare, wilcoxon
    except ImportError:
        to_pt_br(pd.DataFrame(
            [{
                "message": "scipy nao instalado. Instale com: python -m pip install -r requirements.txt"
            }]
        )).to_csv(out_path, index=False)
        return out_path

    rows = []
    for keys, group in df.groupby(["source_csv", "n", "W", "V"], observed=False):
        pivot = group.pivot_table(index="rep", columns="algorithm", values="time_seconds", observed=False)
        source_csv, n, w, v = keys

        available_algorithms = [alg for alg in ALGORITHM_ORDER if alg in pivot.columns]
        if len(available_algorithms) < 2:
            continue

        complete = pivot.dropna(subset=available_algorithms)
        if len(complete) < 2:
            continue

        if len(available_algorithms) >= 3:
            stat, pvalue = friedmanchisquare(*(complete[alg] for alg in available_algorithms))
            rows.append({
                "source_csv": source_csv,
                "n": n,
                "W": w,
                "V": v,
                "test": "friedman",
                "comparison": "_vs_".join(available_algorithms),
                "statistic": stat,
                "p_value": pvalue,
                "significant_0_05": pvalue < 0.05,
            })

        for i, a in enumerate(available_algorithms):
            for b in available_algorithms[i + 1:]:
                pair = pivot[[a, b]].dropna()
                if len(pair) < 2:
                    continue
                stat, pvalue = wilcoxon(pair[a], pair[b], zero_method="zsplit")
                rows.append({
                    "source_csv": source_csv,
                    "n": n,
                    "W": w,
                    "V": v,
                    "test": "wilcoxon",
                    "comparison": f"{a}_vs_{b}",
                    "statistic": stat,
                    "p_value": pvalue,
                    "significant_0_05": pvalue < 0.05,
                })

    to_pt_br(pd.DataFrame(rows)).to_csv(out_path, index=False)
    return out_path


# Gera os graficos principais com matplotlib/seaborn ou usa SVG simplificado como fallback.
def save_plots(df: pd.DataFrame, out_dir: Path) -> list[Path]:
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
    except ImportError as exc:
        (out_dir / "plots_missing.txt").write_text(
            "Dependencias ausentes para graficos: matplotlib/seaborn.\n"
            "Foram gerados graficos SVG simplificados como fallback.\n"
            "Para graficos PNG mais elaborados, instale com: python -m pip install -r requirements.txt\n",
            encoding="utf-8",
        )
        return save_fallback_svg_plots(df, out_dir)

    plots_dir = out_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")
    plot_paths: list[Path] = []

    for source, source_df in df.groupby("source_csv", observed=False):
        safe_source = Path(str(source)).stem

        plt.figure(figsize=(10, 5.5))
        sns.lineplot(
            data=source_df,
            x="n",
            y="time_seconds",
            hue="algorithm",
            marker="o",
            estimator="mean",
            errorbar="sd",
        )
        plt.yscale("log")
        plt.title(f"Tempo medio por n - {source}")
        plt.xlabel("Quantidade de itens (n)")
        plt.ylabel("Tempo medio em segundos (escala log)")
        plt.tight_layout()
        path = plots_dir / f"{safe_source}_tempo_por_n.png"
        plt.savefig(path, dpi=160)
        plt.close()
        plot_paths.append(path)

        mean_by_n = (
            source_df.groupby(["n", "algorithm"], observed=False)["time_seconds"]
            .mean()
            .reset_index()
        )
        plt.figure(figsize=(10, 5.5))
        sns.barplot(data=mean_by_n, x="n", y="time_seconds", hue="algorithm")
        plt.yscale("log")
        plt.title(f"Tempo medio por n e algoritmo - {source}")
        plt.xlabel("Quantidade de itens (n)")
        plt.ylabel("Tempo medio em segundos (escala log)")
        plt.tight_layout()
        path = plots_dir / f"{safe_source}_barras_n_algoritmo.png"
        plt.savefig(path, dpi=160)
        plt.close()
        plot_paths.append(path)

        for variable, label in [("W", "peso"), ("V", "volume")]:
            mean_by_variable = (
                source_df.groupby([variable, "algorithm"], observed=False)["time_seconds"]
                .mean()
                .reset_index()
            )
            plt.figure(figsize=(10, 5.5))
            sns.lineplot(
                data=mean_by_variable,
                x=variable,
                y="time_seconds",
                hue="algorithm",
                marker="o",
            )
            plt.yscale("log")
            plt.title(f"Tempo medio por {label} - {source}")
            plt.xlabel("Capacidade de peso (W)" if variable == "W" else "Capacidade de volume (V)")
            plt.ylabel("Tempo medio em segundos (escala log)")
            plt.tight_layout()
            path = plots_dir / f"{safe_source}_tempo_medio_por_{variable}.png"
            plt.savefig(path, dpi=160)
            plt.close()
            plot_paths.append(path)

    return plot_paths


# Gera graficos SVG simples quando as bibliotecas de graficos nao estao instaladas.
def save_fallback_svg_plots(df: pd.DataFrame, out_dir: Path) -> list[Path]:
    plots_dir = out_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)
    plot_paths: list[Path] = []
    colors = {"dp": "#2563eb", "bt": "#dc2626", "bb": "#16a34a"}

    for source, source_df in df.groupby("source_csv", observed=False):
        safe_source = Path(str(source)).stem
        mean_by_n = (
            source_df.groupby(["n", "algorithm"], observed=False)["time_seconds"]
            .mean()
            .reset_index()
        )
        path = plots_dir / f"{safe_source}_tempo_medio_por_n.svg"
        path.write_text(
            line_svg(
                mean_by_n,
                x_col="n",
                y_col="time_seconds",
                series_col="algorithm",
                title=f"Tempo medio por n - {source}",
                x_label="Quantidade de itens (n)",
                y_label="Tempo medio (s, escala log)",
                colors=colors,
            ),
            encoding="utf-8",
        )
        plot_paths.append(path)

        for variable, label in [("W", "peso"), ("V", "volume")]:
            mean_by_variable = (
                source_df.groupby([variable, "algorithm"], observed=False)["time_seconds"]
                .mean()
                .reset_index()
            )
            path = plots_dir / f"{safe_source}_tempo_medio_por_{variable}.svg"
            path.write_text(
                line_svg(
                    mean_by_variable,
                    x_col=variable,
                    y_col="time_seconds",
                    series_col="algorithm",
                    title=f"Tempo medio por {label} - {source}",
                    x_label="Capacidade de peso (W)" if variable == "W" else "Capacidade de volume (V)",
                    y_label="Tempo medio (s, escala log)",
                    colors=colors,
                ),
                encoding="utf-8",
            )
            plot_paths.append(path)

    return plot_paths


# Monta um grafico de linhas em SVG usando apenas pandas e biblioteca padrao.
def line_svg(df: pd.DataFrame, x_col: str, y_col: str, series_col: str, title: str,
             x_label: str, y_label: str, colors: dict[str, str]) -> str:
    width, height = 920, 520
    left, right, top, bottom = 86, 28, 54, 76
    plot_w = width - left - right
    plot_h = height - top - bottom

    data = df.copy()
    data = data[data[y_col] > 0]
    if data.empty:
        return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"><text x="20" y="30">Sem dados</text></svg>'

    xs = sorted(data[x_col].unique())
    min_x, max_x = min(xs), max(xs)
    if min_x == max_x:
        max_x = min_x + 1

    data["_log_y"] = data[y_col].map(lambda value: __import__("math").log10(float(value)))
    min_y = float(data["_log_y"].min())
    max_y = float(data["_log_y"].max())
    if min_y == max_y:
        min_y -= 1
        max_y += 1

    def sx(value: float) -> float:
        return left + (float(value) - min_x) / (max_x - min_x) * plot_w

    def sy(log_value: float) -> float:
        return top + (max_y - log_value) / (max_y - min_y) * plot_h

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="{width / 2}" y="28" text-anchor="middle" font-family="Arial" font-size="18" font-weight="700">{html.escape(title)}</text>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" stroke="#444"/>',
        f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" stroke="#444"/>',
    ]

    for i in range(6):
        t = i / 5
        y = top + t * plot_h
        log_value = max_y - t * (max_y - min_y)
        label = 10 ** log_value
        svg.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + plot_w}" y2="{y:.1f}" stroke="#e5e7eb"/>')
        svg.append(f'<text x="{left - 10}" y="{y + 4:.1f}" text-anchor="end" font-family="Arial" font-size="11">{label:.3g}</text>')

    for value in xs:
        x = sx(value)
        svg.append(f'<line x1="{x:.1f}" y1="{top + plot_h}" x2="{x:.1f}" y2="{top + plot_h + 5}" stroke="#444"/>')
        svg.append(f'<text x="{x:.1f}" y="{top + plot_h + 22}" text-anchor="middle" font-family="Arial" font-size="11">{html.escape(str(value))}</text>')

    legend_x = left + 10
    for idx, algorithm in enumerate(ALGORITHM_ORDER):
        series = data[data[series_col] == algorithm].sort_values(x_col)
        if series.empty:
            continue
        points = [(sx(row[x_col]), sy(row["_log_y"])) for _, row in series.iterrows()]
        point_text = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
        color = colors.get(algorithm, "#111827")
        svg.append(f'<polyline points="{point_text}" fill="none" stroke="{color}" stroke-width="2.5"/>')
        for x, y in points:
            svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{color}"/>')
        ly = top + 22 + idx * 20
        svg.append(f'<rect x="{legend_x}" y="{ly - 10}" width="12" height="12" fill="{color}"/>')
        svg.append(f'<text x="{legend_x + 18}" y="{ly}" font-family="Arial" font-size="12">{html.escape(ALGORITHM_NAMES.get(algorithm, algorithm))}</text>')

    svg.append(f'<text x="{left + plot_w / 2}" y="{height - 20}" text-anchor="middle" font-family="Arial" font-size="13">{html.escape(x_label)}</text>')
    svg.append(f'<text x="18" y="{top + plot_h / 2}" text-anchor="middle" transform="rotate(-90 18 {top + plot_h / 2})" font-family="Arial" font-size="13">{html.escape(y_label)}</text>')
    svg.append("</svg>")
    return "\n".join(svg)


# Converte uma imagem local para data URI, permitindo embutir graficos no HTML.
def image_to_data_uri(path: Path) -> str:
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    mime = "image/svg+xml" if path.suffix.lower() == ".svg" else "image/png"
    return f"data:{mime};base64,{data}"



# Gera uma pequena visualizacao HTML das primeiras linhas de uma tabela CSV.
def table_preview(path: Path, rows: int = 12) -> str:
    df = pd.read_csv(path)
    return df.head(rows).to_html(index=False, classes="table")


# Cria o dashboard HTML final com cards, tabelas e graficos embutidos.
def save_dashboard(df: pd.DataFrame, out_dir: Path, table_paths: dict[str, Path], stats_path: Path,
                   plot_paths: list[Path], presentation_paths: list[Path]) -> Path:
    dashboard_path = out_dir / "dashboard.html"
    total_runs = len(df)
    csvs = ", ".join(sorted(map(str, df["source_csv"].unique())))
    combinations = df[["source_csv", "n", "W", "V"]].drop_duplicates().shape[0]

    global_summary_html = table_preview(table_paths["global_summary"])
    ratios_html = table_preview(table_paths["ratios"])
    winners_html = table_preview(table_paths["winners"])
    consistency = pd.read_csv(table_paths["consistency"])
    inconsistent = consistency[~consistency["mesmo_lucro_todos_algoritmos"]]

    if plot_paths:
        images = "\n".join(
        f'<section><h3>{html.escape(path.stem)}</h3><img src="{image_to_data_uri(path)}" alt="{html.escape(path.stem)}"></section>'
        for path in plot_paths
        )
    else:
        images = (
            "<p class=\"note\">Graficos nao foram gerados porque matplotlib/seaborn nao estao instalados. "
            "Instale as dependencias com <code>python -m pip install -r requirements.txt</code> e rode novamente.</p>"
        )

    html_text = f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <title>Dashboard - Mochila 0-1</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; color: #202020; }}
    h1, h2, h3 {{ margin-bottom: 8px; }}
    .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 12px; margin: 16px 0 24px; }}
    .card {{ border: 1px solid #ddd; border-radius: 6px; padding: 12px; background: #fafafa; }}
    .value {{ font-size: 24px; font-weight: bold; }}
    .table {{ border-collapse: collapse; width: 100%; font-size: 13px; margin-bottom: 24px; }}
    .table th, .table td {{ border: 1px solid #ddd; padding: 6px 8px; text-align: right; }}
    .table th {{ background: #f0f0f0; }}
    img {{ width: 100%; max-width: 1100px; border: 1px solid #ddd; border-radius: 6px; }}
    section {{ margin-bottom: 28px; }}
    .note {{ color: #555; }}
  </style>
</head>
<body>
  <h1>Dashboard - Mochila 0-1 com duas restricoes</h1>
  <p class="note">CSVs analisados: {html.escape(csvs)}</p>
  <div class="cards">
    <div class="card"><div>Total de execucoes</div><div class="value">{total_runs}</div></div>
    <div class="card"><div>Combinacoes analisadas</div><div class="value">{combinations}</div></div>
    <div class="card"><div>Lucros divergentes</div><div class="value">{len(inconsistent)}</div></div>
  </div>

  <h2>Resumo global</h2>
  {global_summary_html}

  <h2>Razoes de tempo medio</h2>
  {ratios_html}

  <h2>Algoritmo mais rapido por combinacao</h2>
  {winners_html}

  <h2>Graficos</h2>
  {images}

  <h2>Arquivos gerados</h2>
  <ul>
    <li>{html.escape(str(table_paths["summary"]))}</li>
    <li>{html.escape(str(table_paths["global_summary"]))}</li>
    <li>{html.escape(str(table_paths["ratios"]))}</li>
    <li>{html.escape(str(table_paths["winners"]))}</li>
    <li>{html.escape(str(table_paths["consistency"]))}</li>
    <li>{html.escape(str(stats_path))}</li>
    {''.join(f'<li>{html.escape(str(path))}</li>' for path in presentation_paths)}
  </ul>
</body>
</html>
"""
    dashboard_path.write_text(html_text, encoding="utf-8")
    return dashboard_path


# Resolve os argumentos de entrada, aceitando tanto arquivos CSV quanto diretorios.
def resolve_inputs(args: argparse.Namespace) -> list[Path]:
    paths: list[Path] = []
    for raw in args.inputs:
        path = Path(raw)
        if path.is_dir():
            paths.extend(sorted(path.glob("*.csv")))
        elif path.is_file():
            paths.append(path)
        else:
            raise SystemExit(f"Entrada nao encontrada: {path}")
    return paths


# Ponto de entrada do script: le argumentos, processa dados e gera todos os artefatos.
def main() -> None:
    parser = argparse.ArgumentParser(description="Gera estatisticas, graficos e dashboard para os CSVs da mochila.")
    parser.add_argument("inputs", nargs="+", help="Arquivos CSV ou diretorios contendo CSVs")
    parser.add_argument("--out-dir", default="analysis_output", help="Diretorio de saida")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    paths = resolve_inputs(args)
    df = load_data(paths)
    table_paths = save_tables(df, out_dir)
    presentation_paths = save_presentation_tables(df, out_dir)
    presentation_paths.extend(save_compact_presentation_tables(df, out_dir))
    stats_path = save_stats(df, out_dir)
    plot_paths = save_plots(df, out_dir)
    dashboard_path = save_dashboard(df, out_dir, table_paths, stats_path, plot_paths, presentation_paths)

    print(f"CSVs analisados: {len(paths)}")
    print(f"Execucoes analisadas: {len(df)}")
    print(f"Tabelas de apresentacao: {out_dir / 'presentation_tables'}")
    print(f"Dashboard: {dashboard_path}")


if __name__ == "__main__":
    main()
