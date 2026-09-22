# Data licensing, consent, and privacy framework

Status: project data-governance baseline for issue #26, researched 2026-09-22.

This document is an engineering and research decision framework. It is not a
claim that a particular use is lawful in every jurisdiction and it is not a
substitute for legal advice. When rights, terms, consent, or privacy status are
unclear, the project treats the source as unavailable until the ambiguity is
resolved.

## Decision summary

The project uses a deny-by-default data policy.

A dataset or asset may enter collection, training, evaluation, publication, or
redistribution only when its manifest records:

- the exact source and version;
- the person or entity that supplied it;
- the relevant copyright or database right holder where known;
- the license, terms, consent record, or other permission relied upon;
- the intended uses, including training, evaluation, publication, and
  redistribution separately;
- whether human personal data, chat, identifiers, voice, video, or other
  potentially identifying information is present;
- retention and deletion rules;
- transformation and derived-artifact lineage;
- unresolved rights or privacy questions; and
- the review decision and reviewer/date.

Public availability, technical downloadability, or an open-source code license
does not by itself establish permission to train on or redistribute the
associated data.

The preferred source for behavioural data is project-collected native telemetry
from consenting participants under a purpose-specific collection protocol.
Synthetic and agent-only trajectories are preferred where human data is not
needed.

## Governing principles

### Separate every rights layer

A single artifact can carry several independent rights and terms.

For example, a Minecraft gameplay video can involve:

- Mojang/Microsoft rights in Minecraft assets;
- the player's copyright or other rights in their recording or creative work;
- music, voice, skins, resource packs, builds, or other third-party material;
- a hosting platform's contract and API/access terms; and
- personal-data obligations if a person is identifiable.

The project does not collapse these into one generic "dataset license".

### Separate use permissions

The manifest records these permissions independently:

- acquire or collect;
- store;
- internally inspect;
- train or fine-tune;
- evaluate;
- create derived labels/features;
- publish examples;
- redistribute raw data;
- redistribute transformed data;
- redistribute model weights or adapters trained on the data.

A permission for one purpose must not be silently reused for another.

### Prefer minimisation over later redaction

Collect only what is needed for the declared research question. Native
observations and actions are preferred to screen, microphone, desktop, account,
or unrelated device capture.

Human chat is excluded by default. It is collected only when the research
question requires language data and the participant has separately opted in.

### Pseudonymisation is not anonymisation

Replacing a username with a participant ID reduces risk but does not by itself
make the data anonymous. Re-identification mappings, timing, distinctive builds,
chat, skins, server logs, and trajectory content can still identify a person.

### Consent is granular and versioned

Where this project chooses consent as its collection basis, consent is recorded
for the specific dataset version and purposes. Participation in a Minecraft
server is not treated as blanket consent for model training or publication.

### Do not promise impossible deletion

The project must not promise that withdrawing one sample can be removed from an
already trained checkpoint unless a tested unlearning or retraining process can
actually deliver that result.

Consent and dataset documentation must distinguish deletion of:

- raw source data;
- normalized telemetry;
- derived labels/features;
- caches and backups;
- published artifacts; and
- trained model parameters.

## Source decision matrix

