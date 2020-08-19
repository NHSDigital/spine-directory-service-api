FROM rodolpheche/wiremock

COPY stubs /home/wiremock

CMD ["java", "-cp", "/var/wiremock/lib/*:/var/wiremock/extensions/*", "com.github.tomakehurst.wiremock.standalone.WireMockServerRunner", "--port", "9000"]
