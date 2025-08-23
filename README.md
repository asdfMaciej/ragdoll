# ragdoll

simple CLI retriever for RAG applications (**WIP**)


## manifesto

so recently I've ordered a N100-based server to build a homelab 

as an Obsidian fan, I've wanted to use it for backuping my personal notes   
(and as a bonus, use the notes for a RAG-based personal assistant)

however, resources are scarce on this machine:   
I'll be stuck with an entry-level CPU with 16 GB RAM

this brought me to an idea:

1. most of the available RAG setups are resource-intensive  
   I don't want to waste my RAM on databases or MQs - or disk space on copies of data;
2. there's no need for a full RAG solution   
   tool calling only requires a retriever
3. modular tools are [cool](https://en.wikipedia.org/wiki/Unix_philosophy)  
4. I know how to do RAG well


## usage

early idea for the API

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

---

thanks @TypicalAM for the name
