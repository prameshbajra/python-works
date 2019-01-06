def is_leap(year):
    n = year
    if n % 400 == 0:
        return True
    if n % 100 == 0:
        return False
    if n % 4 == 0:
        return True
    else:
        return False


year = int(input("Enter a year :: "))
print(is_leap(year))
