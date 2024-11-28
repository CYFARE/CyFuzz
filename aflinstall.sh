sudo apt update
sudo apt install -y build-essential python3-dev automake cmake git flex bison libglib2.0-dev libpixman-1-dev python3-setuptools cargo libgtk-3-dev
sudo apt install -y lld-14 llvm-14 llvm-14-dev clang-14 || sudo apt-get install -y lld llvm llvm-dev clang
sudo apt install -y gcc-$(gcc --version|head -n1|sed 's/\..*//'|sed 's/.* //')-plugin-dev libstdc++-$(gcc --version|head -n1|sed 's/\..*//'|sed 's/.* //')-dev
sudo apt install -y ninja-build
sudo apt install -y cpio libcapstone-dev
sudo apt install -y wget curl
sudo apt install -y python3-pip
git clone https://github.com/AFLplusplus/AFLplusplus
cd AFLplusplus
make distrib PERFORMANCE=1
sudo make install