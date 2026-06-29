#include "../include/common.hpp"

#include <cstdio>
#include <filesystem>
#include <limits>
#include <random>

#ifdef _WIN32
#define popen _popen
#define pclose _pclose
#endif

// Converte uma lista separada por virgulas em vetor de inteiros.
static std::vector<int> parseList(const std::string &text) {
    std::vector<int> values;
    std::stringstream ss(text);
    std::string part;
    while (std::getline(ss, part, ',')) {
        if (!part.empty()) {
            values.push_back(std::stoi(part));
        }
    }
    if (values.empty()) {
        throw std::runtime_error("Lista vazia: " + text);
    }
    return values;
}

// Coloca aspas duplas em caminhos usados nos comandos externos.
static std::string quote(const std::string &path) {
    return "\"" + path + "\"";
}

// Ajusta o diretorio atual para a raiz do projeto quando executado a partir de build.
static void enterProjectRoot(const char *programPath) {
    std::filesystem::path path(programPath);
    if (!path.has_parent_path()) {
        return;
    }

    path = std::filesystem::absolute(path).parent_path();
    if (path.filename() == "build") {
        std::filesystem::current_path(path.parent_path());
    }
}

// Executa um comando e captura toda a saida padrao produzida por ele.
static std::string runAndCapture(const std::string &command) {
    FILE *pipe = popen(command.c_str(), "r");
    if (!pipe) {
        throw std::runtime_error("Falha ao executar: " + command);
    }

    std::string output;
    char buffer[512];
    while (fgets(buffer, sizeof(buffer), pipe)) {
        output += buffer;
    }

    int status = pclose(pipe);
    if (status != 0) {
        throw std::runtime_error("Comando falhou: " + command + "\n" + output);
    }
    return output;
}

// Extrai o lucro maximo da saida textual de um algoritmo.
static long long parseProfit(const std::string &output) {
    std::istringstream in(output);
    std::string line;
    while (std::getline(in, line)) {
        const std::string marker = "Lucro maximo:";
        if (line.rfind(marker, 0) == 0) {
            return std::stoll(line.substr(marker.size()));
        }
    }
    throw std::runtime_error("Lucro maximo nao encontrado na saida:\n" + output);
}

// Extrai o tempo de execucao da saida textual de um algoritmo.
static double parseTime(const std::string &output) {
    std::istringstream in(output);
    std::string line;
    while (std::getline(in, line)) {
        const std::string marker = "Tempo:";
        if (line.rfind(marker, 0) == 0) {
            std::stringstream ss(line.substr(marker.size()));
            double seconds;
            ss >> seconds;
            return seconds;
        }
    }
    throw std::runtime_error("Tempo nao encontrado na saida:\n" + output);
}

// Extrai a lista de itens escolhidos da saida textual de um algoritmo.
static std::string parseChosenItems(const std::string &output) {
    std::istringstream in(output);
    std::string line;
    while (std::getline(in, line)) {
        const std::string marker = "Itens escolhidos:";
        if (line.rfind(marker, 0) == 0) {
            std::string chosen = line.substr(marker.size());
            while (!chosen.empty() && chosen.front() == ' ') {
                chosen.erase(chosen.begin());
            }
            if (chosen == "nenhum") {
                return "";
            }
            return chosen;
        }
    }
    throw std::runtime_error("Itens escolhidos nao encontrados na saida:\n" + output);
}

// Escapa texto para ser escrito com seguranca em uma celula CSV.
static std::string csvText(const std::string &text) {
    std::string escaped = "\"";
    for (char c : text) {
        if (c == '"') {
            escaped += "\"\"";
        } else {
            escaped += c;
        }
    }
    escaped += "\"";
    return escaped;
}

// Gera uma instancia aleatoria usada pelos experimentos automatizados.
static void generateInstance(const std::string &path, int n, int w, int v, unsigned seed) {
    const std::filesystem::path parent = std::filesystem::path(path).parent_path();
    if (!parent.empty()) {
        std::filesystem::create_directories(parent);
    }

    std::mt19937 rng(seed);
    std::uniform_int_distribution<int> weightDist(1, std::max(1, w));
    std::uniform_int_distribution<int> volumeDist(1, std::max(1, v));
    std::uniform_int_distribution<int> valueDist(1, 1000);

    std::ofstream out(path);
    if (!out) {
        throw std::runtime_error("Nao foi possivel criar instancia: " + path);
    }
    out << w << '\t' << v << '\n';
    for (int i = 0; i < n; ++i) {
        out << weightDist(rng) << '\t' << volumeDist(rng) << '\t' << valueDist(rng) << '\n';
    }
}

