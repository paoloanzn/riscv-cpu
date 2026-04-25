main:
  lui x5, 0x1             # x5 = 0x1000
  lui x6, 0xFFFFF         # x6 = 0xFFFFF000 (sign-extended upper 32 bits)
  addi x7, x0, 0x42       # x7 = 0x42
  lui x7, 0x12345         # x7 = 0x12345000
# expect x5=0x1000, x6=0xFFFFFFFFFFFFF000, x7=0x12345000