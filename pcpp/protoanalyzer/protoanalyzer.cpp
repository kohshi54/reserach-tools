#include "protoanalyzer.hpp"

/*
	pcap protocol analyzer
	argv[1] pcapfile
*/

std::string getProtocolTypeAsString(pcpp::ProtocolType protocolType)
{
    switch (protocolType)
    {
    case pcpp::Ethernet:
        return "Ethernet";
    case pcpp::VLAN:
        return "VLAN";
    case pcpp::PPP_PPTP:
        return "PPP_PPTP";
    case pcpp::PPPoE:
        return "PPPoE";
    case pcpp::MPLS:
        return "MPLS";
    case pcpp::IPv4:
        return "IPv4";
	case pcpp::IPv6:
        return "IPv6";
	case pcpp::ARP:
        return "ARP";
	case pcpp::ICMP:
        return "ICMP";
    case pcpp::GRE:
        return "GRE";
    case pcpp::IGMP:
        return "IGMP";
    case pcpp::VXLAN:
        return "VXLAN";
    case pcpp::TCP:
        return "TCP";
	case pcpp::UDP:
        return "UDP";
    case pcpp::SSL:
        return "SSL";
    case pcpp::HTTP:
        return "HTTP";
	case pcpp::DNS:
        return "DNS";
	case pcpp::DHCP:
        return "DHCP";
	case pcpp::SIP:
        return "SIP";
    default:
        return "Unknown";
    }
}

int main(int argc, char* argv[])
{
	if (argc < 2) {
		std::cout << "invalid input" << std::endl;
		std::cout << "format: pcapfile" << std::endl;
		return 1;
	}

    std::string pcapfile = argv[1];

    // open a pcap file for reading
    pcpp::IFileReaderDevice* reader = pcpp::IFileReaderDevice::getReader(pcapfile);
    if (!reader->open()) {
        std::cerr << "Error opening the pcap file" << std::endl;
        return 1;
    }

	std::unordered_map<pcpp::ProtocolType, size_t> L2type_count;
	std::unordered_map<pcpp::ProtocolType, size_t> L3type_count;
	std::unordered_map<pcpp::ProtocolType, size_t> L4type_count;
	std::unordered_map<pcpp::ProtocolType, size_t> L6type_count;
	std::unordered_map<pcpp::ProtocolType, size_t> L7type_count;
	std::unordered_map<pcpp::ProtocolType, size_t> unknown_count;
	
    pcpp::RawPacket rawPacket;
    while (reader->getNextPacket(rawPacket)) {
        pcpp::Packet parsedPacket(&rawPacket);

		for (pcpp::Layer* curLayer = parsedPacket.getFirstLayer(); curLayer != NULL; curLayer = curLayer->getNextLayer())
		{
			pcpp::DnsOverTcpLayer *dnsOverTcpLayer = parsedPacket.getLayerOfType<pcpp::DnsOverTcpLayer>();
			if (!dnsOverTcpLayer) {
			} else {
				std::cout << "dns over tcp detected" << std::endl;
			}
			if (curLayer->getProtocol() == pcpp::DNS) {
			}
			switch (curLayer->getProtocol())
			{
			case pcpp::Ethernet:
			case pcpp::VLAN:
			case pcpp::PPP_PPTP:
			case pcpp::PPPoE:
			case pcpp::MPLS:
				L2type_count[curLayer->getProtocol()] += 1;
				break;
			case pcpp::IPv4:
			case pcpp::IPv6:
			case pcpp::ARP:
			case pcpp::ICMP:
			case pcpp::GRE:
			case pcpp::IGMP:
			case pcpp::VXLAN:
				L3type_count[curLayer->getProtocol()] += 1;
				break;
			case pcpp::TCP:
			case pcpp::UDP:
			case pcpp::SSL:
				L4type_count[curLayer->getProtocol()] += 1;
				break;
			case pcpp::HTTP:
			case pcpp::DNS:
			case pcpp::DHCP:
			case pcpp::SIP:
				L7type_count[curLayer->getProtocol()] += 1;
				break;
			default:
				unknown_count[curLayer->getProtocol()] += 1;
			}
		}
    }

	std::cout << "-- l2 layer --" << std::endl;
	for (auto proto_count : L2type_count) {
		std::cout << getProtocolTypeAsString(proto_count.first) << ":" << proto_count.second << std::endl;
	}
	std::cout << "-- l3 layer --" << std::endl;
	for (auto proto_count : L3type_count) {
		if (getProtocolTypeAsString(proto_count.first) == "Unknown") {
			std::cout << (proto_count.first) << ":" << proto_count.second << std::endl;
			continue;
		}
		std::cout << getProtocolTypeAsString(proto_count.first) << ":" << proto_count.second << std::endl;
	}
	std::cout << "-- l4 layer --" << std::endl;
	for (auto proto_count : L4type_count) {
		std::cout << getProtocolTypeAsString(proto_count.first) << ":" << proto_count.second << std::endl;
	}

	std::cout << "-- l6 layer --" << std::endl;
	for (auto proto_count : L6type_count) {
		std::cout << getProtocolTypeAsString(proto_count.first) << ":" << proto_count.second << std::endl;
	}

	std::cout << "-- l7 layer --" << std::endl;
	for (auto proto_count : L7type_count) {
		std::cout << getProtocolTypeAsString(proto_count.first) << ":" << proto_count.second << std::endl;
	}

	std::cout << "-- unknown layer --" << std::endl;
	for (auto proto_count : unknown_count) {
		std::cout << "0x" << std::hex << (proto_count.first) << std::dec << ":" << proto_count.second << std::endl;
	}
    // close the file
    reader->close();

	delete reader;

    return 0;
}

