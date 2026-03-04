# minimal in-GDB memory copy/paste/exchange/compare
import gdb
from ..memutils import _read, _write, SHAREDMEM
from .. import memutils

class _Exchange(gdb.Command):
    def __init__(self): super().__init__("exchange", gdb.COMMAND_DATA)
    def invoke(self, arg, from_tty):
        argv = gdb.string_to_argv(arg)
        if len(argv) != 3:
            gdb.write("Usage: exchange ADDR1 ADDR2 SIZE\n", gdb.STDERR); return
        addr1 = int(gdb.parse_and_eval(argv[0]))
        addr2 = int(gdb.parse_and_eval(argv[1]))
        size = int(gdb.parse_and_eval(argv[2]))
        try:
            data_addr1 = bytearray(_read(addr1, size))
            data_addr2 = bytearray(_read(addr2, size))
            _write(addr1, data_addr2)
            _write(addr2, data_addr1)
            gdb.write(f"[exchange] {size} bytes exchange {addr1:#x} with {addr2:#x}\n")
        except gdb.MemoryError:
            gdb.write("[exchange] memory read failed\n", gdb.STDERR)

class _Copy(gdb.Command):
    def __init__(self): super().__init__("copy", gdb.COMMAND_DATA)
    def invoke(self, arg, from_tty):
        argv = gdb.string_to_argv(arg)
        if len(argv) != 2:
            gdb.write("Usage: copy ADDR SIZE\n", gdb.STDERR); return
        addr = int(gdb.parse_and_eval(argv[0]))
        size = int(gdb.parse_and_eval(argv[1]))
        try:
            SHAREDMEM[:] = bytearray(_read(addr, size))
            memutils.SNAP_ADDR = addr
            memutils.SNAP_SIZE = size
            gdb.write(f"[copy] {size} bytes from {addr:#x}\n")
        except gdb.MemoryError:
            gdb.write("[copy] memory read failed\n", gdb.STDERR)

class _Paste(gdb.Command):
    def __init__(self): super().__init__("paste", gdb.COMMAND_DATA)
    def invoke(self, arg, from_tty):
        argv = gdb.string_to_argv(arg)
        if len(argv) != 1:
            gdb.write("Usage: paste ADDR\n", gdb.STDERR); return
        addr = int(gdb.parse_and_eval(argv[0]))
        if not SHAREDMEM:
            gdb.write("[paste] clipboard empty\n", gdb.STDERR); return
        try:
            _write(addr, SHAREDMEM)
            gdb.write(f"[paste] {len(SHAREDMEM)} bytes to {addr:#x}\n")
        except gdb.MemoryError:
            gdb.write("[paste] memory write failed\n", gdb.STDERR)

class _Compare(gdb.Command):
    def __init__(self): super().__init__("compare", gdb.COMMAND_DATA)
    def invoke(self, arg, from_tty):
        if gdb.string_to_argv(arg):
            gdb.write("Usage: compare\n", gdb.STDERR); return
        if memutils.SNAP_ADDR is None or memutils.SNAP_SIZE <= 0 or not SHAREDMEM:
            gdb.write("[compare] nothing copied yet. Do: copy ADDR SIZE\n", gdb.STDERR)
            return
        addr = memutils.SNAP_ADDR
        size = memutils.SNAP_SIZE
        try:
            cur = bytearray(_read(addr, size))
        except gdb.MemoryError:
            gdb.write("[compare] memory read failed\n", gdb.STDERR)
            return

        if cur == SHAREDMEM:
            gdb.write(f"[compare] no change at {addr:#x} (+{size:#x})\n")
            return

        diffs = []
        for i in range(size):
            a = SHAREDMEM[i]
            b = cur[i]
            if a != b:
                diffs.append((i, a, b))
        gdb.write(f"[compare] changed bytes: {len(diffs)}/{size} at {addr:#x}\n")
        cap = 32
        for (off, old, new) in diffs[:cap]:
            gdb.write(f"  {addr+off:#x}  +{off:#x}: {old:02x} -> {new:02x}\n")
        if len(diffs) > cap:
            gdb.write(f"  ... ({len(diffs)-cap} more)\n")

class _VimDiff(gdb.Command):
    def __init__(self): super().__init__("vdiff", gdb.COMMAND_DATA)
    def invoke(self, arg, from_tty):
        if gdb.string_to_argv(arg):
            gdb.write("Usage: vdiff\n", gdb.STDERR); return
        if memutils.SNAP_ADDR is None or memutils.SNAP_SIZE <= 0 or not SHAREDMEM:
            gdb.write("[vdiff] nothing copied yet. Do: copy ADDR SIZE\n", gdb.STDERR)
            return

        addr = memutils.SNAP_ADDR
        size = memutils.SNAP_SIZE

        try:
            cur = bytearray(_read(addr, size))
        except gdb.MemoryError:
            gdb.write("[vdiff] memory read failed\n", gdb.STDERR)
            return

        old = SHAREDMEM
        if cur == old:
            gdb.write(f"[vdiff] no change at {addr:#x} (+{size:#x})\n")
            return

        def u64_le(buf, off):
            b = buf[off:off+8]
            if len(b) < 8:
                b = b + b"\x00" * (8 - len(b))
            return int.from_bytes(b, "little")

        qcount = (size + 7) // 8
        changed = []
        for qi in range(qcount):
            off = qi * 8
            if old[off:off+8] != cur[off:off+8]:
                changed.append(qi)

        if not changed:
            gdb.write(f"[vdiff] no change at {addr:#x} (+{size:#x})\n")
            return

        base_qi = changed[0]
        base_addr = addr + base_qi * 8

        gdb.write("                                           OLD                    NEW\n")

        last_rel_qi = None
        for qi in changed:
            rel_qi = qi - base_qi
            if last_rel_qi is not None and rel_qi - last_rel_qi > 1:
                gdb.write("      ... skip ...\n")

            line_addr = addr + qi * 8
            rel_off = line_addr - base_addr
            old_q = u64_le(old, qi * 8)
            new_q = u64_le(cur, qi * 8)

            gdb.write(
                f"{line_addr:#018x}|+{rel_off:#06x}|+{rel_qi:03d}: "
                f"0x{old_q:016x} | 0x{new_q:016x}\n"
            )
            last_rel_qi = rel_qi

def register():
    _Copy()
    _Paste()
    _Exchange()
    _Compare()
    _VimDiff()
