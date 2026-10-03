FROM golang:1.24-alpine AS build
WORKDIR /src
COPY go.mod *.go index.html ./
ARG VERSION=dev
RUN CGO_ENABLED=0 go build -trimpath -ldflags "-s -w -X main.version=${VERSION}" -o /ghostfile .

FROM scratch
COPY --from=build /ghostfile /ghostfile
# Uploads land in /src; mount a host directory there.
WORKDIR /src
EXPOSE 5000
ENTRYPOINT ["/ghostfile"]
