#include "dnscounter.hpp"
void showStats(pcapStat_t &allStat, std::unordered_map<uint32_t, flowStat_t> &flowStats);
void showIndividualStat(std::unordered_map<uint32_t, flowStat_t> &flowStats, std::ofstream &ofs);

/*
	pcap dns extracter (dns count/rate in each connection)
	argv[1] pcapfile
	argv[2] serverIP_range
	argv[3] outfile (option)
*/

int main(int argc, char* argv[])
{
	if (argc < 3) {
		std::cerr << "invalid input" << std::endl;
		std::cerr << "format: pcapfile, serverIp_range(219.100.37.0/24), (optinal) outfile" << std::endl;
		return 1;
	}
	std::string pcapfile = argv[1];
	std::string serverNet = argv[2];
	std::ofstream ofs;
	if (argc == 4) {
		std::string outfile = argv[3];
		ofs.open(outfile);
    	if (!ofs) {
        	std::cerr << "Error opening outfile" << std::endl;
    	}
	}

    pcpp::IFileReaderDevice* reader = pcpp::IFileReaderDevice::getReader(pcapfile);
    if (!reader->open()) {
        std::cerr << "Error opening pcap file" << std::endl;
		delete reader;
        return 1;
    }

	std::unordered_map<uint32_t, flowStat_t> flowStats;
	pcapStat_t allStat;
    pcpp::RawPacket rawPacket;
    while (reader->getNextPacket(rawPacket)) {
        pcpp::Packet parsedPacket(&rawPacket);

		pcpp::IPLayer* ipLayer = parsedPacket.getLayerOfType<pcpp::IPLayer>();
		if (!ipLayer) continue;
		pcpp::IPAddress srcIP = ipLayer->getSrcIPAddress();
		pcpp::IPAddress dstIP = ipLayer->getDstIPAddress();

		//if (parsedPacket.isPacketOfType(pcpp::HTTP)) allStat.http_count += 0;

		allStat.all_pkts_count += 1;

		pcpp::TcpLayer* tcpLayer = parsedPacket.getLayerOfType<pcpp::TcpLayer>();
		pcpp::UdpLayer* udpLayer = parsedPacket.getLayerOfType<pcpp::UdpLayer>();
		if (!tcpLayer && !udpLayer) continue;

		if (tcpLayer) allStat.tcp_pkts_count += 1;
		if (udpLayer) allStat.udp_pkts_count += 1;

		if (srcIP.isIPv4() && dstIP.isIPv4()) {
			pcpp::IPv4Address srcv4IP = srcIP.getIPv4();
			pcpp::IPv4Address dstv4IP = dstIP.getIPv4();
			/*
			if (srcv4IP.matchNetwork(serverNet) && dstv4IP.matchNetwork(serverNet)) {
			std::cout << srcv4IP.toString() << " " << dstv4IP.toString() << " " << srcv4IP.matchNetwork(serverNet) << " " << dstv4IP.matchNetwork(serverNet) << std::endl;
			}
			*/
			// lan to lan packet can be disregared since both src/dst is not client
			if (srcv4IP.matchNetwork(serverNet) && dstv4IP.matchNetwork(serverNet)) continue;
			uint32_t hash = pcpp::hash5Tuple(&parsedPacket);
			flowStats[hash].pkts_count += 1;
			if (parsedPacket.isPacketOfType(pcpp::HTTP)) flowStats[hash].http_count += 1; 

			//if srcip is serverip, then dst is client ip, and viceversa
			if (srcv4IP.matchNetwork(serverNet)) {
				flowStats[hash].clientIP = dstIP;
				flowStats[hash].serverIP = srcIP;
				if (udpLayer) {
					if (udpLayer->getDstPort() == 53) {
						//std::cout << "here" << std::endl;
						flowStats[hash].dns_count += 1;
						flowStats[hash].dns_s2c += 1;
						flowStats[hash].dns_udp += 1;
						// maybe count fall back?
					}
				} else if (tcpLayer) {
					if (tcpLayer->getDstPort() == 53) {
						//std::cout << "here" << std::endl;
						flowStats[hash].dns_count += 1;
						flowStats[hash].dns_s2c += 1;
						flowStats[hash].dns_tcp += 1;
						// maybe count fall back?
					}
				}
			} else {
				flowStats[hash].clientIP = srcIP;
				flowStats[hash].serverIP = dstIP;
				if (udpLayer) {
					if (udpLayer->getSrcPort() == 53) {
						//std::cout << "here" << std::endl;
						flowStats[hash].dns_count += 1;
						flowStats[hash].dns_c2s += 1;
						flowStats[hash].dns_udp += 1;
					}
				} else if (tcpLayer) {
					if (tcpLayer->getSrcPort() == 53) {
						//std::cout << "here" << std::endl;
						flowStats[hash].dns_count += 1;
						flowStats[hash].dns_c2s += 1;
						flowStats[hash].dns_tcp += 1;
					}
				}
			}
		} else if (srcIP.isIPv6() && dstIP.isIPv6()) {
			pcpp::IPv6Address srcv6IP = srcIP.getIPv6();
			pcpp::IPv6Address dstv6IP = dstIP.getIPv6();
			// lan to lan packet can be disregared since both src/dst is not client
			// ff02::1 is RA, so can be ignored
			if (srcv6IP.matchNetwork(serverNet) && dstv6IP.matchNetwork(serverNet)) continue;
			uint32_t hash = pcpp::hash2Tuple(&parsedPacket);
			flowStats[hash].pkts_count += 1;
			//if srcip is serverip, then dst is client ip, and viceversa
			if (srcv6IP.matchNetwork(serverNet)) {
				flowStats[hash].clientIP = dstIP;
				flowStats[hash].serverIP = srcIP;
				if (udpLayer) {
					if (udpLayer->getDstPort() == 53) {
						flowStats[hash].dns_count += 1;
						flowStats[hash].dns_s2c += 1;
						flowStats[hash].dns_udp += 1;
						// maybe count fall back?

					}
				} else if (tcpLayer) {
					if (tcpLayer->getDstPort() == 53) {
						flowStats[hash].dns_count += 1;
						flowStats[hash].dns_s2c += 1;
						flowStats[hash].dns_tcp += 1;
						// maybe count fall back?
					}
				}
			} else {
				flowStats[hash].clientIP = srcIP;
				flowStats[hash].serverIP = dstIP;
				if (udpLayer) {
					if (udpLayer->getSrcPort() == 53) {
						flowStats[hash].dns_count += 1;
						flowStats[hash].dns_c2s += 1;
						flowStats[hash].dns_udp += 1;
					}
				} else if (tcpLayer) {
					if (tcpLayer->getSrcPort() == 53) {
						flowStats[hash].dns_count += 1;
						flowStats[hash].dns_c2s += 1;
						flowStats[hash].dns_tcp += 1;
					}
				}
			}
		}
    }

	//showIndividualStat(flowStats, ofs);
	showStats(allStat, flowStats);

	delete reader;
	ofs.close();
	return 0;
}

