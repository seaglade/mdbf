FROM python:3.13-alpine AS base

WORKDIR /app

FROM base AS builder

# Set environment vars for UV
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Mount uv + project config and generate a virtual environment
RUN --mount=from=ghcr.io/astral-sh/uv,source=/uv,target=/bin/uv \
    --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --compile-bytecode --no-install-project --no-dev --no-editable

FROM base AS runtime

# Set environment vars for Python
ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1 \
    USER=runner \
    UID=1000 \
    GROUP=runner \
    GID=1000

RUN addgroup -g $GID -S $GROUP \
    && adduser -u $UID -G $GROUP -D $USER

# Copy the virtual environment from the previous step
# and the bot's source code from the project
COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}
COPY main.py ./
COPY cogs ./cogs/

# Run the bot
USER $USER
ENTRYPOINT ["python", "main.py"]
