# data — study data for the accompanying article

Derived data for the corpus study that this scale comes from. Everything here can be
regenerated from the scripts in `src/zhmd/`.

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
| `translation` | 57 | English articles translated into Chinese by the same local models |

## What is not here, and why

The human articles themselves are not redistributed. All 184 are openly downloadable from
the three publishing journals, and `human_article_list.csv` identifies each one, but the
articles are under the journals' copyright and are not ours to republish.

A batch of Gemini outputs was generated and then excluded from the study because the API
returned incomplete responses; those texts are not included here either.
