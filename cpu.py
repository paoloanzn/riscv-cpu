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

def csr_name(addr: int) -> str:
    """Return a human-readable name for common CSR addresses, or a hex string."""
    names = {
        0x000: "ustatus",  0x001: "fflags",   0x002: "frm",
        0x003: "fcsr",     0x004: "uie",      0x005: "utvec",
        0x100: "sstatus",  0x102: "sedeleg",  0x103: "sideleg",
        0x104: "sie",      0x105: "stvec",    0x140: "sscratch",
        0x141: "sepc",     0x142: "scause",   0x143: "stval",
        0x144: "sip",      0x300: "mstatus",  0x301: "misa",
        0x302: "medeleg",  0x303: "mideleg",  0x304: "mie",
        0x305: "mtvec",    0x330: "mepc",     0x340: "mscratch",
        0x341: "mcause",   0x342: "mtval",    0x343: "mip",
        0xB00: "mcycle",   0xB02: "minstret",
        0xF11: "mvendorid", 0xF12: "marchid", 0xF13: "mimpid",
        0xF14: "mhartid",  0x7C0: "tselect",  0x7C1: "tdata1",
        0x7C2: "tdata2",   0x7C3: "tdata3",
    }
    return names.get(addr, f"0x{addr:03x}")


def disasm(d: "DecodedInstr") -> str:
    key = (d.opcode, d.funct3, d.funct7)
    csr_addr = (d.imm & 0xFFF) if d.imm is not None else 0
    uimm = d.rs1

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
    elif key == (0x23, 0x00, None):  # sb
        return f"sb x{d.rs2}, {d.imm}(x{d.rs1})"
    elif key == (0x23, 0x01, None):  # sh
        return f"sh x{d.rs2}, {d.imm}(x{d.rs1})"
    elif key == (0x23, 0x02, None):  # sw
        return f"sw x{d.rs2}, {d.imm}(x{d.rs1})"
    elif key == (0x23, 0x03, None):  # sd
        return f"sd x{d.rs2}, {d.imm}(x{d.rs1})"
    elif key == (0x37, None, None):  # lui
        return f"lui x{d.rd}, {d.imm}"
    elif key == (0x17, None, None):  # auipc
        return f"auipc x{d.rd}, {d.imm}"
    elif key == (0x6f, None, None):  # jal
        return f"jal x{d.rd}, {d.imm}"
    elif key == (0x67, 0x00, None):  # jalr
        return f"jalr x{d.rd}, {d.imm}(x{d.rs1})"

    # Branch instructions (opcode 0x63)
    elif key == (0x63, 0x0, None):  # beq
        return f"beq x{d.rs1}, x{d.rs2}, {d.imm}"
    elif key == (0x63, 0x1, None):  # bne
        return f"bne x{d.rs1}, x{d.rs2}, {d.imm}"
    elif key == (0x63, 0x4, None):  # blt
        return f"blt x{d.rs1}, x{d.rs2}, {d.imm}"
    elif key == (0x63, 0x5, None):  # bge
        return f"bge x{d.rs1}, x{d.rs2}, {d.imm}"
    elif key == (0x63, 0x6, None):  # bltu
        return f"bltu x{d.rs1}, x{d.rs2}, {d.imm}"
    elif key == (0x63, 0x7, None):  # bgeu
        return f"bgeu x{d.rs1}, x{d.rs2}, {d.imm}"

    # CSR instructions (opcode 0x73)
    elif key == (0x73, 0x1, None):     # csrrw
        return f"csrrw x{d.rd}, {csr_name(csr_addr)}, x{d.rs1}"
    elif key == (0x73, 0x2, None):     # csrrs
        return f"csrrs x{d.rd}, {csr_name(csr_addr)}, x{d.rs1}"
    elif key == (0x73, 0x3, None):     # csrrc
        return f"csrrc x{d.rd}, {csr_name(csr_addr)}, x{d.rs1}"
    elif key == (0x73, 0x5, None):     # csrrwi
        return f"csrrwi x{d.rd}, {csr_name(csr_addr)}, {uimm}"
    elif key == (0x73, 0x6, None):     # csrrsi
        return f"csrrsi x{d.rd}, {csr_name(csr_addr)}, {uimm}"
    elif key == (0x73, 0x7, None):     # csrrci
        return f"csrrci x{d.rd}, {csr_name(csr_addr)}, {uimm}"
    else:
        return f"<unknown 0x{d.raw:08x}>"

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
        self.pc_modified = False # track whenever pc is modified within an instructions execution -> avoid double increments

        # Control Status Registers
        self.csrs = [0] * 4096

        # bound memory
        self.memory = memory

        # set stack pointer -> reg x2
        self.registers[2] = MEM_SIZE # stack grows backwards so -> start and the end of memory
        
        # Counters for logging
        self.cycle = 0
        self.instruction_count = 0

    def __str__(self) -> str:
        lines = [str([f"0x{x:02x}" for x in self.registers])]
        lines.append(f"pc: {self.pc}")
        lines.append(f"sp: {self.registers[2]}")

        # Dump non-zero CSRs
        written_csrs = [(addr, val) for addr, val in enumerate(self.csrs) if val != 0]
        if written_csrs:
            lines.append("CSRs:")
            for addr, val in written_csrs:
                lines.append(f"  {csr_name(addr)} (0x{addr:03x}) = 0x{val:x}")

        return "\n".join(lines)

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
            0b1110011: "I",
            0b1100111: "I",
            0b0110011: "R",
            0b0100011: "S",
            0b0110111: "U",
            0b0010111: "U",
            0b1101111: "UJ",
            0b1100011: "SB", 
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

        if d.instruction_format == "S":
            d.funct3    = mem_layout_chunks["funct3"](raw)
            d.rs1       = mem_layout_chunks["rs1"](raw)
            d.rs2       = mem_layout_chunks["rs2"](raw)
            imm_lo      = extract_bits(raw, 11, 7)
            imm_hi      = extract_bits(raw, 31, 25)
            d.imm       = sign_extend((imm_hi << 5) | imm_lo, 12)

        if d.instruction_format == "U":
            d.rd     = mem_layout_chunks["rd"](raw)
            d.imm    = extract_bits(raw, 31, 12)

        if d.instruction_format == "UJ":
            d.rd        = mem_layout_chunks["rd"](raw)
            imm_20      = extract_bits(raw, 31, 31) # 1 bit
            imm_10_1    = extract_bits(raw, 30, 21) # 10 bits
            imm_11      = extract_bits(raw, 20, 20) # 1 bit
            imm_19_12   = extract_bits(raw, 19, 12) # 8 bits

            imm         = (imm_20 << 20) | (imm_19_12 << 12) | (imm_11 << 11) | (imm_10_1 << 1)
            d.imm       = sign_extend(imm, 21)

        if d.instruction_format == "SB":
            d.rd        = mem_layout_chunks["rd"](raw)
            d.funct3    = mem_layout_chunks["funct3"](raw)
            d.rs1       = mem_layout_chunks["rs1"](raw)
            d.rs2       = mem_layout_chunks["rs2"](raw)
            imm_12      = extract_bits(raw, 31, 31) # 1 bit
            imm_10_5    = extract_bits(raw, 30, 25) # 6 bits
            imm_4_1     = extract_bits(raw, 11, 8)  # 4 bits
            imm_11      = extract_bits(raw, 7, 7) # 1 bit

            imm         = (imm_12 << 12) | (imm_11 << 11) | (imm_10_5 << 5) | (imm_4_1 << 1)
            d.imm       = sign_extend(imm, 13)

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

    # M[R[rs1]+imm](7:0) = R[rs2](7:0) 
    def _sb(self, d: DecodedInstr) -> None:
        addr = (self.registers[d.rs1] + d.imm) & XMASK
        value = self.registers[d.rs2] & 0xFF
        self.memory.store(addr, 1, [value])

    # M[R[rs1]+imm](15:0) = R[rs2](15:0) 
    def _sh(self, d: DecodedInstr) -> None:
        addr = (self.registers[d.rs1] + d.imm) & XMASK
        value = self.registers[d.rs2] & 0xFFFF
        bytes_array = [
            value & ((1 << 8) - 1),
            value >> 8
        ]
        self.memory.store(addr, 2, bytes_array)

    # M[R[rs1]+imm](31:0) = R[rs2](31:0)
    def _sw(self, d: DecodedInstr) -> None:
        addr = (self.registers[d.rs1] + d.imm) & XMASK
        value = self.registers[d.rs2] & 0xFFFFFFFF
        bytes_array = [
            value & ((1 << 8) - 1),
            (value >> 8) & ((1 << 8) - 1),
            (value >> 16) & ((1 << 8) - 1),
            value >> 24
        ]
        self.memory.store(addr, 4, bytes_array)

    # M[R[rs1]+imm](63:0) = R[rs2](63:0) 
    def _sd(self, d: DecodedInstr) -> None:
        addr = (self.registers[d.rs1] + d.imm) & XMASK
        value = self.registers[d.rs2] & 0xFFFFFFFFFFFFFFFF
        bytes_array = [
            value & ((1 << 8) - 1),
            (value >> 8) & ((1 << 8) - 1),
            (value >> 16) & ((1 << 8) - 1),
            (value >> 24) & ((1 << 8) - 1),
            (value >> 32) & ((1 << 8) - 1),
            (value >> 40) & ((1 << 8) - 1),
            (value >> 48) & ((1 << 8) - 1),
            value >> 56
        ]
        self.memory.store(addr, 8, bytes_array)

    # R[rd] = CSR; CSR = R[rs1]
    def _csrrw(self, d: DecodedInstr) -> None:
        value_old = self.csrs[d.imm]
        self.csrs[d.imm] = self.registers[d.rs1]
        if d.rd != 0:
            self.registers[d.rd] = value_old

    # R[rd] = CSR; CSR = CSR | R[rs1] 
    def _csrrs(self, d: DecodedInstr) -> None:
        value_old = self.csrs[d.imm]
        self.csrs[d.imm] = self.csrs[d.imm] | self.registers[d.rs1]
        if d.rd != 0:
            self.registers[d.rd] = value_old

    # R[rd] = CSR;CSR = CSR & ~R[rs1]
    def _csrrc(self, d: DecodedInstr) -> None:
        value_old = self.csrs[d.imm]
        self.csrs[d.imm] = (self.csrs[d.imm] & ~self.registers[d.rs1]) & XMASK
        if d.rd != 0:
            self.registers[d.rd] = value_old

    # R[rd] = CSR; CSR = imm
    def _csrrwi(self, d: DecodedInstr) -> None:
        value_old = self.csrs[d.imm]
        self.csrs[d.imm] = d.rs1 
        if d.rd != 0:
            self.registers[d.rd] = value_old

    # R[rd] = CSR; CSR = CRS | imm
    def _csrrsi(self, d: DecodedInstr) -> None:
        value_old = self.csrs[d.imm]
        self.csrs[d.imm] = self.csrs[d.imm] | d.rs1 
        if d.rd != 0:
            self.registers[d.rd] = value_old

    # R[rd] = CSR;CSR = CSR & ~R[rs1]
    def _csrrci(self, d: DecodedInstr) -> None:
        value_old = self.csrs[d.imm]
        self.csrs[d.imm] = (self.csrs[d.imm] & ~d.rs1) & XMASK
        if d.rd != 0:
            self.registers[d.rd] = value_old

    # R[rd] = {32b'imm<31>, imm, 12'b0}
    def _lui(self, d: DecodedInstr) -> None:
        value = d.imm << 12
        value = sign_extend(value, 32) & XMASK
        if d.rd != 0:
            self.registers[d.rd] = value

    # R[rd] = PC + {imm, 12'b0}
    def _auipc(self, d: DecodedInstr) -> None:
        value = d.imm << 12
        old_pc = self.pc
        value = (old_pc + sign_extend(value, 32)) & XMASK 
        if d.rd != 0:
            self.registers[d.rd] = value

    # R[rd] = PC+4; PC = PC + {imm,1b'0}
    def _jal(self, d: DecodedInstr) -> None:
        if d.rd != 0:
            self.registers[d.rd] = self.pc + 4
        self.pc = (self.pc + d.imm) & XMASK
        self.pc_modified = True
        
    # R[rd] = PC+4; PC = R[rs1]+imm
    def _jarl(self, d: DecodedInstr) -> None:
        if d.rd != 0:
            self.registers[d.rd] = self.pc + 4
        self.pc = (self.registers[d.rs1] + d.imm) & XMASK
        self.pc_modified = True

    # if(R[rs1]=R[rs2) PC=PC+{imm, 1b'0}
    def _beq(self, d: DecodedInstr) -> None:
        if self.registers[d.rs1] == self.registers[d.rs2]:
            self.pc = (self.pc + d.imm) & XMASK
            self.pc_modified = True

    # if(R[rs1] != R[rs2) PC=PC+{imm, 1b'0}
    def _bne(self, d: DecodedInstr) -> None:
        if self.registers[d.rs1] != self.registers[d.rs2]:
            self.pc = (self.pc + d.imm) & XMASK
            self.pc_modified = True

    # if(R[rs1]<R[rs2) PC=PC+{imm,1b'0}
    def _blt(self, d: DecodedInstr) -> None:
        if sign_extend(self.registers[d.rs1], 64) < sign_extend(self.registers[d.rs2], 64):
            self.pc = (self.pc + d.imm) & XMASK
            self.pc_modified = True

    # if(R[rs1]>=R[rs2) PC=PC+{imm,1b'0}
    def _bge(self, d: DecodedInstr) -> None:
        if sign_extend(self.registers[d.rs1], 64) >= sign_extend(self.registers[d.rs2], 64):
            self.pc = (self.pc + d.imm) & XMASK
            self.pc_modified = True

    # if(R[rs1]<R[rs2) PC=PC+{imm,1b'0}  (unsigned comparison)
    def _bltu(self, d: DecodedInstr) -> None:
        if (self.registers[d.rs1] & XMASK) < (self.registers[d.rs2] & XMASK):
            self.pc = (self.pc + d.imm) & XMASK
            self.pc_modified = True

    # if(R[rs1]>=R[rs2) PC=PC+{imm,1b'0}  (unsigned comparison)
    def _bgeu(self, d: DecodedInstr) -> None:
        if (self.registers[d.rs1] & XMASK) >= (self.registers[d.rs2] & XMASK):
            self.pc = (self.pc + d.imm) & XMASK
            self.pc_modified = True

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
            (0x03, 0x06, None): self._lwu,
            (0x23, 0x00, None): self._sb,
            (0x23, 0x01, None): self._sh,
            (0x23, 0x02, None): self._sw,
            (0x23, 0x03, None): self._sd,
            (0x37, None, None): self._lui,
            (0x17, None, None): self._auipc,
            (0x6f, None, None): self._jal,
            (0x67, 0x00, None): self._jarl,

            # branching
            (0x63, 0x00, None): self._beq,
            (0x63, 0x01, None): self._bne,
            (0x63, 0x04, None): self._blt,
            (0x63, 0x05, None): self._bge,
            (0x63, 0x06, None): self._bltu,
            (0x63, 0x07, None): self._bgeu,

            # control status registers instructions
            (0x73, 0x01, None): self._csrrw,
            (0x73, 0x02, None): self._csrrs,
            (0x73, 0x03, None): self._csrrc,
            (0x73, 0x05, None): self._csrrwi,
            (0x73, 0x06, None): self._csrrsi,
            (0x73, 0x07, None): self._csrrci,
        }

        key = (d.opcode, d.funct3, d.funct7)
        if key not in mnemonic_lookup:
            raise IllegalInstruction(
                pc=self.pc,
                raw=d.raw,
                reason=f"opcode 0x{d.opcode:02x} not in dispatch table"
            )
        
        mnemonic_lookup[key](d)
        return

    def _cycle(self) -> None:
        self.cycle += 1
        self.instruction_count += 1
        self.pc_modified = False
        
        # Fetch
        mem_bytes = self._fetch()
        logger.debug(f"[{self.cycle:06d}] FETCH  pc=0x{self.pc:08x}  bytes={[hex(x) for x in mem_bytes]}")

        # Decode
        decoded_instruction = self._decode(mem_bytes)
        logger.debug(f"[{self.cycle:06d}] DECODE {disasm(decoded_instruction)}")

        if decoded_instruction.raw == 0x00:
            raise IllegalInstruction(
                pc=self.pc,
                raw=decoded_instruction.raw,
                reason="all zeros (NOP or halt)"
            )

        # Execute
        self._execute(decoded_instruction)
        logger.debug(f"[{self.cycle:06d}] EXEC")
        
        if not self.pc_modified:
            self.pc += 4 # move pc to the next instruction

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