| Source | Rights/terms to record | Intended project use | Training status | Redistribution status | Unresolved questions / required review |
| --- | --- | --- | --- | --- | --- |
| Agent-only or synthetic native telemetry generated in project-owned worlds | Minecraft EULA/Usage Guidelines, project code/data license, world provenance | Interface testing, evaluation, pretraining where useful | **Preferred** when no human data is required | Conditional; avoid bundling Minecraft game assets or third-party world content | Confirm each exported field does not reproduce restricted game assets beyond the permitted research artifact |
| Project-collected human native gameplay telemetry | Participant consent/collection agreement, privacy notice, Minecraft policies, server/world provenance | Behavioural cloning, evaluation, interface research | **Preferred human-data path** after approved protocol | Only within the participant's explicit release scope and after de-identification review | Jurisdiction, age eligibility, third-party content in world/session, withdrawal handling |
| Human chat or text communication | Separate opt-in, privacy notice, participant identity mapping, server terms | Language grounding research only when necessary | **Off by default**; purpose-specific opt-in required | Normally no raw public redistribution | Free text may reveal sensitive information about the speaker or third parties; redaction cannot be assumed complete |
| Voice/audio from players | Separate explicit opt-in plus rights for all speakers/audio content | Not required for the current baseline | **Blocked by default** | Blocked | Biometric/voice, bystanders, music, transcription, age and special-category risks require dedicated review |
| Project-owned or contributor-created worlds | Contributor license/permission, asset/mod/resource-pack manifest, Minecraft policies | Evaluation, demonstrations, reproducible scenarios | Conditional | Conditional on every bundled component | A world may contain third-party builds, textures, datapacks, mods, books, signs, or other content not owned by the submitter |
| Publicly downloaded community worlds/maps | Site terms, creator license, included asset licenses, Minecraft policies | Possible comparison/evaluation fixtures | **Blocked until artifact-specific review** | Blocked unless an explicit compatible license covers redistribution | Public download is not proof of training or redistribution rights |
| Project-created skins | Author assignment/license plus Minecraft policies and asset provenance | Persistent agent identity | **Preferred skin source** | Allowed only under recorded license | Avoid official/third-party branded artwork unless separately cleared |
| Third-party or "popular" community skins | Creator license, source terms, provenance, Minecraft policies | Candidate curated skin catalog | **Blocked until each skin has an explicit redistributable license/permission** | Blocked without explicit redistribution permission | A skin being visible/downloadable from a profile or skin site does not establish reusable rights |
| OpenAI VPT contractor demonstrations | OpenAI repository/version, contractor-data release page, Minecraft policies, any data-specific terms | Pixel/low-level imitation comparison, transfer experiments | **Review required** | Raw redistribution blocked pending data-specific rights confirmation | The repository's MIT license expressly covers software/documentation; the README releases contractor data and demonstrates fine-tuning, but this review did not find a separate data license that safely answers every downstream use |
| OpenAI VPT internet-video corpus or arbitrary public Minecraft videos | Individual creator rights, platform terms, Minecraft policies | Historical research reference only | **Blocked for project ingestion by default** | Blocked | YouTube API policy restricts downloading/storing audiovisual content without approval; creator permission and platform access terms are separate requirements |
| MineRL 2019 demonstration datasets | Exact dataset/version record, MineRL repository license, Zenodo record, participant collection terms if available, Minecraft policies | Historical imitation/evaluation comparison | **Review required before use** | Blocked until exact dataset rights are resolved | The current MineRL repository root license is CC BY-NC-SA 4.0 while package metadata/history may differ; the linked Zenodo backup exposes the files but its visible Rights field did not state a license during this review |
| MineDojo code | MineDojo repository MIT license and dependency licenses | Research reference/prototyping only; not the core architecture | Allowed subject to dependency review | Per MIT/dependencies | Minecraft/runtime dependencies have their own terms |
| MineDojo YouTube database layer | MineDojo README states CC BY 4.0 for the YouTube database; underlying creator/platform rights remain separate | Metadata/research-reference experiments | Metadata only after review | Database layer only, with attribution, if the exact artifact is covered | CC BY on the database must not be treated as a license to copy underlying YouTube audiovisual content |
| MineDojo Wiki database layer | MineDojo README states CC BY-NC-SA 3.0 | Research reference only | Not in default training set | Subject to NC/SA and attribution requirements | Non-commercial/share-alike obligations and underlying source content make release/training compatibility a dedicated review item |
| MineDojo Reddit database layer or newly acquired Reddit content | MineDojo README states CC BY 4.0 for its database; current Reddit Data API Terms also apply to new API access | Historical research reference only | **No new Reddit ML ingestion without required permissions** | Blocked by default | Current Reddit terms state that User Content may not be used for ML/AI training without express permission of applicable rightsholders and restrict model training via Reddit Services/Data without Reddit permission |
| Derived labels, embeddings, summaries, or features | Source lineage plus transformation code/version and source permissions | Training/evaluation | Only if every upstream source permits the intended use | Only if upstream rights and privacy status permit it | Transformation does not automatically erase copyright, contractual, privacy, or re-identification concerns |
| Trained checkpoints/adapters | Complete training-data manifest, model/base license, training code/config, deletion limitations | Research model artifacts | Only from approved training manifests | Separate release review required | Determine whether source licenses/consent constrain weight release and whether memorisation or personal-data leakage tests are required |

## Minecraft-specific findings

The current Minecraft Usage Guidelines define game code, graphics, textures,
models, sounds, and gameplay videos/screenshots as Minecraft assets. They permit
players and fans to create and share gameplay videos and screenshots subject to
their stated conditions, while reserving Mojang/Microsoft rights and noting
that the guidelines can change.

The Minecraft EULA permits original Java Edition mods but distinguishes a mod
from a distributed modded copy of Minecraft. This project's release pipeline
therefore distributes project code/artifacts, not bundled game software.

These permissions do not answer the separate rights of a human participant,
skin creator, world creator, video uploader, music rightsholder, hosting
platform, or data subject. Those layers remain in the dataset manifest.

## Third-party dataset findings

