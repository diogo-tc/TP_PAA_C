#include <cstdlib>
#include <filesystem>
#include <iostream>
#include <random>
#include <string>

static int readInt(const std::string &label, int minValue = 1) {
    while (true) {
        std::cout << label;
        std::string line;
        std::getline(std::cin, line);

        try {
            int value = std::stoi(line);
            if (value >= minValue) {
                return value;
            }
        } catch (...) {
        }

        std::cout << "Valor invalido. Digite um inteiro >= " << minValue << ".\n";
    }
}

static std::string readText(const std::string &label, const std::string &defaultValue = "") {
    std::cout << label;
    if (!defaultValue.empty()) {
        std::cout << " [" << defaultValue << "]";
    }
    std::cout << ": ";

    std::string value;
    std::getline(std::cin, value);
    if (value.empty()) {
        return defaultValue;
    }
    return value;
}

static std::string quote(const std::string &value) {
    return "'" + value + "'";
}

static int runCommand(const std::string &command) {
    std::cout << "\nExecutando: " << command << "\n\n";
    int status = std::system(command.c_str());
    if (status != 0) {
        std::cout << "Comando finalizou com erro. Verifique se o projeto foi compilado com make.\n";
    }
    std::cout << "\n";
    return status;
}

static void enterProjectRoot(const char *programPath) {
    std::filesystem::path path(programPath);
    if (path.has_parent_path()) {
        path = std::filesystem::absolute(path).parent_path();
        if (path.filename() == "build") {
            std::filesystem::current_path(path.parent_path());
        }
    }
}

static std::string algorithmExecutable(int option) {
    switch (option) {
        case 1: return "./build/mochila_dp";
        case 2: return "./build/mochila_bt";
        case 3: return "./build/mochila_bb";
        default: return "";
    }
}

static void generateInstance() {
    const std::string path = readText("Arquivo de saida", "instances/manual.txt");
    const int n = readInt("Quantidade de itens: ");
    const int capacityWeight = readInt("Peso maximo da mochila (W): ");
    const int capacityVolume = readInt("Volume maximo da mochila (V): ");
    const int itemWeightMax = readInt("Peso maximo de cada item: ");
    const int itemVolumeMax = readInt("Volume maximo de cada item: ");
    const int valueMax = readInt("Valor maximo de cada item: ");
    const unsigned seed = std::random_device{}();

    std::string command = "./build/gerador_instancias "
        + quote(path) + " "
        + std::to_string(n) + " "
        + std::to_string(capacityWeight) + " "
        + std::to_string(capacityVolume) + " "
        + std::to_string(seed) + " "
        + std::to_string(itemWeightMax) + " "
        + std::to_string(itemVolumeMax) + " "
        + std::to_string(valueMax);
    runCommand(command);
}

static void runOneAlgorithm() {
    std::cout << "Algoritmo 1: Programacao dinamica\n";
    std::cout << "Algoritmo 2: Backtracking com poda\n";
    std::cout << "Algoritmo 3: Branch-and-bound\n";
    const int algorithm = readInt("Escolha o algoritmo: ", 1);
    if (algorithm > 3) {
        std::cout << "Algoritmo invalido.\n";
        return;
    }

    const std::string instance = readText("Arquivo da instancia", "instances/manual.txt");
    runCommand(algorithmExecutable(algorithm) + " " + quote(instance));
}

static void runAllAlgorithms() {
    const std::string instance = readText("Arquivo da instancia", "instances/manual.txt");
    for (int algorithm = 1; algorithm <= 3; ++algorithm) {
        runCommand(algorithmExecutable(algorithm) + " " + quote(instance));
    }
}

static void runCsvExperiment() {
    std::cout << "Use listas separadas por virgula para testar varias combinacoes.\n";
    std::cout << "Serao geradas 10 instancias aleatorias para cada combinacao n x W x V.\n";
    const std::string nValues = readText("Quantidades de itens", "10,20,30");
    const std::string wValues = readText("Pesos maximos W", "50,100");
    const std::string vValues = readText("Volumes maximos V", "50,100");
    const std::string output = readText("CSV de saida", "results/resultados.csv");

    std::string command = "./build/run_experiments --n " + quote(nValues)
        + " --w " + quote(wValues)
        + " --v " + quote(vValues)
        + " --reps 10"
        + " --out " + quote(output);
    runCommand(command);
}

static void printMenu() {
    std::cout << "========================================\n";
    std::cout << "Mochila 0-1 com duas restricoes\n";
    std::cout << "========================================\n";
    std::cout << "1. Gerar instancia\n";
    std::cout << "2. Rodar um algoritmo\n";
    std::cout << "3. Rodar os tres algoritmos\n";
    std::cout << "4. Rodar experimento e gerar CSV\n";
    std::cout << "0. Sair\n";
}

int main(int argc, char **argv) {
    if (argc > 0) {
        enterProjectRoot(argv[0]);
    }

    while (true) {
        printMenu();
        const int option = readInt("Opcao: ", 0);
        std::cout << "\n";

        switch (option) {
            case 1:
                generateInstance();
                break;
            case 2:
                runOneAlgorithm();
                break;
            case 3:
                runAllAlgorithms();
                break;
            case 4:
                runCsvExperiment();
                break;
            case 0:
                return 0;
            default:
                std::cout << "Opcao invalida.\n";
                break;
        }
    }
}
