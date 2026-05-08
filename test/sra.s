.option norelax
main:
  # basic: -8 >> 1 = -4
  addi x1, x0, -8
  addi x2, x0, 1
  sra x3, x1, x2
  # shift by 0: -1 >> 0 = -1
  addi x4, x0, -1
  sra x5, x4, x0
  # -1 >> 4 = -1 (sign-fill)
  addi x6, x0, 4
  sra x7, x4, x6
  # positive: 0x7FFFFFFFFFFFFFFF >> 2 = 0x1FFFFFFFFFFFFFFF
  addi x8, x0, -2
  srli x9, x8, 1         # x9 = 0x7FFFFFFFFFFFFFFF
  addi x10, x0, 2
  sra x11, x9, x10
# expect x1=-8, x2=1, x3=-4, x4=-1, x5=-1, x6=4, x7=-1, x8=-2, x9=0x7FFFFFFFFFFFFFFF, x10=2, x11=0x1FFFFFFFFFFFFFFF