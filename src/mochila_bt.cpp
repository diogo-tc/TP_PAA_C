#include "../include/common.hpp"

// Implementa o resolvedor por backtracking com ordenacao e podas.
struct BacktrackingSolver {
    Instance inst;
    std::vector<Item> items;
    std::vector<long long> suffixValue;
    long long bestValue = 0;
    std::vector<int> bestChosen;
    std::vector<int> currentChosen;

    // Prepara os itens ordenados e a soma de valores restantes para poda.
    explicit BacktrackingSolver(const Instance &instance) : inst(instance), items(instance.items) {
        std::sort(items.begin(), items.end(), [&](const Item &a, const Item &b) {
            return normalizedDensity(a, inst.capacityWeight, inst.capacityVolume)
                 > normalizedDensity(b, inst.capacityWeight, inst.capacityVolume);
        });

        suffixValue.assign(items.size() + 1, 0);
        for (int i = static_cast<int>(items.size()) - 1; i >= 0; --i) {
            suffixValue[i] = suffixValue[i + 1] + items[i].value;
        }
    }

    // Explora recursivamente incluir ou nao incluir cada item, aplicando podas.
    void search(int pos, int weight, int volume, long long value) {
        if (weight > inst.capacityWeight || volume > inst.capacityVolume) {
            return;
        }
        if (value + suffixValue[pos] <= bestValue) {
            return;
        }
        if (pos == static_cast<int>(items.size())) {
            if (value > bestValue) {
                bestValue = value;
                bestChosen = currentChosen;
            }
            return;
        }

        const Item &item = items[pos];

        currentChosen.push_back(item.index);
        search(pos + 1, weight + item.weight, volume + item.volume, value + item.value);
        currentChosen.pop_back();

        search(pos + 1, weight, volume, value);
    }

    // Executa a busca completa e devolve a melhor solucao encontrada.
    Solution solve() {
        auto start = std::chrono::steady_clock::now();
        search(0, 0, 0, 0);
        auto end = std::chrono::steady_clock::now();

        Solution sol;
        sol.profit = bestValue;
        sol.chosen = bestChosen;
        sol.seconds = elapsedSeconds(start, end);
        return sol;
    }
};

// Le a instancia, executa o backtracking e imprime a solucao.
int main(int argc, char **argv) {
    if (argc != 2) {
        std::cerr << "Uso: " << argv[0] << " <arquivo_instancia>\n";
        return 1;
    }

    try {
        Instance inst = readInstance(argv[1]);
        BacktrackingSolver solver(inst);
        printSolution("Backtracking", solver.solve());
    } catch (const std::exception &ex) {
        std::cerr << "Erro: " << ex.what() << "\n";
        return 1;
    }

    return 0;
}
