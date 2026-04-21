# LawMCP

MCP server for Polish legal databases — [SAOS](https://www.saos.org.pl/) (court judgments) and [ISAP/ELI](https://api.sejm.gov.pl/eli.html) (legal acts).

Exposes Polish law data as tools for LLMs via the [Model Context Protocol](https://modelcontextprotocol.io/).

## Tools

| Tool | Description |
|------|-------------|
| `search_judgments` | Search court judgments by text, date, court type, judgment type |
| `get_judgment` | Get full judgment details (text, judges, legal bases, references) |
| `search_legal_acts` | Search legal acts by title, keywords, publisher, type, date |
| `get_legal_act` | Get act metadata and references |
| `get_legal_act_text` | Get full text of a legal act (HTML→plaintext) |
| `get_legal_act_by_eli` | Look up act by ELI identifier (e.g. `DU/2024/1673`) |

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

### Claude Code

Add the server directly from the project directory:

```bash
claude mcp add law-mcp -- python -m law_mcp
```

Or with Docker:

```bash
claude mcp add law-mcp -- docker run --rm -i law-mcp
```

### MCP Inspector

Test and debug the server interactively with the [MCP Inspector](https://github.com/modelcontextprotocol/inspector):

```bash
mcp dev src/law_mcp/server.py
```

This opens a web UI where you can call each tool, inspect parameters, and see responses.

### Direct (stdio)

Run the server directly — it communicates via stdin/stdout using the MCP protocol:

```bash
law-mcp
```

Or:

```bash
python -m law_mcp
```

### Docker Compose

```bash
docker compose up -d
```

## Tool Details

### search_judgments

Search court judgments in the SAOS database.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | — | Full-text search query |
| `date_from` | string | — | Earliest date (`yyyy-MM-dd`) |
| `date_to` | string | — | Latest date (`yyyy-MM-dd`) |
| `court_type` | string | — | `COMMON`, `SUPREME`, `ADMINISTRATIVE`, `CONSTITUTIONAL_TRIBUNAL`, `NATIONAL_APPEAL_CHAMBER` |
| `judgment_type` | string | — | `SENTENCE`, `DECISION`, `RESOLUTION`, `REASONS` |
| `sort_by` | string | — | `JUDGMENT_DATE` or `DATABASE_ID` |
| `sort_dir` | string | — | `ASC` or `DESC` |
| `page_size` | int | 10 | Results per page (1–100) |
| `page_number` | int | 0 | Page number |

### get_judgment

Get full details of a single judgment by its SAOS ID (returned by `search_judgments`).

| Parameter | Type | Description |
|-----------|------|-------------|
| `judgment_id` | int | Numeric judgment ID |

### search_legal_acts

Search legal acts in the ISAP database.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `title` | string | — | Search in act titles |
| `keywords` | string | — | Comma-separated keywords |
| `publisher` | string | — | `DU` (Dziennik Ustaw) or `MP` (Monitor Polski) |
| `act_type` | string | — | `Ustawa`, `Rozporządzenie`, `Obwieszczenie`, `Uchwała` |
| `date_from` | string | — | Earliest date (`yyyy-MM-dd`) |
| `date_to` | string | — | Latest date (`yyyy-MM-dd`) |
| `limit` | int | 20 | Max results (1–500) |
| `offset` | int | 0 | Pagination offset |
| `sort` | string | — | Sort field (e.g. `date`, `-date` for descending) |

### get_legal_act

Get act metadata and references by publisher, year, and position.

| Parameter | Type | Description |
|-----------|------|-------------|
| `publisher` | string | `DU` or `MP` |
| `year` | int | Publication year |
| `position` | int | Position number |

### get_legal_act_text

Get the full text of a legal act as plain text. Long acts are truncated at 100,000 characters.

| Parameter | Type | Description |
|-----------|------|-------------|
| `publisher` | string | `DU` or `MP` |
| `year` | int | Publication year |
| `position` | int | Position number |

### get_legal_act_by_eli

Look up an act by its ELI identifier — parses the string and returns full details with references.

| Parameter | Type | Description |
|-----------|------|-------------|
| `eli` | string | ELI in format `PUBLISHER/YEAR/POSITION` (e.g. `DU/2024/1673`) |

## Development

```bash
pip install -e ".[dev]"
pytest -v
ruff check src/ tests/
```

## Data Sources

- **SAOS** — System Analizy Orzeczeń Sądowych ([API docs](https://www.saos.org.pl/help/index.php/dokumentacja-api))
- **ISAP/ELI** — Internetowy System Aktów Prawnych ([API docs](https://api.sejm.gov.pl/eli.html))

Both APIs are public and require no authentication.

## License

MIT
