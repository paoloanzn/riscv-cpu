#! /usr/bin/python3
import subprocess, pathlib, tempfile, os

# compile assembly file to bytes -> strip the ELF wrapper
def compile_asm_to_bytes(file_path=str) -> bytes:
    with tempfile.NamedTemporaryFile(delete=False) as out:
        out_path = out.name 
    try:
        subprocess.run(
            args=f'/opt/homebrew/opt/llvm/bin/clang --target=riscv64 -march=rv64i -mabi=lp64 -nostdlib -O3 -c {file_path} -o {out_path}'.split(),
            stderr=None,
            check=True
        )

        subprocess.run(
            args=f'llvm-objcopy -O binary -j .text {out_path} {out_path.replace(".o", ".bin")}'.split(),
            stderr=None,
            check=True
        )

        with open(out_path, 'rb') as f:
            return f.read()

    finally:
        try:
            os.unlink(out_path)
        except FileNotFoundError:
            pass

def hexdump(b: bytes):
    for i in range(0, len(b), 16):
        c = b[i:i+16]
        h = " ".join(f"{x:02x}" for x in c)
        a = "".join(chr(x) if 32 <= x < 127 else "." for x in c)
        print(f"{i:08x}  {h:<47}  |{a}|")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("[ERROR] Missing input file path: <file_path>.")
        sys.exit(1)
    compiled_bytes = compile_asm_to_bytes(sys.argv[1])
    hexdump(compiled_bytes)
    sys.exit(0)