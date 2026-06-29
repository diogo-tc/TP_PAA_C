#include "../include/common.hpp"

#include <unordered_map>

// Representa um estado da DP, guardando valor e ponteiro para reconstruir a solucao.
struct State {
    long long value;
    int node;
};

// Guarda a ligacao entre uma escolha feita e o estado anterior.
struct ParentNode {
    int itemIndex;
    int previous;
};

// Empacota peso e volume em uma chave unica para usar no mapa de estados.
static std::uint64_t makeKey(int weight, int volume) {
    return (static_cast<std::uint64_t>(static_cast<std::uint32_t>(weight)) << 32)
           | static_cast<std::uint32_t>(volume);
}

// Recupera o peso armazenado em uma chave de estado.
static int keyWeight(std::uint64_t key) {
    return static_cast<int>(key >> 32);
}

// Recupera o volume armazenado em uma chave de estado.
static int keyVolume(std::uint64_t key) {
    return static_cast<int>(key & 0xffffffffu);
}

// Estrutura auxiliar para consultar rapidamente dominancia por volume e valor.
class FenwickMax {
public:
    // Inicializa a arvore Fenwick com valores sentinela.
    explicit FenwickMax(int n) : tree(n + 1, -1) {}

    // Atualiza o melhor valor conhecido para um indice de volume.
    void update(int index, long long value) {
        for (++index; index < static_cast<int>(tree.size()); index += index & -index) {
            tree[index] = std::max(tree[index], value);
        }
    }

    // Consulta o maior valor ate um indice de volume.
    long long query(int index) const {
        long long best = -1;
        for (++index; index > 0; index -= index & -index) {
            best = std::max(best, tree[index]);
        }
        return best;
    }

private:
    std::vector<long long> tree;
};

// Remove estados dominados para reduzir memoria e tempo da programacao dinamica.
static void pruneDominated(std::unordered_map<std::uint64_t, State> &states, int capacityVolume) {
    struct Entry {
        int weight;
        int volume;
        std::uint64_t key;
        long long value;
    };

    std::vector<Entry> entries;
    entries.reserve(states.size());
    for (const auto &kv : states) {
        entries.push_back({keyWeight(kv.first), keyVolume(kv.first), kv.first, kv.second.value});
    }

    std::sort(entries.begin(), entries.end(), [](const Entry &a, const Entry &b) {
        if (a.weight != b.weight) return a.weight < b.weight;
        return a.volume < b.volume;
    });

    FenwickMax fenwick(capacityVolume);
    std::vector<std::uint64_t> dominated;
    dominated.reserve(entries.size() / 4);

    for (const auto &e : entries) {
        if (fenwick.query(e.volume) >= e.value) {
            dominated.push_back(e.key);
        } else {
            fenwick.update(e.volume, e.value);
        }
    }

    for (std::uint64_t key : dominated) {
        states.erase(key);
    }
}

// Resolve a mochila usando programacao dinamica com estados esparsos.
static Solution solveDP(const Instance &inst) {
    auto start = std::chrono::steady_clock::now();

    std::unordered_map<std::uint64_t, State> states;
    states.reserve(1024);
    std::vector<ParentNode> parents;
    parents.push_back({0, -1});
    states.emplace(makeKey(0, 0), State{0, 0});

    for (int itemPos = 0; itemPos < static_cast<int>(inst.items.size()); ++itemPos) {
        const Item &item = inst.items[itemPos];
        std::vector<std::pair<std::uint64_t, State>> snapshot;
        snapshot.reserve(states.size());
        for (const auto &kv : states) {
            snapshot.push_back(kv);
        }

        for (const auto &kv : snapshot) {
            const int weight = keyWeight(kv.first) + item.weight;
            const int volume = keyVolume(kv.first) + item.volume;
            if (weight > inst.capacityWeight || volume > inst.capacityVolume) {
                continue;
            }

            const long long candidate = kv.second.value + item.value;
            const std::uint64_t key = makeKey(weight, volume);
            auto it = states.find(key);
            if (it == states.end() || candidate > it->second.value) {
                parents.push_back({item.index, kv.second.node});
                states[key] = {candidate, static_cast<int>(parents.size()) - 1};
            }
        }

        if (states.size() > 200000 && itemPos % 5 == 4) {
            pruneDominated(states, inst.capacityVolume);
        }
    }

    std::uint64_t bestKey = makeKey(0, 0);
    State best{0, 0};
    for (const auto &kv : states) {
        if (kv.second.value > best.value) {
            bestKey = kv.first;
            best = kv.second;
        }
    }
    (void)bestKey;

    Solution sol;
    sol.profit = best.value;
    for (int node = best.node; node > 0; node = parents[node].previous) {
        sol.chosen.push_back(parents[node].itemIndex);
    }

    auto end = std::chrono::steady_clock::now();
    sol.seconds = elapsedSeconds(start, end);
    return sol;
}

// Le a instancia, executa a programacao dinamica e imprime a solucao.
int main(int argc, char **argv) {
    if (argc != 2) {
        std::cerr << "Uso: " << argv[0] << " <arquivo_instancia>\n";
        return 1;
    }

    try {
        Instance inst = readInstance(argv[1]);
        printSolution("Programacao Dinamica", solveDP(inst));
    } catch (const std::exception &ex) {
        std::cerr << "Erro: " << ex.what() << "\n";
        return 1;
    }

    return 0;
}
