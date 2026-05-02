.option norelax
main:
  addi x1, x0, 10         # x1 = 10
  addi x2, x0, -3         # x2 = -3 (signed)
  bge x1, x2, taken       # should be taken: 10 >= -3
  addi x3, x0, 1          # skipped
taken:
  addi x4, x0, 2          # x4 = 2
  addi x5, x0,  2         # x5 = 2
  addi x6, x0, 10         # x6 = 10
  bge x5, x6, not_taken   # should NOT be taken: 2 < 10
  addi x7, x0, 3          # executed
not_taken:
  addi x8, x0, 4          # x8 = 4
  # test equal values
  addi x9, x0, 15         # x9 = 15
  addi x10, x0, 15        # x10 = 15
  bge x9, x10, taken2     # should be taken: 15 >= 15
  addi x11, x0, 1         # skipped
taken2:
  addi x12, x0, 5         # x12 = 5
# expect x1=10, x2=-3, x3=0, x4=2, x5=2, x6=10, x7=3, x8=4, x9=15, x10=15, x11=0, x12=5
