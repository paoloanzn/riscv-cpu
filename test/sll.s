.option norelax
main:
  # basic: 1 << 3 = 8
  addi x1, x0, 1
  addi x2, x0, 3
  sll x3, x1, x2
  # shift by 0: 0xAB << 0 = 0xAB
  addi x4, x0, 0xAB
  sll x5, x4, x0
  # large shift: 1 << 31
  addi x6, x0, 31
  sll x7, x1, x6
  # shift by 63 (top bit): 1 << 63
  addi x8, x0, 63
  sll x9, x1, x8
  # shift only uses low 6 bits of rs2: rs2 = 64+3 = 67, low 6 bits = 3, result = 8
  addi x10, x0, 64
  add x10, x10, x2        # x10 = 67
  sll x11, x1, x10        # 1 << (67 & 63) = 1 << 3 = 8
  # overflow wrap: msb << 1 = 0
  sll x12, x9, x1         # x9 = 0x8000000000000000, << 1 should wrap to 0
# expect x1=1, x2=3, x3=8, x4=0xAB, x5=0xAB, x6=31, x7=0x80000000, x8=63, x9=0x8000000000000000, x10=67, x11=8, x12=0