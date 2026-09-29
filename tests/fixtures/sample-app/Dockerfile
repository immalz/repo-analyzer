FROM --platform=linux/amd64 eclipse-temurin:21-jre AS runtime
ENV DB_PASSWORD=supersecret APP_MODE=prod
COPY certs/truststore.jks /app/truststore.jks
RUN keytool -importcert -file /tmp/ca.crt -keystore /app/truststore.jks
USER root
EXPOSE 8080
VOLUME /data
HEALTHCHECK CMD curl -f http://localhost:8080/actuator/health || exit 1
ENTRYPOINT ["java", "-javaagent:/opt/applicationinsights-agent.jar", "-jar", "/app/app.jar"]
