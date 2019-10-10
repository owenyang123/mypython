class Solution:

    def getIntersectionNode(self, headA, headB):
        if headA is None or headB is None:
            return None

        def get_length(head):
            length = 0
            while head is not None:
                length += 1
                head = head.next
            return length

        lenA = get_length(headA)
        lenB = get_length(headB)

        if lenA > lenB:
            for i in range(lenA - lenB):
                headA = headA.next
        elif lenB > lenA:
            for i in range(lenB - lenA):
                headB = headB.next

        while headA != headB:
            headA = headA.next
            headB = headB.next

        return headA