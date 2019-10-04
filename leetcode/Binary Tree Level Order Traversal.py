class Solution:
    """
Definition of TreeNode:
class TreeNode:
    def __init__(self, val):
        self.val = val
        self.left, self.right = None, None
    """
    def levelOrder(self, root):
        # write your code here
        if not root: return []
        queue,result,last = [(root,1)],[],0
        while (queue):
            node,level = queue.pop(0)
            if level==last: result[-1].append(node.val)
            else: result.append([node.val])
            if node.left: queue.append((node.left,level+1))
            if node.right: queue.append((node.right,level+1))
            last = level
        return result


"""
Definition of TreeNode:
class TreeNode:
    def __init__(self, val):
        self.val = val
        self.left, self.right = None, None
"""

class Solution:
    """
    @param root: A tree
    @return: buttom-up level order a list of lists of integer
    """
    def levelOrderBottom(self, root):
        if not root: return []
        queue,result,last = [(root,1)],[],0
        while (queue):
            node,level = queue.pop(0)
            if level==last: result[-1].append(node.val)
            else: result.append([node.val])
            if node.left: queue.append((node.left,level+1))
            if node.right: queue.append((node.right,level+1))
            last = level
            print level
        return result[::-1]


class Solution:
    """
    @param root: A Tree
    @return: A list of lists of integer include the zigzag level order traversal of its nodes' values.
    """

    def zigzagLevelOrder(self, root):
        # write your code here
        if not root: return []
        queue, result, last = [(root, 1)], [], 0
        while (queue):
            node, level = queue.pop(0)
            if level == last:
                result[-1].append(node.val)
            else:
                result.append([node.val])
            if node.left: queue.append((node.left, level + 1))
            if node.right: queue.append((node.right, level + 1))
            last = level
        l = []
        k = 0
        for i in result:
            if k % 2 == 0:
                l.append(i)
            else:
                l.append(i[::-1])
            k = k + 1

        return l


"""
Definition of TreeNode:
class TreeNode:
    def __init__(self, val):
        this.val = val
        this.left, this.right = None, None
Definition for singly-linked list.
class ListNode:
    def __init__(self, x):
        self.val = x
        self.next = None
"""
class Solution:
    # @param {TreeNode} root the root of binary tree
    # @return {ListNode[]} a lists of linked list
    def binaryTreeToLists(self, root):
        if not root: return []
        queue,result,last = [(root,1)],[],0
        while (queue):
            node,level = queue.pop(0)
            if level==last: result[-1].append(node.val)
            else: result.append([node.val])
            if node.left: queue.append((node.left,level+1))
            if node.right: queue.append((node.right,level+1))
            last = level
        l=[]
        for i in result:
            link1=ListNode(-1)
            link1.next=ListNode(i[0])
            link1.next.val=i[0]
            cur=link1.next
            for j in range(len(i)-1):
                if j<len(i)-1:
                    print i[j+1]
                    cur.next=ListNode(i[j+1])
                    cur.next.val=i[j+1]
                    cur=cur.next
            l.append(link1.next)
        return l



class Solution:
    # @param {TreeNode} root the root of binary tree
    # @return {ListNode[]} a lists of linked list
    def binaryTreeToLists(self, root):
        if not root: return []
        queue,result,last = [(root,1)],[],0
        while (queue):
            node,level = queue.pop(0)
            if level==last: result[-1].append(node.val)
            else: result.append([node.val])
            if node.left: queue.append((node.left,level+1))
            if node.right: queue.append((node.right,level+1))
            last = level
        l=[]
        for i in result:
            link1=ListNode(-1)
            link1.next=ListNode(i[0])
            link1.next.val=i[0]
            cur=link1.next
            for j in range(len(i)-1):
                if j<len(i)-1:
                    print i[j+1]
                    cur.next=ListNode(i[j+1])
                    cur.next.val=i[j+1]
                    cur=cur.next
            l.append(link1.next)
        return l