### LIST FUNCTION
source /opt/gdb-src/mygdb/loader.py

### GLOBAL SETUP
set debuginfod enabled off
set history save off
set history filename ~/.gdb_history
set follow-fork-mode parent

### PWNDBG
define init-pwndbg
source /opt/gdb-src/pwndbg/gdbinit.py
end
document init-pwndbg
Initializes PwnDBG
end

### GEF
define init-gef
source /opt/gdb-src/gef/gef.py
end
document init-gef
Initializes GEF (GDB Enhanced Features)
end

### GEF-KERNEL
define init-gef-kernel
source /opt/gdb-src/gef-kernel/gef.py
end
document init-gef-kernel
Initializes GEF-KERNEL (GDB Enhanced Features)
end