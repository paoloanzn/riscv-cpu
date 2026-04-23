#! /usr/bin/python3
import sys, signal, os, logging
from dataclasses import dataclass
from typing import Optional, Tuple
from memory import Memory, MEM_SIZE

log_level_str = os.environ.get("LOG", "WARNING").upper()
log_level = getattr(logging, log_level_str, logging.WARNING)
logging.basicConfig(
    level=log_level,
    format="%(message)s",
)
logger = logging.getLogger(__name__)


class IllegalInstruction(Exception):
    def __init__(self, pc: int, raw: int, reason: str):
        self.pc = pc
        self.raw = raw
        self.reason = reason
        msg = f"IllegalInstruction at pc=0x{pc:08x}: raw=0x{raw:08x} ({reason})"
        super().__init__(msg)

def disasm(d: "DecodedInstr") -> str:
    key = (d.opcode, d.funct3, d.funct7)
    
    if key == (0x13, 0x00, None):  # addi
        return f"addi x{d.rd}, x{d.rs1}, {d.imm}"
    elif key == (0x33, 0x00, 0x00):  # add
        return f"add x{d.rd}, x{d.rs1}, x{d.rs2}"
    elif key == (0x03, 0x00, None):  # lb
        return f"lb x{d.rd}, {d.imm}(x{d.rs1})"
    elif key == (0x03, 0x01, None):  # lh
        return f"lh x{d.rd}, {d.imm}(x{d.rs1})"
    elif key == (0x03, 0x02, None):  # lw
        return f"lw x{d.rd}, {d.imm}(x{d.rs1})"
    elif key == (0x03, 0x03, None):  # ld
        return f"ld x{d.rd}, {d.imm}(x{d.rs1})"
    elif key == (0x03, 0x04, None):  # lbu
        return f"lbu x{d.rd}, {d.imm}(x{d.rs1})"
    elif key == (0x03, 0x05, None):  # lhu
        return f"lhu x{d.rd}, {d.imm}(x{d.rs1})"
    elif key == (0x03, 0x06, None):  # lwu
        return f"lwu x{d.rd}, {d.imm}(x{d.rs1})"
    else:
        return f"<unknown 0x{d.raw:08x}>"


# Takes a bits-wide unsigned value and return its signed interpretation
def sign_extend(value, bits) -> int:
    sign_bit = 1 << (bits - 1)
    return (value & (sign_bit -1)) - (value & sign_bit)

# Instruction Format
# opcode bits[6:0]
# rd bits[11:7]
# funct3 bits[14:12]
# rs1 bits[19:15]
# rs2 bits[24:20]
# funct7 bits[31:25]
# imm varies based on the format -> 'R', 'I', 'S', 'B', 'U', 'J'

@dataclass
class DecodedInstr:
    raw: int
    opcode: int
    rd: int
    funct3: int
    rs1: int
    rs2: int
    funct7: int
    imm: int
    instruction_format: str

    def __str__(self) -> str:
        return disasm(self)


# RISC-V 64 bit (little-endian)

REGISTERS_COUNT = 32
REGISTERS_BIT_SIZE = 64
XMASK = (1 << 64) - 1 # 64 bit mask


