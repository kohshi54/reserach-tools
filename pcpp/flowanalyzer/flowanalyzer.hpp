#ifndef FLOW_ANALYZER_HPP
#define FLOW_ANALYZER_HPP

# include <iostream>
# include <SystemUtils.h>
# include <PcapFileDevice.h>
# include <Packet.h>
# include <EthLayer.h>
# include <IPv4Layer.h>
# include <TcpLayer.h>
# include <DnsLayer.h>
# include <arpa/inet.h>
# include <unordered_map>
# include <IpAddress.h>
# include <PacketUtils.h>
# include <VlanLayer.h>

typedef struct tcpConnInfo {
	pcpp::IPAddress clientIP;
	pcpp::IPAddress serverIP;
	uint16_t clientPort;
	uint16_t serverPort;
	size_t pkts_count = 0;
	size_t pkts_cli_to_server = 0;
	size_t pkts_server_to_cli = 0;
	//size_t seqnum; // ack received?
	uint32_t seqnum_c2s = 0;
	uint32_t seqnum_s2c = 0;
	//size_t nextseq;
	uint32_t nextseq_c2s = -1;
	uint32_t nextseq_s2c = -1;
	//size_t ackrx;
	//size_t miss_count;
	size_t miss_count_c2s = 0;
	size_t miss_count_s2c = 0;
	//size_t resent_count;
	size_t resent_count_c2s = 0;
	size_t resent_count_s2c = 0;
} tcpConnInfo_t;

#endif
