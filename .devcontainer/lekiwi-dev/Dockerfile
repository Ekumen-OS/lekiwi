################################################################################
# Base Image
################################################################################

ARG BASE_IMAGE=jammy
FROM mcr.microsoft.com/devcontainers/base:${BASE_IMAGE}

################################################################################
# Configuration
################################################################################

ARG RUST_VERSION=1.88.0

################################################################################
# User 'dev'
################################################################################

ARG USERNAME=dev
ARG UID=1000
ARG GID=1000

RUN groupadd -o --gid ${GID} ${USERNAME}
RUN useradd -o --uid ${UID} --gid ${GID} -s "/bin/bash" -m ${USERNAME} && \
    apt-get install -y sudo && \
    echo "${USERNAME} ALL=NOPASSWD: ALL" > /etc/sudoers.d/${USERNAME} && \
    chmod 0440 /etc/sudoers.d/${USERNAME}

RUN usermod -a -G dialout $USERNAME

COPY .devcontainer/lekiwi-dev/dev.bashrc /home/${USERNAME}/.bashrc.d/dev.bashrc
RUN echo "source /home/${USERNAME}/.bashrc.d/dev.bashrc" >> /home/${USERNAME}/.bashrc

RUN mkdir -p /home/${USERNAME}/.local/share/bash-completion/completions/ && \
    chown -R ${USERNAME}:${USERNAME} /home/${USERNAME}/.local

################################################################################
# Tools & Utilities
################################################################################

RUN apt-get update && apt-get install -y --no-install-recommends \
    # development
    curl \
    bash \
    bash-completion \
    g++ \
    gcc \
    git \
    graphviz \
    make \
    pkg-config \
    ssh \
    wget \
    vim \
    less \
    zip \
    # python
    python3-dev \
    python3-pip \
    # linux
    libudev-dev \
    # cv2 deps
    ffmpeg libsm6 libxext6 \
    # gl deps
    mesa-utils libvulkan1 libvulkan-dev vulkan-tools libegl1 libgles2 \
    # Rerun specifically needs libxkbcommon-dev, libxkbcommon-x11-0
    libasound2-dev libudev-dev libx11-dev  libxinerama-dev libxkbcommon-dev libxkbcommon-x11-0 x11-apps x11-xserver-utils \
    && apt-get autoremove -y && apt-get clean -y && rm -rf /var/lib/apt/lists/*

RUN pip install \
  pre-commit==2.20.0

################################################################################
# Installs Rust toolchain for specified rust version (RUST_VERSION).
# Installs Rust autocompletion for bash.
################################################################################

ENV RUSTUP_HOME="/opt/rustup"
ENV CARGO_HOME="/opt/cargo"
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y  --default-toolchain ${RUST_VERSION} \
    && . "${CARGO_HOME}/env" \
    && rustup component add clippy \
    && rustup component add rustfmt \
    && cargo install cargo-deb \
    && cargo install cargo-expand \
    && cargo install cargo-rdme \
    && rustup target add x86_64-unknown-linux-gnu \
    && rustup completions bash cargo >> /home/${USERNAME}/.local/share/bash-completion/completions/cargo \
    && echo "export RUSTUP_HOME=${RUSTUP_HOME}" >> /etc/profile \
    && echo "export PATH=${CARGO_HOME}/bin:\${PATH}" >> /etc/profile
ENV PATH="$CARGO_HOME/bin/:$PATH"

# The previous command roots permissions in ${CARGO_HOME} and ${RUSTUP_HOME}.
# Establish wide permissions for user 'dev'. This step takes several minutes.

RUN find ${CARGO_HOME} -type d -exec chmod 777 {} + && \
    find ${CARGO_HOME} -type f -exec chmod a+rw {} + && \
    find ${RUSTUP_HOME} -type d -exec chmod 777 {} + && \
    find ${RUSTUP_HOME} -type f -exec chmod a+rw {} +

##############################################################################
# Final configuration
##############################################################################

# Update pip: Default pip version(22.) presents issues with
# installing packages without setupt.py file:
# See https://stackoverflow.com/questions/78034052/unknown-project-name-and-version-number-for-my-own-pip-package
RUN pip install --upgrade pip

# Install desired cargo bin crates
RUN cargo install \
    # Depending on binary crates doesn't allow you to use them from cli.
    # https://github.com/rust-lang/cargo/issues/2267
    dora-cli --version 0.3.13

# The previous commands roots permissions in ${CARGO_HOME} and ${RUSTUP_HOME}.
# Establish wide permissions for user 'dev'. This step takes several minutes.
RUN find ${CARGO_HOME} -type d -exec chmod 777 {} + && \
    find ${CARGO_HOME} -type f -exec chmod a+rw {} + && \
    find ${RUSTUP_HOME} -type d -exec chmod 777 {} + && \
    find ${RUSTUP_HOME} -type f -exec chmod a+rw {} +

USER ${USERNAME}

################################################################################
# Python dev install
################################################################################

# Install uv package manager: https://github.com/astral-sh/uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

################################################################################
# NVIDIA
################################################################################

ENV NVIDIA_VISIBLE_DEVICES ${NVIDIA_VISIBLE_DEVICES:-all}
ENV NVIDIA_DRIVER_CAPABILITIES ${NVIDIA_DRIVER_CAPABILITIES:+$NVIDIA_DRIVER_CAPABILITIES,}graphics,display,video,utility,compute

################################################################################
# Login Shell
################################################################################

ENV TERM xterm-256color
ENTRYPOINT ["/bin/bash", "--login", "-i"]
