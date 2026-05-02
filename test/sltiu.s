.option norelax
main:
  # basic: 3 < 7 => 1 (unsigned same as signed for small positives)
  addi x1, x0, 3
  sltiu x2, x1, 7
  # not less: 10 < 3 => 0
  addi x3, x0, 10
  sltiu x4, x3, 3
  # large positive vs zero: 0xFF < 0x100 => 1
  addi x5, x0, 255
  sltiu x6, x5, 256     # 256 = 0x100, but signed imm => encoded as 256
  # unsigned: -1 is huge => -1 < 5 is false unsigned
  addi x7, x0, -1       # -1 = 0xFFFFFFFFFFFFFFFF
  sltiu x8, x7, 5       # 0xFFFFFFFFFFFFFFFF < 5 => 0
  # unsigned: 5 < -1 is true (5 < huge unsigned value)
  addi x9, x0, 5
  sltiu x10, x9, -1     # 5 < 0xFFFFFFFFFFFFFFFF => 1
  # equal: 7 < 7 => 0
  addi x11, x0, 7
  sltiu x12, x11, 7
  # zero < 1 => 1
  sltiu x13, x0, 1
# expect x1=3, x2=1, x3=10, x4=0, x5=255, x6=1, x7=-1, x8=0, x9=5, x10=1, x11=7, x12=0, x13=1
