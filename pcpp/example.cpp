# include <iostream>
# include <SystemUtils.h>
# include <PcapFileDevice.h>
# include <Packet.h>
# include <EthLayer.h>
# include <IPv4Layer.h>
# include <TcpLayer.h>
# include <arpa/inet.h>

/*
	pcap example parse ethernet, ip, tcp (L2, L3, L4) skip if other
	argv[1] pcapfile
*/

std::string printTcpFlags(pcpp::TcpLayer* tcpLayer)
{
    std::string result = "";
    if (tcpLayer->getTcpHeader()->synFlag == 1)
        result += "SYN ";
    if (tcpLayer->getTcpHeader()->ackFlag == 1)
        result += "ACK ";
    if (tcpLayer->getTcpHeader()->pshFlag == 1)
        result += "PSH ";
    if (tcpLayer->getTcpHeader()->cwrFlag == 1)
        result += "CWR ";
    if (tcpLayer->getTcpHeader()->urgFlag == 1)
        result += "URG ";
    if (tcpLayer->getTcpHeader()->eceFlag == 1)
        result += "ECE ";
    if (tcpLayer->getTcpHeader()->rstFlag == 1)
        result += "RST ";
    if (tcpLayer->getTcpHeader()->finFlag == 1)
        result += "FIN ";

    return result;
}

std::string printTcpOptionType(pcpp::TcpOptionType optionType)
{
    switch (optionType)
    {
    case pcpp::PCPP_TCPOPT_NOP:
        return "NOP";
    case pcpp::PCPP_TCPOPT_TIMESTAMP:
        return "Timestamp";
    default:
        return "Other";
    }
}

std::string getProtocolTypeAsString(pcpp::ProtocolType protocolType)
{
    switch (protocolType)
    {
    case pcpp::Ethernet:
        return "Ethernet";
    case pcpp::IPv4:
        return "IPv4";
    case pcpp::TCP:
        return "TCP";
    case pcpp::HTTPRequest:
    case pcpp::HTTPResponse:
        return "HTTP";
    default:
        return "Unknown";
    }
}

int main(int argc, char* argv[])
{
	if (argc < 2) {
		std::cout << "invalid input" << std::endl;
		std::cout << "format: pcapfile, (opton) fllter_protocol" << std::endl;
		return 1;
	}

    std::string pcapfile = argv[1];
	//std::string protocol = argv[2];

    // open a pcap file for reading
	//pcpp::PcapFileReaderDevice reader("tshark.pcap"); use getReader() for pcapng file.
    pcpp::IFileReaderDevice* reader = pcpp::IFileReaderDevice::getReader(pcapfile);
    if (!reader->open()) {
        std::cerr << "Error opening the pcap file" << std::endl;
        return 1;
    }
    //std::ofstream ofs("outfile");
    //if (!ofs) {
    //    std::cerr << "Error opening outfile " << std::endl;
    //}

    pcpp::RawPacket rawPacket;
    while (reader->getNextPacket(rawPacket)) {
		//reader->getNextPacket(rawPacket);
        pcpp::Packet parsedPacket(&rawPacket);

		// first let's go over the layers one by one and find out its type, its total length, its header length and its payload length
		for (pcpp::Layer* curLayer = parsedPacket.getFirstLayer(); curLayer != NULL; curLayer = curLayer->getNextLayer())
		{
			std::cout
				<< "Layer type: " << getProtocolTypeAsString(curLayer->getProtocol()) << "; " // get layer type
				<< "Total data: " << curLayer->getDataLen() << " [bytes]; " // get total length of the layer
				<< "Layer data: " << curLayer->getHeaderLen() << " [bytes]; " // get the header length of the layer
				<< "Layer payload: " << curLayer->getLayerPayloadSize() << " [bytes]" // get the payload length of the layer (equals total length minus header length)
				<< std::endl;
		}

		pcpp::EthLayer* ethernetLayer = parsedPacket.getLayerOfType<pcpp::EthLayer>();
		if (!ethernetLayer) {
			std::cerr << "couldn't parse ethernet" << std::endl;
			continue;
			delete reader;
		}
		std::cout 
			<< "Source MAC address: " << ethernetLayer->getSourceMac() << std::endl
			<< "Destination MAC address: " << ethernetLayer->getDestMac() << std::endl
			<< "Ether type = 0x" << std::hex << pcpp::netToHost16(ethernetLayer->getEthHeader()->etherType) << std::endl;
		
		pcpp::IPv4Layer* ipLayer = parsedPacket.getLayerOfType<pcpp::IPv4Layer>();
		if (!ipLayer) {
			std::cerr << "couldn't parse ip" << std::endl;
			continue;
			delete reader;
		}
		std::cout
			<< "Source IP address: " << ipLayer->getSrcIPAddress() << std::endl
			<< "Destination IP address: " << ipLayer->getDstIPAddress() << std::endl
			<< "IP ID; 0x" << std::hex<< pcpp::netToHost16(ipLayer->getIPv4Header()->ipId) << std::endl
			<< "TTL: " << std::dec << (int)ipLayer->getIPv4Header()->timeToLive << std::endl;

		pcpp::TcpLayer* tcpLayer = parsedPacket.getLayerOfType<pcpp::TcpLayer>();
		if (!tcpLayer) {
			std::cerr << "couldn't parse tcp" << std::endl;
			continue;
			delete reader;
		}
		std::cout
			<< "Source TCP port: " << tcpLayer->getSrcPort() << std::endl
			<< "Destination TCP port: " << tcpLayer->getDstPort() << std::endl
			<< "Window Size: " << pcpp::netToHost16(tcpLayer->getTcpHeader()->windowSize) << std::endl
			<< "TCP flags: " << printTcpFlags(tcpLayer) << std::endl;

		// go over all TCP options in this layer and print its type
		std::cout << "TCP options: ";
		for (pcpp::TcpOption tcpOption = tcpLayer->getFirstTcpOption(); tcpOption.isNotNull(); tcpOption = tcpLayer->getNextTcpOption(tcpOption))
		{
			std::cout << printTcpOptionType(tcpOption.getTcpOptionType()) << " ";
		}
		std::cout << std::endl;

		std::cout << "TCP Sequence Number: " << ntohl(tcpLayer->getTcpHeader()->sequenceNumber) << std::endl; // network byte order to host (big endian to little)
		std::cout << "TCP Ack Number: " << ntohl(tcpLayer->getTcpHeader()->ackNumber) << std::endl; // network byte order to host (big endian to little)

		break;

    }

    // close the file
    reader->close();

	delete reader;

    return 0;
}

