.option norelax
main:
  addi x1, x0, 5        # x1 = 5
  addi x2, x0, 5        # x2 = 5
  beq x1, x2, taken     # should be taken: 5 == 5
  addi x3, x0, 1        # skipped
taken:
  addi x4, x0, 2        # x4 = 2
  addi x5, x0, 7        # x5 = 7
  beq x1, x5, taken2    # should NOT be taken: 5 != 7
  addi x6, x0, 3        # executed
taken2:
# expect x1=5, x2=5, x3=0, x4=2, x5=7, x6=3
