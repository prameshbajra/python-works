from itertools import permutations
S, k = input().split()

for i in range(0, int(k) + 1):
    [print(*p, sep="") for p in list(permutations(sorted(S), int(i)))]