### OpenAI VPT

The OpenAI Video-Pre-Training repository uses the MIT license for its software
and documentation. Its README publicly links contractor recordings and
explicitly demonstrates using those recordings for behavioural-cloning
fine-tuning.

That is useful evidence that training use was contemplated by the publisher,
but the repository license alone is not treated as a blanket license for every
hosted recording, world save, model weight, or downstream redistribution mode.
Before VPT data is copied into a project dataset, the exact data release terms
and intended output license must be reviewed and recorded.

The much larger internet-video stage described by VPT is not a default data
source for this project. Repeating an internet-video scraping pipeline would
introduce creator-rights and platform-terms questions that are unnecessary when
native, consented telemetry can be collected directly.

### MineRL

The MineRL repository points users to a Zenodo backup of the 2019 human
demonstration datasets. The Zenodo record identifies the MineRL Team and the
files but, at review time, its rendered Rights section did not specify a
license.

The current repository's root LICENSE is CC BY-NC-SA 4.0. Because repository
licensing, package metadata, historical versions, and dataset records can differ,
the project must identify the exact MineRL artifact/version and its data-specific
terms before use. No generic "MineRL is open source" conclusion is sufficient.

### MineDojo knowledge bases

MineDojo's README distinguishes component licenses:

- codebase: MIT;
- YouTube database: CC BY 4.0;
- Wiki database: CC BY-NC-SA 3.0; and
- Reddit database: CC BY 4.0.

Those labels are useful for the database artifacts supplied by MineDojo. They do
not automatically license the underlying audiovisual or user-authored content
for every purpose.

For new YouTube API access, current YouTube API policy states that API clients
must not download, import, back up, cache, or store copies of YouTube
audiovisual content without prior written approval. The project therefore does
not build a new YouTube-video training scraper under the baseline policy.

For new Reddit acquisition, current Reddit Data API Terms state that User
Content is owned by users and do not grant a right to use it for machine
learning or AI training without express permission of applicable rightsholders.
The Developer Terms also restrict using Reddit Services and Data to train models
without Reddit permission. Historical third-party database licensing therefore
does not justify new Reddit ingestion.

## Human research collection policy

### Default collection mode

A human gameplay study should collect native gameplay telemetry only:

- versioned observations exposed by the approved native interface;
- actions and outcomes;
- game/session time;
- experiment/scenario identifiers;
- pseudonymous participant ID;
- consent-policy version;
- world/version/configuration provenance; and
- technical diagnostics required to validate the recording.

Do not collect by default:

- real name;
- email address in the trajectory dataset;
- Microsoft/Xbox credentials or account tokens;
- raw IP address after operational necessity ends;
- desktop/window contents outside Minecraft;
- microphone audio;
- voice chat;
- unrelated filesystem/device information;
- private messages outside the study;
- exact external account identifiers; or
- human chat unless the study separately requires and obtains consent for it.

The consent/identity registry must be stored separately from research
trajectories and linked with a random participant identifier.

### Age baseline

Because Minecraft is widely used by children, project-run human-data collection
defaults to adult participants only until a specific study implements an
approved age-verification/guardian-consent process and jurisdiction-specific
review.

This is a conservative project rule, not a statement that every jurisdiction
uses the same age threshold.

### Chat and free text

Chat is a separate optional data class. If collected:

- explain exactly why it is required;
- obtain a separate opt-in;
- warn participants not to disclose private third-party information;
- record whether messages came from a study participant, non-participant, or
  agent;
- exclude non-participant messages unless a reviewed protocol permits them;
- redact direct identifiers where practical;
- restrict raw access; and
- review examples before publication.

A pseudonymous username does not make chat anonymous.

## Consent template requirements

Every human collection protocol must produce a versioned consent record that
contains at least:

1. **Study identity**
   - project/study name and version;
   - controller/research contact;
   - date and consent-form version.
2. **Purpose**
   - the concrete research questions;
   - whether data is for training, evaluation, publication, or all three.
3. **Data collected**
   - exact telemetry categories;
   - whether chat, audio, video, identifiers, or world saves are included;
   - what is explicitly not collected.
4. **Participation scope**
   - session duration and environment;
   - whether other humans can appear;
   - participant eligibility and age rule.
5. **Use permissions**
   - internal research;
   - model training/fine-tuning;
   - benchmark/evaluation;
   - publication of aggregate results;
   - publication of examples;
   - raw or transformed dataset release;
   - model/checkpoint release.
6. **Access and processors**
   - who can access raw data;
   - storage providers or external processors, if any;
   - cross-border transfer information when applicable.
7. **Retention**
   - finite raw-data retention period or event;
   - backup expiry;
   - retention for approved derived data.
