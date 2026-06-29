#include "../include/common.hpp"

#include <filesystem>
#include <random>

// Exibe o modo de uso do gerador de instancias.
static void usage(const char *program) {
    std::cerr << "Uso: " << program
              << " <saida.txt> <n> <W> <V> [seed] [peso_item_max] [volume_item_max] [valor_max]\n";
}

// Le os parametros, gera itens aleatorios e grava a instancia em arquivo.
int main(int argc, char **argv) {
    if (argc < 5 || argc > 9) {
        usage(argv[0]);
        return 1;
    }

    try {
        const std::string outPath = argv[1];
        const int n = std::stoi(argv[2]);
        const int capacityWeight = std::stoi(argv[3]);
        const int capacityVolume = std::stoi(argv[4]);
        const unsigned seed = argc >= 6 ? static_cast<unsigned>(std::stoul(argv[5])) : std::random_device{}();
        const int maxItemWeight = argc >= 7 ? std::stoi(argv[6]) : std::max(1, capacityWeight);
        const int maxItemVolume = argc >= 8 ? std::stoi(argv[7]) : std::max(1, capacityVolume);
        const int maxValue = argc >= 9 ? std::stoi(argv[8]) : 1000;

        if (n <= 0 || capacityWeight <= 0 || capacityVolume <= 0 ||
            maxItemWeight <= 0 || maxItemVolume <= 0 || maxValue <= 0) {
            throw std::runtime_error("Todos os parametros numericos devem ser positivos.");
        }

        const std::filesystem::path path(outPath);
        const std::filesystem::path parent = path.parent_path();
        if (!parent.empty()) {
            std::filesystem::create_directories(parent);
        }

        std::mt19937 rng(seed);
        std::uniform_int_distribution<int> weightDist(1, maxItemWeight);
        std::uniform_int_distribution<int> volumeDist(1, maxItemVolume);
        std::uniform_int_distribution<int> valueDist(1, maxValue);

        std::ofstream out(outPath);
        if (!out) {
            throw std::runtime_error("Nao foi possivel criar: " + outPath);
        }

        out << capacityWeight << '\t' << capacityVolume << '\n';
        for (int i = 0; i < n; ++i) {
            out << weightDist(rng) << '\t'
                << volumeDist(rng) << '\t'
                << valueDist(rng) << '\n';
        }

        std::cout << "Instancia gerada: " << outPath << "\n";
        std::cout << "Seed: " << seed << "\n";
    } catch (const std::exception &ex) {
        std::cerr << "Erro: " << ex.what() << "\n";
        return 1;
    }

    return 0;
}
