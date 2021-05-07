for i in range(2,51):
    print("set policy-options policy-statement 2dut term "+str(i)+" from route-filter 150."+str(i)+".0.0/16 prefix-length-range /20-/32")
    print("set policy-options policy-statement 2dut term "+str(i)+" then next-hop 20.20.1."+str(i))
    print("set policy-options policy-statement 2dut term "+str(i)+" then accept")





'''
set policy-options policy-statement 2dut term 1 from route-filter 150.0.0.0/16 prefix-length-range /20-/32
set policy-options policy-statement 2dut term 1 then next-hop 20.20.1.1
set policy-options policy-statement 2dut term 1 then accept
'''