8. **Withdrawal and deletion**
   - how to request withdrawal;
   - which linked data can be deleted;
   - the cut-off after which published artifacts cannot be recalled;
   - whether an already trained checkpoint can actually be retrained or
     unlearned.
9. **Risks**
   - possible identification from gameplay, builds, skins, or chat;
   - possible model memorisation where relevant;
   - limits of de-identification.
10. **Third-party content**
    - participant promise not to intentionally submit material they lack rights
      to provide;
    - procedure for reporting accidental third-party content.
11. **Choice**
    - required and optional purposes are separated;
    - optional chat/public-release/model-release choices are not preselected.
12. **Record**
    - participant pseudonymous ID;
    - consent timestamp;
    - consent choices;
    - withdrawal/restriction history.

A protocol is not collectable if required consent/provenance fields are missing.

## Dataset manifest requirements

Every dataset release or internal training snapshot must have an immutable
manifest containing:

- dataset ID and semantic version;
- creation timestamp and responsible maintainer;
- source categories and source artifact IDs;
- per-source license/terms reference and captured revision/date;
- consent-policy version and permitted-use flags;
- participant count and eligibility rule where applicable;
- personal-data classes present;
- redaction/anonymisation/pseudonymisation method;
- transformations with code revision and parameters;
- Minecraft, mod, schema, world/scenario, and telemetry versions;
- hashes/checksums;
- train/validation/test split provenance;
- known exclusions and deletion tombstones;
- retention/expiry;
- approved release license, if any;
- unresolved issues and use restrictions; and
- downstream checkpoint/experiment IDs that consumed the dataset.

Training code must refuse a manifest whose intended training permission is not
affirmatively approved.

## Retention, withdrawal, and deletion

### Required lineage

Raw records, transformed datasets, experiments, and checkpoints must remain
traceable through stable artifact IDs. Deletion cannot be reliable if source
lineage is discarded.

### Withdrawal flow

For consent-based project collection, a withdrawal request should:

1. authenticate the request without copying unnecessary identity data into the
   research store;
2. mark the participant/source as blocked from future ingestion;
3. locate raw and derived artifacts through lineage;
4. delete or restrict the copies the project promised are deletable;
5. propagate tombstones to active dataset manifests and caches;
6. prevent the data from entering future training runs;
7. identify already trained checkpoints that consumed the source;
8. apply the checkpoint policy actually promised to the participant; and
9. record a minimal audit outcome without retaining the deleted research
   content.

Published third-party copies, legitimately retained compliance records, and
model parameters may not be technically recallable. These limitations must be
disclosed before collection rather than discovered after a request.

### Trained artifacts

Until the project has validated machine-unlearning or deterministic retraining,
the default promise is:

- withdrawal stops future use of linked raw/derived data;
- deletable project-controlled copies are removed according to the declared
  policy;
- affected checkpoints are marked in provenance;
- release decisions may require retraining without the withdrawn source; and
- no claim is made that a participant's influence has been surgically removed
  from already trained parameters.

## Privacy engineering baseline

The project adopts these controls independent of the minimum law that might
apply in one deployment:

- data minimisation;
- purpose limitation in the manifest;
- separate identity/consent registry;
- random participant identifiers;
- least-privilege raw-data access;
- encryption in transit and at rest where human data is stored;
- audit logging for raw-data export;
- no human-data secrets in Git history;
- finite retention;
- deletion/tombstone support;
- no production telemetry upload by default;
- privacy review before dataset or checkpoint publication; and
- synthetic fixtures in automated tests.

As one relevant regulatory reference, current UK ICO research guidance states
that research safeguards should include data minimisation and, where possible,
anonymisation or pseudonymisation. It also emphasizes that pseudonymised data
remains personal data. ICO guidance on erasure notes that erasure rights are not
absolute and depend on the processing circumstances. These are review inputs,
not universal legal conclusions for every deployment.

## Risk register

