.option norelax
main:
  addi x1, x0, 5          # x1 = 5
  addi x2, x0, 7          # x2 = 7
  bne x1, x2, taken       # should be taken: 5 != 7
  addi x3, x0, 1          # skipped
taken:
  addi x4, x0, 2          # x4 = 2
  addi x5, x0, 9          # x5 = 9
  addi x6, x0, 9          # x6 = 9
  bne x5, x6, taken2      # should NOT be taken: 9 == 9
  addi x7, x0, 3          # executed
taken2:
# expect x1=5, x2=7, x3=0, x4=2, x5=9, x6=9, x7=3
