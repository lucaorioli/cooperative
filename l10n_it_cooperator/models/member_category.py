# Copyright 2026 Luca Orioli <lucaorioli@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

# kept separately in the members register (art. 2421 of the civil code)
SHARE_CATEGORIES = [
    ("cooperator", "Cooperator members' shares"),
    # soci sovventori (art. 4 of law 59/1992)
    ("supporter", "Supporting members' shares"),
    # soci finanziatori (art. 2526 of the civil code)
    ("financing", "Financing members' instruments"),
]

MEMBER_TYPES = [
    ("worker", "Worker member"),
    ("user", "User member"),
    # soci volontari (art. 2 of law 381/1991), social cooperatives only
    ("volunteer", "Volunteer member"),
]

TERMINATION_REASONS = [
    # art. 2532 of the civil code
    ("withdrawal", "Withdrawal"),
    # art. 2533 of the civil code
    ("exclusion", "Exclusion"),
    # art. 2534 of the civil code
    ("death", "Death"),
    ("transfer", "Transfer of all the shares"),
    ("other", "Other"),
]
