#include "rttextractor.hpp"
//#include <nlohmann/json.hpp>

/*
	pcap rtt extractor
	argv[1] pcapfile
	argv[2] serverIP_range
	argv[3] outfile (option)
*/

// double timespecToMs(const struct timespec& ts) {
// 	//std::cout << ts.tv_nsec / 1e6 << std::endl;
// 	//std::cout << (double)ts.tv_sec * 1000.0 + (double)ts.tv_nsec / 1e6 << std::endl;
//     return (double)ts.tv_sec * 1000.0 + (double)ts.tv_nsec / (double)1e6;
//     //return ts.tv_sec * 1000000.0 + ts.tv_nsec / 1e3;
// }

double timespecToMs(const struct timespec& ts) {
    return (double)ts.tv_sec * 1000.0 + (double)ts.tv_nsec / 1e6;
}

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
			//std::cout << srcIP.toString() << " " << dstIP.toString() << std::endl;
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
		//std::cout << "novpnip: " << novpnip << std::endl;

/*
経路の遅延を知るために
other <a= capture <b- vpnserver
other =a> capture -b> vpnserver

aが経路上の遅延
キャプチャポイントはvpnserver側なので
経路はaの方を知りたい.

vpnサーバ-アクセス先サーバの場合
vpnserver - accessserver
syn->
	<- syn/ack
の時間を計測
vpnサーバからsynを送ってからsyn/ackまでの時間が経路遅延.
(クライアントがvpnサーバ)

vpnサーバ-ユーザサーバの場合
syn/ack->
		<-ack
vpnサーバはサーバ側なのでsynは送らない(クライアントがsynで接続要求してくる）
vpnサーバからsyn/ackを送ってからackが返ってくるまでの時間が経路遅延.
(ユーザがクライアント）
*/

/*
//vpnサーバ - アクセス先サーバの遅延 synに対するsyn/ack
		pcpp::tcphdr* tcpheader = tcpLayer->getTcpHeader();
		//if (tcpheader->synFlag && tcpheader->ackFlag && tcpheader->pshFlag) { // pshFlag?
		if (tcpheader->synFlag && tcpheader->ackFlag && novpnip == srcIP) { // novpnip -a-> capture -b-> vpn (aが知りたい)
			uint32_t hash = pcpp::hash5Tuple(&parsedPacket);
			uint32_t acknum = ntohl(tcpheader->ackNumber);
			if (iprttmp[hash].syntimemp.find(acknum - 1) != iprttmp[hash].syntimemp.end()) {
				struct timespec syntime = iprttmp[hash].syntimemp[acknum - 1];
				struct timespec synacktime = rawPacket.getPacketTimeStamp();
				// std::cout << "start: " << syntime.tv_sec << " seconds and " << syntime.tv_nsec << " nanoseconds" << std::endl;
				// std::cout << "end: " << synacktime.tv_sec << " seconds and " << synacktime.tv_nsec << " nanoseconds" << std::endl;
				double starttime = syntime.tv_sec + (syntime.tv_nsec / 1e9);
				double endtime = synacktime.tv_sec + (synacktime.tv_nsec / 1e9);
				double rtt = (endtime - starttime) * 1000.0;
				iprttmp[hash].rttvec.push_back({rtt, syntime, synacktime});
				// std::cout << std::fixed << std::setprecision(6);
				// std::cout << "start: " << timespecToMs(syntime) << "\n";
				// std::cout << "end: " << timespecToMs(synacktime) << "\n";
				// std::cout << "rtt: " << timespecToMs(synacktime) - timespecToMs(syntime) << std::endl;
			}
		//} else if (tcpheader->synFlag && tcpheader->pshFlag) { // pshFlag necessary?
		} else if (tcpheader->synFlag && novpnip == dstIP) { // kotchatonisinaito konai // novpnip <-a- capture <-b- vpn (aが知りたい)
			uint32_t hash = pcpp::hash5Tuple(&parsedPacket);
			iprttmp[hash].ipaddress = novpnip;
			uint32_t seqnum = ntohl(tcpheader->sequenceNumber);
			iprttmp[hash].syntimemp[seqnum] = rawPacket.getPacketTimeStamp();
			//std::cout << seqnum << std::endl;
		}
*/
//vpnサーバ - クライアントの遅延 syn/ackに対するack
///*
		pcpp::tcphdr* tcpheader = tcpLayer->getTcpHeader();
		//if (tcpheader->synFlag && tcpheader->ackFlag && tcpheader->pshFlag) { // pshFlag?
		if (tcpheader->synFlag && tcpheader->ackFlag && novpnip == dstIP) { // novpnip <-a- capture <-b- vpn (aが知りたい) syn/ack
			uint32_t hash = pcpp::hash5Tuple(&parsedPacket);
			//std::cout << novpnip << std::endl;
			iprttmp[hash].ipaddress = novpnip;
			uint32_t seqnum = ntohl(tcpheader->sequenceNumber);
			iprttmp[hash].syntimemp[seqnum] = rawPacket.getPacketTimeStamp();
		//} else if (tcpheader->synFlag && tcpheader->pshFlag) { // pshFlag necessary?
		} else if (tcpheader->ackFlag && novpnip == srcIP) { // novpnip -a-> capture -b-> vpn (aが知りたい) ack
			uint32_t hash = pcpp::hash5Tuple(&parsedPacket);
			uint32_t acknum = ntohl(tcpheader->ackNumber);
			if (iprttmp[hash].syntimemp.find(acknum - 1) != iprttmp[hash].syntimemp.end()) {
				struct timespec syntime = iprttmp[hash].syntimemp[acknum - 1];
				struct timespec synacktime = rawPacket.getPacketTimeStamp();
				double starttime = syntime.tv_sec + (syntime.tv_nsec / 1e9);
				double endtime = synacktime.tv_sec + (synacktime.tv_nsec / 1e9);
				double rtt = (endtime - starttime) * 1000.0;
				//std::cout << rtt << std::endl;
				//std::cout << srcIP << ">" << dstIP << std::endl;
				//iprttmp[hash].rttvec.push_back(rtt);
				iprttmp[hash].rttvec.push_back({rtt, syntime, synacktime});
			}
		}
