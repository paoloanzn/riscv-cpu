.option norelax
main:
  # basic: 0x0F & 0x33 = 0x03
  addi x1, x0, 0x0F
  addi x2, x0, 0x33
  and x3, x1, x2
  # with zero: x & 0 = 0
  and x4, x1, x0
  # with -1: x & -1 = x
  addi x5, x0, -1
  and x6, x1, x5
  # clear low bits: -1 & 0xFFFFFFFFFFFFFF00
  addi x7, x0, -256      # 0xFFFFFFFFFFFFFF00 (sign-extended from -256)
  and x8, x5, x7
# expect x1=0x0F, x2=0x33, x3=0x03, x4=0, x5=-1, x6=0x0F, x7=-256, x8=-256