// Exibe o modo de uso do runner de experimentos.
static void usage(const char *program) {
    std::cerr
        << "Uso: " << program << " --n 10,20 --w 50,100 --v 50,100 --out resultados.csv [--reps 10] [--seed 123]\n";
}

// Processa os parametros, gera instancias, executa algoritmos e grava o CSV.
int main(int argc, char **argv) {
    if (argc > 0) {
        enterProjectRoot(argv[0]);
    }

    std::string nText, wText, vText, outPath = "results/resultados.csv";
    int reps = 10;
    unsigned baseSeed = std::random_device{}();

    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        auto requireValue = [&](const std::string &name) -> std::string {
            if (i + 1 >= argc) {
                throw std::runtime_error("Parametro sem valor: " + name);
            }
            return argv[++i];
        };

        if (arg == "--n") nText = requireValue(arg);
        else if (arg == "--w") wText = requireValue(arg);
        else if (arg == "--v") vText = requireValue(arg);
        else if (arg == "--reps") reps = std::stoi(requireValue(arg));
        else if (arg == "--out") outPath = requireValue(arg);
        else if (arg == "--seed") baseSeed = static_cast<unsigned>(std::stoul(requireValue(arg)));
        else {
            usage(argv[0]);
            return 1;
        }
    }

    if (nText.empty() || wText.empty() || vText.empty() || reps <= 0) {
        usage(argv[0]);
        return 1;
    }

    try {
        std::vector<int> nValues = parseList(nText);
        std::vector<int> wValues = parseList(wText);
        std::vector<int> vValues = parseList(vText);

        const std::filesystem::path outAbsolutePath = std::filesystem::absolute(outPath);
        const std::filesystem::path outParent = outAbsolutePath.parent_path();
        if (!outParent.empty()) {
            std::filesystem::create_directories(outParent);
        }
        std::ofstream csv(outAbsolutePath);
        if (!csv) {
            throw std::runtime_error("Nao foi possivel criar CSV: " + outAbsolutePath.string());
        }

        const std::vector<std::pair<std::string, std::string>> algorithms = {
            {"dp", "./build/mochila_dp"},
            {"bt", "./build/mochila_bt"},
            {"bb", "./build/mochila_bb"},
        };

        csv << "n,W,V,rep,instance,algorithm,profit,chosen_items,time_seconds,time_unit\n";
        csv.flush();
        std::cout << "Diretorio atual: " << std::filesystem::current_path().string() << "\n";
        std::cout << "Gerando CSV em: " << outAbsolutePath.string() << "\n";

        for (int n : nValues) {
            for (int w : wValues) {
                for (int v : vValues) {
                    for (int rep = 1; rep <= reps; ++rep) {
                        std::seed_seq seedSequence{baseSeed, static_cast<unsigned>(n),
                                                   static_cast<unsigned>(w),
                                                   static_cast<unsigned>(v),
                                                   static_cast<unsigned>(rep)};
                        std::vector<unsigned> generatedSeeds(1);
                        seedSequence.generate(generatedSeeds.begin(), generatedSeeds.end());
                        unsigned seed = generatedSeeds.front();
                        std::string instancePath = "instances/n" + std::to_string(n)
                            + "_w" + std::to_string(w)
                            + "_v" + std::to_string(v)
                            + "_r" + std::to_string(rep) + ".txt";
                        generateInstance(instancePath, n, w, v, seed);

                        for (const auto &algorithm : algorithms) {
                            const std::string command = quote(algorithm.second) + " " + quote(instancePath);
                            const std::string output = runAndCapture(command);
                            const long long profit = parseProfit(output);
                            const std::string chosenItems = parseChosenItems(output);
                            const double seconds = parseTime(output);

                            csv << n << ',' << w << ',' << v << ',' << rep << ','
                                << instancePath << ',' << algorithm.first
                                << ',' << profit << ',' << csvText(chosenItems)
                                << ',' << std::fixed << std::setprecision(9)
                                << seconds << ",seconds\n";
                            csv.flush();

                            std::cout << "n=" << n << " W=" << w << " V=" << v
                                      << " rep=" << rep << " alg=" << algorithm.first
                                      << " tempo=" << seconds << "s\n";
                        }
                    }
                }
            }
        }

        std::cout << "CSV gerado: " << outPath << "\n";
    } catch (const std::exception &ex) {
        std::cerr << "Erro: " << ex.what() << "\n";
        return 1;
    }

    return 0;
}
