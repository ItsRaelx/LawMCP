# LawMCP

MCP server for Polish and EU legal databases — [ISAP](https://api.sejm.gov.pl/eli.html) (legal acts), [SAOS](https://www.saos.org.pl/) (court judgments), [EUR-Lex](https://eur-lex.europa.eu/) (EU legislation & CJEU case law), and [Sejm API](https://api.sejm.gov.pl/sejm.html) (legislative process).

Exposes legal data as tools for LLMs via the [Model Context Protocol](https://modelcontextprotocol.io/).

## Tools

| Tool | Sources | Description |
|------|---------|-------------|
| `search_legislation` | ISAP + EUR-Lex | Search Polish and EU legislation in parallel. Only in-force acts by default. |
| `read_act` | ISAP | Read a Polish legal act — metadata, references, and full text in one call. |
| `search_case_law` | SAOS + CJEU | Search Polish and EU court judgments in parallel. |
| `read_judgment` | SAOS | Read a Polish court judgment by its SAOS ID. |
| `read_eu_document` | EUR-Lex | Read an EU document by its CELEX number. |
| `search_legislative_process` | Sejm API | Search legislative processes in the Polish parliament. |

## Installation

### From source

```bash
git clone https://github.com/ItsRaelx/LawMCP.git
cd LawMCP
pip install -e .
```

### With Docker

```bash
git clone https://github.com/ItsRaelx/LawMCP.git
cd LawMCP
docker build -t law-mcp .
```

## Usage

### Claude Desktop

Add to your Claude Desktop config file:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

**Using pip install:**

```json
{
  "mcpServers": {
    "law-mcp": {
      "command": "law-mcp"
    }
  }
}
```

**Using Docker:**

```json
{
  "mcpServers": {
    "law-mcp": {
      "command": "docker",
      "args": ["run", "--rm", "-i", "law-mcp"]
    }
  }
}
```

### Remote (Streamable HTTP)

Run the server with HTTP transport for remote access:

```bash
law-mcp --transport streamable-http --port 8000
```

Connect via `http://host:8000/mcp`. Set `LAWMCP_ALLOWED_HOSTS` environment variable to restrict allowed Host headers (e.g. `LAWMCP_ALLOWED_HOSTS=lawmcp.example.com`).

### Claude Code

```bash
claude mcp add law-mcp -- python -m law_mcp
```

Or with Docker:

```bash
claude mcp add law-mcp -- docker run --rm -i law-mcp
```

### MCP Inspector

```bash
mcp dev src/law_mcp/server.py
```

### Docker Compose

```bash
docker compose up -d
```

## Tool Details

### search_legislation

Search legislation across Polish (ISAP) and EU (EUR-Lex) databases in parallel. By default only returns acts currently in force.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | — | Full-text search query |
| `title` | string | — | Search in Polish act titles (ISAP-specific) |
| `keywords` | string | — | Comma-separated keywords (ISAP-specific) |
| `date_from` | string | — | Earliest date (`yyyy-MM-dd`) |
| `date_to` | string | — | Latest date (`yyyy-MM-dd`) |
| `source` | string | — | `PL` (Polish only), `EU` (EU only), or omit for both |
| `in_force` | bool | true | Only return acts currently in force |
| `limit` | int | 10 | Max results per source |

### read_act

Read a Polish legal act — returns metadata, references, and full text in one call. Accepts either an ELI identifier or publisher+year+position.

| Parameter | Type | Description |
|-----------|------|-------------|
| `eli` | string | ELI identifier, e.g. `DU/2024/1673` |
| `publisher` | string | `DU` (Dziennik Ustaw) or `MP` (Monitor Polski) |
| `year` | int | Publication year |
| `position` | int | Position number in the journal |

### search_case_law

Search case law across Polish courts (SAOS) and EU Court of Justice (CJEU) in parallel.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | — | Full-text search query |
| `date_from` | string | — | Earliest judgment date (`yyyy-MM-dd`) |
| `date_to` | string | — | Latest judgment date (`yyyy-MM-dd`) |
| `court_type` | string | — | Polish court filter: `COMMON`, `SUPREME`, `ADMINISTRATIVE`, `CONSTITUTIONAL_TRIBUNAL`, `NATIONAL_APPEAL_CHAMBER` |
| `source` | string | — | `PL` (Polish only), `EU` (EU only), or omit for both |
| `limit` | int | 10 | Max results per source |

### read_judgment

Read a Polish court judgment by its SAOS ID. Returns the full text, judges, legal bases, and referenced regulations.

| Parameter | Type | Description |
|-----------|------|-------------|
| `judgment_id` | int | Numeric judgment ID from SAOS |

### read_eu_document

Read an EU legal document by its CELEX number from EUR-Lex. Works for regulations, directives, decisions, and CJEU judgments.

| Parameter | Type | Description |
|-----------|------|-------------|
| `celex` | string | CELEX identifier, e.g. `32016R0679` (GDPR) or `62014CJ0362` (Schrems) |

### search_legislative_process

Search legislative processes in the Polish Sejm (parliament).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `title` | string | — | Search in process titles |
| `date_from` | string | — | Earliest date (`yyyy-MM-dd`) |
| `date_to` | string | — | Latest date (`yyyy-MM-dd`) |
| `term` | int | 10 | Sejm term number (current: 10) |
| `limit` | int | 20 | Max results |

## Data Sources

| Source | Type | API |
|--------|------|-----|
| [ISAP/ELI](https://api.sejm.gov.pl/eli.html) | Polish legal acts (Dziennik Ustaw, Monitor Polski) | REST/JSON |
| [SAOS](https://www.saos.org.pl/help/index.php/dokumentacja-api) | Polish court judgments (500k+ records) | REST/JSON |
| [EUR-Lex CELLAR](https://op.europa.eu/en/web/cellar) | EU legislation and CJEU case law | SPARQL |
| [Sejm API](https://api.sejm.gov.pl/sejm.html) | Polish legislative process | REST/JSON |

All APIs are public and require no authentication.

## Future Integrations

The following commercial legal information systems could be integrated with API keys:

- **LEX (Wolters Kluwer)** — commentaries, glosses, consolidated texts with annotations
- **Legalis (C.H. Beck)** — legal commentaries, journal articles, case law annotations

These require commercial subscriptions and are not currently supported.

## Development

```bash
pip install -e ".[dev]"
pytest -v
ruff check src/ tests/
```

## License

MIT
