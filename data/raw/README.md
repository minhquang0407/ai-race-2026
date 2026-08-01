# Medical Knowledge Data

This directory contains local knowledge CSV files used by retrieval/candidate generation.

## Current sample files

- `icd10_sample.csv`: tiny ICD-10-like tree for tests only.
- `rxnorm_sample.csv`: tiny RxNorm dictionary for tests only.

These files are **not sufficient for final scoring**. They are intentionally small.

## Full data filenames

Recommended local filenames:

- `icd10_full.csv`
- `rxnorm_full.csv`

Run the pipeline with:

```powershell
python main.py --input-dir input --output-dir output_llm_fullkb --extractor llm --limit 10 --safe --icd-path data/raw/icd10_full.csv --rxnorm-path data/raw/rxnorm_full.csv
```

## ICD-10 CSV schema

Required columns:

```csv
code,name,parent_code,level,aliases
ROOT,ICD-10,,0,
A00-B99,Certain infectious and parasitic diseases,ROOT,1,"bệnh nhiễm trùng|bệnh ký sinh trùng"
A00-A09,Intestinal infectious diseases,A00-B99,2,"bệnh nhiễm trùng đường ruột"
A00,Cholera,A00-A09,3,"tả|bệnh tả"
```

Columns:

- `code`: ICD code or block code.
- `name`: canonical English or Vietnamese name.
- `parent_code`: parent node code. `ROOT` must have an empty parent.
- `level`: integer depth/level for metadata.
- `aliases`: optional `|`-separated aliases. Add Vietnamese disease names here.

The ICD graph must be a rooted directed tree/arborescence.

## RxNorm CSV schema

Required columns:

```csv
rxcui,name,tty,synonyms
1191,Aspirin,IN,"acetylsalicylic acid|aspirin"
2193,Ceftriaxone,IN,"ceftriaxone|ceftriaxon"
```

Columns:

- `rxcui`: RxNorm concept ID.
- `name`: canonical concept name.
- `tty`: RxNorm term type.
- `synonyms`: optional `|`-separated aliases.

## Licensing note

Do not commit restricted or large official datasets unless repository policy allows it. If needed, keep raw full data local and document how to obtain it.
