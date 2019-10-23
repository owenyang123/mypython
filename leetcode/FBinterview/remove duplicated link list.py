class Solution:
    """
    @param head: head is the head of the linked list
    @return: head of linked list
    """

    def deleteDuplicates(self, head):
        # write your code here
        if head is None:
            return None
        if head.next is None:
            return head
        temp1, temp2 = head, head.next
        while temp2 is not None:
            if temp1.val != temp2.val:
                temp2 = temp2.next
                temp1 = temp1.next
            else:
                temp2 = temp2.next
                temp1.next = temp2

        return head