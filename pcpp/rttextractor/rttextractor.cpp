#include "rttextractor.hpp"

/*
	pcap rtt extractor
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

	std::unordered_map<uint32_t, rttInfo_t> iprttmp;

    pcpp::RawPacket rawPacket;
    while (reader->getNextPacket(rawPacket)) {
        pcpp::Packet parsedPacket(&rawPacket);

		pcpp::IPLayer* ipLayer = parsedPacket.getLayerOfType<pcpp::IPLayer>();
		if (!ipLayer) continue;
		pcpp::TcpLayer* tcpLayer = parsedPacket.getLayerOfType<pcpp::TcpLayer>();
		if (!tcpLayer) continue;

		pcpp::IPAddress srcIP = ipLayer->getSrcIPAddress();
		pcpp::IPAddress dstIP = ipLayer->getDstIPAddress();

		pcpp::IPAddress novpnip;
		if (srcIP.isIPv4() && dstIP.isIPv4()) {
			pcpp::IPv4Address srcv4IP = srcIP.getIPv4();
			pcpp::IPv4Address dstv4IP = dstIP.getIPv4();
			// lan to lan packet can be disregared since both src/dst is not client
			if (srcv4IP.matchNetwork(serverNet) && dstv4IP.matchNetwork(serverNet)) continue;
			//if srcip is serverip, then dst is client ip, and viceversa
			if (srcv4IP.matchNetwork(serverNet)) {
				novpnip = dstIP;
			} else {
				novpnip = srcIP;
			}
		} else if (srcIP.isIPv6() && dstIP.isIPv6()) {
			pcpp::IPv6Address srcv6IP = srcIP.getIPv6();
			pcpp::IPv6Address dstv6IP = dstIP.getIPv6();
			// lan to lan packet can be disregared since both src/dst is not client
			// ff02::1 is RA, so can be ignored
			if (srcv6IP.matchNetwork(serverNet) && dstv6IP.matchNetwork(serverNet)) continue;
			//if srcip is serverip, then dst is client ip, and viceversa
			if (srcv6IP.matchNetwork(serverNet)) {
				novpnip = dstIP;
			} else {
				novpnip = srcIP;
			}
		}

		pcpp::tcphdr* tcpheader = tcpLayer->getTcpHeader();
		//if (tcpheader->synFlag && tcpheader->ackFlag && tcpheader->pshFlag) { // pshFlag?
		if (tcpheader->synFlag && tcpheader->ackFlag) {
			uint32_t hash = pcpp::hash5Tuple(&parsedPacket);
			uint32_t acknum = ntohl(tcpheader->ackNumber);
			if (iprttmp[hash].syntimemp.find(acknum - 1) != iprttmp[hash].syntimemp.end()) {
				struct timespec syntime = iprttmp[hash].syntimemp[acknum - 1];
				struct timespec synacktime = rawPacket.getPacketTimeStamp();
				double starttime = syntime.tv_sec + (syntime.tv_nsec / 1e9);
				double endtime = synacktime.tv_sec + (synacktime.tv_nsec / 1e9);
				double rtt = (endtime - starttime) * 1000.0;
				iprttmp[hash].rttvec.push_back(rtt);
			}
		//} else if (tcpheader->synFlag && tcpheader->pshFlag) { // pshFlag necessary?
		} else if (tcpheader->synFlag) { // kotchatonisinaito konai
			uint32_t hash = pcpp::hash5Tuple(&parsedPacket);
			iprttmp[hash].ipaddress = novpnip;
			uint32_t seqnum = ntohl(tcpheader->sequenceNumber);
			iprttmp[hash].syntimemp[seqnum] = rawPacket.getPacketTimeStamp();
			//std::cout << seqnum << std::endl;
		}
    }

	for (const auto &iprtt : iprttmp) {
		double rttsum = 0;
		double rttmin = 10000000;
		double rttmax = 0;
		std::vector<double> rttvec = iprtt.second.rttvec;
		if (rttvec.size() == 0) continue;
		std::cout << "------" << std::endl;
		//std::cout << iprtt.second.ipaddress.toString() << ":";
		for (const auto &rtt : rttvec) {
			std::cout << rtt << " ";
			if (rtt < rttmin) {
				rttmin = rtt;
			}
			if (rtt > rttmax) {
				rttmax = rtt;
			}
			rttsum += rtt;
		}
		std::cout << std::endl;
		double rttavg = rttsum / rttvec.size();
		if (ofs.is_open()) {
			ofs << iprtt.second.ipaddress.toString() << " " << rttavg << " " << rttmin << " " << rttmax << std::endl;
		} else {
			std::cout << iprtt.second.ipaddress.toString() << " " << rttavg << " " << rttmin << " " << rttmax << std::endl;
		}
	}

	delete reader;
	ofs.close();
	return 0;
}
