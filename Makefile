CC      ?= gcc
CFLAGS  ?= -O3 -Wall
CFLAGS  += -Icomum
LDLIBS  := -lm -pthread

BIN_DIR := bin
COMUM   := comum/mandelbrot.c comum/mandelbrot.h

all: $(BIN_DIR)/sequencial $(BIN_DIR)/processos $(BIN_DIR)/threads | out

# bin/: executáveis | out/: imagens geradas (usada nos exemplos e nos testes)
$(BIN_DIR) out:
	mkdir -p $@

# Cada executável = seu código-fonte + a lib comum (comum/mandelbrot.c)
$(BIN_DIR)/sequencial: sequencial/sequencial.c $(COMUM) | $(BIN_DIR)
	$(CC) $(CFLAGS) $(filter %.c,$^) -o $@ $(LDLIBS)

$(BIN_DIR)/processos: processos/processos.c $(COMUM) | $(BIN_DIR)
	$(CC) $(CFLAGS) $(filter %.c,$^) -o $@ $(LDLIBS)

$(BIN_DIR)/threads: threads/threads.c $(COMUM) | $(BIN_DIR)
	$(CC) $(CFLAGS) $(filter %.c,$^) -o $@ $(LDLIBS)

clean:
	rm -rf $(BIN_DIR) *.ppm out/*.ppm

.PHONY: all clean
