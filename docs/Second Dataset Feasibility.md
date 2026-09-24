# Second Dataset Feasibility

Status: desk assessment, 2026-09-25. **No dataset was downloaded or run.** The question is not whether a dataset is another Android malware corpus but whether it can support the same controlled family-exposure decomposition (hidden family at a client, peer-present, family-absent-everywhere control, full-exposure reference, own-domain evaluation, peer dose, primary and replication family sets, identity-safe split). Facts come from the dataset papers or official pages retrieved in this session; anything not stated there is marked "not stated" and treated as unknown, not as absent or present.

## 1. What the CTK design needs from a corpus

From the frozen protocol and the current implementation:

1. malware **family labels** with enough support: eligibility uses at least 150 peer fit rows and 50 federation test rows per hidden family, 15 own-domain test rows, and at least 20 target fit rows (`configs/data.yaml`, primary profile), inside a 60/20/20 identity-safe split, so a usable family needs on the order of a few hundred distinct (de-duplicated) samples, present at two or more clients;
2. **benign** samples at every client (the 5% FPR operating point is calibrated on benign calibration data);
3. a **defensible client/domain construction** (market, source, era) that gives real cross-client heterogeneity and lets the same families appear at several clients;
4. a **stable identity** (SHA-256, package) for identity-safe grouping and leakage control;
5. **static binary features** available or reproducible (the primary representation is 925 binary features);
6. enough families for **two disjoint family sets** (primary and replication);
7. tolerable licence and access, one workstation.

For contrast, the primary corpus (LAMDA, AndroZoo-derived) gives 1,008,381 rows, 1,380 families, four market/era clients, precomputed features, and per-sample hashes.

## 2. Candidate matrix

Verdicts: STRONG CANDIDATE, POSSIBLE, WEAK CANDIDATE, NOT SUITABLE, UNKNOWN / NEEDS ACCESS. Independence is judged against LAMDA, whose apps come from AndroZoo.

