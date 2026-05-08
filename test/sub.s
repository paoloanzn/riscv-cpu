.option norelax
main:
  # basic: 10 - 3 = 7
  addi x1, x0, 10
  addi x2, x0, 3
  sub x3, x1, x2
  # zero result: 5 - 5 = 0
  addi x4, x0, 5
  sub x5, x4, x4
  # larger - smaller: 3 - 10 = -7
  sub x6, x2, x1
  # negative result: 0 - 3 = -3
  sub x7, x0, x2
  # negative operands: -5 - (-8) = 3, and -5 - 3 = -8
  addi x8, x0, -5
  addi x9, x0, -8
  sub x10, x8, x9       # -5 - (-8) = 3
  sub x11, x8, x2        # -5 - 3 = -8
# expect x1=10, x2=3, x3=7, x4=5, x5=0, x6=-7, x7=-3, x8=-5, x9=-8, x10=3, x11=-8