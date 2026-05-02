.option norelax
main:
  # basic: 3 < 7 => 1
  addi x1, x0, 3
  slti x2, x1, 7
  # not less: 10 < 3 => 0
  addi x3, x0, 10
  slti x4, x3, 3
  # signed: -5 < 2 => 1
  addi x5, x0, -5
  slti x6, x5, 2
  # signed: 2 < -5 => 0
  addi x7, x0, 2
  slti x8, x7, -5
  # negative immediates: -3 < -1 => 1
  slti x9, x5, -1     # x5 = -5, imm = -1
  # zero immediate: -5 < 0 => 1
  slti x10, x5, 0
# expect x1=3, x2=1, x3=10, x4=0, x5=-5, x6=1, x7=2, x8=0, x9=1, x10=1