| Dataset | Family labels | Benign | Static features | Sample identity | Client/domain metadata | Family support | Cross-client family overlap | Own-domain feasible | Dose feasible | Full-exposure feasible | Leakage control feasible | Licensing/access | Estimated effort | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **KronoDroid** (Guerra-Manzanares et al., Comput. Secur. 2021) | yes: 240 (real device) / 209 (emulator); label source not stated | yes: 36,755 / 35,246 | yes: 200 static (permissions, intent filters, metadata) plus 289 syscalls, processed CSV public | not stated in the page (APKs by controlled access) | timestamps (four per sample), 2008–2020, no market field; source (AndroZoo/VirusShare) not stated | 41,382 malware / 240 families = about 172 per family on average; distribution not stated, likely long-tailed | unknown; families are era-specific, which may limit peers | possible if enough per-era support | possible where support is high | yes (pool) | only if a hash or package column exists in the CSV (not verified) | research use, cite the paper; APKs need researcher credentials | medium (new loader, era-based clients, family mapping, eligibility recompute) | UNKNOWN / NEEDS ACCESS (most promising on paper) |
| **CCCS-CIC-AndMal-2020** (CIC/CCCS) | yes: 191 families in 14 categories, per-family tables published | yes: 200,000 (drawn from AndroZoo, so overlaps LAMDA benign) | manifest-derived static features are **not precomputed**; about 146 dynamic features documented | not stated | none: no market, no time span stated | large in aggregate (200,000 malware; e.g. Riskware 97,349 across 21 families) | unknown; no client axis | infeasible without an artificial client construction | possible | yes | not verified | freely redistributable with citation; direct download | high (extract static features from APKs, invent clients) | WEAK CANDIDATE (support yes, client construction no) |
| **MH-1M** (Bragança et al., 2025) | **no real families**: four VT-derived superclasses (adware, trojan, riskware, other); families derivable only from raw VT reports | yes: 1,221,421 of 1,340,515 (91%) | yes: 22,810 static attributes precomputed (API calls, intents, opcodes, permissions), 45.6 GB | SHA-256 | AndroZoo submission year (2010–2024); no market column | 119,094 malware; family sizes not stated | unknown | possible by year | possible if families are re-derived | yes | SHA-256 only; repackaging not analysed | data on Figshare/GitHub, raw on Dataverse (over 400 GB); licence not stated | high | WEAK CANDIDATE (not independent: **AndroZoo-only**, overlaps LAMDA; families are not provided) |
| **McNdroid** (Kamol et al., 2026) | yes: AVClass2 families, 1,354 (same labelling method and same top families as LAMDA: dowgin, airpush, kuguo, smsreg, gappusin, revmob ...) | yes: about 535,000 | yes: 2,390 binary static (Drebin-style), plus 17,483 dynamic and 2,793 call-graph features, precomputed | SHA-256, strict de-duplication | AndroZoo submission year (2013–2025, 2015 excluded); no market | 323,500 malware; family-size distribution not stated | likely high (same source as LAMDA) | possible by year | possible | yes | SHA-256 only | Hugging Face + GitHub; licence not stated | medium | POSSIBLE **for a different purpose**: not independent (AndroZoo, same era and labelling as LAMDA), but a strong test of representation dependence (see section 4) |
| **AndroTruth** (Bai et al., 2025/26) | yes, **expert-report** labels, 187 families | **no** | yes: about 99 Drebin-style Androguard features per app (precomputed release not stated) | SHA-256 | VT first-submission date 2016–2025; source per report vendor; no market | 8,172 malware; only about 4 to 7 families have at least 250 samples, 91 have fewer than 10 | unknown | infeasible (too few clients with support) | no | partial | SHA-256 only | GitHub; licence and size not stated; from Koodous by hash (independence from AndroZoo not analysed) | high | NOT SUITABLE as a CTK replication corpus (no benign, too few supported families); useful only as a label-quality check |
| **AMD** (Wei et al., 2017) | yes: 71 families, 135 varieties | **no** (malware only) | not precomputed | not stated | none | 24,650 malware; distribution not stated | unknown | no | limited | partial | repackaging is documented in the literature (AndroMalPack reports about 30% repackaged) | access terms not verified here | medium | WEAK CANDIDATE (would need external benign, confounds source with label) |
| **Drebin** (Arp et al., 2014) | yes: 179 families | **no** (external benign sets used in the literature, e.g. Bi et al.) | not verified here | hashes (not verified) | none | 5,560 malware only | low | no | no | limited | AndroMalPack reports about half of Drebin apps are repackaged clones | access terms not verified here | low to medium | NOT SUITABLE (too small; malware only) |
| **MalGenome** | yes | no | n/a | n/a | none | about 1,200 (not verified here) | low | no | no | no | n/a | sharing discontinued (Wei et al.: authors stopped sharing as of 2015) | n/a | NOT SUITABLE |
| **CICMalDroid 2020** | **no**: five categories, not families | yes | 301 static + 263 dynamic | not stated | none | 17,341 apps | n/a | no | no | no | not stated | research download | n/a | NOT SUITABLE (no families) |
| **Maloid-DS** (Almomani et al., IEEE Access 2024) | yes: 345 families | not stated | not stated | not stated | not stated | 47,971 malware; not stated per family | unknown | unknown | unknown | unknown | unknown | not verified | unknown | UNKNOWN / NEEDS ACCESS (abstract only read) |
| **OmniDroid** (Martín et al., 2019) | not stated | yes | static and dynamic features | not stated | none stated | 22,000 samples | unknown | unknown | unknown | unknown | unknown | CC BY-NC-SA 4.0 | medium | UNKNOWN / NEEDS ACCESS |
| **Ciaramella et al. dataset** (IST 2025) | yes: 71 families in more than 40,000 apps | yes | images from bytecode in the paper | not stated | none stated | not stated | unknown | unknown | unknown | unknown | unknown | availability not stated | unknown | UNKNOWN / NEEDS ACCESS |
| **AndroZoo-derived corpora** (AndroZoo++, AndroVul, and similar) | via AVClass on VT reports | yes | reproducible from APKs | SHA-256 | AndroZoo `markets` and dates | large | high | yes | yes | yes | yes | AndroZoo terms | medium | **same source as LAMDA**: not an independent second dataset; at best an out-of-sample re-draw |

## 3. Can the CTK protocol be reused, per plausible candidate?

Plausible candidates after screening: KronoDroid (best on paper, unverified), CCCS-CIC-AndMal-2020 (support but no client axis), McNdroid and MH-1M (not independent; useful only for a representation or feature-extraction replication).

