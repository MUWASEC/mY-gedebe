### LIST FUNCTION
source /opt/gdb-src/custom.py

### GLOBAL SETUP
set debuginfod enabled off
set history save off
set history filename /.gdb_history
set follow-fork-mode parent

### GEF-KERNEL
define init-gef-kernel
source /opt/gdb-src/gef-kernel/gef.py
end
document init-gef-kernel
Initializes GEF-KERNEL (GDB Enhanced Features)
end