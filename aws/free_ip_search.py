#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"

from dxd_tools_dev.modules import dogfish
import argparse

description = '''
Script to find available ip subnets in a given region or parent
[==========================================================================]
Usage given a region: free_ip_search.py -R dub -r ".*customer.*space" -m 30
Usage given a parent: free_ip_search.py -p 52.95.104.0/22 -m 30
[==========================================================================]
'''
parser = argparse.ArgumentParser(description=description)
parser.add_argument('-R','--region', type=str, metavar = '', required = False, help = 'Region to work with, example: dub')
parser.add_argument('-r','--regex', type=str, metavar = '', required = False, help = 'Regex pattern to filter, normally: ".*customer.*space" ')
parser.add_argument('-m','--min_mask', type=str, metavar = '', required = False, help = 'Minimum mask to filter entries, example: 30')
parser.add_argument('-p','--parent', type=str, metavar = '', required = False, help = 'Parent prefix, example: 52.95.104.0/22')
args = parser.parse_args()

df = dogfish.DogFish("com.amazon.credentials.isengard.894712427633.user/dx-deploy-df-user")

if args.region != None and args.regex != None and  args.min_mask != None and args.parent == None:
    if 0 < float(args.min_mask) < 33 and len(args.region) == 3:
        print("\n[INFO] Searching for results in region '{}' with regex '{}{}' and min_mask '{}'".format(args.region.upper(), args.region, args.regex, args.min_mask))
        print("[INFO] The proccess may take few minutes depending of the region")
        
        result = df.dogfish_find_from_region(args.region, args.regex, args.min_mask)
        
        if len(result) != 0:
            for k,v in result.items(): print("\n[INFO] Found {} free subnets in parent {} with description '{}': \n\t{}".format(str(len(v["free_blocks"])), k, v["description"], "\n\t".join(v["free_blocks"])))
            print("\n[WARNING] Make sure to pick a free subnet from the appropiate parent description.")
        else:
            print("\n[WARNING] No parent prefixes were found with provided regex and region")
    else: print("\n[WARNING] Provided variables are incorrect: region '{}', min_mask '{}', regex '{}'\n". format(args.region, args.min_mask, args.regex))
        
elif args.region == None and args.regex == None and  args.min_mask != None and args.parent != None:
    if 0 < float(args.min_mask) < 33 and "/" in args.parent:
        result = df.dogfish_find_from_parent(args.parent, args.min_mask)
        print("\n[INFO] Found {} free subnets in parent {} with min_mask {}: \n\t{}".format(str(len(result)), args.parent, args.min_mask, "\n\t".join(result)))
    else: print("\n[WARNING] Provided variables are incorrect: min_mask '{}', parent '{}'\n". format(args.min_mask, args.parent))

else: 
    print("\n[WARNING] Provided variables are incorrect: region '{}', regex '{}', min_mask '{}', parent '{}'". format(args.region, args.regex, args.min_mask, args.parent))
    print("[INFO] Use 'free_ip_search.py -h' command to see the proper usage\n")
