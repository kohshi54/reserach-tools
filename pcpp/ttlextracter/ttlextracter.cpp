#include "ttlextracter.hpp"

/*
	pcap ttl extracter
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

	std::unordered_map<std::string, std::vector<uint8_t>> ipttlmp;

    pcpp::RawPacket rawPacket;
    while (reader->getNextPacket(rawPacket)) {
        pcpp::Packet parsedPacket(&rawPacket);

		pcpp::IPLayer* ipLayer = parsedPacket.getLayerOfType<pcpp::IPLayer>();
		if (!ipLayer) continue;
		pcpp::IPAddress srcIP = ipLayer->getSrcIPAddress();
		pcpp::IPAddress dstIP = ipLayer->getDstIPAddress();

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
			//if srcip is serverip, then dst is client ip, and viceversa
			if (srcv4IP.matchNetwork(serverNet)) {
				/* captured in server so ttl is 0. thus not consider.
				pcpp::iphdr* header = dstv4IP.getIPv4Header();
				uint8_t ttl = header->timeToLive;
				ipttlmp[dstIP.toString()].push_back(ttl);
				*/
			} else {
				//pcpp::VlanLayer* vlanLayer = parsedPacket.getLayerOfType<pcpp::VlanLayer>();
				//pcpp::Layer* nextLayer = vlanLayer->getNextLayer();
				//pcpp::IPv4Layer* ipv4Layer = dynamic_cast<pcpp::IPv4Layer*>(nextLayer);
				//uint8_t ttl = ipv4Layer->getIPv4Header()->timeToLive;
				pcpp::IPv4Layer* ipv4layer = parsedPacket.getLayerOfType<pcpp::IPv4Layer>();
				pcpp::iphdr* header = ipv4layer->getIPv4Header();
				uint8_t ttl = header->timeToLive;
				//std::cout << (int)ttl << std::endl; // (int) works. (uint8_t) not work.
				ipttlmp[srcIP.toString()].push_back(ttl);
			}
		} else if (srcIP.isIPv6() && dstIP.isIPv6()) {
			pcpp::IPv6Address srcv6IP = srcIP.getIPv6();
			pcpp::IPv6Address dstv6IP = dstIP.getIPv6();
			// lan to lan packet can be disregared since both src/dst is not client
			// ff02::1 is RA, so can be ignored
			if (srcv6IP.matchNetwork(serverNet) && dstv6IP.matchNetwork(serverNet)) continue;
			//if srcip is serverip, then dst is client ip, and viceversa
			if (srcv6IP.matchNetwork(serverNet)) {
				/*
				pcpp::iphdr* header = dstv4IP.getIPv6Header();
				uint8_t ttl = header->timeToLive;
				ipttlmp[dstIP.toString()].push_back(ttl);
				*/
			} else {
				pcpp::IPv6Layer* ipv6layer = parsedPacket.getLayerOfType<pcpp::IPv6Layer>();
				pcpp::ip6_hdr* header = ipv6layer->getIPv6Header();
				uint8_t ttl = header->hopLimit;
				ipttlmp[srcIP.toString()].push_back(ttl);
			}
		}
    }

	for (const auto &ipttl : ipttlmp) {
		size_t count = 0;
		size_t hopsum = 0;
		for (const uint8_t ttl : ipttl.second) {
			count += 1;
			hopsum += (int)ttl;
			//std::cout << (int)ttl << " ";
			//printf("%d ", ttl);
		}
		//std::cout << std::endl;
		float hopavg = hopsum / count;
		if (ofs.is_open()) {
			ofs << ipttl.first << " " << hopavg << std::endl;
		} else {
			std::cout << std::setw(15) << ipttl.first << " ";
			std::cout << hopavg << std::endl;
		}
	}

	delete reader;
	ofs.close();
	return 0;
}
