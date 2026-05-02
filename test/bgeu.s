.option norelax
main:
  addi x1, x0, 7          # x1 = 7
  addi x2, x0, 3          # x2 = 3
  bgeu x1, x2, taken      # should be taken: 7 >= 3 (unsigned)
  addi x3, x0, 1          # skipped
taken:
  addi x4, x0, 2          # x4 = 2
  addi x5, x0, 5          # x5 = 5
  addi x6, x0, 8          # x6 = 8
  bgeu x5, x6, not_taken  # should NOT be taken: 5 < 8 (unsigned)
  addi x7, x0, 3          # executed
not_taken:
  addi x8, x0, 4          # x8 = 4
  # test equal values
  addi x9, x0, 20         # x9 = 20
  addi x10, x0, 20        # x10 = 20
  bgeu x9, x10, taken2    # should be taken: 20 >= 20
  addi x11, x0, 1         # skipped
taken2:
  addi x12, x0, 5         # x12 = 5
  # test sign difference: -1 is very large unsigned
  addi x13, x0, -1        # x13 = -1 = 0xFFFFFFFFFFFFFFFF
  addi x14, x0, 5         # x14 = 5
  bgeu x13, x14, taken3   # should be taken: 0xFFF... >= 5
  addi x15, x0, 1         # skipped
taken3:
  addi x16, x0, 6         # x16 = 6
# expect x1=7, x2=3, x3=0, x4=2, x5=5, x6=8, x7=3, x8=4, x9=20, x10=20, x11=0, x12=5, x13=-1, x14=5, x15=0, x16=6
