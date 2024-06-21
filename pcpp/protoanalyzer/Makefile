NAME = protoanalyzer

CXX = g++
CXXFLAGS = -fsanitize=address
PCPPDIR = /home/c241511i/pcapplusplus-23.09-ubuntu-22.04-gcc-11.2.0-x86_64/
OBJ_DIR = obj/

SRCS = protoanalyzer.cpp
OBJS = $(addprefix $(OBJ_DIR), $(SRCS:%.cpp=%.o))

INCLUDES = -I$(PCPPDIR)include/pcapplusplus/
LIBRARY = -L$(PCPPDIR)lib/ -lPcap++ -lPacket++ -lCommon++ -lpcap

all: $(OBJ_DIR) $(NAME)

$(OBJ_DIR):
	@mkdir -p $@

$(OBJ_DIR)%.o: %.cpp
	$(CXX) $(CXXFLAGS) $(INCLUDES) -c $< -o $@

$(NAME): $(OBJS)
	$(CXX) $(CXXFLAGS) $(OBJS) $(LIBRARY) -o $(NAME)

clean:
	rm -rf $(OBJS) $(OBJ_DIR) $(NAME)

