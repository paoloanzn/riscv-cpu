.option norelax
main:
  # basic: 8 >> 2 = 2
  addi x1, x0, 8
  addi x2, x0, 2
  srl x3, x1, x2
  # shift by 0: 0xABCD >> 0 = 0xABCD
  addi x4, x0, 0x7FF
  srl x5, x4, x0
  # logical shift of -1: -1 >> 4 = 0x0FFFFFFFFFFFFFFF
  addi x6, x0, -1
  addi x7, x0, 4
  srl x8, x6, x7
  # shift only uses low 6 bits of rs2: rs2 = 64+2 = 66, result = 2
  addi x9, x0, 64
  add x9, x9, x2         # x9 = 66
  srl x10, x1, x9        # 8 >> (66 & 63) = 8 >> 2 = 2
# expect x1=8, x2=2, x3=2, x4=0x7FF, x5=0x7FF, x6=-1, x7=4, x8=0x0FFFFFFFFFFFFFFF, x9=66, x10=2