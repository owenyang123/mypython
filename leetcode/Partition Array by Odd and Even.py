def partitionArray(self, nums):
            # write your code here
            if len(nums) < 2: return

            lp, rp = 0, len(nums) - 1
            p = 0
            while p <= rp:
                if nums[p] % 2 == 1:
                    nums[lp], nums[p] = nums[p], nums[lp]
                    p += 1
                    lp += 1
                else:
                    nums[rp], nums[p] = nums[p], nums[rp]
                    rp -= 1