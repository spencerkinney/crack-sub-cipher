from cipher_utils import CipherUtils

def main():
    ciphertext = """PCQ VMJYPD LBYK LYSO KBXBJXWXV BXV ZCJPO EYPD KBXBJYUXJ LBJOO KCPK. 
    CP LBO LBCMKXPV XPV IYJKL PYDBL, QBOP KBO BXV OPVOV LBO LXRO CI SX'XJMI, KBO JCKO XPV 
    EYKKOV LBO DJCMPV ZOICJO BYS, KXUYPD: DJOXL EYPD, ICJ X LBCMKXPV XPV CPO PYDBLK Y 
    BXNO ZOOP JOACMLPYPD LC UCM LBO IXZROK CI FXKL XDOK XPV LBO RODOPVK CI XPAYOPL EYPDK. 
    SXU Y SXEO KC ZCRV XK LC AJXNO X IXNCMJ CI UCMJ SXGOKLU?"""

    cipher = CipherUtils(ciphertext)
    decrypted, key = cipher.decrypt(callback=lambda i, s, _: print(f"Iteration {i}: Score {s:.2f}"))

    print("\nDecrypted text:")
    print(decrypted)
    print("\nKey:")
    for k, v in key.items():
        print(f"{k} -> {v}")

if __name__ == "__main__":
    main()