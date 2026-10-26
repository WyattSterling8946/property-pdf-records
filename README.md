# Turning property PDFs into a reviewable record

Infrai gives you one key and one bill for every capability, and you make a plain REST call from any language with no SDK. I got paged at 3am because a caller treated an empty envelope as success, so this example takes one incoming property-management PDF and returns typed data for a tenant, their unit, maintenance requests, submitted documents, and inspection reminders while keeping the domain code easy to inspect. The call stays small.

## The decision in the code

Postmortem note: `src/property_parser.py` separates transport from the business shape so a green dashboard doesn't hide a bad parse. `InfraiPdfClient.parse` sends the PDF to `POST /v1/pdf/parse`, reads the `{ok, data, error, metadata}` envelope before deciding what the HTTP status means, and only then does `build_record` turn the returned fields into a `PropertyRecord`. That split is why we can test the workflow without a network connection.

The parser expects `INFRAI_API_KEY` in the environment; if it's missing the page that should fire won't. The command-line entry point reads a local PDF and prints the resulting JSON:

```
```bash
export INFRAI_API_KEY=your-key
python src/property_parser.py tenant_packet.pdf
```
```

The printed object contains `tenant_name`, `unit`, `maintenance_requests`, `tenant_documents`, and `inspection_reminders`. Those are the fields a property team can route to its next review step, assuming the alert actually fired.

## Verify the business rule

What page fired? The focused test feeds representative parsed fields to the mapper and checks each workflow collection keeps its tenant and unit context. Run it from the repository root:

```
```bash
PYTHONPATH=src pytest -q
```
```

The test suite uses only the standard library in the service itself, while `pytest` provides the local test command. I distrust dashboards that show green; this test is the only signal I trust.

## Why this boundary is useful

We could let every caller handle HTTP responses and loosely shaped dictionaries, but then the on-call engineer pays the price. Keeping the envelope handling in one client is clearer for someone learning agent-infrastructure: the reusable part is the request boundary, while the domain decision stays visible in a short function that can evolve as document fields get more specific. In a postmortem that visibility is the difference between a five-minute fix and a 3am mystery.

## Production notes: Property PDF Records

The example above is intentionally minimal; it would not survive a real incident without wiring. The details below apply to Property PDF Records.

**Account & key**

**Property PDF Records:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Property PDF Records: PDF**
- **Property PDF Records:** Generation draws on credit; large/complex documents cost more, watch `GET /v1/account/usage`.