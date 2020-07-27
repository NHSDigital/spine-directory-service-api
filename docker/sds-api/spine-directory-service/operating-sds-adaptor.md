# Operating the SDS Adaptor

This following is a guide to operational considerations where the SDS Adaptor is deployed within your infrastructure

## Log consumption
The SDS Adaptor emit logs and audit records on standard I/O streams which are captured by the Docker containers they are hosted within. 
Whichever Docker container orchestration technology is used, these log streams can be captured and/or forwarded to an appropriate log indexing 
service for consumption, storage and subsequent query.

### Audit consumption
Audit logs are emitted through the same channel as other log messages, via the standard I/O streams captured and forwarded by Docker. Audit log messages have a log level of AUDIT which is used to differentiate them from other logs. Due to the potential sensitivity of the data held in AUDIT logs and the need to ensure that AUDIT logs have stronger controls around them to prevent the possibility of tampering, it is strongly advised that the log indexing tooling chosen should be configured to filter AUDIT logs out of the main log bucket and divert them into their own audit log bucket, which can be stored and controlled separately.

## Log Format

Log messages produced by the SDS Adaptor are in human readable form and important data is included within the log message as pipe-separated fields so that they can be parsed 
and used for searching, filtering, agregation, graphing etc. Few first logs don't follow the pattern as they are written before logger initialization. 
Those are minor read-config logs.

Pattern: 
<!-- TODO correct log pattern as it should be different for SDS-->
```text
[%(asctime)sZ] | %(levelname)s | %(process)d | %(interaction_id)s | %(message_id)s | %(correlation_id)s | %(inbound_message_id)s | %(name)s | %(message)s
```
Example:
```text
2020-03-26T10:31:52.118165Z | AUDIT | 40186 | QUPC_IN160101UK05 | 4DE4BBB7-F1DE-48BD-8824-E8FFCE4FC703 | 1 |  | outbound.mhs_common.workflow.asynchronous_express | WorkflowName=async-express outbound workflow invoked.
```

- The start of the log line included a datetime-stamp in ISO8601 timestamp format and always in UTC timezone.
- The end of the log line contains log message

<!-- TODO check log fields -->
| Common Key | Purpose |
| ---------- |:------- |
| `Time` | Datetime-stamp in ISO8601 timestamp format and always in UTC timezone. |
| `LogLevel` | The level at which the log line was raised. |
| `pid` | Process ID, identifies the running instance of a component that produced the log message. |
| `InteractionId` | ID of interaction that you want to invoke. Each interaction has an associated workflow (sync, async express, async reliable and forward reliable)) and a corresponding syn-async flag.
| `MessageId` | A unique ID which is generated at the very start of a workflow if not already assigned. |
| `CorrelationId` | A unique ID which is generated at the very start of a workflow and is used throughout all log messages related to that work, such that all the logs in the chain can be tied together for a single work item. CorrelationId can be passed into the SDS components from the supplier's calling client to allow for the CorrelationId to also tie the workflow together with the client system. |
| `RefToMessageId` | A unique ID which is generated at the very start of a workflow as the MessageID if not already assigned. When a message is returned from spine originating from outbound, this UUID will be assigned as the RefToMessageId in spine. Incoming inbound messages will have a new MessageId, and RefToMessageId that refer to original message_id of outbound message. Used to find if message id exists in state database to determine if message is unsolicited or not. |
| `LoggerName` | Identifies the sub-component within the solution which produced the logs.  It's a dot-separated name where the first part is the component that produced the log. |
| `Log Message` | Information that is logged. |

## Log Level
The logs produced by the SDS Adaptor application components have one of the following log levels, the following table describes the semantics of each log level:

