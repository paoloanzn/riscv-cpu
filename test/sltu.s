.option norelax
main:
  # basic: 3 < 7 => 1
  addi x1, x0, 3
  addi x2, x0, 7
  sltu x3, x1, x2
  # not less: 10 < 3 => 0
  addi x4, x0, 10
  sltu x5, x4, x1
  # equal: 7 < 7 => 0
  sltu x6, x2, x2
  # unsigned: -1 is huge => -1 < 5 is false
  addi x7, x0, -1
  addi x8, x0, 5
  sltu x9, x7, x8        # 0xFFF... < 5 => 0
  # unsigned: 5 < -1 is true
  sltu x10, x8, x7       # 5 < 0xFFF... => 1
  # zero < anything => 1
  sltu x11, x0, x8       # 0 < 5 => 1
  # anything < 0 => 0
  sltu x12, x8, x0       # 5 < 0 => 0
# expect x1=3, x2=7, x3=1, x4=10, x5=0, x6=0, x7=-1, x8=5, x9=0, x10=1, x11=1, x12=0