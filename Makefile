CC      ?= gcc
CFLAGS  ?= -O3 -Wall
LDLIBS  := -lm -pthread

BIN_DIR := bin

SEQ_SRC  := $(firstword $(wildcard sequencial/*.c) $(wildcard src/sequencial*.c))
PROC_SRC := $(firstword $(wildcard processos/*.c) $(wildcard src/processes*.c))
THR_SRC  := $(firstword $(wildcard threads/*.c) $(wildcard src/threads*.c))

ALVOS := $(BIN_DIR)/sequencial \
         $(if $(PROC_SRC),$(BIN_DIR)/processos) \
         $(if $(THR_SRC),$(BIN_DIR)/threads)

all: $(ALVOS)

$(BIN_DIR):
	mkdir -p $(BIN_DIR)

$(BIN_DIR)/sequencial: $(SEQ_SRC) | $(BIN_DIR)
	$(CC) $(CFLAGS) $< -o $@ $(LDLIBS)

$(BIN_DIR)/processos: $(PROC_SRC) | $(BIN_DIR)
	$(CC) $(CFLAGS) $< -o $@ $(LDLIBS)

$(BIN_DIR)/threads: $(THR_SRC) | $(BIN_DIR)
	$(CC) $(CFLAGS) $< -o $@ $(LDLIBS)

clean:
	rm -rf $(BIN_DIR) *.ppm out/*.ppm

.PHONY: all clean