void showStats(pcapStat_t &pcapStat, std::unordered_map<uint32_t, flowStat_t> &flowStats) {
	size_t all_dns_count = 0;
	size_t all_dns_udp = 0;
	size_t all_dns_tcp = 0;
	size_t dns_connection = 0;
	size_t http_connection = 0;
	size_t all_connection = flowStats.size();
	for (const auto &stat : flowStats) {
		all_dns_count += stat.second.dns_count;
		all_dns_udp += stat.second.dns_udp;
		all_dns_tcp += stat.second.dns_tcp;
		if (stat.second.dns_count > 0) {
			dns_connection += 1;
		}
		if (stat.second.http_count > 0) {
			http_connection += 1;
		}

	}
	std::cout << pcapStat.all_pkts_count << " "
				<< pcapStat.udp_pkts_count << " "
				<< pcapStat.tcp_pkts_count << " "
				<< all_dns_count << " "
				<< all_dns_udp << " "
				<< all_dns_tcp << std::endl;
	
	std::cout << "-- per connection --" << std::endl;
	std::cout << "(c,53,s,sport)setnum:" << flowStats.size() << std::endl;
	std::cout << "dnsconnectionnum:" << dns_connection << std::endl;
	std::cout << "httpconnectionnum:" << http_connection << std::endl;
	std::cout << "dnsconnrate(dns/allconn):" << (float)dns_connection / (float)all_connection * 100 << "%" << std::endl;
	std::cout << "dnsconnrate:(dns/httpconn)" << (float)dns_connection / (float)http_connection * 100 << "%" << std::endl;
}

void showIndividualStat(std::unordered_map<uint32_t, flowStat_t> &flowStats, std::ofstream &ofs) {
	for (const auto stat : flowStats) {
		if (ofs.is_open()) {
			ofs << stat.first << " "
				<< stat.second.clientIP << " "
				<< stat.second.dns_count << " "
				<< stat.second.pkts_count << " "
				//<< float(stat.second.dns_count / stat.second.pkts_count) 
				<< std::endl;	
		} else {
			if (stat.second.dns_count == 0) continue;
			std::cout << stat.first << " "
				<< stat.second.clientIP << " "
				<< stat.second.dns_count << " "
				<< stat.second.pkts_count << " "
				<< float(stat.second.dns_count / stat.second.pkts_count) 
				<< std::endl;	
		}
	}
}
