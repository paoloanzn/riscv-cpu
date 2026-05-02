.option norelax
main:
  addi x1, x0, 3          # x1 = 3
  addi x2, x0, 7          # x2 = 7
  bltu x1, x2, taken      # should be taken: 3 < 7 (unsigned)
  addi x3, x0, 1          # skipped
taken:
  addi x4, x0, 2          # x4 = 2
  addi x5, x0, 10         # x5 = 10
  addi x6, x0,  2         # x6 = 2
  bltu x5, x6, not_taken  # should NOT be taken: 10 > 2 (unsigned)
  addi x7, x0, 3          # executed
not_taken:
  addi x8, x0, 4          # x8 = 4
  # test equal values
  addi x9, x0, 5          # x9 = 5
  addi x10, x0, 5         # x10 = 5
  bltu x9, x10, not_taken2 # should NOT be taken: 5 == 5
  addi x11, x0, 5         # executed
not_taken2:
  # test sign difference: -1 is large unsigned
  addi x12, x0, -1        # x12 = -1 = 0xFFFFFFFFFFFFFFFF (very large unsigned)
  addi x13, x0, 1         # x13 = 1
  bltu x13, x12, taken2   # should be taken: 1 < 0xFFF... (unsigned)
  addi x14, x0, 1         # skipped
taken2:
  addi x15, x0, 6         # x15 = 6
# expect x1=3, x2=7, x3=0, x4=2, x5=10, x6=2, x7=3, x8=4, x9=5, x10=5, x11=5, x12=-1, x13=1, x14=0, x15=6