| Question | KronoDroid | CCCS-CIC-AndMal-2020 | McNdroid / MH-1M |
|---|---|---|---|
| 1. Same estimands unchanged? | yes, once clients exist | yes | yes |
| 2. Same family eligibility logic? | yes, but few families likely meet 150/50 support at two or more clients | yes for large families | yes |
| 3. Same 60/20/20 identity-safe split? | only if per-sample hash/package are available; not verified | not verified | SHA-256 available; package names in MH-1M |
| 4. Family-absent-everywhere control? | yes (data operation) | yes | yes |
| 5. Full exposure? | yes | yes | yes |
| 6. Own-domain evaluation defined? | needs hidden-family test support at each client | needs an invented client axis | yes by era |
| 7. Peer dose manipulable? | limited by per-family support | yes | yes |
| 8. Primary and replication family sets? | uncertain (about 172 samples per family on average) | probably | yes |
| 9. Client definitions defensible? | era windows are defensible but confound families with time | **no** (no market, time or source) | era windows only |
| 10. Design change so large it is a different study? | moderate: different features (200 static), era-based clients, unknown label provenance: a conceptual replication | large: clients would have to be invented | small, but it is then a re-analysis of largely the same apps, not an independent replication |

## 4. A cheaper, different check: representation replication on McNdroid

McNdroid provides the same style of AndroZoo apps (2013–2025) with three feature modalities (static 2,390 binary, dynamic 17,483, call-graph 2,793) and AVClass2 families that include the same top families (dowgin, airpush, kuguo, smsreg, gappusin, revmob, adwo ...). It is not an independent corpus: it very probably overlaps LAMDA in apps and shares its labelling method. Its value is different: it could test the exposure-versus-representation part of the story (whether families that stay poorly detected under full exposure with static features, such as hiddad and gappusin, are rescued by dynamic or graph features). That would inform N7 but does not address the external-validity limitation. Apps overlap with LAMDA was not measured and would have to be checked by SHA-256 before any use.

## 5. Verdict on a second independent Android dataset

**OPTIONAL, feasibility-gated. Not currently supported by verified public data; downgraded from the RECOMMENDED verdict of the previous round.**

- No public candidate examined meets all requirements. Large family-labelled corpora with benign samples that are truly independent of AndroZoo are rare in this search: CCCS-CIC-AndMal-2020 (malware from the Canadian Centre for Cyber Security, benign from AndroZoo) has support but no client, time or market axis; KronoDroid has benign, families and timestamps but average family support is small (about 172 samples per family) and its label provenance, source and per-family distribution are not stated on the pages read; AndroTruth has the best label quality but no benign samples and very thin family support; MH-1M and McNdroid are AndroZoo-derived and therefore overlap LAMDA; Drebin, AMD, MalGenome and CICMalDroid are too small, malware-only or lack families.
- The internal evidence is already broad (families, model classes, supports, operating points, salts, grouping, natural exposure, negative controls), so the marginal internal value is low, but a second corpus is the only check on corpus dependence.
- A bad second dataset (thin support, invented clients, source confounded with label) would be worse than a clean one-corpus study: it could produce a failed or noisy replication that reflects the client construction and not the phenomenon.
- **Gate before any commitment (no training needed):** for KronoDroid (and only if the processed CSV proves usable), tabulate family support per era-window client and the number of families with at least 250 de-duplicated samples present in at least two windows, and check for a hash or package column. Proceed only if at least about 14 families qualify (a pragmatic feasibility cut-off mirroring the current family-set size, not a scientific threshold) (7 primary plus 7 replication, matching the current family-set size) at three or more clients. If not, record "NOT FEASIBLE WITH CURRENT PUBLIC DATA" and keep the single-corpus scope with the external-validity limitation.

Estimated implementation difficulty if the gate passes: medium. New data loader and feature map; era-based client construction; family-label mapping and provenance check; recomputed eligibility; a new frozen protocol and fresh seed range; roughly the same compute as one confirmatory experiment family. Overall it is a conceptual replication rather than an exact one because clients, features and labelling differ.

## 6. Recommendation summary

| Item | Verdict |
|---|---|
| Independent second Android dataset | OPTIONAL, feasibility-gated (KronoDroid pre-check) |
| Best candidate | KronoDroid (unverified support), then CCCS-CIC-AndMal-2020 (no client axis) |
| Can it reproduce the same CTK decomposition unchanged? | Not established; estimands and gates are reusable, clients, features and labels are not |
| Representation replication on McNdroid | possible, cheap, informs N7 only, requires an overlap check |
| Datasets to drop | Drebin, AMD, MalGenome, CICMalDroid (too small, malware-only or no families); AndroTruth (no benign, thin support) |
| Datasets needing access before judgement | Maloid-DS, OmniDroid, Ciaramella et al. dataset |