| Risk | Failure mode | Baseline mitigation |
| --- | --- | --- |
| Public-equals-permitted assumption | Public video, skin, world, or post is copied into training without usable rights | Deny by default; record artifact-specific permission |
| Code-license/data-license confusion | MIT/GPL/CC license on software is assumed to cover hosted datasets or weights | Separate code, data, weights, assets, and platform terms in manifests |
| Database/underlying-content confusion | A database license is treated as a license to the underlying creator media | Record both database rights and content rights |
| Platform-term drift | A previously acceptable acquisition method becomes prohibited | Store terms URL/revision/date and trigger re-review on change |
| Minecraft-policy drift | Usage permissions change or are withdrawn | Record policy date and review releases/upgrades |
| Unlicensed skins/worlds | Community assets enter releases without creator permission | Use project-owned/contributor-licensed assets; provenance gate |
| Non-participant capture | Chat or multiplayer telemetry records people who never consented | Controlled study worlds; filter/exclude non-participants; separate review |
| Sensitive free text | Chat reveals health, beliefs, location, credentials, or third-party information | Chat off by default; separate opt-in, restricted access, publication review |
| Re-identification | Pseudonymous trajectories reveal a player through username, skin, timing, builds, or text | Minimise fields, separate mappings, release-risk testing |
| Minor participation | Child data is collected without an approved process | Adult-only default for project studies; dedicated review for any exception |
| Consent-purpose drift | Data collected for evaluation is later used for training/public release | Machine-readable permitted-use flags; training gate |
| Retention creep | Raw human data remains indefinitely | Finite declared retention and automated expiry |
| Broken deletion lineage | Project cannot find derived copies/checkpoints after withdrawal | Mandatory source IDs, transformation lineage, tombstones |
| Impossible unlearning promise | Consent claims weights can be purged when no tested method exists | Disclose limits; retrain/rollback policy; never promise unsupported deletion |
| Model memorisation | Released weights reproduce identifying or copyrighted source material | Memorisation/privacy evaluation before release; source-aware release review |
| Third-party processor leakage | Human data is uploaded to an unreviewed service | Processor/access review and explicit manifest entry |
| License incompatibility | NC/SA/attribution terms conflict with intended artifact release | License-compatibility review before training and release |

## Mandatory review triggers

Re-run data/legal/privacy review when any of the following happens:

- a new dataset, website, platform, skin catalog, world source, or data broker is
  introduced;
- source terms, API policy, Minecraft EULA/Usage Guidelines, or a dataset
  license changes;
- human chat, voice, video, screenshots, account identifiers, IP addresses, or
  precise external location are added;
- participants under the current adult-only baseline are proposed;
- collection expands to a new jurisdiction or institution with different
  obligations;
- raw data or model weights will be published;
- a previously internal dataset will be redistributed;
- the project begins commercial use of a source carrying non-commercial terms;
- data is transferred to a new cloud/processor or outside the declared storage
  region;
- retention is extended;
- datasets are merged in a way that changes re-identification risk;
- a new model architecture materially increases memorisation risk;
- deletion/unlearning promises change;
- a source cannot be traced to its original license/consent record; or
- a maintainer discovers that an existing manifest contains unresolved or
  contradictory rights information.

When triggered, the affected source is frozen for new ingestion/training until
the review outcome is recorded.

## Decision outcomes

Use four explicit outcomes for each source:

- **approved** — permissions and privacy controls support the declared uses;
- **approved with restrictions** — only listed purposes/outputs are allowed;
- **hold** — evidence is incomplete or terms conflict;
- **rejected** — the proposed use is incompatible with the recorded terms,
  consent, privacy constraints, or project principles.

Silence or missing metadata means **hold**, not approval.

## Source references

Minecraft and Microsoft:

- [Minecraft EULA](https://www.minecraft.net/en-us/eula)
- [Minecraft Usage Guidelines](https://www.minecraft.net/en-us/usage-guidelines)
- [Microsoft Privacy Statement](https://www.microsoft.com/en-us/privacy/privacystatement)

Privacy/research guidance:

- [ICO research provisions](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/the-research-provisions/)
- [ICO research safeguards](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/the-research-provisions/what-are-the-appropriate-safeguards/)
- [ICO pseudonymisation guidance](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/data-sharing/anonymisation/pseudonymisation/)
- [ICO right to erasure guidance](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/individual-rights/individual-rights/right-to-erasure/)

Third-party platforms and datasets:

- [YouTube API Services policies](https://developers.google.com/youtube/terms/developer-policies)
- [Reddit Data API Terms](https://redditinc.com/policies/data-api-terms)
- [Reddit Developer Terms](https://redditinc.com/policies/developer-terms)
- [OpenAI Video-Pre-Training repository](https://github.com/openai/Video-Pre-Training)
- [MineRL repository](https://github.com/minerllabs/minerl)
- [MineRL 2019 Zenodo backup](https://zenodo.org/records/12659939)
- [MineDojo repository](https://github.com/MineDojo/MineDojo)

## Follow-up implications

This policy unblocks design work on:

- imitation-learning dataset strategy (#24);
- telemetry/dataset manifests (#25);
- native human collection and consent instrumentation;
- privacy controls (#97); and
- later checkpoint/model-card/release policy.

Those issues must implement this framework rather than re-deciding the same
baseline from scratch.
