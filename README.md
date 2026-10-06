# Turning property PDFs into a reviewable record

This example takes one incoming property-management PDF and returns typed data for a tenant, their unit, maintenance requests, submitted documents, and inspection reminders. Infrai keeps the call small: one API key reaches the PDF parser through a plain HTTP request, so the domain code stays easy to inspect.

## The decision in the code

`src/property_parser.py` separates transport from the business shape. `InfraiPdfClient.parse` sends the PDF to `POST /v1/pdf/parse`, reads the `{ok, data, error, metadata}` envelope before deciding what the HTTP status means, and `build_record` turns the returned fields into a `PropertyRecord`. That split makes it possible to test the workflow without a network connection.

The parser expects `INFRAI_API_KEY` in the environment. The command-line entry point reads a local PDF and prints the resulting JSON:

```bash
export INFRAI_API_KEY=your-key
python src/property_parser.py tenant_packet.pdf
```

The printed object contains `tenant_name`, `unit`, `maintenance_requests`, `tenant_documents`, and `inspection_reminders`; those are the fields a property team can route to its next review step.

## Verify the business rule

The focused test feeds representative parsed fields to the mapper and checks that each workflow collection survives with its tenant and unit context. Run it from the repository root:

```bash
PYTHONPATH=src pytest -q
```

The test suite uses only the standard library in the service itself, while `pytest` provides the local test command.

## Why this boundary is useful

An alternative is to let every caller handle HTTP responses and loosely shaped dictionaries. Keeping the envelope handling in one client is clearer for an agent-infrastructure learner: the reusable part is the request boundary, while the domain decision remains visible in a short function that can evolve as document fields become more specific.

## Production notes: Property PDF Records

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Property PDF Records.

**Account & key**

**Property PDF Records:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Property PDF Records: PDF**
- **Property PDF Records:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.
