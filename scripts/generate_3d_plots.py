import argparse
from pathlib import Path

try:
    import pandas as pd
except ImportError as exc:
    raise SystemExit(
        "Dependencia ausente: pandas.\n"
        "Instale com: python -m pip install -r requirements.txt"
    ) from exc

try:
    import matplotlib.pyplot as plt
except ImportError as exc:
    raise SystemExit(
        "Dependencia ausente: matplotlib.\n"
        "Instale com: python -m pip install -r requirements.txt"
    ) from exc

try:
    import numpy as np
except ImportError as exc:
    raise SystemExit(
        "Dependencia ausente: numpy.\n"
        "Instale com: python -m pip install -r requirements.txt"
    ) from exc


ALGORITHM_NAMES = {
    "bt": "Backtracking",
    "bb": "Branch-and-bound",
    "dp": "Programacao dinamica",
}

ALGORITHM_FILE_NAMES = {
    "bt": "backtracking",
    "bb": "branch_and_bound",
    "dp": "programacao_dinamica",
}


# Carrega o CSV, valida as colunas obrigatorias e remove execucoes com timeout/erro.
def load_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"n", "W", "V", "algorithm", "time_seconds"}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"CSV sem colunas obrigatorias: {sorted(missing)}")

    df["time_seconds"] = pd.to_numeric(df["time_seconds"], errors="coerce")
    if "status" in df.columns:
        df = df[df["status"].fillna("ok") == "ok"]
    df = df.dropna(subset=["time_seconds"])
    return df


# Agrega os tempos medios por algoritmo e combinacao de n, W e V.
def aggregate(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(["algorithm", "n", "W", "V"], observed=False)["time_seconds"]
        .mean()
        .reset_index()
        .rename(columns={"time_seconds": "mean_time_seconds"})
    )


# Cria uma linha 3D quando nao ha pontos suficientes para formar superficie.
def plot_3d_line(data: pd.DataFrame, algorithm: str, out_dir: Path, stem: str,
                 x_col: str, x_label: str, y_col: str, y_label: str, suffix: str) -> Path:
    fig = plt.figure(figsize=(10.8, 7.6), facecolor="white")
    ax = fig.add_subplot(111, projection="3d")
    line_data = data.sort_values([y_col, x_col])

    ax.plot(
        line_data[x_col],
        line_data[y_col],
        line_data["mean_time_seconds"],
        color="#2563eb",
        linewidth=2.5,
        marker="o",
        markersize=6,
    )

    ax.set_title(
        f"{ALGORITHM_NAMES.get(algorithm, algorithm)} - Tempo medio 3D (dados em linha)",
        fontsize=17,
        fontweight="bold",
        pad=18,
    )
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_zlabel("Tempo medio (s)")
    ax.view_init(elev=28, azim=-138)
    ax.grid(True)
    ax.xaxis.pane.set_facecolor((0.95, 0.95, 0.95, 1.0))
    ax.yaxis.pane.set_facecolor((0.95, 0.95, 0.95, 1.0))
    ax.zaxis.pane.set_facecolor((0.98, 0.98, 0.98, 1.0))

    file_name = ALGORITHM_FILE_NAMES.get(algorithm, algorithm)
    path = out_dir / f"{stem}_{file_name}_linha_3d_{suffix}.png"
    plt.tight_layout()
    plt.savefig(path, dpi=190)
    plt.close(fig)
    return path


# Cria uma superficie 3D usando duas variaveis escolhidas e tempo medio.
def plot_surface(data: pd.DataFrame, algorithm: str, out_dir: Path, stem: str,
                 x_col: str, x_label: str, y_col: str, y_label: str,
                 suffix: str, title_suffix: str) -> Path:
    pivot = data.pivot_table(index=y_col, columns=x_col, values="mean_time_seconds", observed=False)
    pivot = pivot.sort_index().sort_index(axis=1)

    if pivot.shape[0] < 2 or pivot.shape[1] < 2:
        print(
            f"Aviso: dados insuficientes para superficie do algoritmo {algorithm}. "
            "Gerando linha 3D como alternativa."
        )
        return plot_3d_line(data, algorithm, out_dir, stem, x_col, x_label, y_col, y_label, suffix)

    x_values = np.array(pivot.columns.to_list(), dtype=float)
    y_values = np.array(pivot.index.to_list(), dtype=float)
    x_grid, y_grid = np.meshgrid(x_values, y_values)
    z_grid = pivot.values.astype(float)

    if np.isnan(z_grid).any():
        z_grid = (
            pd.DataFrame(z_grid)
            .interpolate(axis=0, limit_direction="both")
            .interpolate(axis=1, limit_direction="both")
            .values
        )

    fig = plt.figure(figsize=(10.8, 7.6), facecolor="white")
    ax = fig.add_subplot(111, projection="3d")

    surface = ax.plot_surface(
        x_grid,
        y_grid,
        z_grid,
        cmap="jet",
        linewidth=0.3,
        edgecolor="#d1d5db",
        antialiased=True,
        alpha=0.96,
    )

    ax.set_title(
        f"{ALGORITHM_NAMES.get(algorithm, algorithm)} - Tempo medio por {title_suffix}",
        fontsize=17,
        fontweight="bold",
        pad=18,
    )
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_zlabel("Tempo medio (s)")
    ax.view_init(elev=28, azim=-138)
    ax.grid(True)
    ax.xaxis.pane.set_facecolor((0.95, 0.95, 0.95, 1.0))
    ax.yaxis.pane.set_facecolor((0.95, 0.95, 0.95, 1.0))
    ax.zaxis.pane.set_facecolor((0.98, 0.98, 0.98, 1.0))

    colorbar = fig.colorbar(surface, ax=ax, shrink=0.66, pad=0.08)
    colorbar.set_label("Tempo medio (s)")

    file_name = ALGORITHM_FILE_NAMES.get(algorithm, algorithm)
    path = out_dir / f"{stem}_{file_name}_superficie_3d_{suffix}.png"
    plt.tight_layout()
    plt.savefig(path, dpi=190)
    plt.close(fig)
    return path


