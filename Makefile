CXX := g++
CXXFLAGS := -std=c++17 -O2 -Wall -Wextra -pedantic
BUILD_DIR := build

.PHONY: all clean

all: $(BUILD_DIR)/mochila_dp $(BUILD_DIR)/mochila_bt $(BUILD_DIR)/mochila_bb $(BUILD_DIR)/gerador_instancias $(BUILD_DIR)/run_experiments $(BUILD_DIR)/menu

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

$(BUILD_DIR)/mochila_dp: src/mochila_dp.cpp include/common.hpp | $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) $< -o $@

$(BUILD_DIR)/mochila_bt: src/mochila_bt.cpp include/common.hpp | $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) $< -o $@

$(BUILD_DIR)/mochila_bb: src/mochila_bb.cpp include/common.hpp | $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) $< -o $@

$(BUILD_DIR)/gerador_instancias: src/gerador_instancias.cpp include/common.hpp | $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) $< -o $@

$(BUILD_DIR)/run_experiments: src/run_experiments.cpp include/common.hpp | $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) $< -o $@

$(BUILD_DIR)/menu: src/menu.cpp | $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) $< -o $@

clean:
	rm -rf build instances results
