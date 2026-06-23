#ifndef COMMON_HPP
#define COMMON_HPP

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

struct Item {
    int index;
    int weight;
    int volume;
    int value;
};

struct Instance {
    int capacityWeight;
    int capacityVolume;
    std::vector<Item> items;
};

struct Solution {
    long long profit = 0;
    std::vector<int> chosen;
    double seconds = 0.0;
};

inline Instance readInstance(const std::string &path) {
    std::ifstream in(path);
    if (!in) {
        throw std::runtime_error("Nao foi possivel abrir o arquivo: " + path);
    }

    Instance inst;
    if (!(in >> inst.capacityWeight >> inst.capacityVolume)) {
        throw std::runtime_error("Primeira linha invalida. Esperado: W V");
    }
    if (inst.capacityWeight < 0 || inst.capacityVolume < 0) {
        throw std::runtime_error("Capacidades devem ser nao negativas.");
    }

    int weight, volume, value;
    int index = 1;
    while (in >> weight >> volume >> value) {
        if (weight <= 0 || volume <= 0 || value <= 0) {
            throw std::runtime_error("Itens devem ter peso, volume e valor inteiros positivos.");
        }
        inst.items.push_back({index++, weight, volume, value});
    }

    return inst;
}

inline void sortChosen(std::vector<int> &chosen) {
    std::sort(chosen.begin(), chosen.end());
}

inline void printSolution(const std::string &algorithm, Solution sol) {
    sortChosen(sol.chosen);
    std::cout << "Algoritmo: " << algorithm << "\n";
    std::cout << "Lucro maximo: " << sol.profit << "\n";
    std::cout << "Itens escolhidos:";
    if (sol.chosen.empty()) {
        std::cout << " nenhum";
    } else {
        for (int id : sol.chosen) {
            std::cout << ' ' << id;
        }
    }
    std::cout << "\n";
    std::cout << std::fixed << std::setprecision(9)
              << "Tempo: " << sol.seconds << " segundos\n";
}

inline double elapsedSeconds(std::chrono::steady_clock::time_point start,
                             std::chrono::steady_clock::time_point end) {
    return std::chrono::duration<double>(end - start).count();
}

inline double normalizedDensity(const Item &item, int capacityWeight, int capacityVolume) {
    const double w = capacityWeight > 0 ? static_cast<double>(item.weight) / capacityWeight : item.weight;
    const double v = capacityVolume > 0 ? static_cast<double>(item.volume) / capacityVolume : item.volume;
    return static_cast<double>(item.value) / (w + v);
}

inline long long totalValueFrom(const std::vector<Item> &items, int start) {
    long long total = 0;
    for (int i = start; i < static_cast<int>(items.size()); ++i) {
        total += items[i].value;
    }
    return total;
}

#endif
