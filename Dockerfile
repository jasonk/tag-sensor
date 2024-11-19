FROM debian:bookworm

SHELL ["sh", "-exc"]

ENV \
  UV_LINK_MODE=copy \
  UV_COMPILE_BYTECODE=1 \
  UV_PROJECT_ENVIRONMENT=/app \
  PYTHONUNBUFFERED=1 \
  DEBIAN_FRONTEND=noninteractive \
  DEBCONF_NOWARNINGS=yes
  # UV_PYTHON=python${PYTHON_VERSION} \
  # UV_PYTHON_DOWNLOADS=never \
  # SETUPTOOLS_USE_DISTUTILS=local

# We put the lockfiles into a directory different from everything
# else because we don't want them to get copied into the runtime
COPY pyproject.toml uv.lock .python-version /_lock/

RUN <<END
apt-get update -qy
apt-get install -qyy --no-install-recommends --no-install-suggests \
  build-essential \
  ca-certificates \
  dumb-init
END
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
RUN uv venv --relocatable --link-mode copy /app


#RUN --mount=type=cache,target=/root/.cache/uv \
#    --mount=type=bind,source=uv.lock,target=uv.lock \
#    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
#    uv sync --frozen --no-install-project --no-dev

# Synchronize only the DEPENDENCIES, not the application. This way
# this layer can be cached longer.
RUN cd /_lock && uv sync --frozen --no-dev --no-install-project

# Then we install the application separately without the dependencies.
COPY . /src
RUN cd /src && uv sync --frozen --no-dev --no-editable

ENV PATH=/app/bin:$PATH

RUN useradd app --home=/app --user-group

COPY entrypoint.sh /
ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD ["/entrypoint.sh"]

#USER app
WORKDIR /app

ARG BUILD_ARCH
ARG BUILD_DATE
ARG BUILD_REF
ARG BUILD_VERSION

LABEL \
  io.hass.name="tag_sensor" \
  io.hass.type="addon" \
  io.hass.description="Create sensors that detect physical tags." \
  io.hass.arch="${BUILD_ARCH}" \
  io.hass.version="${BUILD_VERSION}" \
  maintainer="Jason Kohles <email@jasonkohles.com>" \
  org.opencontainers.image.authors="Jason Kohles <email@jasonkohles.com>" \
  org.opencontainers.image.url="https://github.com/jasonk/homeassistant-addons" \
  org.opencontainers.image.source="https://github.com/jasonk/tag-sensor" \
  org.opencontainers.image.documentation="https://github.com/jasonk/tag-sensor/blob/main/README.md" \
  org.opencontainers.image.licenses="MIT" \
  org.opencontainers.image.title="Home Assistant Add-on: Tag Sensor" \
  org.opencontainers.image.description="Create sensors that detect physical tags." \
  org.opencontainers.image.created="${BUILD_DATE}" \
  org.opencontainers.image.revision="${BUILD_REF}" \
  org.opencontainers.image.version="${BUILD_VERSION}"
