#ifndef RTT_EXTRACTOR_HPP
#define RTT_EXTRACTOR_HPP

# include <iostream>
# include <SystemUtils.h>
# include <PcapFileDevice.h>
# include <Packet.h>
# include <EthLayer.h>
# include <IPv4Layer.h>
# include <IPv6Layer.h>
# include <TcpLayer.h>
# include <DnsLayer.h>
# include <arpa/inet.h>
# include <unordered_map>
# include <IpAddress.h>
# include <PacketUtils.h>
# include <VlanLayer.h>
# include <iomanip>
# include <vector>
# include <time.h>

typedef struct rttInfo {
	pcpp::IPAddress ipaddress;
	std::unordered_map<uint32_t, struct timespec> syntimemp; // synack:timestamp
	std::vector<double> rttvec;
} rttInfo_t;

#endif

