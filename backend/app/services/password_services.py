def analyse_password(pw: str):
    return {
        "length": len(pw),
        "has_digit": any(c.isdigit() for c in pw),
        "has_upper": any(c.isupper() for c in pw),
        "has_lower": any(c.islower() for c in pw),
        "has_special": any(not c.isalnum() for c in pw)
    }
