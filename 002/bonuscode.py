import random
import string

forSelect = string.ascii_letters + string.digits
t=string.
print t
def generate_code(count, length):
    for x in range(count):
        Re = ""
        for y in range(length):
            Re += random.choice(forSelect)
        print(Re)


if __name__ == '__main__':
    generate_code(200, 20)