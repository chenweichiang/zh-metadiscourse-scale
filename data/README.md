# data — study data for the accompanying article

Derived data for the corpus study that this scale comes from. The counts for the 201 machine
and translated texts can be regenerated from `data/machine_texts/` with `src/zhmd/`; the human
counts cannot, because the articles are not redistributed. How the sets are compared is spelled
out in `tests/readme_repro.py`.

| File | Contents |
|---|---|
| `marker_counts.csv` | Per-text marker counts, 385 texts × 10 markers, with set, model, prompt condition, sampling temperature and character count |
| `marker_definitions.csv` | The ten markers, their Hyland category and the regular expression used |
| `human_article_list.csv` | Bibliographic identifiers for the 184 human articles, by journal and issue |
| `machine_texts/` | The 201 generated and translated texts used in the study, as plain UTF-8 |

## Sets in `marker_counts.csv`

| Set | n | What it is |
|---|---|---|
| `human_2018_2022` | 122 | Articles published before ChatGPT was released; the baseline for the main analysis |
| `human_2024_2026` | 62 | Recent human articles, used as a contemporary reference point |
| `machine_local` | 48 | Three local open-weight models × two prompt conditions × eight titles, temperature 0.8 |
| `machine_commercial` | 64 | Four commercial models, 16 texts each |
| `temperature_variant` | 32 | gemma4:26b at temperatures 0.3 and 1.2, for the sensitivity check |
| `translation` | 57 | English text translated into Chinese by local models, in two batches: 15 paper paragraphs by gemma4 (`T_` files) and 42 arXiv cs.HC abstracts by gemma4-26b and gpt-oss-20b (`T2_` files). The `model` column is blank for this set |

## What is not here, and why

The human articles themselves are not redistributed. All 184 are openly downloadable from
the three publishing journals, and `human_article_list.csv` identifies each one, but the
articles are under the journals' copyright and are not ours to republish.

A batch of Gemini outputs was generated and then excluded from the study because the API
returned incomplete responses; those texts are not included here either.
