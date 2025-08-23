# ragdoll

simple CLI retriever for RAG applications 

**Note:** WIP - it doesn't work yet


## manifesto

recently I've ordered a N100-based server to build a homelab 

as a note-taking enthusiast, I want to use the server for a RAG-based personal assistant

however, resources are scarce on this machine:   
I'll be stuck with an entry-level CPU and 16 GB RAM


- most of the available RAG setups are resource-intensive  
I don't want to run DB/MQ services for this

- there's also no need for a full RAG solution   
   tool calling only requires a retriever
- [modular tools are cool](https://en.wikipedia.org/wiki/Unix_philosophy)  
- I know how to do RAG well

introduce: ragdoll


## install

currently only available in dev mode via `uv` - clone the repo and run:

```
uv run ragdoll --help
```

## use

index, retrieve and manage your files via commands

### add a file

```bash
ragdoll add "path/to/file.md" --metadata='{"id": "x-y-z"}'
```

### index your files

```bash
ragdoll index --limit=20  # up to 20 files
ragdoll index --refresh   # run as a worker
```

### list your files

```bash
ragdoll list
```

```json
{
	"files": [{
		"id": "uuidv7",
		"path": "path/to/file.md",
		"indexed_at": null,
		"content_hash": "hash",
		"metadata": {"id": "x-y-z"}
	}],
	"pagination": {
		"page": 1, "per_page": 20, "page_count": 1, "total_count": 1
	}	
}
```

### retrieve

```bash
ragdoll search "what's ragdoll?" --limit=1
```

```json
{
	"results": [
	{
		"id": "uuidv7",
		"path": "path/to/file.md",
		"indexed_at": null,
		"content_hash": "hash",
		"metadata": {"id": "x-y-z"},
		"score": 0.93214
	}
	],
	"pagination": null
}
```

### remove your files

```bash
ragdoll delete "path/to/file.md"
```

## license

ragdoll is licensed under the Apache-2.0 License.

---


shoutout @TypicalAM for the cool name
