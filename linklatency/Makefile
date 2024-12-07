type=client #server or client or (both *todo)
TARGET=$(OUT_DIR)/link_latencies_$(strip $(type)).csv #link_latencies.csv
route_mx=$(DATA_DIR)/routing_matrix_$(strip $(type)).csv #routing_matrix.csv
odrtt_timeseries=$(DATA_DIR)/odrtt_timeseries_$(strip $(type)).csv #odrtt_timeseries.csv
odasnrtt=$(DATA_DIR)/$(strip $(type))asnrtt.csv
odrtt=./../$(strip $(type))rtt.csv
DATA_DIR=data
OUT_DIR=output

all: $(TARGET) 

$(TARGET): $(OUT_DIR) $(route_mx) $(odrtt_timeseries)
	python3 fukusoutimeseries_cv.py $(route_mx) $(odrtt_timeseries) $(TARGET)

$(route_mx): $(odasnrtt)
	python3 makeroutemx2.py $(odasnrtt) $(route_mx)

$(odrtt_timeseries): $(odasnrtt)
	python3 makeodrtttimeseries.py $(odasnrtt) $(odrtt_timeseries)

$(odasnrtt): $(odrtt)
	python3 makeasnrttcsv.py $(odrtt) $(odasnrtt)

ifeq ($(type), server)
$(odrtt): /data/vpngate/dump_local-20240514-00.pcap
	make -C rttextractor/
	./rttextractor /data/vpngate/dump_local-20240514-00.pcap 10.0.0.0/8 $(odrtt)
else ifeq ($(type), client)
$(odrtt): /data/vpngate/dump_global-20240514-00.pcap
	make -C rttextractor/
	./rttextractor /data/vpngate/dump_global-20240514-00.pcap 219.100.37.0/24 $(odrtt)
endif

$(OUT_DIR):
	mkdir output

