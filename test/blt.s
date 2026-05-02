.option norelax
main:
  addi x1, x0, -5         # x1 = -5 (signed)
  addi x2, x0,  3         # x2 = 3 (signed)
  blt x1, x2, taken       # should be taken: -5 < 3
  addi x3, x0, 1          # skipped
taken:
  addi x4, x0, 2          # x4 = 2
  addi x5, x0, 10         # x5 = 10
  addi x6, x0, -2         # x6 = -2 (signed)
  blt x5, x6, not_taken   # should NOT be taken: 10 >= -2
  addi x7, x0, 3          # executed
not_taken:
  addi x8, x0, 4          # x8 = 4
  # test equal values
  addi x9, x0, 7          # x9 = 7
  addi x10, x0, 7         # x10 = 7
  blt x9, x10, not_taken2 # should NOT be taken: 7 == 7
  addi x11, x0, 5         # executed
not_taken2:
# expect x1=-5, x2=3, x3=0, x4=2, x5=10, x6=-2, x7=3, x8=4, x9=7, x10=7, x11=5
