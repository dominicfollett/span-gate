FROM resin/raspberrypi3-buildpack-deps:jessie

# GStreamer  and openCV deps
# Several retries is a workaround for flaky downloads
RUN packages="findutils coreutils zip software-properties-common pkg-config libgtk2.0-dev libatlas-dev libgraphicsmagick1-dev graphicsmagick wget git libboost-all-dev python3-picamera curl python python-dev unzip supervisor libzmq3 libzmq3-dev v4l-utils python3-pip python3-dev python3-numpy python-numpy libgstreamer1.0-dev libgstreamer1.0-0 libgstreamer-vaapi1.0-dev libgstreamer-vaapi1.0-0 libgstreamer-plugins-base1.0-dev libgstreamer-plugins-bad1.0-dev libgstreamer-plugins-bad1.0-0 libgstreamer-plugins-base1.0-0 gstreamer1.0-tools gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-omx build-essential cmake libeigen3-dev libjpeg-dev libtiff5-dev libtiff5 libjasper-dev libjasper1 libpng12-dev libpng12-0 libavcodec-dev  libavcodec56 libavformat-dev libavformat56 libswscale-dev libswscale3 libv4l-dev libv4l-0 libatlas-base-dev libatlas3-base gfortran libblas-dev libblas3 liblapack-dev liblapack3 python3-dev libpython3-dev" \
    && apt-get -y update \
    && apt-get -y install $packages \
    || apt-get -y install $packages \
    || apt-get -y install $packages \
    || apt-get -y install $packages \
    || apt-get -y install $packages \
    || apt-get -y install $packages \
    || apt-get -y install $packages \
    || apt-get -y install $packages

# Build Dlib without MKL
RUN cd /tmp \
    && git clone https://github.com/davisking/dlib.git \
    && cd dlib \
    && mkdir build \
    && cd build \
    && cmake .. -DDLIB_USE_CUDA=0 -DUSE_AVX_INSTRUCTIONS=1 -DDLIB_USE_MKL_FFT=0 -DLIB_USE_MKL_FFT_STR=0 -DLIB_USE_BLAS=0 -DLIB_USE_LAPACK=0 \
    && cmake --build . \
    && cd .. \
    && python3 setup.py install --yes USE_AVX_INSTRUCTIONS --no DLIB_USE_CUDA --no DLIB_USE_MKL_FFT --no DLIB_USE_MKL_FFT_STR --no DLIB_USE_BLAS --no DLIB_USE_LAPACK \
    && cd / \
    && rm -rf /tmp/*dlib*

# We might consider installing pip, pip3, pip numpy here
# if it provides any performance/bug fixes

# OpenCV installation
# this says it can't find lots of stuff, but VideoCapture(0) and Python3 bindings work.
# IDK if LAPACK/BLAS/etc works, or gstreamer backend
# TODO: Where are the build logs?
# PYTHON_DEFAULT_EXECUTABLE
RUN cd /tmp \
    && git clone git://github.com/opencv/opencv \
    && git clone git://github.com/opencv/opencv_contrib \
    && cd opencv \
    && mkdir build \
    && cd build \
    && cmake -DCMAKE_BUILD_TYPE=RELEASE \
    -DCMAKE_INSTALL_PREFIX=/usr/local \
    -DINSTALL_C_EXAMPLES=OFF \
    -DINSTALL_PYTHON_EXAMPLES=OFF \
    -DOPENCV_EXTRA_MODULES_PATH=../../opencv_contrib/modules \
    -DBUILD_EXAMPLES=OFF \
    -DENABLE_VFPV3=ON \
    -DENABLE_NEON=ON \
    -DHARDFP=ON \
    -DWITH_CAROTENE=OFF \
    -DBUILD_NEW_PYTHON_SUPPORT=ON \
    -DWITH_FFMPEG=OFF \
    -DWITH_GSTREAMER=ON \
    -DWITH_CUDA=OFF \
    -DWITH_CUFFT=OFF \
    -DWITH_CUBLAS=OFF \
    -DWITH_LAPACK=ON \
    .. \
    && make -j`nproc` \
    && make install \
    && make package \
    && make clean \
    && cd / \
    && rm -rf /tmp/*opencv*

# Install Torch
RUN git clone https://github.com/torch/distro.git ~/torch --recursive \
    && cd ~/torch \
    && bash install-deps \
    && ./install.sh \
    && cd / \
    && source ~/.bashrc

# Install Torch dependencies
RUN for NAME in dpnn nn optim optnet csvigo cutorch cunn fblualib torchx tds; do luarocks install $NAME; done

# Install openface
RUN git clone https://github.com/cmusatyalab/openface.git \
    && cd openface/ \
    && sudo python3 setup.py install \
    && cd ./models \
    && ./get_models.sh \
    && cd / \

# Set our working directory
WORKDIR /usr/src/app

# Copy requirements.txt first for better cache on later pushes
COPY ./requirements.txt /requirements.txt

# pip install python deps from requirements.txt on the resin.io build server
RUN pip3 install -r /requirements.txt --upgrade

# This will copy all files in our root to the working  directory in the container
COPY . ./

# switch on systemd init system in container
ENV INITSYSTEM on

# main.py will run when container starts up on the device
CMD modprobe bcm2835-v4l2 && python3 main.py --port 80 --picamera 1