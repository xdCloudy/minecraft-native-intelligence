#!/usr/bin/env python3
"""Validate, score and deterministically generate the MNI progress system.

The declared scope is deliberately extensible; catalog completion is not capability completion.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'docs/progress/progress.json'
SCHEMA = ROOT / 'docs/progress/progress.schema.json'
README_START, README_END = '<!-- MNI_PROGRESS_START -->', '<!-- MNI_PROGRESS_END -->'
ROADMAP_START, ROADMAP_END = '<!-- MNI_ROADMAP_PROGRESS_START -->', '<!-- MNI_ROADMAP_PROGRESS_END -->'
STATUS = {
 'research':['not_investigated','prior_art_reviewed','hypothesis_established','feasibility_evaluated','experiment_designed','experiment_conducted','baselines_compared','reproducibility_validated','research_concluded'],
 'experimentalOutcome':['not_assessed','positive','negative','inconclusive','infeasible','superseded'],
 'implementation':['not_implemented','experimental','prototype','functional','locally_tested','integrated','regression_tested','production_validated'],
 'validation':['untested','unit_tested','integration_tested','in_game_tested','reproducibly_benchmarked','independently_verified'],
 'productionReadiness':['not_assessed','experimental','locally_validated','ci_validated','integrated_into_main','release_validated','production_validated'],
}
IMPLEMENTED_MAIN={'integrated','regression_tested','production_validated'}
IN_GAME_VALIDATION={'in_game_tested','reproducibly_benchmarked','independently_verified'}
COMPETENCY_GROUPS={
 'Survival and progression','Combat and entities','Dimensions and traversal',
 'Construction and automation','Multiplayer and world lifecycle',
}
LEGACY_PLACEHOLDERS=(
 'Determine whether and how ',
 'Determine whether ',
 'Define a falsifiable protocol for ',
 'Design and run a falsifiable comparison for ',
 'Pre-register task distribution and metrics for ',
 'Pre-register measurable success and failure criteria for ',
 'Which approach, if any, measurably improves ',
 'Which approach, if any, improves ',
)

class InvalidProgress(ValueError): pass

def need(condition: bool, message: str) -> None:
 if not condition: raise InvalidProgress(message)

def schema_check(value, schema, at='$', root=None):
 """Validate the checked-in JSON Schema subset without third-party dependencies."""
 if root is None: root=schema
 if '$ref' in schema:
  ref=root
  for part in schema['$ref'][2:].split('/'): ref=ref[part]
  return schema_check(value,ref,at,root)
 if 'const' in schema: need(value==schema['const'],f'{at}: expected constant {schema["const"]!r}')
 if 'enum' in schema: need(value in schema['enum'],f'{at}: value {value!r} is outside enum')
 typ=schema.get('type'); types={'object':dict,'array':list,'string':str,'integer':int,'number':(int,float),'boolean':bool}
 if typ: need(isinstance(value,types[typ]) and not (typ=='integer' and isinstance(value,bool)),f'{at}: expected {typ}')
 if isinstance(value,str):
  need(len(value)>=schema.get('minLength',0),f'{at}: string shorter than minLength')
  if 'pattern' in schema: need(re.fullmatch(schema['pattern'],value) is not None,f'{at}: invalid string pattern')
  if schema.get('format')=='date':
   try: date.fromisoformat(value)
   except ValueError: raise InvalidProgress(f'{at}: invalid ISO date')
  if schema.get('format')=='uri': need(value.startswith(('https://','http://','repo:')),f'{at}: expected URL or repo reference')
 if isinstance(value,(int,float)) and not isinstance(value,bool):
  need(value>=schema.get('minimum',value),f'{at}: below minimum'); need(value<=schema.get('maximum',value),f'{at}: above maximum')
 if isinstance(value,list):
  need(len(value)>=schema.get('minItems',0),f'{at}: too few items'); need(len(value)<=schema.get('maxItems',float('inf')),f'{at}: too many items')
  if 'items' in schema:
   for i,item in enumerate(value): schema_check(item,schema['items'],f'{at}[{i}]',root)
 if isinstance(value,dict):
  for key in schema.get('required',[]): need(key in value,f'{at}: missing required property {key}')
  props=schema.get('properties',{})
  if schema.get('additionalProperties') is False: need(set(value)<=set(props),f'{at}: unexpected properties {sorted(set(value)-set(props))}')
  for key,item in value.items():
   if key in props: schema_check(item,props[key],f'{at}.{key}',root)
   elif isinstance(schema.get('additionalProperties'),dict): schema_check(item,schema['additionalProperties'],f'{at}.{key}',root)

def all_avenues(data): return [(dom,av) for dom in data['domains'] for av in dom['avenues']]
def all_items(data):
 items=[(dom,av,'avenue') for dom,av in all_avenues(data)]
 by={d['id']:d for d in data['domains']}
 items.extend((by[item['workstream']],item,'model') for item in data['modelCandidates'])
 items.extend((by[item['workstream']],item,'training') for item in data['trainingMethods'])
 return items

def validate(data,schema):
 schema_check(data,schema)
 need(data['schemaVersion']==3,'unsupported progress schemaVersion')
 need(data['assessment']['baseline']=='main','assessment must describe main')
 need(data['assessment']['sourceRevision']==data['assessment']['defaultBranchRevision'],'sourceRevision must match the audited main baseline')
 historic=set(data['assessment'].get('historicalMainRevisions',[]))
 need(all(re.fullmatch(r'[a-f0-9]{40}',sha) and sha!=data['assessment']['defaultBranchRevision'] for sha in historic),'invalid historical main revisions')
 need(data['branchAudit']['defaultBranchRevision']==data['assessment']['defaultBranchRevision'],'branch audit must match main assessment')
 github=data['githubState']
 need(github['repository']=='xdCloudy/minecraft-native-intelligence','GitHub state refers to another repository')
 need(all(isinstance(github[key],int) and not isinstance(github[key],bool) and github[key]>=0 for key in ['openIssueCount','openPullRequestCount','issuesClosedAdministratively']),'invalid GitHub workflow counts')
 for key,count in [('openIssueNumbers','openIssueCount'),('openPullRequestNumbers','openPullRequestCount')]:
  ids=github[key]
  need(len(ids)==github[count] and len(ids)==len(set(ids)) and all(isinstance(x,int) and x>0 for x in ids),f'invalid GitHub {key} snapshot')
 need(github['openPullRequestCount']==sum(pr['state']=='open' for pr in data['unmergedWork']),'GitHub PR count disagrees with tracked open PR records')
 need(set(github['openPullRequestNumbers'])=={int(pr['id'][3:]) for pr in data['unmergedWork'] if pr['state']=='open'},'GitHub PR number snapshot disagrees with tracked records')
 need(data['statusDefinitions']==STATUS,'statusDefinitions differ from generator vocabulary')
 scoring=data['scoring']
 score_keys={'researchCompletion':'research','experimentalEffectiveness':'experimentalOutcome','implementationMaturity':'implementation','validationCoverage':'validation','productionReadiness':'productionReadiness'}
 for dim,status_key in score_keys.items():
  need(set(scoring[dim])==set(STATUS[status_key]),f'scoring.{dim} must cover every state')
  need(all(isinstance(x,(int,float)) and not isinstance(x,bool) and 0<=x<=1 for x in scoring[dim].values()),f'scoring.{dim} values must be 0..1')
 need(set(scoring['overallScopedProgress'])=={'demonstratedCapability','implementationMaturity','validationCoverage','productionReadiness'},'overallScopedProgress weights are incomplete')
 need(abs(sum(scoring['overallScopedProgress'].values())-1)<1e-9,'overall scoped progress weights must sum to 1')
 need(set(scoring['milestoneGate'])=={'open','prototype','partial','met'},'milestoneGate statuses are invalid')
 ids=set()
 def unique(item,label):
  ident=item.get('id'); need(isinstance(ident,str) and bool(ident) and ident not in ids,f'{label}: missing/duplicate ID {ident!r}'); ids.add(ident)
 evidence={}
 for e in data['evidence']:
  unique(e,'evidence'); evidence[e['id']]=e
  if e['url'].startswith('repo:'): need((ROOT/e['url'][5:]).is_file(),f'{e["id"]}: broken repository evidence path {e["url"]}')
 domains={}
 for dom in data['domains']:
  unique(dom,'workstream'); domains[dom['id']]=dom
  need(1<=dom['weight']<=5,f'{dom["id"]}: workstream weight must be 1..5')
  for av in dom['avenues']:
   for field in ('objective','methodology'):
    value=av.get(field,'')
    need(not any(value.startswith(phrase) for phrase in LEGACY_PLACEHOLDERS),f'{av["id"]}: generic research boilerplate in {field}; define a domain-specific scenario, comparator, measurement and failure boundary')
   for field in ('acceptanceCriteria','openQuestions','remainingWork'):
    need(not any(text.startswith(phrase) for text in av.get(field,[]) for phrase in LEGACY_PLACEHOLDERS),f'{av["id"]}: generic research boilerplate in {field}')
 items={}
 for dom,item,kind in all_items(data):
  unique(item,kind); items[item['id']]=(dom,item,kind)
  required=['workstream','category','description','scope','objective','priority','dependencies','status','acceptanceCriteria','evidence','relatedIssues','relatedPRs','relatedCommits','limitations','remainingWork','lastAssessment','history','completionCriteria','milestones','lastVerifiedRevision']
  need(all(k in item for k in required),f'{item["id"]}: missing required tracked-item field')
  need(item['workstream']==dom['id'],f'{item["id"]}: workstream does not match its matrix')
  need(1<=item['priority']<=5,f'{item["id"]}: priority must be 1..5')
  need(item['lastAssessment']==data['assessment']['date'],f'{item["id"]}: stale assessment date')
  need(re.fullmatch(r'[a-f0-9]{40}',item['lastVerifiedRevision']) is not None,f'{item["id"]}: invalid assessed revision')
  prs={p['id']:p for p in data['unmergedWork']}
  need(item['lastVerifiedRevision']==data['assessment']['defaultBranchRevision'] or item['lastVerifiedRevision'] in {p['headRevision'] for p in data['unmergedWork']},f'{item["id"]}: untracked assessed revision')
  for key,allowed in STATUS.items(): need(item['status'][key] in allowed,f'{item["id"]}: invalid {key} state')
  for ref in item['evidence']: need(ref in evidence,f'{item["id"]}: unknown evidence {ref}')
  for ref in item.get('priorWork',[]): need(ref in evidence,f'{item["id"]}: unknown prior-work evidence {ref}')
  for issue in item['relatedIssues']: need(re.fullmatch(r'#[1-9][0-9]*',issue) is not None,f'{item["id"]}: invalid issue reference {issue}')
  for pr_id in item['relatedPRs']: need(pr_id in prs and item['id'] in prs[pr_id]['affectedAvenues'],f'{item["id"]}: related PR does not list this item')
  if item['lastVerifiedRevision']!=data['assessment']['defaultBranchRevision']:
   pr=next(p for p in data['unmergedWork'] if p['headRevision']==item['lastVerifiedRevision'])
   need(pr['id'] in item['relatedPRs'] or item['id'] in pr['affectedAvenues'],f'{item["id"]}: branch revision provenance is not linked')
  if item['status']['implementation'] in IMPLEMENTED_MAIN:
   need(item['lastVerifiedRevision']==data['assessment']['defaultBranchRevision'],f'{item["id"]}: integrated implementation requires main evidence')
  if item['status']['productionReadiness'] in {'integrated_into_main','release_validated','production_validated'}:
   need(item['lastVerifiedRevision']==data['assessment']['defaultBranchRevision'],f'{item["id"]}: production-readiness credit requires main evidence')
  if item['status']['research']=='research_concluded':
   need(item['evidence'] and item['limitations'] and item['remainingWork'],f'{item["id"]}: concluded research requires evidence and limitations')
  if item['status']['implementation']=='production_validated':
   need(item['status']['validation'] in IN_GAME_VALIDATION,f'{item["id"]}: production validated requires in-game or stronger evidence')
   need(item['status']['experimentalOutcome']=='positive',f'{item["id"]}: production validated requires a positive recorded outcome')
  for mid in item['milestones']: need(mid in {m['id'] for m in data['milestones']},f'{item["id"]}: unknown milestone {mid}')
  for hist in item['history']: need(hist['revision'] in historic or hist['revision']==data['assessment']['defaultBranchRevision'] or hist['revision'] in {p['headRevision'] for p in data['unmergedWork']},f'{item["id"]}: history revision is not audited')
  if 'competency' in item:
   c=item['competency']
   need(kind=='avenue' and item['id'].startswith('GP-'),f'{item["id"]}: gameplay competency must be a tracked gameplay avenue')
   need(c.get('group') in COMPETENCY_GROUPS,f'{item["id"]}: invalid competency group')
   for field in ('scenario','failureBoundary','evidenceRequired'):
    need(isinstance(c.get(field),str) and len(c[field].strip())>=20,f'{item["id"]}: missing competency {field}')
  if item['id'].startswith('GP-'):
   need('competency' in item,f'{item["id"]}: gameplay avenue lacks independently testable competency gate')
 # Every experiment outcome needs a matching provenance record. A branch record may remain pending independent assessment.
 deps={ident:item['dependencies'] for ident,(_,item,_) in items.items()}
 for ident,(_dom,item,_kind) in items.items():
  for dep in item['dependencies']: need(dep in items or dep in {m['id'] for m in data['milestones']},f'{ident}: missing dependency {dep}')
  if item['status']['experimentalOutcome']!='not_assessed':
   need(any(r['trackedItemId']==ident and r['outcome']==item['status']['experimentalOutcome'] and r['status'] in {'experiment_conducted','baselines_compared','reproducibility_validated','research_concluded'} for r in data['experimentRecords']),f'{ident}: outcome lacks a completed, matching experiment record')
 visiting=set(); visited=set()
 def visit(ident):
  need(ident not in visiting,f'dependency cycle includes {ident}')
  if ident in visited:return
  visiting.add(ident)
  for dep in deps[ident]:
   if dep in items: visit(dep)
  visiting.remove(ident); visited.add(ident)
 for ident in items: visit(ident)
 for candidate in data['modelCandidates']:
  need(candidate['decisionStatus'] in {'candidate_only','reference_only','project_hypothesis','rejected'},f'{candidate["id"]}: invalid decisionStatus')
  for ref in candidate['evidence']: pass
 model_names=[candidate['name'].casefold().strip() for candidate in data['modelCandidates']]
 need(len(set(model_names))==len(model_names),'duplicated model architecture candidate names; explain distinct hypotheses')
 for cell in data['compatibilityCells']:
  unique(cell,'compatibility cell')
  for ref in cell['evidence']: need(ref in evidence,f'{cell["id"]}: unknown evidence {ref}')
 for record in data['experimentRecords']:
  unique(record,'experiment record')
  need(record['trackedItemId'] in items,f'{record["id"]}: unknown tracked item')
  need(record['status'] in STATUS['research'] and record['outcome'] in STATUS['experimentalOutcome'],f'{record["id"]}: unsupported experiment state')
  need(re.fullmatch(r'[a-f0-9]{40}',record['revision']) is not None,f'{record["id"]}: invalid source revision')
  for key in ['environment','minecraftVersion','modelVersion','datasetVersion','configuration','seeds','hardware','methodology','rawResults','reproduction','limitations','evidence']:
   need(key in record and record[key] not in ('',None,[]),f'{record["id"]}: missing reproducibility field {key}')
  for ref in record['evidence']: need(ref in evidence,f'{record["id"]}: unknown evidence {ref}')
  if record.get('sourcePR'): need(record['sourcePR'] in {p['id'] for p in data['unmergedWork']},f'{record["id"]}: unknown source PR')
 for pr in data['unmergedWork']:
  unique(pr,'PR snapshot')
  need(pr['state'] in {'open','closed'} and pr['integrated'] is False and pr['countsAsShipped'] is False,f'{pr["id"]}: unmerged work cannot receive integrated/shipped credit')
  if pr['base']=='main':
   need(re.fullmatch(r'[a-f0-9]{40}',pr['baseRevision']) is not None,f'{pr["id"]}: invalid base revision')
   if pr['state']=='open': need(pr['baseRevision']==data['assessment']['defaultBranchRevision'],f'{pr["id"]}: open PR main base SHA differs from assessment')
  else: need(any(parent['head']==pr['base'] and parent['headRevision']==pr['baseRevision'] for parent in data['unmergedWork']),f'{pr["id"]}: stacked base is not an audited PR head')
  need(pr['headRevision'] and len({c['name'] for c in pr['checks']})==len(pr['checks']),f'{pr["id"]}: invalid check snapshot')
  for ref in pr['affectedAvenues']: need(ref in items,f'{pr["id"]}: unknown affected item {ref}')
 # Maintain all documented roadmap milestone IDs and validate explicit item maps, gates and dependency DAG.
 need(len(data['milestones'])==12,'the v0.1–v1.0 roadmap must retain 12 milestones')
 milestone_by={}
 for m in data['milestones']:
  unique(m,'milestone'); milestone_by[m['id']]=m
  need(set(m['items'])<=set(items),f'{m["id"]}: item map references unknown progress item')
  need(set(m['avenues'])<=set(items),f'{m["id"]}: avenue map references unknown progress item')
  need(set(m['avenues'])<=set(m['items']),f'{m["id"]}: avenue IDs missing from overall item map')
  need(m['items'],f'{m["id"]}: milestone must map research/feature records')
  for c in m['criteria']:
   unique(c,'milestone criterion')
   need(c['status'] in scoring['milestoneGate'],f'{c["id"]}: unsupported milestone gate state')
   for ref in c['evidence']: need(ref in evidence,f'{c["id"]}: unknown milestone evidence')
   if c['status']=='met': need(c['evidence'] and all(evidence[x]['kind'] in {'repository','implementation'} for x in c['evidence']),f'{c["id"]}: completed integrated gate needs main repository evidence')
  for dep in m['dependsOn']: need(dep in {x['id'] for x in data['milestones']},f'{m["id"]}: missing milestone dependency {dep}')
  if m['status']=='complete_as_documented': need(all(c['status']=='met' for c in m['criteria']),f'{m["id"]}: completed milestone has open gates')
 mvisit=set(); mdone=set()
 def visit_milestone(mid):
  need(mid not in mvisit,f'milestone dependency cycle includes {mid}')
  if mid in mdone:return
  mvisit.add(mid)
  for dep in milestone_by[mid]['dependsOn']:visit_milestone(dep)
  mvisit.remove(mid);mdone.add(mid)
 for mid in milestone_by:visit_milestone(mid)
 referenced=set()
 for _,item,_ in all_items(data): referenced.update(item['evidence']);referenced.update(item.get('priorWork',[]))
 for r in data['experimentRecords']:referenced.update(r['evidence'])
 for c in data['compatibilityCells']:referenced.update(c['evidence'])
 for m in data['milestones']:
  for c in m['criteria']:referenced.update(c['evidence'])
 orphans=set(evidence)-referenced
 need(not orphans,f'orphan evidence sources: {sorted(orphans)}')
 return items,evidence,milestone_by

def importance(dom,item): return dom['weight']*item['priority']
def work_items(data): return all_items(data)
def score(data,dimension,subset=None):
 rows=[(d,x,k) for d,x,k in all_items(data) if subset is None or subset(d,x,k)]
 mapping=data['scoring'][dimension]; den=sum(importance(d,x) for d,x,_ in rows)
 return sum(importance(d,x)*mapping[x['status'][{'researchCompletion':'research','experimentalEffectiveness':'experimentalOutcome','implementationMaturity':'implementation','validationCoverage':'validation','productionReadiness':'productionReadiness'}[dimension]]] for d,x,_ in rows)/den if den else 0.0
def metrics(data):
 rows=all_items(data)
 fields=['workstream','category','description','scope','objective','dependencies','priority','status','acceptanceCriteria','evidence','relatedIssues','relatedPRs','relatedCommits','limitations','remainingWork','lastAssessment','history','completionCriteria','milestones']
 def scoped(item):
  for key in fields:
   if key not in item or item[key] is None:return False
   value=item[key]
   if isinstance(value,str) and not value.strip():return False
  return bool(item['acceptanceCriteria'] and item['evidence'] and item['history'] and item['completionCriteria'] and item['milestones'])
 complete=sum(scoped(x) for _,x,_ in rows)/len(rows)
 demo_rows=[(d,x,k) for d,x,k in rows if x['status']['experimentalOutcome']=='positive' and x['status']['implementation'] in {'functional','locally_tested','integrated','regression_tested','production_validated'} and x['status']['validation'] in IN_GAME_VALIDATION and x['lastVerifiedRevision']==data['assessment']['defaultBranchRevision']]
 den=sum(importance(d,x) for d,x,_ in rows)
 demonstrated=sum(importance(d,x) for d,x,_ in demo_rows)/den if den else 0
 vals={
  'researchCoverage':complete,
  'researchCompletion':score(data,'researchCompletion'),
  'implementationMaturity':score(data,'implementationMaturity'),
  'experimentalEffectiveness':score(data,'experimentalEffectiveness'),
  'demonstratedCapabilities':demonstrated,
  'validationCoverage':score(data,'validationCoverage'),
  'productionReadiness':score(data,'productionReadiness'),
 }
 vals['overallScopedProgress']=sum(data['scoring']['overallScopedProgress'][key]*vals[name] for key,name in [('demonstratedCapability','demonstratedCapabilities'),('implementationMaturity','implementationMaturity'),('validationCoverage','validationCoverage'),('productionReadiness','productionReadiness')])
 vals['modelResearch']=score(data,'researchCompletion',lambda d,x,k:k=='model')
 vals['trainingResearch']=score(data,'researchCompletion',lambda d,x,k:k=='training')
 return vals
def pct(value): return f'{100*value:.1f}%'
def bar(value,width=16):
 n=round(max(0,min(1,value))*width);return '█'*n+'░'*(width-n)
def linked_evidence(ref,sources):
 e=sources[ref];url=e['url']
 if url.startswith('repo:'):url=os.path.relpath(ROOT/url[5:],ROOT/'docs').replace('\\','/')
 return f'[{e["title"]}]({url})'
def current_milestone(data): return next((m for m in data['milestones'] if m['status']=='in_progress'),data['milestones'][0])
def milestone_score(data,m):
 gate=data['scoring']['milestoneGate']; cs=m['criteria']
 return sum(gate[c['status']] for c in cs)/len(cs) if cs else 0
def section_score(data,workstream,dimension='researchCompletion'):
 return score(data,dimension,lambda d,x,k:d['id']==workstream)

def gameplay_competencies(data):
 return [(dom,item) for dom,item in all_avenues(data) if 'competency' in item]

def update_marked(original,start,end,content,label):
 need(original.count(start)==1 and original.count(end)==1,f'{label}: expected exactly one generated marker pair')
 left=original.index(start)+len(start);right=original.index(end);need(left<=right,f'{label}: markers reversed')
 return original[:left]+'\n'+content.rstrip()+'\n'+original[right:]

def render(data):
 sources={e['id']:e for e in data['evidence']}; rows=all_items(data); m=metrics(data); now=current_milestone(data)
 byid={x['id']:(d,x,k) for d,x,k in rows}
 # Compact project dashboard; details remain in generated matrices.
 overview=['# Research and development progress','',f"Assessment: `{data['assessment']['date']}` · assessed main `{data['assessment']['defaultBranchRevision']}` · {len(data['domains'])} workstreams · {len(rows)} tracked features, research candidates and methods.",'','> The percentages track evidence against this declared research scope. They do not measure intelligence, autonomy, consciousness or human-level ability. No Minecraft-native intelligent agent is demonstrated on the assessed main revision. Unmerged PRs and their historical checks are recorded separately and receive no integrated or shipped credit.','', '| Dimension | Progress | Percent | Interpretation |','|---|---|---:|---|']
 labels=[('researchCoverage','Research coverage','Catalog completeness, not amount of research conducted.'),('researchCompletion','Research completion','Investigation can conclude negatively or as infeasible.'),('experimentalEffectiveness','Experimental effectiveness','Positive outcomes only; a negative result can still conclude research.'),('demonstratedCapabilities','Demonstrated capabilities','Positive, functional and in-game or stronger evidence on main.'),('implementationMaturity','Implementation maturity','Functional states on the assessed main revision.'),('validationCoverage','Validation coverage','Unit through independent verification; gameplay requires in-game evidence.'),('productionReadiness','Production readiness','Operational, security, privacy, compatibility and release gates.'),('overallScopedProgress','Overall scoped progress','60% demonstrated capabilities, 20% implementation, 10% validation, 10% readiness.')]
 for key,label,meaning in labels: overview.append(f'| {label} | {bar(m[key])} | {pct(m[key])} | {meaning} |')
 overview+=['','Research coverage and completion are distinct. Expanding scope can lower completion. Weights are `workstream weight × item priority`; neither is adjusted to preserve a trend. [Scoring and definitions](PROGRESS_WORKFLOW.md).','',f'## Current milestone','',f"**{now['id']} — {now['name']}** · {pct(milestone_score(data,now))} of evidence-reviewed exit gates. This delivery milestone does not imply agent capability.",'','### Model and training research','',f"- Model architecture research completion: **{pct(m['modelResearch'])}** across {len(data['modelCandidates'])} candidates.",f"- Training and learning research completion: **{pct(m['trainingResearch'])}** across {len(data['trainingMethods'])} methods.",'','### Workstream view','','| Workstream | Items | Research | Implementation | Validation | Readiness |','|---|---:|---:|---:|---:|---:|']
 for dom in data['domains']:
  count=sum(1 for d,x,k in rows if d['id']==dom['id'])
  overview.append(f'| {dom["name"]} | {count} | {pct(section_score(data,dom["id"]))} | {pct(section_score(data,dom["id"],"implementationMaturity"))} | {pct(section_score(data,dom["id"],"validationCoverage"))} | {pct(section_score(data,dom["id"],"productionReadiness"))} |')
 priority=sorted(rows,key=lambda r:(-importance(r[0],r[1]),r[1]['id']))
 overview+=['','## Main blockers','','| Item | Workstream | Main status | Acceptance evidence still needed |','|---|---|---|---|']
 for dom,item,kind in [r for r in priority if r[1]['status']['implementation']!='production_validated'][:5]:
  overview.append(f'| [`{item["id"]}` {item["title"]}](FEATURE_MATRIX.md#{item["id"].lower()}) | {dom["name"]} | {item["status"]["implementation"]} / {item["status"]["validation"]} | {item["acceptanceCriteria"][0]} |')
 overview+=['','## Roadmap progress','','Gate percentage is calculated from each milestone’s evidence-reviewed criteria (open=0, prototype=25%, partial=50%, met=100%). Item mappings are shown in the feature matrix; a PR cannot satisfy an integrated gate.','', '| Milestone | Stage | Gate progress | Gates met / total |','|---|---|---:|---:|']
 for mile in data['milestones']:
  met=sum(c['status']=='met' for c in mile['criteria']);overview.append(f'| {mile["id"]} — {mile["name"]} | {mile["status"]} | {pct(milestone_score(data,mile))} | {met}/{len(mile["criteria"])} |')
 state=data['githubState']
 overview+=['','## GitHub workflow audit','',f"Checked: {state['checkedAt']} · open issues: **{state['openIssueCount']}** · open PRs: **{state['openPullRequestCount']}** · issues closed administratively: **{state['issuesClosedAdministratively']}**.",'',state['note'],'','## Unmerged PR history (including closed PRs)','','| PR / state | Branch | Base → head | Historical checks | Integrated credit |','|---|---|---|---|---|']
 for pr in data['unmergedWork']:
  checks='; '.join(f'{c["name"]}: {c["conclusion"]}' for c in pr['checks'])
  overview.append(f'| [#{pr["id"][3:]}]({pr["url"]}) {pr["state"]} | `{pr["head"]}` | `{pr["base"]}` → `{pr["headRevision"][:8]}` | {checks} | excluded |')
 overview+=['','## Detailed matrices','','- [Feature and engineering matrix](FEATURE_MATRIX.md) — every scoped subsystem item and its five independent status dimensions.','- [Minecraft gameplay competency matrix](MINECRAFT_COMPETENCY_MATRIX.md) — concrete legal Survival scenarios and negative tests.','- [Research inventory](RESEARCH_MATRIX.md) — full questions, alternatives, prior work, methods, evidence and open issues.','- [Model architectures and training methods](MODEL_TRAINING_MATRIX.md) — candidate-by-candidate research and measured unknowns.','- [Experiments, compatibility and production readiness](PRODUCTION_READINESS.md) — reproducible evidence, branch audit, readiness gates and rejected approaches.','- [Progress maintenance workflow](PROGRESS_WORKFLOW.md).','']

 overview+=[f"**Minecraft-specific competency scenarios inventoried: {len(gameplay_competencies(data))}.** This is a declared, extensible scope, not proof all mechanics are known or tested. Each scenario requires separate legal-action, in-game and failure-boundary evidence.",'']
 feature=['# Feature and engineering matrix','','This is the implementation and validation view of every canonical item. Its 0% capability-oriented baseline does not erase the project’s documented v0.1 foundation; it indicates that documentation and contracts are not implemented Minecraft-native agent capabilities. Administratively closed issues and closed unmerged PRs are historical links, not completed acceptance criteria.','', 'Items are grouped by workstream for navigation. Every item retains its stable ID and direct-link anchor.','']
 for workstream in data['domains']:
  feature += [f'## {workstream["name"]}','','| ID / capability | Workstream / category | Description and scope | Dependencies / milestones | Implementation | Validation | Production readiness | Priority | Evidence / issues / PRs / main revision |','|---|---|---|---|---|---|---|---:|---|']
  for dom,item,kind in rows:
   if dom['id'] != workstream['id']: continue
   deps=', '.join(f'`{d}`' for d in item['dependencies']) or '—'; milestones=', '.join(item['milestones'])
   refs=', '.join(linked_evidence(x,sources) for x in item['evidence']) or '—'
   issues=', '.join(f'[#'+x[1:]+'](https://github.com/xdCloudy/minecraft-native-intelligence/issues/'+x[1:]+')' for x in item['relatedIssues']) or '—'
   prs=', '.join(f'[{x}]({next(p["url"] for p in data["unmergedWork"] if p["id"]==x)}) ({next(p["state"] for p in data["unmergedWork"] if p["id"]==x)})' for x in item['relatedPRs']) or '—'
   feature.append(f'| <a id="{item["id"].lower()}"></a>`{item["id"]}` {item["title"]} | {dom["name"]}<br>{item["category"]} | {item["description"]}<br>**Scope:** {item["scope"]} | **Depends:** {deps}<br>**Milestones:** {milestones} | {item["status"]["implementation"]} | {item["status"]["validation"]} | {item["status"]["productionReadiness"]} | {item["priority"]} | {refs}<br>Issues: {issues}<br>PRs (unmerged): {prs}<br>Main revision `{item["lastVerifiedRevision"]}` |')
  feature.append('')

 competency=['# Minecraft-specific competency matrix','',
  'Every listed scenario is a research and engineering target, not a demonstrated native-game skill. A generic movement or crafting interface does not establish competence on these mechanics.','']
 for group in sorted(COMPETENCY_GROUPS):
  competency += [f'## {group}','','| Item | Research objective | Acceptance scenario | Failure and legality boundary | Prerequisite / milestone | Research / implementation / validation | Evidence requirements |','|---|---|---|---|---|---|---|']
  for dom,item in gameplay_competencies(data):
   if item['competency']['group']!=group: continue
   gate=item['competency']
   refs=', '.join(linked_evidence(x,sources) for x in item['evidence'])
   competency.append(f'| [`{item["id"]}`](FEATURE_MATRIX.md#{item["id"].lower()}) {item["title"]} | {item["objective"]} | {gate["scenario"]} | {gate["failureBoundary"]} | {", ".join(item["dependencies"]) or "none"} / {", ".join(item["milestones"])} | {item["status"]["research"]} / {item["status"]["implementation"]} / {item["status"]["validation"]} | {gate["evidenceRequired"]}<br>{refs}<br>{item["limitations"]} |')
  competency.append('')
 competency+=['## Completion rule','','Require pinned Java Edition and loader versions, world seeds, ordinary Survival action outcomes, no-privilege instrumentation, raw successes and failures, and held-out generalization. Completing a parent item does not automatically complete individual mechanics.','']

 research=['# Research inventory','','Every avenue is independently scoped. “Not investigated” is used when a question is merely named or supported by contextual literature links. External papers are prior-work references, not MNI experimental outcomes.','']
 for dom in data['domains']:
  research += [f'## {dom["name"]}','',dom['description'],'','| ID / research question | Objective and scope | Approaches / alternatives | Prior work | Feasibility, limitations and compute | Method and completion criteria | Research / outcome | Evidence, conclusion and remaining work |','|---|---|---|---|---|---|---|---|']
  for item in dom['avenues']:
   links=', '.join(linked_evidence(x,sources) for x in item['priorWork']) or '—'
   research.append(f'| <a id="{item["id"].lower()}"></a>`{item["id"]}` {item["title"]}<br>{item["objective"]} | {item["description"]}<br>**Scope:** {item["scope"]} | {"; ".join(item["approaches"])} | {links} | **Benefits:** {item["benefit"]}<br>**Limits:** {item["limitations"]}<br>**Compute:** {item["computationalRequirements"]} | {item["methodology"]}<br>**Research 100% when:** {item["completionCriteria"]["research"]}<br>**Accept:** {"; ".join(item["acceptanceCriteria"])} | {item["status"]["research"]} / {item["status"]["experimentalOutcome"]} | **Evidence:** {", ".join(linked_evidence(x,sources) for x in item["evidence"])}<br>**Conclusion:** {item["conclusion"]}<br>**Remaining:** {item["remainingWork"]}<br>**Questions:** {"; ".join(item["openQuestions"])} |')
  research.append('')
 research+=['## Independent research portfolio','','Relevant prior work is inventoried by evidence ID and linked in avenue rows and the model/training comparison. References include MineRL, MineDojo, VPT, STEVE-1, Voyager, MineCLIP, Mindcraft, DreamerV3, hierarchical options, continual RL, curiosity, learned multi-agent communication, Minecraft construction planning, Transformers, Mamba, Switch Transformers, Decision Transformer, Diffusion Policy and D4RL. Citation does not imply code/data reuse or project validation; inspect each license and transfer limitation before adoption.','']

 model=['# Model architecture and training-method matrices','','No foundation model is selected. The matrix distinguishes theory/prior art from MNI outcomes. “Unknown” is preserved where parameter counts, active parameters, hardware needs, latency, throughput or licensing are not measured or source-pinned.','', '## Architecture candidates','', '| Candidate | Hypothesis / intended role | Architecture | Inputs → outputs | Parameters / active | Context and memory | Training / inference / hardware / quantization / latency / throughput | Generalization / grounding | Continual and multi-agent suitability | License / research and implementation status |','|---|---|---|---|---|---|---|---|---|---|---|']
 for mrow in data['modelCandidates']:
  refs=', '.join(linked_evidence(x,sources) for x in mrow['evidence'])
  model.append(f'| `{mrow["id"]}` {mrow["name"]} | {mrow["objective"]} | {mrow["family"]}<br>{mrow["architecture"]} | {"; ".join(mrow["inputModalities"])} → {"; ".join(mrow["outputModalities"])} | {mrow["parameterCount"]}<br>Active: {mrow["activeParameterCount"]} | {mrow["contextMemory"]} | **Training:** {mrow["trainingRequirements"]}<br>**Inference:** {mrow["inferenceRequirements"]}<br>**Quantization:** {mrow["quantization"]}<br>**Latency:** {mrow["latency"]}; **throughput:** {mrow["throughput"]} | {mrow["generalization"]}<br>{mrow["grounding"]} | {mrow["continualLearning"]}<br>{mrow["multiAgentScalability"]} | {mrow["licenseAndRedistribution"]}<br>Research `{mrow["status"]["research"]}`; outcome `{mrow["status"]["experimentalOutcome"]}`; implementation `{mrow["status"]["implementation"]}`<br>{refs}<br>Decision: {mrow["decisionStatus"]}; {mrow["limitations"]} |')
 model+=['','## Training and learning methods','','Memory/retrieval adaptation is not model training. Parameter updates, synthetic environments and shared model updates require separate data governance, retention and rollback evidence.','', '| Method | Hypothesis / objective | Prior work | Approaches / alternatives | Data, compute and methodology | Evaluation and acceptance | Research / outcome / implementation / validation / readiness | Evidence, limitations, remaining work |','|---|---|---|---|---|---|---|---|']
 for tr in data['trainingMethods']:
  refs=', '.join(linked_evidence(x,sources) for x in tr['evidence'])
  statuses=' / '.join(tr['status'][key] for key in ('research','experimentalOutcome','implementation','validation','productionReadiness'))
  model.append(f'| `{tr["id"]}` {tr["name"]} | {tr["objective"]} | {", ".join(linked_evidence(x,sources) for x in tr["priorWork"])} | {"; ".join(tr["alternatives"])} | {tr["dataAndCompute"]}<br>{tr["methodology"]} | {"; ".join(tr["evaluation"])}<br>**Accept:** {"; ".join(tr["acceptanceCriteria"])} | {statuses} | {refs}<br>**Limits:** {tr["limitations"]}<br>**Remaining:** {tr["remainingWork"]} |')
 model+=['','## Matched comparison protocol','','Pin exact code, model/checkpoint, data and licenses, environment, observations/actions, configuration, seeds, model context, compute/hardware and inference runtime. Compare shared-model-plus-persistent-individual-memory against independent-model controls. Include memory-only, retrieval, supervised, offline/online RL and from-scratch baselines where applicable. Report held-out generalization, grounding, capability, retention, identity isolation, p50/p95/p99 latency, throughput and cost separately.','']

 readiness=['# Experiment, compatibility and production-readiness matrix','','## Experiment records','','A recorded experiment is not automatically a positive result or integrated capability. External runs may count as research evidence when exact revisions, environment, versions, configuration, seeds, hardware, artifacts and reproduction steps are available; unmerged results never receive main implementation credit.','', '| Record / tracked item | Research state / outcome | Revision / branch | Environment / Minecraft / model / dataset | Configuration / seeds / hardware | Method / raw results / reproduction / limitations |','|---|---|---|---|---|---|']
 for r in data['experimentRecords']:
  readiness.append(f'| `{r["id"]}` / `{r["trackedItemId"]}` | {r["status"]} / **{r["outcome"]}**; independent assessment: {r["independentAssessment"]} | `{r["revision"]}` / {r.get("branch","main")} / {r.get("sourcePR","main baseline")} | {r["environment"]}; {r["minecraftVersion"]}; {r["modelVersion"]}; {r["datasetVersion"]} | {r["configuration"]}; seeds {r["seeds"]}; {r["hardware"]} | {r["methodology"]}; [{r["rawResults"]}]({r["rawResults"]}); {r["reproduction"]}; {r["limitations"]} |')
 readiness+=['','## Compatibility matrix','','| Cell | Loader / version | Server mode | Client | Status | Evidence / limitation |','|---|---|---|---|---|---|']
 for cell in data['compatibilityCells']:readiness.append(f'| `{cell["id"]}` | {cell["loader"]}; {cell["minecraftVersion"]} | {cell["serverMode"]} | {cell["clientMode"]} | {cell["status"]} | {", ".join(linked_evidence(x,sources) for x in cell["evidence"])}<br>{cell["notes"]} |')
 readiness+=['','## Production readiness gates','','Per-item readiness advances only when declared acceptance evidence is present. `CI validated` does not imply integrated capability; `integrated into main` requires main-revision provenance. `Production validated` requires installation/update/rollback, compatibility, player-equivalent mechanics, in-game validation, security/privacy/consent, runtime reliability, monitoring/resource budgets, recovery and user/operator documentation as applicable.','', '| Readiness concern | Current state on main | Required evidence to advance |','|---|---|---|']
 for title,req in [('Packaging and installation','Installable release artifact, pinned compatibility matrix and clean install/update/uninstall tests.'),('Integrated/dedicated servers and clients','In-game tests on each declared server mode and compatible vanilla client presentation.'),('Survival and information parity','Server-authoritative tests for movement, reach, inventory, crafting, damage, death/respawn and no hidden-state access.'),('Security, privacy, consent and licensing','Threat cases, operator controls, data provenance/consent/deletion and dependency/model/dataset licence audit.'),('Reliability, monitoring and recovery','Long-run restarts, fault containment, backups, resource/tick budgets, metrics and recovery drills.'),('Agent capability','Reproducible held-out Minecraft scenarios showing acquired behavior and excluding scripted/privileged execution.')]:readiness.append(f'| {title} | No production-ready Minecraft-native agent capability recorded on main. | {req} |')
 readiness+=['','## Rejected, deferred and out-of-scope approaches','','| ID | Approach | Decision | Evidence-based rationale |','|---|---|---|---|']
 for r in data['rejectedApproaches']:readiness.append(f'| `{r["id"]}` | {r["approach"]} | {r["status"]} | {r["reason"]} |')
 readiness+=['','## Open questions and blockers','','Outstanding questions are grouped by workstream; these rows describe future work, not verified capability.','']
 for workstream in data['domains']:
  workstream_blockers=[(dom,item) for dom,item,kind in rows if dom['id']==workstream['id'] and (item['remainingWork'] or item['openQuestions'])]
  if not workstream_blockers: continue
  readiness += [f'### {workstream["name"]}','','| ID | Remaining question/work | Workstream | Dependencies | Acceptance criteria |','|---|---|---|---|---|']
  for dom,item in workstream_blockers:
   question='; '.join(item.get('openQuestions',[])[:2])
   readiness.append(f'| `{item["id"]}` | {item["remainingWork"]}; {question} | {dom["name"]} | {", ".join(item["dependencies"]) or "—"} | {"; ".join(item["acceptanceCriteria"])} |')
  readiness.append('')
 readiness+=['## Historical unmerged pull requests','',f"Audited main {data['assessment']['defaultBranchRevision']}. {sum(pr['state']=='open' for pr in data['unmergedWork'])} tracked PRs remain open; {sum(pr['state']=='closed' for pr in data['unmergedWork'])} were closed without merging. Historical head/base revisions, reviewed paths and check snapshots are preserved. Stacked-branch success does not imply main integration. All records are excluded from shipped capability credit.",'', '| PR / state / branch | Historical base → head | Review summary and files | Affected items | Historical check snapshot |','|---|---|---|---|---|']
 for pr in data['unmergedWork']:
  files='<br>'.join(f'`{f}`' for f in pr['reviewedFiles']); checks='; '.join(f'{c["name"]}: {c["conclusion"]} ({c["completedAt"]})' for c in pr['checks'])
  readiness.append(f'| [#{pr["id"][3:]}]({pr["url"]}) {pr["state"]} `{pr["head"]}` (draft={str(pr["draft"]).lower()}) | `{pr["base"]}` `{pr["baseRevision"]}` → `{pr["headRevision"]}` | {pr["changeSummary"]}<br>{files} | {", ".join(f"`{x}`" for x in pr["affectedAvenues"])} | run `{pr["latestCheckRun"]}` at {pr["checkSnapshotAt"]}: {checks}<br>Integrated: no; shipped: no |')

 return {
  ROOT/'docs/PROGRESS.md':'\n'.join(overview),ROOT/'docs/FEATURE_MATRIX.md':'\n'.join(feature),ROOT/'docs/MINECRAFT_COMPETENCY_MATRIX.md':'\n'.join(competency),ROOT/'docs/RESEARCH_MATRIX.md':'\n'.join(research),ROOT/'docs/MODEL_TRAINING_MATRIX.md':'\n'.join(model),ROOT/'docs/PRODUCTION_READINESS.md':'\n'.join(readiness),
  ROOT/'README.md':None,ROOT/'ROADMAP.md':None
 }

def final_outputs(data,outputs):
 readme=ROOT/'README.md';road=ROOT/'ROADMAP.md';m=metrics(data);current=current_milestone(data)
 dash=['### Live research and engineering progress','',f"**{len(data['domains'])} workstreams · {len(all_items(data))} tracked research/engineering items · current milestone: {current['id']} {current['name']}.** The dashboard reflects evidence on the assessed main revision. No intelligent Minecraft-native agent has been demonstrated.",'','| Progress dimension | Current |','|---|---:|']
 for key,label in [('researchCoverage','Research coverage'),('researchCompletion','Research completion'),('modelResearch','Model architecture research'),('trainingResearch','Training-method research'),('experimentalEffectiveness','Experimental effectiveness'),('demonstratedCapabilities','Demonstrated capabilities'),('implementationMaturity','Implementation maturity'),('validationCoverage','Validation coverage'),('productionReadiness','Production readiness'),('overallScopedProgress','Overall scoped progress')]:dash.append(f'| {label} | {pct(m[key])} |')
 dash+=['',f"**Minecraft-specific competency scenarios inventoried: {len(gameplay_competencies(data))}.** Each remains unproven until independently evaluated in-game. A full catalog is not a guarantee that every possible mechanic has been enumerated.",'','**Main gaps:** no integrated Minecraft agent mod, player embodiment, Survival-parity in-game validation, selected foundation architecture or demonstrated learning/autonomy. Historical unmerged PRs are displayed separately and do not count as integrated.','', '[Full progress dashboard](docs/PROGRESS.md) · [Feature matrix](docs/FEATURE_MATRIX.md) · [Minecraft competency matrix](docs/MINECRAFT_COMPETENCY_MATRIX.md) · [Research inventory](docs/RESEARCH_MATRIX.md) · [Model and training matrices](docs/MODEL_TRAINING_MATRIX.md) · [Experiment and production readiness](docs/PRODUCTION_READINESS.md) · [Scoring and maintenance workflow](docs/PROGRESS_WORKFLOW.md)','']
 outputs[readme]=update_marked(readme.read_text(encoding='utf-8'),README_START,README_END,'\n'.join(dash),'README')
 roadmap_lines=['','| Milestone | Status | Gate progress | Evidence gates met |','|---|---|---:|---:|']
 for mile in data['milestones']:
  met=sum(c['status']=='met' for c in mile['criteria']);roadmap_lines.append(f'| {mile["id"]} — {mile["name"]} | {mile["status"]} | {pct(milestone_score(data,mile))} | {met}/{len(mile["criteria"])} |')
 outputs[road]=update_marked(road.read_text(encoding='utf-8'),ROADMAP_START,ROADMAP_END,'\n'.join(roadmap_lines),'ROADMAP')
 planned={p.resolve() for p in outputs}
 for path,content in outputs.items():
  for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)',content):
   if target.startswith(('https://','http://','mailto:','#')):continue
   rel=unquote(target.split('#',1)[0]);need(bool(rel),f'{path.relative_to(ROOT)}: empty Markdown link')
   resolved=(path.parent/rel).resolve();need(resolved.exists() or resolved in planned,f'{path.relative_to(ROOT)}: broken generated link {target}')
 return outputs

def apply_outputs(outputs,check=False):
 stale=[]
 for path,content in outputs.items():
  if not content.endswith('\n'): content += '\n'
  if not path.exists() or path.read_text(encoding='utf-8')!=content:
   stale.append(path)
   if not check:path.write_text(content,encoding='utf-8',newline='\n')
 return stale

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=['validate','generate','check'],nargs='?',default='validate');parser.add_argument('--check',action='store_true',help='alias for check');args=parser.parse_args();command='check' if args.check else args.command
 try:
  data=json.loads(DATA.read_text(encoding='utf-8'));schema=json.loads(SCHEMA.read_text(encoding='utf-8'));items,evidence,milestones=validate(data,schema)
  if command=='validate':
   m=metrics(data);print(f'Valid: {len(data["domains"])} workstreams, {sum(len(x["avenues"]) for x in data["domains"])} avenues, {len(data["modelCandidates"])} model candidates, {len(data["trainingMethods"])} training methods, {len(items)} scored items; coverage {pct(m["researchCoverage"])}');return 0
  outputs=final_outputs(data,render(data));stale=apply_outputs(outputs,check=command=='check')
  if command=='check' and stale:
   for path in stale:print(f'stale generated output: {path.relative_to(ROOT)}',file=sys.stderr)
   return 1
  print('Generated output is current.' if not stale else f'Updated {len(stale)} deterministic files.');return 0
 except (OSError,json.JSONDecodeError,InvalidProgress,KeyError,TypeError,ValueError) as exc:
  print(f'progress {command} failed: {exc}',file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
