#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"

# https://code.amazon.com/packages/DxVpnCM2014/blobs/mainline/--/cm/nicklewi/PDT/gracefulshift/gsc.py
# https://w.amazon.com/bin/view/AWSDirectConnect/DxRivuletService/
# https://w.amazon.com/bin/view/AWSDirectConnect/DxRivuletService/juniper-dump
# https://code.amazon.com/packages/RivuletGateway/blobs/mainline/--/examples/junos.sh
# https://code.amazon.com/packages/PavilionDeviceConnectors/blobs/mainline/--/src/com/amazon/awsdx/pavilion/connector/RivuletDeviceConnector.java

# https://w.amazon.com/bin/view/Networkscript_baseline/
# /apollo/env/DXDeploymentTools/bin/ipython3
# brazil-runtime-exec get_slax_record.py
# https://w.amazon.com/bin/view/Main/Search?text=nms_ndc.connector%20import&f_type=DOCUMENT&f_locale=en&f_locale=&r=1
# https://code.amazon.com/packages/RivuletGateway/blobs/mainline/--/examples/junos.sh
# https://code.amazon.com/packages/NetworkDeviceConnector/blobs/mainline-1.3/--/lib/nms_ndc/connector.py
#   def for_device(cls, address_list, credential_provider=None, ip_provider=None, **kw):
#
#   def _connection_helper(cls, discovery_types, family, address_list, default_ports, credential_provider, **kw):
#          connection, host, platform = cls._get_device_information(
#                                       discovery, family, address_list, default_ports, credential_provider, **kw)
#          return connection, host, platform, discovery
#
#   def _get_device_information(discovery, family, address_list, default_ports, credential_provider, **kw):
#       discovery_method = device_discovery.get_discovery_method(discovery, family)
#       for a in address_list:
#           try:
#               connection, host, platform = discovery_method(a, default_ports.get(discovery, None),
#                                                               credential_provider, **kw)
#
#   def get_discovery_method(connection_type, family):
#     """Get the discovery method by type,
#     the discovery method type implementation may
#     vary by family
#     """
#
#     discovery_method_provider = \
#         _available_discovery_method_providers.get(connection_type, None)
#     if discovery_method_provider is None:
#         return None
#
#     return discovery_method_provider.discovery_method(family)

# https://w.amazon.com/bin/view/Networking/FST/NEM/Addis/UserGuide

from nms_ndc.connector import DeviceConnector
from nms_ndc.credentials.base import SimpleCredentialProvider, CredentialPair
from contextlib import closing

USERNAME = "porttest"
PASSWORD = "p0rtt3st"
USERNAME = "wanwill"
PASSWORD = "NoM@yGuess1t!!"
def main():

    creds = SimpleCredentialProvider(
        cli=[
            CredentialPair(
                principal= USERNAME,
                credential=PASSWORD
            )
        ],
        # snmp=[CredentialPair(principal=None, credential="vIwtJc8iihQfxE3YHj2f")]
    )

    host = "nrt4-vc-cas-nrt-p1-v3-r104"
    # host = "syd1-vc-car-syd-r5"
    device_connector = DeviceConnector.for_device(host,
                                                  credential_provider=creds,
                                                  disabled_connections=['snmp'],
                                                  device_family='junos',
                                                  verify_hostname=False,
                                                  ndcl_native_auto=False)
    command = "show version | no-more"

    with closing(device_connector.get_connection("cli")) as cli:
        try:
            res = cli.run_command(command)
        except CommandFailure as e:
            print('{0}: {1} command has been failed on the device with exception {2}'.format(
                device_connector.endpoint.hostname, command, e))

    print(res)

def main2():
    pass
if __name__ == '__main__':
    print("start get_slax")
    main()