# Gera um conjunto de superficies usando pares de variaveis e agregando a terceira pela media.
def generate_pairwise_plots(csv_path: Path, out_dir: Path) -> list[Path]:
    df = load_csv(csv_path)
    aggregated = aggregate(df)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = csv_path.stem

    variations = [
        {
            "x_col": "n",
            "x_label": "Quantidade de itens (n)",
            "y_col": "W",
            "y_label": "Capacidade de peso (W)",
            "group_cols": ["algorithm", "n", "W"],
            "suffix": "peso_x_itens_agregando_volume",
            "title_suffix": "peso W e itens n",
        },
        {
            "x_col": "n",
            "x_label": "Quantidade de itens (n)",
            "y_col": "V",
            "y_label": "Capacidade de volume (V)",
            "group_cols": ["algorithm", "n", "V"],
            "suffix": "volume_x_itens_agregando_peso",
            "title_suffix": "volume V e itens n",
        },
        {
            "x_col": "W",
            "x_label": "Capacidade de peso (W)",
            "y_col": "V",
            "y_label": "Capacidade de volume (V)",
            "group_cols": ["algorithm", "W", "V"],
            "suffix": "volume_x_peso_agregando_itens",
            "title_suffix": "volume V e peso W",
        },
    ]

    generated: list[Path] = []
    for variation in variations:
        grouped = (
            aggregated.groupby(variation["group_cols"], observed=False)["mean_time_seconds"]
            .mean()
            .reset_index()
        )
        for algorithm in ["bt", "bb", "dp"]:
            data = grouped[grouped["algorithm"] == algorithm]
            if data.empty:
                continue
            generated.append(
                plot_surface(
                    data,
                    str(algorithm),
                    out_dir,
                    stem,
                    variation["x_col"],
                    variation["x_label"],
                    variation["y_col"],
                    variation["y_label"],
                    variation["suffix"],
                    variation["title_suffix"],
                )
            )

    return generated


# Gera exatamente uma superficie 3D para cada algoritmo no modo de capacidade igual.
def generate_capacity_plots(csv_path: Path, out_dir: Path, ignore_equal_capacity: bool) -> list[Path]:
    df = load_csv(csv_path)
    if ignore_equal_capacity:
        y_col = "W"
        y_label = "Capacidade de peso (W)"
        suffix = "peso_agregando_volume"
        title_suffix = "peso W e itens n"
    else:
        df = df[df["W"] == df["V"]].copy()
        if df.empty:
            raise SystemExit("Nao ha linhas no CSV em que W e V possuem o mesmo valor.")
        df["capacity"] = df["W"]
        y_col = "capacity"
        y_label = "Capacidade da mochila (W = V)"
        suffix = "capacidade_igual"
        title_suffix = "capacidade W=V e itens n"

    aggregated = aggregate(df)
    if ignore_equal_capacity:
        aggregated = (
            aggregated.groupby(["algorithm", "n", "W"], observed=False)["mean_time_seconds"]
            .mean()
            .reset_index()
        )
    else:
        aggregated["capacity"] = aggregated["W"]
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = csv_path.stem

    generated: list[Path] = []
    for algorithm in ["bt", "bb", "dp"]:
        data = aggregated[aggregated["algorithm"] == algorithm]
        if data.empty:
            continue
        generated.append(
            plot_surface(
                data,
                str(algorithm),
                out_dir,
                stem,
                "n",
                "Quantidade de itens (n)",
                y_col,
                y_label,
                suffix,
                title_suffix,
            )
        )

    return generated


# Ponto de entrada: interpreta argumentos e gera os arquivos PNG.
def main() -> None:
    parser = argparse.ArgumentParser(description="Gera graficos 3D a partir de um CSV de experimentos.")
    parser.add_argument("csv", help="Arquivo CSV gerado pelo run_experiments")
    parser.add_argument("--out-dir", default="graficos_3d", help="Diretorio de saida dos graficos")
    parser.add_argument(
        "--pairwise",
        action="store_true",
        help="Gera 9 graficos: peso x itens, volume x itens e volume x peso para cada algoritmo.",
    )
    parser.add_argument(
        "--ignore-equal-capacity",
        action="store_true",
        help="Nao filtra W=V. Usa W no eixo Y e agrega os tempos sobre os diferentes valores de V.",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.is_file():
        raise SystemExit(f"CSV nao encontrado: {csv_path}")

    if args.pairwise:
        generated = generate_pairwise_plots(csv_path, Path(args.out_dir))
    else:
        generated = generate_capacity_plots(csv_path, Path(args.out_dir), args.ignore_equal_capacity)
    print(f"Graficos gerados: {len(generated)}")
    for path in generated:
        print(path)


if __name__ == "__main__":
    main()
