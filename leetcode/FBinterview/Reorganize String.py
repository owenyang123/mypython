class Solution:

    def reorganizeString(self, S):
        # write your code here
        if (S == ""):
            return ""
        from collections import Counter
        counter = Counter(S).most_common() # 1
        _, max_freq = counter[0]
        if max_freq > (len(S)+1)//2:
            return ""
        else:
            buckets = [[] for i in range(max_freq)] #2
            begin = 0
            for letter, count in counter:
                for i in range(count):
                    buckets[(i+begin)%max_freq].append(letter) #3
                begin += count
        return "".join("".join(bucket) for bucket in buckets) #4