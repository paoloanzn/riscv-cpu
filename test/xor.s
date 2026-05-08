.option norelax
main:
  # basic: 0x0F ^ 0x33 = 0x3C
  addi x1, x0, 0x0F
  addi x2, x0, 0x33
  xor x3, x1, x2
  # identity: x ^ 0 = x
  xor x4, x1, x0
  # self-cancellation: x ^ x = 0
  xor x5, x1, x1
  # with all-ones: -1 ^ 0x55 = 0xFFFFFFFFFFFFFFAA
  addi x6, x0, -1
  addi x7, x0, 0x55
  xor x8, x6, x7
  # complement: -1 ^ x = ~x, so -1 ^ 0x0F = -16
  addi x9, x0, 0x0F
  xor x10, x6, x9
# expect x1=0x0F, x2=0x33, x3=0x3C, x4=0x0F, x5=0, x6=-1, x7=0x55, x8=0xFFFFFFFFFFFFFFAA, x9=0x0F, x10=-16