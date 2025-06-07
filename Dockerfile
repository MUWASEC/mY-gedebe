FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive

# update and install necessary packages
RUN apt-get update -y && apt-get upgrade -y && \
    apt-get install -y \
        build-essential \
        tzdata gdb-multiarch wget binutils python3-pip ruby-dev git file colordiff imagemagick binwalk \
        git && \
    rm -rf /var/lib/apt/lists/*

# clone selected gdb plugin 
RUN mkdir -p /opt/gdb-src/
RUN git clone https://github.com/bata24/gef /opt/gdb-src/gef-kernel/

## https://github.com/bata24/gef
RUN pip3 install setuptools crccheck unicorn capstone ropper keystone-engine tqdm magika codext pycryptodome pillow pyzbar --break-system-packages
RUN pip3 install angr==9.2.154 --break-system-packages
RUN gem install seccomp-tools one_gadget
RUN wget -q https://github.com/0vercl0k/rp/releases/download/v2.1.4/rp-lin-clang.zip -P /tmp && \
    unzip /tmp/rp-lin-clang.zip -d /usr/local/bin/ && \
    rm /tmp/rp-lin-clang.zip

COPY gdbinit /root/.gdbinit
COPY custom.py /opt/gdb-src/
COPY bin/ /usr/bin/
RUN chmod +x /usr/bin/*

# Set default command (optional)
WORKDIR /
CMD ["/bin/bash"]