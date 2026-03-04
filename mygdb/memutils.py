import gdb

SHAREDMEM = bytearray()
SNAP_ADDR = None
SNAP_SIZE = 0

def _read(addr: int, size: int) -> bytes:
    return gdb.selected_inferior().read_memory(addr, size).tobytes()

def _write(addr: int, data: bytes) -> None:
    gdb.selected_inferior().write_memory(addr, data)