//*/
    }

	if (ofs.is_open()) {
		ofs << "ipaddr,rtt,syntime(ms),synacktime(ms),rtt2" << std::endl;
	} else {
		std::cout << "ipaddr,rtt,syntime(ms),synacktime(ms),rtt2" << std::endl;
	}
	for (const auto &iprtt : iprttmp) {
		std::vector<tsRtt_t> rttvec = iprtt.second.rttvec;
		for (const auto &rtt : rttvec) {
			if (ofs.is_open()) {
				// std::cout << std::fixed << std::setprecision(6);
				// std::cout << "start: " << timespecToMs(syntime) << "\n";
				// std::cout << "end: " << timespecToMs(synacktime) << "\n";
				// std::cout << "rtt: " << timespecToMs(synacktime) - timespecToMs(syntime) << std::endl;

				ofs << iprtt.second.ipaddress.toString() << ",";
				ofs << rtt.rtt << ",";
				ofs << std::fixed << std::setprecision(6);
				ofs << timespecToMs(rtt.syntime) << ",";
				ofs << timespecToMs(rtt.synacktime) << ",";
				ofs << timespecToMs(rtt.synacktime) - timespecToMs(rtt.syntime) << std::endl;
				// ofs << iprtt.second.ipaddress.toString() << "," << rtt.rtt << "," << timespecToMs(rtt.syntime) << "," << timespecToMs(rtt.synacktime) << std::endl;
				//ofs << j.dump(4) << " " << rtt << std::endl; //key must be unique but here not so can't use

			} else {
				std::cout << iprtt.second.ipaddress.toString() << ",";
				std::cout << rtt.rtt << ",";
				std::cout << std::fixed << std::setprecision(6);
				std::cout << timespecToMs(rtt.syntime) << ",";
				std::cout << timespecToMs(rtt.synacktime) << ",";
				std::cout << timespecToMs(rtt.synacktime) - timespecToMs(rtt.syntime) << std::endl;
				//std::cout << iprtt.second.ipaddress.toString() << "," << rtt.rtt << "," << timespecToMs(rtt.syntime) << "," << timespecToMs(rtt.synacktime) << std::endl;
				//std::cout << iprtt.second.ipaddress.toString() << " " << rtt.rtt << std::endl;
				//std::cout << j.dump(4) << " " << rtt << std::endl;
			}
		}
	}

/*
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
*/

	delete reader;
	ofs.close();
	return 0;
}
