def gcf(a, b):
    if b > a: return gcf(b, a)
    if a % b == 0: return b
    while (a % b != 0):
        return gcf(a - b, b)


animals = ['dog', 'cat', 'parrot', 'rabbit']

uppered_animals = list(map(lambda animal: str.upper(animal),animals))

print uppered_animals