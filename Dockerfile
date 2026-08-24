FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y \
        build-essential \
        cmake \
        ninja-build \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install \
    --no-cache-dir \
    -r requirements.txt

COPY cpp ./cpp
COPY factory ./factory
COPY scenarios ./scenarios
COPY tests ./tests
COPY analysis ./analysis

RUN cmake \
    -S cpp \
    -B build \
    -G Ninja \
    -DCMAKE_BUILD_TYPE=Release

RUN cmake \
    --build build

RUN python \
    -m pytest \
    tests \
    -v

CMD ["python", "factory/run_factory.py", "--workers", "4", "--model-version", "v3", "--duration", "30", "--no-db"]