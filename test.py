#!/usr/bin/python3
import sys, os, glob
from cpu import CPU, REGISTERS_COUNT, XMASK
from memory import Memory
from compile import compile_asm_to_bytes

TEST_DIR = os.path.join(os.path.dirname(__file__), "test")

def run_test(asm_path, expected_regs, expected_csrs=None):
    """Compile and run a single test, checking expected register and CSR values."""
    if expected_csrs is None:
        expected_csrs = {}
    compiled_bytes = [b for b in compile_asm_to_bytes(asm_path)]
    mem = Memory(preloaded_bytes=compiled_bytes)
    cpu = CPU(mem)

    # Suppress logging during tests
    import logging
    logging.disable(logging.CRITICAL)

    try:
        cpu.start()
    except SystemExit:
        pass

    passed = True
    for reg, expected in expected_regs.items():
        actual = cpu.registers[reg] & XMASK
        expected = expected & XMASK
        if actual != expected:
            passed = False
            print(f"  FAIL: x{reg} = 0x{actual:x}, expected 0x{expected:x}")

    for csr_addr, expected in expected_csrs.items():
        actual = cpu.csrs[csr_addr] & XMASK
        expected = expected & XMASK
        if actual != expected:
            passed = False
            print(f"  FAIL: csr[{csr_addr:#05x}] = 0x{actual:x}, expected 0x{expected:x}")

    return passed

def discover_tests():
    """Find all .s files in the test directory and their expected register/CSR values."""
    tests = []
    for asm_file in sorted(glob.glob(os.path.join(TEST_DIR, "*.s"))):
        expected_regs = parse_expected_regs(asm_file)
        expected_csrs = parse_expected_csrs(asm_file)
        tests.append((asm_file, expected_regs, expected_csrs))
    return tests

def parse_expected_regs(asm_path):
    """Parse expected register values from comments like # expect x31=42."""
    expected = {}
    with open(asm_path) as f:
        for line in f:
            line = line.strip()
            if line.startswith("# expect "):
                parts = line[len("# expect "):].split(",")
                for part in parts:
                    part = part.strip()
                    if "=" in part and not part.startswith("csr["):
                        reg, val = part.split("=", 1)
                        reg = reg.strip().lstrip("x")
                        expected[int(reg, 0)] = int(val.strip(), 0)
    return expected


def parse_expected_csrs(asm_path):
    """Parse expected CSR values from comments like # expect csr[0x300]=0xAB."""
    expected = {}
    with open(asm_path) as f:
        for line in f:
            line = line.strip()
            if line.startswith("# expect "):
                parts = line[len("# expect "):].split(",")
                for part in parts:
                    part = part.strip()
                    if part.startswith("csr[") and "=" in part:
                        inside_eq = part.split("=", 1)
                        addr_str = inside_eq[0].strip()
                        val_str = inside_eq[1].strip()
                        addr = int(addr_str[4:-1], 0)  # strip "csr[" and "]"
                        expected[addr] = int(val_str, 0)
    return expected

def main():
    tests = discover_tests()
    if not tests:
        print("No tests found in", TEST_DIR)
        sys.exit(1)

    passed = 0
    failed = 0

    for asm_path, expected_regs, expected_csrs in tests:
        name = os.path.basename(asm_path)
        if not expected_regs and not expected_csrs:
            print(f"SKIP {name} (no # expect comments)")
            continue

        ok = run_test(asm_path, expected_regs, expected_csrs)
        if ok:
            print(f"PASS {name}")
            passed += 1
        else:
            print(f"FAIL {name}")
            failed += 1

    print(f"\n{passed} passed, {failed} failed, {passed + failed} total")
    sys.exit(1 if failed > 0 else 0)

if __name__ == "__main__":
    main()
