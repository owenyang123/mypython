def multiply(self, num1, num2):
    # write your code here
    len1, len2 = len(num1), len(num2)
    dig1 = dig2 = 0
    for i in range(len1):
        dig1 = dig1 * 10 + ord(num1[i]) - ord('0')

    for i in range(len2):
        dig2 = dig2 * 10 + ord(num2[i]) - ord('0')

    return str(dig1 * dig2)