class CPU:
    def __init__(self, memory):
        # init registers 
        self.registers = [0] * (REGISTERS_COUNT) # reg x0 - x31
        self.pc = 0

        # bound memory
        self.memory = memory

        # set stack pointer -> reg x2
        self.registers[2] = MEM_SIZE # stack grows backwards so -> start and the end of memory
        
        # Counters for logging
        self.cycle = 0
        self.instruction_count = 0

    def __str__(self) -> str:
        return (str([f"0x{x:02x}" for x in self.registers]) + "\n" + f"pc: {self.pc}" + "\n" + f"sp: {self.registers[2]}")

    def get_state(self) -> str:
        return self.__str__()

    # fetch instruction from memory
    def _fetch(self) -> int:
        # instructions are 4 bytes long
        return self.memory.load(self.pc, 4)

    def _decode(self, mem_bytes) -> DecodedInstr:
        format_references = {
            0b0010011: "I",
            0b0000011: "I",
            0b0110011: "R",
        }

        def extract_bits(value: int, hi: int, lo: int) -> int:
            return (value >> lo) & ((1 << ((hi - lo) + 1)) - 1)

        # mem_layout -> { "mem_region_name": extracted_value, ...}
        mem_layout_chunks = {
            "opcode": lambda x : extract_bits(x, 6, 0),
            "rd": lambda x : extract_bits(x, 11, 7),
            "funct3": lambda x : extract_bits(x, 14, 12),
            "rs1": lambda x : extract_bits(x, 19, 15),
            "rs2": lambda x : extract_bits(x, 24, 20),
            "funct7": lambda x : extract_bits(x, 31, 25)
        }
        
        # memory arrives as 4 distinct bytes -> 0xAA 0xBB 0xCC 0xDD
        # we don't read in 8 bit (1 bytes) chunks so we first need to join
        # [0xAA, 0xBB, 0xCC, 0XDD] -> 0xAABBCCDD 
        d = DecodedInstr(raw=None, opcode=None, rd=None, funct3=None, rs1=None, rs2=None, funct7=None, imm=None, instruction_format='')
        raw = mem_bytes[0] | mem_bytes[1] << 8 | mem_bytes[2] << 16 | mem_bytes[3] << 24
        d.raw = raw

        d.opcode = d.raw & ((1 << 7) -1)
        d.instruction_format = format_references.get(d.opcode)

        if d.instruction_format == "I":
            d.rd     = mem_layout_chunks["rd"](raw)
            d.funct3 = mem_layout_chunks["funct3"](raw)
            d.rs1    = mem_layout_chunks["rs1"](raw)
            d.imm    = sign_extend(extract_bits(raw, 31, 20), 12)

        if d.instruction_format == "R":
            d.rd     = mem_layout_chunks["rd"](raw)
            d.funct3 = mem_layout_chunks["funct3"](raw)
            d.rs1    = mem_layout_chunks["rs1"](raw)
            d.rs2    = mem_layout_chunks["rs2"](raw)
            d.funct7 = mem_layout_chunks["funct7"](raw)
            # no immediate

        return d

    # R[rd] = R[rs1] + imm
    def _addi(self, d: DecodedInstr) -> None:
        self.registers[d.rd] = self.registers[d.rs1] + d.imm
        return

    # R[rd] = R[rs1] + R[rs2]
    def _add(self, d: DecodedInstr) -> None:
        self.registers[d.rd] = self.registers[d.rs1] + self.registers[d.rs2]
        return

    # R[rd] = {56'bM[](7),M[R[rs1]+imm](7:0)}
    def _lb(self, d: DecodedInstr) -> None:
        # In RISC-V there is no overflow exception
        # Overflowed values get masked and are still valid addrs
        addr = (self.registers[d.rs1] + d.imm) & XMASK
        bytes_data = self.memory.load(addr, 1)
        value = bytes_data[0]
        value = sign_extend(value, 8) & XMASK
        if d.rd != 0: # x0 guard
            self.registers[d.rd] = value

    # R[rd] = {48'bM[](15),M[R[rs1]+imm](15:0)}
    def _lh(self, d: DecodedInstr) -> None:
        addr = (self.registers[d.rs1] + d.imm) & XMASK
        bytes_data = self.memory.load(addr, 2)
        value = bytes_data[0] | bytes_data[1] << 8
        value = sign_extend(value, 16) & XMASK
        if d.rd != 0: # x0 guard
            self.registers[d.rd] = value

    # R[rd] = {32'bM[](31),M[R[rs1]+imm](31:0)}
    def _lw(self, d: DecodedInstr) -> None:
        addr = (self.registers[d.rs1] + d.imm) & XMASK
        bytes_data = self.memory.load(addr, 4)
        value = bytes_data[0] | bytes_data[1] << 8 | bytes_data[2] << 16 | bytes_data[3] << 24
        value = sign_extend(value, 32) & XMASK
        if d.rd != 0: # x0 guard
            self.registers[d.rd] = value

    # R[rd] = M[R[rs1]+imm](63:0)
    def _ld(self, d: DecodedInstr) -> None:
        addr = (self.registers[d.rs1] + d.imm) & XMASK
        bytes_data = self.memory.load(addr, 8)
        value = bytes_data[0] | bytes_data[1] << 8 | bytes_data[2] << 16 | bytes_data[3] << 24 | bytes_data[4] << 32 | bytes_data[5] << 40 | bytes_data[6] << 48 | bytes_data[7] << 56
        value = value & XMASK
        if d.rd != 0: # x0 guard
            self.registers[d.rd] = value

    # R[rd] = {56'b0,M[R[rs1]+imm](7:0)}
    def _lbu(self, d: DecodedInstr) -> None:
        addr = (self.registers[d.rs1] + d.imm) & XMASK
        bytes_data = self.memory.load(addr, 1)
        value = bytes_data[0]
        if d.rd != 0: # x0 guard
            self.registers[d.rd] = value

    # R[rd] = {48'b0,M[R[rs1]+imm](15:0)}
    def _lhu(self, d: DecodedInstr) -> None:
        addr = (self.registers[d.rs1] + d.imm) & XMASK
        bytes_data = self.memory.load(addr, 2)
        value = bytes_data[0] | bytes_data[1] << 8
        if d.rd != 0: # x0 guard
            self.registers[d.rd] = value

    # R[rd] = {32'b0,M[R[rs1]+imm](31:0)}
    def _lwu(self, d: DecodedInstr) -> None:
        addr = (self.registers[d.rs1] + d.imm) & XMASK
        bytes_data = self.memory.load(addr, 4)
        value = bytes_data[0] | bytes_data[1] << 8 | bytes_data[2] << 16 | bytes_data[3] << 24
        if d.rd != 0: # x0 guard
            self.registers[d.rd] = value
      

    def _execute(self, d: DecodedInstr) -> None:
        # key(opcode, funct3, funct7) 
        mnemonic_lookup = {
            (0x13, 0x00, None): self._addi,
            (0x33, 0x00, 0x00): self._add,
            (0x03, 0x00, None): self._lb,
            (0x03, 0x01, None): self._lh,
            (0x03, 0x02, None): self._lw,
            (0x03, 0x03, None): self._ld,
            (0x03, 0x04, None): self._lbu,
            (0x03, 0x05, None): self._lhu,
            (0x03, 0x06, None): self._lwu
        }

        key = (d.opcode, d.funct3, d.funct7)
        if key not in mnemonic_lookup:
            raise IllegalInstruction(
                pc=self.pc - 4,
                raw=d.raw,
                reason=f"opcode 0x{d.opcode:02x} not in dispatch table"
            )
        
        mnemonic_lookup[key](d)
        return

    def _cycle(self) -> None:
        self.cycle += 1
        self.instruction_count += 1
        
        # Fetch
        mem_bytes = self._fetch()
        logger.debug(f"[{self.cycle:06d}] FETCH  pc=0x{self.pc:08x}  bytes={[hex(x) for x in mem_bytes]}")

        self.pc += 4 # move pc to the next instruction

        # Decode
        decoded_instruction = self._decode(mem_bytes)
        logger.debug(f"[{self.cycle:06d}] DECODE {disasm(decoded_instruction)}")

        if decoded_instruction.raw == 0x00:
            raise IllegalInstruction(
                pc=self.pc - 4,
                raw=decoded_instruction.raw,
                reason="all zeros (NOP or halt)"
            )

        # Execute
        self._execute(decoded_instruction)
        logger.debug(f"[{self.cycle:06d}] EXEC")

        # INFO level: one line per instruction with disasm + register delta
        if logger.isEnabledFor(logging.INFO):
            info_line = f"{(self.pc - 4):08x}  {decoded_instruction.raw:08x}  {disasm(decoded_instruction):<20}"
            logger.info(info_line)

        return

    def start(self) -> None:
        try:
            while self.pc < self.memory.size:
                self._cycle()

        except IllegalInstruction as e:
            logger.error(str(e))
            logger.warning(f"\nFinal state after {self.instruction_count} instructions, {self.cycle} cycles:")
            logger.warning(self.get_state())
            sys.exit(1)

        except KeyboardInterrupt:
            logger.warning(f"\nInterrupted after {self.instruction_count} instructions, {self.cycle} cycles:")
            logger.warning(self.get_state())
            sys.exit(0)
        
        # Normal completion
        logger.warning(f"\nCompleted {self.instruction_count} instructions, {self.cycle} cycles:")
        logger.warning(self.get_state())



if __name__ == "__main__":
    from compile import compile_asm_to_bytes
    if len(sys.argv) < 2:
        print("[ERROR] Missing input file path: <file_path>.")
        sys.exit(1)
    compiled_bytes = [byte for byte in compile_asm_to_bytes(sys.argv[1])]
    mem = Memory(preloaded_bytes=compiled_bytes)

    cpu = CPU(mem)
    logger.warning("[CPU] STATE")
    logger.warning(cpu.get_state())
    logger.warning(f"Log level: {log_level_str}")
    logger.warning("\n")
    cpu.start()