# Contributor documentation audit

Status: v0.1 onboarding audit for issue #53.

This file records the audit and its acceptance evidence. It is **not** an
authoritative source for project goals, architecture, testing, research, data,
or security policy. Follow the linked source documents when they differ from
this audit.

## Audit scope

Reviewed:

- README contributor journey and documentation navigation;
- CONTRIBUTING issue selection and first-task workflow;
- AGENTS orientation requirements;
- glossary terminology;
- issue forms for bugs, design, experiments, features, research, and security;
- pull-request template;
- research reproducibility guidance;
- testing and CI guidance; and
- local documentation links.

The audit intentionally avoids copying authoritative policy into onboarding
documents. Navigation points contributors to the existing source instead.

## Changes made

The audit resulted in focused navigation changes:

- README now links directly to evaluation, experiment, testing, CI, data
  governance, and runtime-boundary documents.
- README includes a short first-contribution path.
- CONTRIBUTING explains how to choose actionable work and which issue form to
  use.
- CONTRIBUTING adds a pre-PR local-validation checklist.
- The glossary includes current evaluation/testing/runtime terminology.
- The pull-request checklist now points to the documented local CI/testing
  workflow and evidence contracts.

The existing issue forms already request the appropriate minimum information:

- bug reports ask for reproduction, versions/seed/configuration, expected
  behaviour, impact, and evidence;
- design proposals ask for constraints, alternatives, consequences, validation,
  and blockers;
- experiments ask for hypothesis/falsification, controls, metrics,
  reproducibility metadata, and results;
- feature proposals ask for problem, goal/non-goals, scope, acceptance criteria,
  architecture impact, and dependencies;
- research tasks ask for question, prior work, methodology, metrics,
  reproducibility, and decision output; and
- security reports are routed to the private advisory flow.

No issue-form rewrite was justified by this audit.

## Representative contributor questions

These questions test whether a new contributor can find the needed answer from
normal repository entry points without relying on maintainer context.

### 1. What is this project actually trying to build, and what is explicitly out of scope?

Answer location:

- [Project Goal](GOAL.md) is authoritative for the ultimate goal, near-term
  engineering goal, native-reality constraint, and non-goals.
- [README](../README.md) provides the short entry-point summary.
- [Design Principles](PRINCIPLES.md) records the main invariants.

Expected contributor conclusion: this is a Minecraft-native persistent
intelligence research programme, not an LLM-command wrapper, screenshot desktop
agent, Mineflayer-style prompted bot, scripted NPC, or consciousness claim.

### 2. What should I work on now, and how do I know whether an issue is blocked?

Answer location:

- [Roadmap](../ROADMAP.md) defines milestone order/current focus.
- [CONTRIBUTING](../CONTRIBUTING.md) instructs contributors to prefer the
  current milestone and `status:ready` work, verify listed blockers, and check
  for overlapping pull requests.
- The issue itself remains authoritative for its concrete dependencies and
  acceptance criteria.

Expected contributor conclusion: do not silently pull blocked later-milestone
work forward just because it is convenient.

### 3. What checks should I run before opening a pull request, and what belongs in CI?

Answer location:

- [Testing](TESTING.md) defines T0–T7 tiers, seeds, flakes, retries, artifacts,
  and PR/nightly/manual gates.
- [CI](CI.md) lists current local equivalents and the path-routed remote checks.
- [CONTRIBUTING](../CONTRIBUTING.md) links both from the pre-PR workflow.

Expected contributor conclusion: validate locally first; ordinary PR CI is for
bounded deterministic checks, not model training or long research studies.

### 4. How do I make a research or capability claim reproducible?

Answer location:

- [Research Programme](../RESEARCH.md) defines the evidence standard.
- [Evaluation](EVALUATION.md) defines versioned scenario/result evidence.
- [Experiments](EXPERIMENTS.md) defines executable run/provenance artifacts.
- The experiment/research issue forms capture hypothesis, methodology, metrics,
  versions, seeds, hardware, artifacts, and conclusions.

Expected contributor conclusion: preserve failed/inconclusive trials,
learned-versus-scripted accounting, raw artifacts, exact revisions, seeds,
variance, and limitations; a compelling demo alone is not evidence.

### 5. Can I use publicly available gameplay, chat, skins, worlds, or datasets?

Answer location:

- [Data Governance](DATA_GOVERNANCE.md) is the collection/use decision
  framework.
- [Data](DATA.md) summarizes telemetry/provenance requirements.
- [Security](../SECURITY.md) defines privacy and untrusted-data boundaries.

Expected contributor conclusion: public/downloadable does not mean approved for
training or redistribution; missing provenance, rights, consent, or permitted
use means the source is on hold.

## Terminology check

The glossary now provides short canonical definitions for terms contributors
will encounter in current v0.1/v0.2 work, including:

- evaluation scenario;
- evaluation result;
- experiment run;
- privileged input;
- scaffolding;
- quality gate; and
- runtime boundary.

Long-form semantics remain in their owning documents rather than being
duplicated in the glossary.

## Template check

### Issue forms

The existing issue forms map cleanly to repository work types and already
request the core information needed for triage. CONTRIBUTING now exposes that
mapping so contributors do not need to inspect every form before choosing one.

### Pull requests

The pull-request template covers:

- issue/problem and scope;
- evidence and validation;
- architecture/vision impact;
- learned/scripted/heuristic accounting;
- data/privacy/security; and
- local checks, documentation/ADR updates, evidence, secrets/data, and scope.

The checklist links the repository's testing/CI policy rather than duplicating
commands that will evolve.

## Link-validation acceptance

All Markdown local and external links are checked by the stack-aware
Documentation CI job whenever Markdown changes.

This audit changes Markdown, so its pull request is expected to exercise that
check. A successful Documentation job is the acceptance evidence for the
repository-wide Markdown link pass.

## Reviewer checklist

For future contributor-documentation changes, check:

- [ ] The authoritative source is linked rather than copied.
- [ ] README provides a useful entry point without becoming a second
      specification.
- [ ] CONTRIBUTING explains workflow rather than redefining architecture.
- [ ] New terminology is added to the glossary when it materially helps
      navigation.
- [ ] Issue/PR templates request evidence appropriate to the work type.
- [ ] Local validation guidance matches `docs/CI.md` and
      `docs/TESTING.md`.
- [ ] Research guidance points to `RESEARCH.md`, `EVALUATION.md`, and
      `EXPERIMENTS.md`.
- [ ] Human/third-party data guidance points to `DATA_GOVERNANCE.md`.
- [ ] Local links and headings pass documentation CI.
- [ ] No authoritative text is duplicated merely for convenience.

## Outcome

The five representative questions are answerable from documented repository
entry points, templates are aligned with the current research/testing workflow,
and contributor navigation points to one authoritative source per policy area.

Future onboarding changes should remain targeted: add navigation when a new
authoritative subsystem document appears rather than copying its content into
the README or contribution guide.
