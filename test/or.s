.option norelax
main:
  # basic: 0x0A | 0x30 = 0x3A
  addi x1, x0, 0x0A
  addi x2, x0, 0x30
  or x3, x1, x2
  # identity: x | 0 = x
  or x4, x1, x0
  # idempotent: x | x = x
  or x5, x1, x1
  # saturation: -1 | anything = -1
  addi x6, x0, -1
  addi x7, x0, 0x123
  or x8, x6, x7
# expect x1=0x0A, x2=0x30, x3=0x3A, x4=0x0A, x5=0x0A, x6=-1, x7=0x123, x8=-1