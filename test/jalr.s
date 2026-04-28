.option norelax
main:
  addi x5, x0, 12       # x5 = 12 (address of target)
  jalr x1, 0(x5)        # jump to target, x1 = PC+4 = 8
  addi x3, x0, 1        # skipped — x3 should stay 0

target:
  addi x4, x0, 2        # x4 = 2
# expect x1=8, x3=0, x4=2, x5=12
