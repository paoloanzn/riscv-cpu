.option norelax
main:
  # basic: 3 < 7 => 1
  addi x1, x0, 3
  addi x2, x0, 7
  slt x3, x1, x2
  # not less: 10 < 3 => 0
  addi x4, x0, 10
  slt x5, x4, x1
  # signed negative: -5 < 2 => 1
  addi x6, x0, -5
  slt x7, x6, x2
  # signed: 2 < -5 => 0
  slt x8, x2, x6
  # equal: 7 < 7 => 0
  slt x9, x2, x2
  # large negative < negative: -8 < -5 => 1
  addi x10, x0, -8
  slt x11, x10, x6
# expect x1=3, x2=7, x3=1, x4=10, x5=0, x6=-5, x7=1, x8=0, x9=0, x10=-8, x11=1