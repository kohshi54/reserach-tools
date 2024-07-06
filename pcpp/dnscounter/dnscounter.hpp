#ifndef DNS_COUNTER_HPP
#define DNS_COUNTER_HPP

# include <iostream>
# include <SystemUtils.h>
# include <PcapFileDevice.h>
# include <Packet.h>
# include <EthLayer.h>
# include <IPv4Layer.h>
# include <TcpLayer.h>
# include <UdpLayer.h>
# include <DnsLayer.h>
# include <arpa/inet.h>
# include <unordered_map>
# include <IpAddress.h>
# include <PacketUtils.h>
# include <VlanLayer.h>
# include <iomanip>

typedef struct flowStat {
	pcpp::IPAddress clientIP;
	pcpp::IPAddress serverIP;
	size_t pkts_count = 0;
	size_t pkts_c2s = 0;
	size_t pkts_s2c = 0;
	size_t dns_count = 0;
	size_t dns_c2s = 0;
	size_t dns_s2c = 0;
	size_t dns_udp = 0;
	size_t dns_tcp = 0;
	size_t http_count = 0;
} flowStat_t;

typedef struct pcapStat {
	size_t all_pkts_count = 0;
	size_t tcp_pkts_count = 0;
	size_t udp_pkts_count = 0;
	//size_t http_count = 0;
} pcapStat_t;

#endif

