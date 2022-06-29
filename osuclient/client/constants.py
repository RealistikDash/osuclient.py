from enum import IntFlag

class Privileges(IntFlag):
    NORMAL = 1 << 0
    MOD = 1 << 1
    SUPPORTER = 1 << 2
    PEPPY = 1 << 3
    DEVELOPER = 1 << 4
