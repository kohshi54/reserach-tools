#include "flowanalyzer.hpp"

/*
	pcap flow analyzer
	argv[1] pcapfile
	argv[2] serverIP_range
	argv[3] log (option)
*/

//uint32_t getReverseHash(pcpp::Packet packet);

int main(int argc, char* argv[])
{
	if (argc < 3) {
		std::cerr << "invalid input" << std::endl;
		std::cerr << "format: pcapfile, serverIp_range(219.100.37.0/24), (optinal) log" << std::endl;
		return 1;
	}
	std::string pcapfile = argv[1];
	std::string serverNet = argv[2];
	std::ofstream ofs;
	if (argc == 4) {
		std::string logfile = argv[3];
		ofs.open(logfile);
    	if (!ofs) {
        	std::cerr << "Error opening logfile " << std::endl;
    	}
	}

    // open a pcap file for reading
    pcpp::IFileReaderDevice* reader = pcpp::IFileReaderDevice::getReader(pcapfile);
    if (!reader->open()) {
        std::cerr << "Error opening pcap file" << std::endl;
		delete reader;
        return 1;
    }

	std::unordered_map<uint32_t, tcpConnInfo_t> tcpConnInfos;
    pcpp::RawPacket rawPacket;
	size_t pkts_count = 0;
    while (reader->getNextPacket(rawPacket)) {
        pcpp::Packet parsedPacket(&rawPacket);

		pcpp::IPv4Layer* ipLayer = parsedPacket.getLayerOfType<pcpp::IPv4Layer>();
		if (!ipLayer) continue;
		pcpp::IPv4Address srcIP = ipLayer->getSrcIPv4Address();
		pcpp::IPv4Address dstIP = ipLayer->getDstIPv4Address();

		pcpp::TcpLayer* tcpLayer = parsedPacket.getLayerOfType<pcpp::TcpLayer>();
		if (!tcpLayer) continue;
		uint16_t srcPort = tcpLayer->getSrcPort();
		uint16_t dstPort = tcpLayer->getDstPort();
		
		uint32_t hash = pcpp::hash5Tuple(&parsedPacket);
		pkts_count++;

		pcpp::IPAddress clientIP, serverIP;
		uint16_t clientPort, serverPort;
		//assume the server is 10.5.138.2/32
		//if (srcIP.matchNetwork("10.5.138.2/32")) {
		//if (srcIP.matchNetwork("10.0.0.0/8")) {
		if (srcIP.matchNetwork(serverNet)) {
			serverIP = srcIP;
			clientIP = dstIP;
			serverPort = srcPort;
			clientPort = dstPort;
		} else {
			serverIP = dstIP;
			clientIP = srcIP;
			serverPort = dstPort;
			clientPort = srcPort;
		}

		//uint32_t reverseHash = getReverseHash(parsedPacket); //hash5Tuple() already consider reverse hash
		//std::cout << "hash:" << hash << " " << srcIP.toString() << " " << dstIP.toString() << " " << srcPort << " " << dstPort << std::endl;
		//std::cout << "hash:" << hash << " " << clientIP.toString() << " " << serverIP.toString() << " " << clientPort << " " << serverPort << std::endl;
		//13.248.151.210 10.245.245.159 443 58242 4247022545
		//ofs << "hash:" << hash << " " << srcIP.toString() << " " << dstIP.toString() << " " << srcPort << " " << dstPort << " ";
		//if (tcpConnInfos.find(hash) == tcpConnInfos.end() && tcpConnInfos.find(reverseHash) == tcpConnInfos.end()) {
/*	
		if (tcpConnInfos.find(hash) == tcpConnInfos.end()) {
			tcpConnInfos[hash] = {clientIP, serverIP, clientPort, serverPort, 1};
			if (serverIP == srcIP) {
				tcpConnInfos[hash].pkts_server_to_cli += 1;
				tcpConnInfos[hash].seqnum_s2c = ntohl(tcpLayer->getTcpHeader()->sequenceNumber);
				tcpConnInfos[hash].nextseq_s2c = tcpConnInfos[hash].seqnum_s2c + tcpLayer->getLayerPayloadSize();
				ofs << "thash:" << hash << " " << srcIP.toString() << " " << dstIP.toString() << " " << srcPort << " " << dstPort << " ";
				ofs << "seqnum=" << tcpConnInfos[hash].seqnum_s2c << ":" << tcpConnInfos[hash].nextseq_s2c << " " << tcpLayer->getLayerPayloadSize() << std::endl;
			} else if (serverIP == dstIP) {
				tcpConnInfos[hash].pkts_cli_to_server += 1;
				tcpConnInfos[hash].seqnum_c2s = ntohl(tcpLayer->getTcpHeader()->sequenceNumber);
				tcpConnInfos[hash].nextseq_c2s = tcpConnInfos[hash].seqnum_c2s + tcpLayer->getLayerPayloadSize();
				ofs << "thash:" << hash << " " << srcIP.toString() << " " << dstIP.toString() << " " << srcPort << " " << dstPort << " ";
				ofs << "seqnum=" << tcpConnInfos[hash].seqnum_c2s << ":" << tcpConnInfos[hash].seqnum_c2s + tcpLayer->getLayerPayloadSize() << " " << tcpLayer->getLayerPayloadSize() << std::endl;
			}
		} else {
*/
			//std::cout << serverIP << " " << srcIP << " " << (serverIP == srcIP) << " " << (serverIP == dstIP) << std::endl;
			if (tcpConnInfos.find(hash) == tcpConnInfos.end()) {
				tcpConnInfos[hash] = {clientIP, serverIP, clientPort, serverPort};
			}
			tcpConnInfos[hash].pkts_count += 1;
			if (serverIP == srcIP) {
				tcpConnInfos[hash].pkts_server_to_cli += 1;
				tcpConnInfos[hash].seqnum_s2c = ntohl(tcpLayer->getTcpHeader()->sequenceNumber);
				if (tcpConnInfos[hash].nextseq_s2c != -1 && tcpConnInfos[hash].nextseq_s2c < tcpConnInfos[hash].seqnum_s2c) {
					tcpConnInfos[hash].miss_count_s2c += 1;
					if (ofs.is_open()) {
						ofs << "miss detected for hash=" << hash << ": expected " << tcpConnInfos[hash].nextseq_s2c << " but got " << tcpConnInfos[hash].seqnum_s2c << std::endl;
					}
				}
				if (tcpConnInfos[hash].nextseq_s2c != -1 && tcpConnInfos[hash].nextseq_s2c > tcpConnInfos[hash].seqnum_s2c) {
					tcpConnInfos[hash].resent_count_s2c += 1;
					if (ofs.is_open()) {
						ofs << "resent detected" << std::endl;
					}
				}
				size_t tcpPayloadSize = 0;
				if  (tcpLayer->getTcpHeader()->synFlag == 1 || tcpLayer->getTcpHeader()->finFlag == 1) { // syn, syn/ack, finはペイロードが0バイトでもseqnumは1増加.
					tcpConnInfos[hash].nextseq_s2c = tcpConnInfos[hash].seqnum_s2c + 1;
				} else {
                	tcpPayloadSize = be16toh(ipLayer->getIPv4Header()->totalLength) - (ipLayer->getHeaderLen() + tcpLayer->getHeaderLen());
					tcpConnInfos[hash].nextseq_s2c = tcpConnInfos[hash].seqnum_s2c + tcpPayloadSize;
					//tcpConnInfos[hash].nextseq_s2c = tcpConnInfos[hash].seqnum_s2c + tcpLayer->getLayerPayloadSize();
				}
				if (ofs.is_open()) {
					ofs << "hash:" << hash << " " << srcIP.toString() << " " << dstIP.toString() << " " << srcPort << " " << dstPort << " ";
					//ofs << "seqnum=" << tcpConnInfos[hash].seqnum_s2c << ":" << tcpConnInfos[hash].nextseq_s2c << " " << tcpLayer->getLayerPayloadSize() << std::endl;
					ofs << "seqnum=" << tcpConnInfos[hash].seqnum_s2c << ":" << tcpConnInfos[hash].nextseq_s2c << " " << tcpPayloadSize << std::endl;
				}
			} else if (serverIP == dstIP) {
				tcpConnInfos[hash].pkts_cli_to_server += 1;
				tcpConnInfos[hash].seqnum_c2s = ntohl(tcpLayer->getTcpHeader()->sequenceNumber);
				if (tcpConnInfos[hash].nextseq_c2s != -1 && tcpConnInfos[hash].nextseq_c2s < tcpConnInfos[hash].seqnum_c2s) {
					tcpConnInfos[hash].miss_count_c2s += 1;
					if (ofs.is_open()) {
						ofs << "miss detected for hash=" << hash << ": expected " << tcpConnInfos[hash].nextseq_c2s << " but got " << tcpConnInfos[hash].seqnum_c2s << std::endl;
					}
				}
				if (tcpConnInfos[hash].nextseq_c2s != -1 && tcpConnInfos[hash].nextseq_c2s > tcpConnInfos[hash].seqnum_c2s) {
					tcpConnInfos[hash].resent_count_c2s += 1;
					if (ofs.is_open()) {
						ofs << "resent detected" << std::endl;
					}
				}
				size_t tcpPayloadSize = 0;
				if  (tcpLayer->getTcpHeader()->synFlag == 1 || tcpLayer->getTcpHeader()->finFlag == 1) {
					tcpConnInfos[hash].nextseq_c2s = tcpConnInfos[hash].seqnum_c2s + 1;
				} else {
                	tcpPayloadSize = be16toh(ipLayer->getIPv4Header()->totalLength) - (ipLayer->getHeaderLen() + tcpLayer->getHeaderLen());
					tcpConnInfos[hash].nextseq_c2s = tcpConnInfos[hash].seqnum_c2s + tcpPayloadSize;
					//tcpConnInfos[hash].nextseq_c2s = tcpConnInfos[hash].seqnum_c2s + tcpLayer->getLayerPayloadSize(); // なぜかvlanがあると動作してない.
				}
				if (ofs.is_open()) {
					ofs << "hash:" << hash << " " << srcIP.toString() << " " << dstIP.toString() << " " << srcPort << " " << dstPort << " ";
					//ofs << "seqnum=" << tcpConnInfos[hash].seqnum_c2s << ":" << tcpConnInfos[hash].nextseq_c2s << " " << tcpLayer->getLayerPayloadSize() << std::endl;
					ofs << "seqnum=" << tcpConnInfos[hash].seqnum_c2s << ":" << tcpConnInfos[hash].nextseq_c2s << " " << tcpPayloadSize << std::endl;
				}
			}
		//}
    }

	tcpConnInfo_t all;
	for (const auto &conn : tcpConnInfos) {
///*
		std::cout
			<< conn.second.clientIP << " "
			<< conn.second.serverIP << " "
			<< conn.second.clientPort << " "
			<< conn.second.serverPort << " "
			<< conn.second.pkts_count << " "
			<< conn.second.pkts_cli_to_server << " "
			<< conn.second.pkts_server_to_cli << " "
			<< conn.second.miss_count_c2s << " "
			<< conn.second.resent_count_c2s << std::endl;

			std::cout << "-- c2s --" << std::endl;
			std::cout << conn.second.miss_count_c2s << " " << conn.second.resent_count_c2s << " " << conn.second.pkts_cli_to_server << std::endl;
			printf("miss rate: %f%%\n", (float)conn.second.miss_count_c2s / (float)conn.second.pkts_cli_to_server * 100);
			printf("resent rate: %f%%\n", (float)conn.second.resent_count_c2s / (float)conn.second.pkts_cli_to_server * 100);
			std::cout << "-- s2c --" << std::endl;
			std::cout << conn.second.miss_count_s2c << " " << conn.second.resent_count_s2c << " " << conn.second.pkts_server_to_cli << std::endl;
			printf("miss rate: %f%%\n", (float)conn.second.miss_count_s2c / (float)conn.second.pkts_server_to_cli * 100);
			printf("resent rate: %f%%\n", (float)conn.second.resent_count_s2c / (float)conn.second.pkts_server_to_cli * 100);

			std::cout << "-- all --" << std::endl;
			std::cout << conn.second.miss_count_c2s + conn.second.miss_count_s2c << " " << conn.second.resent_count_c2s + conn.second.miss_count_c2s << " " << conn.second.pkts_count << std::endl;
			printf("miss rate: %f%%\n", (float)(conn.second.miss_count_c2s + conn.second.miss_count_s2c) / (float)conn.second.pkts_count * 100);
			printf("resent rate: %f%%\n", (float)(conn.second.resent_count_c2s + conn.second.resent_count_s2c) / (float)conn.second.pkts_count * 100);

//*/
			all.miss_count_c2s += conn.second.miss_count_c2s;
			all.resent_count_c2s += conn.second.resent_count_c2s;
			all.miss_count_s2c += conn.second.miss_count_s2c;
			all.resent_count_s2c += conn.second.resent_count_s2c;
			all.pkts_cli_to_server += conn.second.pkts_cli_to_server;
			all.pkts_server_to_cli += conn.second.pkts_server_to_cli;
	}

	std::cout << std::endl;
	std::cout << "-- c2s all --" << std::endl;
	std::cout << all.miss_count_c2s << " " << all.resent_count_c2s << " " << all.pkts_cli_to_server << std::endl;
	printf("miss rate: %f%%\n", (float)all.miss_count_c2s / (float)all.pkts_cli_to_server * 100);
	printf("resent rate: %f%%\n", (float)all.resent_count_c2s / (float)all.pkts_cli_to_server * 100);
	std::cout << "-- s2c all --" << std::endl;
	std::cout << all.miss_count_s2c << " " << all.resent_count_s2c << " " << all.pkts_server_to_cli << std::endl;
	printf("miss rate: %f%%\n", (float)all.miss_count_s2c / (float)all.pkts_server_to_cli * 100);
	printf("resent rate: %f%%\n", (float)all.resent_count_s2c / (float)all.pkts_server_to_cli * 100);
	std::cout << "-- all all --" << std::endl;
	std::cout << all.miss_count_c2s + all.miss_count_s2c << " " << all.resent_count_c2s + all.resent_count_c2s << " " << pkts_count << std::endl;
	printf("miss rate: %f%%\n", (float)(all.miss_count_c2s + all.miss_count_s2c) / (float)pkts_count * 100);
	printf("resent rate: %f%%\n", (float)(all.resent_count_c2s + all.resent_count_s2c) / (float)pkts_count * 100);

    // close the file
    reader->close();

	delete reader;

    return 0;
}

