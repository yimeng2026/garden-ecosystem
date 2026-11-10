"""Independent arithmetic for isotope coefficients and pressure slopes."""

import json
import math


def isotope_alpha(tc_h, tc_d, mass_h=1.0, mass_d=2.0):
    if min(tc_h, tc_d, mass_h, mass_d) <= 0 or mass_h == mass_d:
        raise ValueError("temperatures must be positive and isotope masses distinct")
    return -(math.log(tc_d) - math.log(tc_h)) / (math.log(mass_d) - math.log(mass_h))


def slope(p1, t1, p2, t2):
    if p1 == p2:
        raise ValueError("pressure interval must be nonzero")
    return (t2 - t1) / (p2 - p1)


def main():
    alpha = {
        "printed_lah10_240_168": isotope_alpha(240, 168),
        "durajski_lah10_249_180": isotope_alpha(249, 180),
        "h3s_203_155": isotope_alpha(203, 155),
    }
    slopes = [
        {"interval": "170->200", "value": slope(170, 259, 200, 271)},
        {"interval": "200->210", "value": slope(200, 271, 210, 249)},
        {"interval": "210->250", "value": slope(210, 249, 250, 246)},
    ]
    print(json.dumps({"alpha": alpha, "slopes_k_per_gpa": slopes}, indent=2))


if __name__ == "__main__":
    main()
