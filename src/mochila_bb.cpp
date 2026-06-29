#include "../include/common.hpp"

// Associa um item a sua posicao na ordem principal da busca.
struct BBItem {
    Item item;
    int orderPos;
};

// Implementa o resolvedor branch-and-bound com solucao inicial gulosa e podas.
struct BranchAndBoundSolver {
    Instance inst;
    std::vector<Item> items;
    std::vector<BBItem> weightOrder;
    std::vector<BBItem> volumeOrder;
    std::vector<long long> suffixValue;
    long long bestValue = 0;
    std::vector<int> currentChosen;
    std::vector<int> bestChosen;

    // Ordena os itens e prepara estruturas auxiliares para calcular limites superiores.
    explicit BranchAndBoundSolver(const Instance &instance) : inst(instance), items(instance.items) {
        std::sort(items.begin(), items.end(), [&](const Item &a, const Item &b) {
            return normalizedDensity(a, inst.capacityWeight, inst.capacityVolume)
                 > normalizedDensity(b, inst.capacityWeight, inst.capacityVolume);
        });

        suffixValue.assign(items.size() + 1, 0);
        for (int i = static_cast<int>(items.size()) - 1; i >= 0; --i) {
            suffixValue[i] = suffixValue[i + 1] + items[i].value;
        }

        weightOrder.reserve(items.size());
        volumeOrder.reserve(items.size());
        for (int i = 0; i < static_cast<int>(items.size()); ++i) {
            weightOrder.push_back({items[i], i});
            volumeOrder.push_back({items[i], i});
        }

        std::sort(weightOrder.begin(), weightOrder.end(), [](const BBItem &a, const BBItem &b) {
            return static_cast<double>(a.item.value) / a.item.weight
                 > static_cast<double>(b.item.value) / b.item.weight;
        });
        std::sort(volumeOrder.begin(), volumeOrder.end(), [](const BBItem &a, const BBItem &b) {
            return static_cast<double>(a.item.value) / a.item.volume
                 > static_cast<double>(b.item.value) / b.item.volume;
        });
    }

    // Calcula um limite superior fracionario considerando apenas a restricao de peso.
    double boundByWeight(int pos, int remainingWeight, long long value) const {
        if (remainingWeight < 0) {
            return 0.0;
        }

        double bound = value;
        int capacity = remainingWeight;
        for (const BBItem &candidate : weightOrder) {
            if (candidate.orderPos < pos) {
                continue;
            }
            const Item &item = candidate.item;
            if (item.weight <= capacity) {
                capacity -= item.weight;
                bound += item.value;
            } else {
                bound += static_cast<double>(item.value) * capacity / item.weight;
                break;
            }
        }
        return bound;
    }

    // Calcula um limite superior fracionario considerando apenas a restricao de volume.
    double boundByVolume(int pos, int remainingVolume, long long value) const {
        if (remainingVolume < 0) {
            return 0.0;
        }

        double bound = value;
        int capacity = remainingVolume;
        for (const BBItem &candidate : volumeOrder) {
            if (candidate.orderPos < pos) {
                continue;
            }
            const Item &item = candidate.item;
            if (item.volume <= capacity) {
                capacity -= item.volume;
                bound += item.value;
            } else {
                bound += static_cast<double>(item.value) * capacity / item.volume;
                break;
            }
        }
        return bound;
    }

    // Combina limites superiores para decidir se um ramo ainda pode melhorar a solucao.
    double upperBound(int pos, int weight, int volume, long long value) const {
        if (weight > inst.capacityWeight || volume > inst.capacityVolume) {
            return 0.0;
        }

        const double byRemainingValue = static_cast<double>(value + suffixValue[pos]);
        const double byWeight = boundByWeight(pos, inst.capacityWeight - weight, value);
        const double byVolume = boundByVolume(pos, inst.capacityVolume - volume, value);
        return std::min(byRemainingValue, std::min(byWeight, byVolume));
    }

    // Constroi uma solucao inicial gulosa para aumentar o poder das podas.
    void greedyInitialSolution() {
        int weight = 0;
        int volume = 0;
        long long value = 0;
        std::vector<int> chosen;

        for (const Item &item : items) {
            if (weight + item.weight <= inst.capacityWeight &&
                volume + item.volume <= inst.capacityVolume) {
                weight += item.weight;
                volume += item.volume;
                value += item.value;
                chosen.push_back(item.index);
            }
        }

        bestValue = value;
        bestChosen = chosen;
    }

    // Explora a arvore de decisao incluindo ou ignorando itens, podando ramos ruins.
    void search(int pos, int weight, int volume, long long value) {
        if (weight > inst.capacityWeight || volume > inst.capacityVolume) {
            return;
        }

        if (value > bestValue) {
            bestValue = value;
            bestChosen = currentChosen;
        }

        if (pos == static_cast<int>(items.size())) {
            return;
        }

        if (upperBound(pos, weight, volume, value) <= static_cast<double>(bestValue)) {
            return;
        }

        const Item &item = items[pos];

        if (weight + item.weight <= inst.capacityWeight &&
            volume + item.volume <= inst.capacityVolume) {
            currentChosen.push_back(item.index);
            search(pos + 1, weight + item.weight, volume + item.volume, value + item.value);
            currentChosen.pop_back();
        }

        search(pos + 1, weight, volume, value);
    }

    // Executa a solucao gulosa inicial, a busca branch-and-bound e mede o tempo.
    Solution solve() {
        auto start = std::chrono::steady_clock::now();

        greedyInitialSolution();
        search(0, 0, 0, 0);

        auto end = std::chrono::steady_clock::now();
        Solution sol;
        sol.profit = bestValue;
        sol.chosen = bestChosen;
        sol.seconds = elapsedSeconds(start, end);
        return sol;
    }
};

// Cria o resolvedor branch-and-bound e retorna a solucao final.
static Solution solveBranchAndBound(const Instance &inst) {
    BranchAndBoundSolver solver(inst);
    return solver.solve();
}

// Le a instancia, executa o branch-and-bound e imprime a solucao.
int main(int argc, char **argv) {
    if (argc != 2) {
        std::cerr << "Uso: " << argv[0] << " <arquivo_instancia>\n";
        return 1;
    }

    try {
        Instance inst = readInstance(argv[1]);
        printSolution("Branch-and-Bound", solveBranchAndBound(inst));
    } catch (const std::exception &ex) {
        std::cerr << "Erro: " << ex.what() << "\n";
        return 1;
    }

    return 0;
}