/*
uint32_t getReverseHash(pcpp::Packet packet) {
	pcpp::IPv4Layer* ipLayer = packet.getLayerOfType<pcpp::IPv4Layer>();
	pcpp::IPv4Address tmp = ipLayer->getSrcIPv4Address();
	ipLayer->setSrcIPv4Address(ipLayer->getDstIPv4Address());
	ipLayer->setDstIPv4Address(tmp);
	
	pcpp::TcpLayer* tcpLayer = packet.getLayerOfType<pcpp::TcpLayer>();
	uint16_t tmp2 = tcpLayer->getSrcPort();
	tcpLayer->getTcpHeader()->portSrc = htons(tcpLayer->getDstPort());
	tcpLayer->getTcpHeader()->portDst = htons(tmp2);

	std::cout << "reverse:" << pcpp::hash5Tuple(&packet) << " " << packet.getLayerOfType<pcpp::IPv4Layer>()->getSrcIPv4Address() << " " << packet.getLayerOfType<pcpp::IPv4Layer>()->getDstIPv4Address() << " " << packet.getLayerOfType<pcpp::TcpLayer>()->getSrcPort() << " " << packet.getLayerOfType<pcpp::TcpLayer>()->getDstPort() << std::endl;

	return pcpp::hash5Tuple(&packet);
}
*/