| Log Level | Description |
| --------- | ----------- |
| `DEBUG` | Low level debug information of data processing. <br/><br/> **The third party libraries used by the SDS Adaptor will likely emit logs at DEBUG if this level is configured on, however suppliers should be aware that DEBUG level logs from components involved in I/O are highly likely to include the entire message payload which in the context of the SDS Adaptor is likely to contain Patient Identifying Information and other sensitive data. As such it is strongly recommended that DEBUG log level never be configured on in Production environments, to ensure that real patient data does not leak into log files.** |
| `INFO` | General information messages and confirmation that things are working as expected. Allows for tracking of work following through the system, points-of-interest, and where uncommon logical flows have been invoked. |
| `AUDIT` | Specific logging of auditable events in the business process. See section below for further coverage of Audit logs. |
| `WARNING` | Indication that something unexpected has happened but is being handled, such as processing of an invalid message, invocation of error handling logic which is not expected to be executed through the specified processing. It can also be used to raise a warning about a potential future problem, such as levels or disk space or memory reaching a threshold. When using WARNING, the software is still working as expected, higher log levels are used when this is not the case. |
| `ERROR` | Due to a more serious and unhandlable error, the software has not been able to perform some function. This may result in a request erroring or an item of work being unable to be processed further without further intervention and remediation. <br/><br/> The application should be able to recover from an ERROR scenario using its error handling logic and continue normal operations, processing other requests/messages without deterioration, if it cannot then a higher log level will be used.|
| `CRITICAL` | Indicates a problem, which may still be handled by error handling logic, but which is likely to compromise the on-going operation of the component. This is also used where error handling logic has failed and final logs are being produced before the process/service dies. |

The SDS Adaptor components have specifically chosen INFO as the lowest log level, rather than DEBUG. The principle here is that all information logged is potentially useful for diagnosing live issues, and so should be available in Production. It is not recommended to enable DEBUG level logging in production, so it is important that the lowest level of logs emitted from the SDS Adaptor components to facilitate diagnostics is INFO.

### Audit Messages

Every request which passes through the SDS Adaptor produces an audit log message. Following is an example of the format:

<!-- TODO add proper SDS example -->
```text
20-03-26T10:31:52.500735Z | AUDIT | 40186 | QUPC_IN160101UK05 | 4DE4BBB7-F1DE-48BD-8824-E8FFCE4FC703 | 1 |  | outbound.mhs_common.workflow.common_asynchronous | WorkflowName=async-express outbound workflow invoked. Message sent to Spine and Acknowledgment=MessageStatus.OUTBOUND_MESSAGE_ACKD received.
```
Audit messages are produced with the log level of AUDIT.

`Acknowledgement` indicates the status of the ACK response received from Spine.

`RequestSentTime` is the time the outgoing message was sent to Spine by the MHS Adaptor.

`AcknowledgementReceivedTime` is the time the ACK response was received from Spine by the MHS Adaptor.

See above for details of `Time`, `LogLevel`, `pid`, `InteractionId`, `MessageId`, `CorrelationID`, `RefToMessageId`, `Loggername` and `Log Message`.

### Cloud Watch

<!-- TODO change to Azure once it's working -->
See below example to write CloudWatch queries to parse logs and search for a given correlation id and filter out healthchecks. 

<!-- TODO check pattern once we have SDS running in Azure -->
 `parse '* | * | * | * | * | * | * | * | *' as timestamp, level, correlation_id, message_id, interaction_id, inbound_message_id, process, name, text `<br>
 `| display timestamp, level, correlation_id, name, text, message_id`<br>
 `| filter text not like 'healthcheck'`<br>
 `| filter correlation_id = '7'`<br>
 `| filter level = 'INFO'`<br>
 `| limit 10`<br>
 
 Parse query in Cloud Watch add `*` for each value wanted such as timestamp, correlation id etc. Multiple values selected are separated by `|`.
 
 Display selected values columns by using keyword `display` and selecting values such as `timestamp`.
 
 Filter search by given value, use keyword `filter` select a value `correlation_id`, choose an operator `=` and add correlation id value wanted `7`.
 
 Limit number of results return using keyword `limit` and the number of results needed, in this example `10`.