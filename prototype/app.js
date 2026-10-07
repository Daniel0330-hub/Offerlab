const rawJobs = window.OFFERLAB_DATA?.jobs || [];
const selected = new Set(JSON.parse(sessionStorage.getItem('offerlab-selected') || '[]'));
const pages = ['profile', 'discover', 'compare', 'evaluate'];
let annotations = JSON.parse(sessionStorage.getItem('offerlab-annotations') || '{}');
const degreeRank = {'大专': 1, '本科': 2, '硕士研究生': 3, '硕士': 3, '博士研究生': 4, '博士': 4};
const synonymGroups = [
  ['ai','人工智能','智能算法','机器学习','深度学习','大模型','生成式ai'], ['大模型','llm','语言模型','生成式ai'],
  ['ai产品','ai 产品','人工智能产品','智能产品','ai产品经理','人工智能产品经理'],
  ['智能体','agent','ai代理','多智能体'], ['需求','用户需求','客户需求','需求调研','需求分析','业务需求'],
  ['方案','解决方案','产品方案','技术方案'], ['交付','实施','落地','上线','验收','投产'],
  ['运维','系统运维','运行维护','巡检','故障处理','稳定运行'], ['网络安全','信息安全','安全','攻防','渗透测试'],
  ['数据治理','数据质量','元数据','数据标准','数据口径','数据可靠性'], ['数据中台','大数据平台','数据平台'],
  ['算法','模型','机器学习','深度学习'], ['部署','工程化','产品化','落地'], ['项目','项目管理','项目实施'],
  ['计算机视觉','图像识别','视觉算法','cv'], ['研发','开发','研制'], ['新媒体','内容运营','社交媒体','全媒体'],
  ['私域','会员运营','用户运营','社群运营'], ['用户分层','用户画像','读者标签','人群分层'],
  ['音视频','媒体制作','视频剪辑','后期制作'], ['数据库','行业数据库','数据整理'],
  ['物联网','aiot','智能终端','智能设备'], ['rag','知识库','知识库问答','检索增强'], ['适航','准入认证','适航审定']
  ,['sql','数据库查询','数据提取','数据分析','数据处理'], ['python','编程','数据处理','自动化脚本'],
  ['c/c++','c++','cpp','c语言','c语言与c++'], ['c语言','c language','c程序设计'],
  ['统计学','统计分析','统计建模','数据分析'], ['精算学','风险分析','统计建模','数据分析'],
  ['大数据','数据科学与大数据技术','数据分析','数据工程','数据平台'], ['人工智能专业','人工智能','机器学习','模型训练']
].map(group => group.map(x => x.toLowerCase()));

const abilityRules=[
  {tests:[/\bsql\b/i],abilities:['数据查询','基础数据分析','数据库基础'],source:'技能 SQL',confidence:'高'},
  {tests:[/\bpython\b/i],abilities:['编程基础','数据处理','自动化脚本'],source:'技能 Python',confidence:'高'},
  {tests:[/pandas|numpy|数据清洗/i],abilities:['数据清洗','数据处理','基础数据分析'],source:'项目或技能证据',confidence:'高'},
  {tests:[/scikit-learn|sklearn|机器学习/i],abilities:['机器学习','模型训练与评估'],source:'项目或技能证据',confidence:'高'},
  {tests:[/统计学|应用统计/i],abilities:['统计分析','统计建模','数据分析'],source:'统计学专业',confidence:'中'},
  {tests:[/精算/i],abilities:['风险分析','统计建模','数据分析'],source:'精算专业',confidence:'中'},
  {tests:[/大数据|数据科学/i],abilities:['数据分析','数据工程基础','数据平台基础'],source:'大数据/数据科学专业',confidence:'中'},
  {tests:[/人工智能|智能科学/i],abilities:['人工智能基础','机器学习基础','模型训练基础'],source:'人工智能相关专业',confidence:'中'},
  {tests:[/计算机|软件工程/i],abilities:['编程基础','软件开发基础','系统设计基础'],source:'计算机/软件专业',confidence:'中'},
  {tests:[/信息管理|管理科学与工程/i],abilities:['需求分析','数据分析','业务流程理解'],source:'信息管理相关专业',confidence:'中'},
  {tests:[/需求调研|用户访谈|需求分析/i],abilities:['需求分析','用户研究','产品方案'],source:'项目或技能证据',confidence:'高'},
  {tests:[/axure|figma|原型/i],abilities:['原型设计','产品表达'],source:'工具或项目证据',confidence:'高'},
  {tests:[/java|spring/i],abilities:['Java开发','后端开发基础'],source:'Java相关技能',confidence:'高'},
  {tests:[/c\+\+|\bcpp\b/i],abilities:['C++开发','系统编程基础'],source:'C++相关技能',confidence:'高'},
  {tests:[/c语言|c language/i],abilities:['C语言开发','系统编程基础'],source:'C语言相关技能',confidence:'高'},
  {tests:[/linux|运维|故障处理/i],abilities:['系统运维基础','故障定位'],source:'运维相关证据',confidence:'高'},
  {tests:[/网络安全|信息安全|渗透/i],abilities:['网络安全基础','安全测试'],source:'安全相关证据',confidence:'高'}
];
const majorGroups=[
  ['统计学','应用统计','数学','精算学','数据科学与大数据技术'],
  ['计算机科学与技术','软件工程','人工智能','智能科学与技术','数据科学与大数据技术','信息管理与信息系统'],
  ['电子信息','通信工程','信息工程','计算机科学与技术'],
  ['金融学','经济学','精算学','保险学','统计学'],
  ['自动化','控制科学与工程','电气工程及其自动化']
].map(x=>x.map(y=>y.toLowerCase()));
function majorRelated(a,b){const x=a.toLowerCase(),y=b.toLowerCase();if(x.includes(y)||y.includes(x))return true;return majorGroups.some(g=>g.some(v=>x.includes(v))&&g.some(v=>y.includes(v)))}

function esc(value='') { return String(value).replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c])); }
function splitList(value='') { return value.split(/[、,，;；\n]+/).map(x => x.trim()).filter(Boolean); }
function normalizeSkills(value='') {const items=splitList(value),text=String(value);if(/c\+\+/i.test(text))items.push('C++');if(/C语言|c language/i.test(text))items.push('C语言');return [...new Set(items)];}
function flatten(value) { return Array.isArray(value) ? value.join(' ') : String(value ?? ''); }
function itemText(items, keys) { return (items || []).flatMap(item => keys.map(k => flatten(item[k]))).join(' ').toLowerCase(); }
function jobFields(job) {
  return {
    title: job.title.toLowerCase(),
    responsibility: itemText(job.responsibilities, ['normalized_label','evidence_span']),
    skill: itemText(job.skills, ['raw_name','normalized_name','evidence_span']),
    domain: itemText(job.base_requirements, ['value','evidence_span'])
  };
}
function fullText(job) { return Object.values(jobFields(job)).join(' '); }
function expand(term) {
  const t = term.toLowerCase(); const out = new Set([t]);
  synonymGroups.forEach(group => { if (group.includes(t)) group.forEach(x => out.add(x)); });
  return out;
}
function grams(text) {
  text = text.toLowerCase().replace(/\s+/g,'');
  const chinese = (text.match(/[\u4e00-\u9fff]/g) || []).join('');
  const result = [];
  [2,3,4].forEach(n => { for(let i=0;i<=chinese.length-n;i++) result.push(chinese.slice(i,i+n)); });
  result.push(...(text.match(/[a-z][a-z0-9+#./-]*/g) || []));
  return result;
}
function counter(values) { const c={}; values.forEach(x => c[x]=(c[x]||0)+1); return c; }
const documents = rawJobs.map(job => new Set(grams(fullText(job))));
const df = {}; documents.forEach(doc => doc.forEach(x => df[x]=(df[x]||0)+1));
function vector(text) {
  const counts=counter(grams(text)); const out={}; const n=rawJobs.length;
  Object.entries(counts).forEach(([token,count]) => out[token]=(1+Math.log(count))*(Math.log((n+1)/((df[token]||0)+1))+1));
  return out;
}
function cosine(a,b) {
  let num=0,da=0,db=0; Object.values(a).forEach(v=>da+=v*v); Object.values(b).forEach(v=>db+=v*v);
  Object.entries(a).forEach(([k,v])=>{if(b[k])num+=v*b[k]}); return da&&db?num/Math.sqrt(da*db):0;
}
const jobVectors = Object.fromEntries(rawJobs.map(job => [job.job_id, vector(fullText(job))]));
function coverage(terms, text) {
  if(!terms.length) return 0;
  return terms.filter(term => [...expand(term)].some(x => text.includes(x))).length / terms.length;
}
function lexical(job,terms) {
  const f=jobFields(job); return .4*coverage(terms,f.responsibility)+.35*coverage(terms,f.skill)+.15*coverage(terms,f.domain)+.1*coverage(terms,f.title);
}
function tokenizeQuery(query) {
  const chunks=splitList(query.replace(/\s+/g,'、'));
  return chunks.length ? chunks : [query.trim()].filter(Boolean);
}
function classify(job) {
  const text=fullText(job);
  const rules=[['AI与算法',['大模型','智能体','机器学习','算法','人工智能','计算机视觉']],['产品与解决方案',['产品','需求分析','解决方案','用户研究','原型']],['数据分析与治理',['数据分析','经营分析','数据治理','数据质量','统计','数据库']],['软件与平台开发',['软件开发','系统开发','java','python','前端','后端','平台研发']],['运维与网络安全',['运维','网络安全','信息安全','云平台','devops']],['测试与质量',['测试','质量监督','适航']],['工程研发',['工程师','研发','设计师']],['业务与运营',['运营','市场','研究员','项目执行']]];
  return rules.find(([,words])=>words.some(w=>text.includes(w)))?.[0] || '其他方向';
}
const jobs = rawJobs.map(job => ({...job, family: classify(job)}));

function getProfile() {
  return {
    graduationYear:Number(document.getElementById('graduation-year').value)||2027,
    degree:document.getElementById('degree').value,
    majors:[document.getElementById('major-master').value,document.getElementById('major-bachelor').value].filter(Boolean),
    locations:splitList(document.getElementById('preferred-locations').value),
    rotation:document.getElementById('rotation').value,
    skills:normalizeSkills(document.getElementById('skills').value),
    experience:document.getElementById('experience').value,
    directions:[...document.querySelectorAll('#direction-chips .chip.selected')].map(x=>x.textContent.trim())
  };
}
function saveProfile() { const p=getProfile(); sessionStorage.setItem('offerlab-profile',JSON.stringify(p)); return p; }
function restoreProfile() {
  const p=JSON.parse(sessionStorage.getItem('offerlab-profile')||'null'); if(!p)return;
  document.getElementById('graduation-year').value=p.graduationYear; document.getElementById('degree').value=p.degree;
  document.getElementById('major-master').value=p.majors?.[0]||''; document.getElementById('major-bachelor').value=p.majors?.[1]||'';
  document.getElementById('preferred-locations').value=(p.locations||[]).join('、'); document.getElementById('rotation').value=p.rotation;
  document.getElementById('skills').value=(p.skills||[]).join('、'); document.getElementById('experience').value=p.experience||'';
  document.querySelectorAll('#direction-chips .chip').forEach(chip=>chip.classList.toggle('selected',(p.directions||[]).includes(chip.textContent.trim())));
}
function profileQuery() { const p=getProfile(); return [...p.majors,...p.directions,...p.skills].join(' '); }

function inferAbilities(profile) {
  const explicit=[...profile.skills].map(name=>({name,kind:'explicit',source:'用户填写技能',confidence:'明确'}));
  const hay=[...profile.majors,...profile.skills,profile.experience,...profile.directions].join(' ');
  const inferred=[];
  abilityRules.forEach(rule=>{if(rule.tests.some(r=>r.test(hay)))rule.abilities.forEach(name=>inferred.push({name,kind:'inferred',source:rule.source,confidence:rule.confidence}))});
  const explicitNames=new Set(explicit.map(x=>x.name.toLowerCase())); const seen=new Set();
  return {explicit,inferred:inferred.filter(x=>!explicitNames.has(x.name.toLowerCase())&&!seen.has(x.name)&&(seen.add(x.name),true))};
}
function allProfileAbilities(profile){const a=inferAbilities(profile);return [...a.explicit,...a.inferred].map(x=>x.name)}
function renderAbilityInference(){
  const root=document.getElementById('ability-inference');if(!root)return;const abilities=inferAbilities(getProfile());
  root.innerHTML=`<strong>系统识别的可迁移能力</strong><p>${abilities.inferred.map(x=>`<span class="status risk" title="${esc(x.source)} · ${esc(x.confidence)}置信度">${esc(x.name)} · ${esc(x.source)}</span>`).join(' ')||'继续填写专业、技能或项目证据后生成'}</p><small>推断能力用于召回与优势解释；具体工具只有用户填写或项目明确出现时才视为已掌握。</small>`;
}

function profileSignals(profile) {
  return {
    directions: profile.directions,
    skills: allProfileAbilities(profile),
    experience: tokenizeQuery(profile.experience),
    majors: profile.majors,
    locations: profile.locations
  };
}

function profileMatch(job, profile, typedQuery='') {
  const f=jobFields(job); const signals=profileSignals(profile);
  const responsibilityAndTitle=`${f.responsibility} ${f.title}`;
  const direction=.75*coverage(signals.directions,responsibilityAndTitle)+.25*coverage(signals.directions,f.domain);
  const skill=.65*coverage(signals.skills,`${f.skill} ${f.responsibility}`)+.35*coverage(signals.skills,f.title);
  const experience=coverage(signals.experience,`${f.responsibility} ${f.skill}`);
  const major=coverage(signals.majors,`${f.domain} ${f.responsibility} ${f.title}`);
  const location=signals.locations.length&&signals.locations.some(l=>job.locations.some(x=>String(x).includes(l)))?1:0;
  let score=.40*direction+.30*skill+.15*experience+.10*major+.05*location;
  const productOnly=profile.directions.includes('AI 产品')&&!profile.directions.some(x=>['软件开发','算法工程','数据开发','系统运维'].includes(x));
  const productEvidence=/产品经理|产品管理|产品规划|产品设计|产品全生命周期|需求分析|需求调研|用户研究|竞品分析/.test(`${f.title} ${f.responsibility}`);
  if(productOnly&&!productEvidence)score*=.35;
  let typed=0;
  if(typedQuery.trim()){
    const terms=tokenizeQuery(typedQuery); typed=.3*lexical(job,terms)+.7*cosine(vector(typedQuery),jobVectors[job.job_id]);
    score=.75*score+.25*typed;
  }
  const reasons=[['目标方向',direction],['技能',skill],['项目经历',experience],['专业',major],['地点',location],['主动搜索',typed]].filter(([,v])=>v>0).sort((a,b)=>b[1]-a[1]).slice(0,3).map(([k,v])=>`${k} ${Math.round(v*100)}%`);if(productOnly&&!productEvidence)reasons.push('缺少产品/需求职责，已降权');
  return {score,components:{direction,skill,experience,major,location,typed},reasons};
}

function requirementValue(job, criterion) { return (job.base_requirements||[]).filter(x=>x.criterion===criterion); }
function qualification(job, profile) {
  const checks=[]; let failed=false, unknown=false;
  const years=requirementValue(job,'graduation_year');
  if(years.length){const values=years.flatMap(x=>Array.isArray(x.value)?x.value:[x.value]).map(Number);const ok=values.includes(profile.graduationYear);checks.push(`${ok?'✓':'×'} 毕业年份${ok?'符合':'不符'}`);failed ||= !ok;}
  const degrees=requirementValue(job,'degree');
  if(degrees.length){const needed=degrees[0].value;const ok=(degreeRank[profile.degree]||0)>=(degreeRank[needed]||0);checks.push(`${ok?'✓':'×'} 学历${ok?'符合':'不符'}`);failed ||= !ok;}
  const majors=requirementValue(job,'major');
  if(majors.length){
    const required=majors.some(x=>x.requirement_level==='required');
    const wanted=majors.flatMap(x=>Array.isArray(x.value)?x.value:[x.value]).map(x=>String(x).toLowerCase());
    const ok=profile.majors.some(m=>wanted.some(w=>majorRelated(m,w)));
    checks.push(`${ok?'✓':required?'×':'△'} 专业${ok?'命中':required?'未命中':'为优先项'}`); failed ||= required&&!ok; unknown ||= !required&&!ok;
  }
  const language=(job.other_explicit_conditions||[]).filter(x=>x.criterion==='language');
  if(language.length){checks.push('△ 语言条件需人工确认');unknown=true;}
  return {label:failed?'存在硬性差距':unknown?'部分待确认':'基础条件符合',className:failed?'fail':unknown?'risk':'pass',checks};
}
function skillAnalysis(job,profile) {
  const abilityProfile=inferAbilities(profile); const explicitHay=[...profile.skills,profile.experience].join(' ').toLowerCase(); const inferredHay=abilityProfile.inferred.map(x=>x.name).join(' ').toLowerCase(); const covered=[],inferred=[],missing=[];
  (job.skills||[]).forEach(skill=>{
    const name=skill.normalized_name||skill.raw_name; const forms=expand(String(name));
    if([...forms].some(x=>explicitHay.includes(x)))covered.push(name);
    else if([...forms].some(x=>inferredHay.includes(x)))inferred.push(name);
    else missing.push(name);
  });
  const advantages=[...new Set([...covered,...inferred])].slice(0,6);
  return {covered:[...new Set(covered)].slice(0,6),inferred:[...new Set(inferred)].slice(0,6),advantages,missing:[...new Set(missing)].slice(0,6)};
}
function matchedEvidence(job,terms) {
  const items=[...(job.responsibilities||[]),...(job.skills||[])];
  const hits=items.filter(item=>{const t=(item.evidence_span||'').toLowerCase();return terms.some(term=>[...expand(term)].some(x=>t.includes(x)))});
  return (hits.length?hits:job.responsibilities||[]).slice(0,2).map(x=>x.evidence_span);
}
function scoreJobs(typedQuery='') {
  const profile=getProfile(); const evidenceTerms=tokenizeQuery(`${typedQuery} ${profileQuery()}`);
  return jobs.map(job=>{
    const match=profileMatch(job,profile,typedQuery); const qual=qualification(job,profile);
    const score=qual.className==='fail'?match.score*.15:match.score;
    return {...job,_score:score,_components:match.components,_matchReasons:match.reasons,_qualification:qual,_skills:skillAnalysis(job,profile),_evidence:matchedEvidence(job,evidenceTerms)};
  }).sort((a,b)=>b._score-a._score||a.title.localeCompare(b.title,'zh-CN'));
}
function matchBand(score,index) { if(index<5&&score>0)return ['优先查看','high']; if(index<15&&score>0)return ['相关候选','medium']; return ['扩展发现','low']; }

function populateFilters() {
  const company=document.getElementById('company-filter'); [...new Set(jobs.map(x=>x.parent_group))].sort().forEach(x=>company.insertAdjacentHTML('beforeend',`<option value="${esc(x)}">${esc(x)}</option>`));
  const location=document.getElementById('location-filter'); const locs=[...new Set(jobs.flatMap(x=>x.locations).flatMap(x=>String(x).split(/[、,，/]/)).map(x=>x.trim()).filter(Boolean))].sort(); locs.forEach(x=>location.insertAdjacentHTML('beforeend',`<option value="${esc(x)}">${esc(x)}</option>`));
  const family=document.getElementById('family-filter'); [...new Set(jobs.map(x=>x.family))].sort().forEach(x=>family.insertAdjacentHTML('beforeend',`<option value="${esc(x)}">${esc(x)}</option>`));
}
function currentQuery() { return document.getElementById('query').value.trim(); }
function inPreferredLocations(job,profile=getProfile()){return !profile.locations.length||profile.locations.some(l=>job.locations.some(x=>String(x).includes(l)))}
function search() {
  const typed=currentQuery(); const company=document.getElementById('company-filter').value; const location=document.getElementById('location-filter').value; const family=document.getElementById('family-filter').value; const scope=document.getElementById('scope-filter').value;
  const profile=getProfile();const pool=scoreJobs(typed).filter(job=>(company==='all'||job.parent_group===company)&&(location==='all'?scope==='all'||inPreferredLocations(job,profile):job.locations.some(x=>String(x).includes(location)))&&(family==='all'||job.family===family));
  const maxScore=pool[0]?._score||0;
  const ranked=scope==='matched'?pool.filter((job,index)=>job._qualification.className!=='fail'&&job._score>=Math.max(.035,maxScore*.20)&&index<40):pool;
  document.getElementById('active-query').textContent=typed?`主动搜索：${typed}；75%画像匹配 + 25%搜索意图`:`实时画像：${profileQuery()}`;
  renderJobs(ranked,pool.length,scope==='matched');
}
function renderJobs(list,totalPool=list.length,prefiltered=false) {
  const profile=getProfile(); const root=document.getElementById('job-list');
  root.innerHTML=list.map((job,index)=>{const [band,bandClass]=matchBand(job._score,index);const preferred=profile.locations.some(l=>job.locations.some(x=>String(x).includes(l)));
    return `<article class="job-card"><div><div class="job-meta">${esc(job.parent_group)} · ${esc(job.company)} · ${esc(job.locations.join('、'))}</div><div class="title-line"><h2>${esc(job.title)}</h2><span class="match-band ${bandClass}">${band}</span>${preferred?'<span class="location-hit">地点符合</span>':''}</div><div class="reason"><strong>画像匹配依据</strong>${job._matchReasons.map(esc).join('；')||'当前画像只有弱相关信号'}<br><strong>岗位优势</strong>${esc(job._skills.advantages.join('、')||'暂无明确技能优势')}<br><strong>JD原文证据</strong>${job._evidence.map(esc).join('；')||'请查看完整职责证据'}</div><div class="status-row"><span class="status ${job._qualification.className}">${job._qualification.label}</span><span class="status ${job._skills.missing.length?'risk':'pass'}">技能缺口：${esc(job._skills.missing.join('、')||'暂未发现')}</span><span class="source-badge">真实JD</span></div></div><div class="job-actions"><button class="detail" data-detail="${esc(job.job_id)}">查看证据</button><a class="source-button" href="${esc(job.source?.url||'#')}" target="_blank" rel="noopener noreferrer">查看原版JD ↗</a><button class="${selected.has(job.job_id)?'remove':'add'}" data-toggle="${esc(job.job_id)}">${selected.has(job.job_id)?'移出比较':'加入比较'}</button><span class="score-note">画像综合分 ${Math.round(job._score*100)} · 职责技能优先</span></div></article>`}).join('');
  document.getElementById('result-total').textContent=prefiltered?`从 ${totalPool} 个岗位中预筛选出 ${list.length} 个 · ${new Set(list.map(x=>x.parent_group)).size} 家集团`:`${list.length} 个岗位 · 共 ${new Set(list.map(x=>x.parent_group)).size} 家集团`;
  document.getElementById('result-note').textContent=prefiltered?'已综合专业、目标方向、技能及硬性资格，并按画像工作地点筛选':'正在查看当前筛选条件下的全部岗位';
  document.getElementById('empty-state').classList.toggle('hidden',list.length>0);
}

function showPage(name){pages.forEach(p=>document.getElementById(`page-${p}`).classList.toggle('active',p===name));document.querySelectorAll('[data-page]').forEach(b=>b.classList.toggle('active',b.dataset.page===name));if(name==='discover')search();if(name==='compare')renderCompare();if(name==='evaluate')renderEvaluation();window.scrollTo({top:0,behavior:'smooth'});}
function findJob(id){return scoreJobs(currentQuery()).find(x=>x.job_id===id)}
function openDrawer(id) {
  const job=findJob(id); if(!job)return; const source=job.source?.url||'#';
  document.getElementById('drawer-content').innerHTML=`<p class="eyebrow">岗位证据详情</p><h1>${esc(job.title)}</h1><p>${esc(job.parent_group)} · ${esc(job.company)} · ${esc(job.locations.join('、'))}</p><div class="reason"><strong>为什么找到</strong>${job._matchReasons.map(esc).join('；')}<br>${job._evidence.map(esc).join('；')}</div><h3>相对优势</h3><div class="evidence">明确技能：${esc(job._skills.covered.join('、')||'暂无')}<br>专业/相关技能推断：${esc(job._skills.inferred.join('、')||'暂无')}</div><h3>需要补充</h3><div class="evidence">${esc(job._skills.missing.join('、')||'暂未发现明确技能缺口')}</div><h3>基础资格核对</h3>${job._qualification.checks.map(x=>`<div class="evidence">${esc(x)}</div>`).join('')||'<div class="evidence">JD未给出可结构化的硬性资格</div>'}<h3>岗位职责原文证据</h3>${job.responsibilities.map(x=>`<div class="evidence"><b>${esc(x.normalized_label)}</b><br>${esc(x.evidence_span)}</div>`).join('')}<h3>技能与画像覆盖</h3><table class="skill-table"><tr><th>JD技能</th><th>级别</th><th>你的证据</th></tr>${job.skills.map(x=>{const name=x.normalized_name||x.raw_name;const state=job._skills.covered.includes(name)?'✓ 明确掌握':job._skills.inferred.includes(name)?'≈ 相关能力推断':'△ 待补充';return `<tr><td>${esc(name)}</td><td>${esc(x.level)}</td><td>${state}</td></tr>`}).join('')||'<tr><td colspan="3">JD未明确列出技能</td></tr>'}</table><h3>其他明确条件</h3>${(job.other_explicit_conditions||[]).map(x=>`<div class="evidence">${esc(x.evidence_span)}</div>`).join('')||'<div class="evidence">无其他结构化条件</div>'}<div class="source-link">来源：<a href="${esc(source)}" target="_blank" rel="noreferrer">打开原始招聘页面 ↗</a><br><small>采集日期 ${esc(job.source?.collected_at||'')}</small></div><div class="drawer-actions"><button class="primary" data-toggle="${esc(job.job_id)}">${selected.has(job.job_id)?'移出比较':'加入比较'}</button></div>`;
  document.getElementById('drawer-backdrop').classList.remove('hidden');document.getElementById('job-drawer').classList.add('open');document.getElementById('job-drawer').setAttribute('aria-hidden','false');
}
function closeDrawer(){document.getElementById('drawer-backdrop').classList.add('hidden');document.getElementById('job-drawer').classList.remove('open');document.getElementById('job-drawer').setAttribute('aria-hidden','true');}
function toggleCompare(id){if(selected.has(id)){selected.delete(id);toast('已移出比较');}else if(selected.size>=3){toast('最多比较3个岗位');return;}else{selected.add(id);toast('已加入比较');}sessionStorage.setItem('offerlab-selected',JSON.stringify([...selected]));document.getElementById('compare-count').textContent=selected.size;search();if(document.getElementById('job-drawer').classList.contains('open'))openDrawer(id);}
function renderCompare(){
  const profile=getProfile(); const list=[...selected].map(findJob).filter(Boolean); document.getElementById('compare-empty').classList.toggle('hidden',list.length>=2);document.getElementById('compare-content').classList.toggle('hidden',list.length<2);if(list.length<2)return;
  const cols=`130px repeat(${list.length},minmax(230px,1fr))`; const rows=[
    ['工作地点',...list.map(j=>esc(j.locations.join('、')))],['基础资格',...list.map(j=>`<span class="status ${j._qualification.className}">${j._qualification.label}</span><br><small>${j._qualification.checks.map(esc).join('<br>')}</small>`)],
    ['核心职责',...list.map(j=>j.responsibilities.slice(0,4).map(x=>esc(x.normalized_label)).join('<br>'))],['你的明确优势',...list.map(j=>esc(j._skills.covered.join('、')||'暂无明确技能证据'))],['专业/可迁移优势',...list.map(j=>esc(j._skills.inferred.join('、')||'暂无能力推断'))],['需要补充',...list.map(j=>`<span class="status ${j._skills.missing.length?'risk':'pass'}">${esc(j._skills.missing.join('、')||'暂未发现')}</span>`)],
    ['来源',...list.map(j=>`<a href="${esc(j.source.url)}" target="_blank" rel="noreferrer">原始页面 ↗</a>`)],['我的决定',...list.map(j=>`<select class="decision-select" data-decision="${esc(j.job_id)}"><option>请选择</option><option>优先投递</option><option>备选</option><option>暂不投递</option></select><textarea class="decision-note" data-note="${esc(j.job_id)}" placeholder="记录理由"></textarea>`)]
  ];
  document.getElementById('compare-grid').innerHTML=`<div class="compare-row compare-head" style="grid-template-columns:${cols}"><div class="compare-cell compare-label">比较维度</div>${list.map(j=>`<div class="compare-cell"><h2>${esc(j.title)}</h2><span>${esc(j.company)}</span><br><button class="text-button" data-toggle="${esc(j.job_id)}">移除</button></div>`).join('')}</div>`+rows.map(r=>`<div class="compare-row" style="grid-template-columns:${cols}"><div class="compare-cell compare-label">${r[0]}</div>${r.slice(1).map(c=>`<div class="compare-cell">${c}</div>`).join('')}</div>`).join('');
  const allSkills=list.map(j=>new Set(j.skills.map(x=>x.normalized_name||x.raw_name)));const common=[...allSkills[0]].filter(x=>allSkills.every(s=>s.has(x)));
  document.getElementById('compare-insights').innerHTML=`<li>共同技能：${esc(common.join('、')||'未发现完全相同的明确技能')}。</li><li>${list.filter(j=>profile.locations.some(l=>j.locations.some(x=>String(x).includes(l)))).length}个岗位命中地点偏好。</li><li>建议先排除硬性资格不符，再比较职责兴趣和技能补齐成本。</li>`;
  const decisions=JSON.parse(sessionStorage.getItem('offerlab-decisions')||'{}');document.querySelectorAll('[data-decision]').forEach(el=>{el.value=decisions[el.dataset.decision]?.decision||'请选择';el.addEventListener('change',saveDecision)});document.querySelectorAll('[data-note]').forEach(el=>{el.value=decisions[el.dataset.note]?.note||'';el.addEventListener('input',saveDecision)});
}
function saveDecision(){const d=JSON.parse(sessionStorage.getItem('offerlab-decisions')||'{}');[...selected].forEach(id=>{d[id]={decision:document.querySelector(`[data-decision="${CSS.escape(id)}"]`)?.value||'请选择',note:document.querySelector(`[data-note="${CSS.escape(id)}"]`)?.value||''}});sessionStorage.setItem('offerlab-decisions',JSON.stringify(d));}
function profileFingerprint(p){return [...p.majors,...p.directions,...p.skills].join('|').toLowerCase()}
function evaluationJobs(){return scoreJobs('').filter(j=>j._qualification.className!=='fail'&&inPreferredLocations(j)).slice(0,10)}
function annotationKey(job){return `${profileFingerprint(getProfile())}:${job.job_id}`}
function persistAnnotations(){sessionStorage.setItem('offerlab-annotations',JSON.stringify(annotations))}
function renderEvaluation(){
  const list=evaluationJobs(),profile=getProfile();
  document.getElementById('evaluation-list').innerHTML=list.map((job,index)=>{const key=annotationKey(job),saved=annotations[key]||{};return `<article class="panel evaluation-card"><div class="evaluation-rank">${index+1}</div><div><div class="job-meta">${esc(job.parent_group)} · ${esc(job.company)} · ${esc(job.locations.join('、'))}</div><h2>${esc(job.title)}</h2><p><strong>系统依据：</strong>${esc(job._matchReasons.join('；')||'弱相关信号')}<br><strong>优势：</strong>${esc(job._skills.advantages.join('、')||'暂无')}　<strong>待补：</strong>${esc(job._skills.missing.join('、')||'暂未发现')}</p><textarea data-annotation-note="${esc(key)}" placeholder="可选：记录判断的关键原因">${esc(saved.note||'')}</textarea></div><div class="relevance-buttons" aria-label="${esc(job.title)}相关性"><button data-label-key="${esc(key)}" data-label="2" class="${saved.label===2?'selected high':''}">2 高度相关</button><button data-label-key="${esc(key)}" data-label="1" class="${saved.label===1?'selected medium':''}">1 一般相关</button><button data-label-key="${esc(key)}" data-label="0" class="${saved.label===0?'selected low':''}">0 不相关</button></div></article>`}).join('');
  document.querySelectorAll('[data-label-key]').forEach(el=>el.addEventListener('click',()=>saveAnnotation(el.dataset.labelKey,Number(el.dataset.label))));
  document.querySelectorAll('[data-annotation-note]').forEach(el=>el.addEventListener('input',()=>{if(annotations[el.dataset.annotationNote]){annotations[el.dataset.annotationNote].note=el.value;persistAnnotations()}}));
  const completed=list.filter(j=>Number.isInteger(annotations[annotationKey(j)]?.label)).length,counts=[0,1,2].map(n=>list.filter(j=>annotations[annotationKey(j)]?.label===n).length);
  document.getElementById('evaluation-progress').textContent=`${completed} / ${list.length}`;document.getElementById('annotation-count').textContent=completed;document.getElementById('evaluation-summary-text').textContent=`当前画像：${profile.majors.join('、')} · ${profile.directions.join('、')}。高度相关 ${counts[2]}，一般相关 ${counts[1]}，不相关 ${counts[0]}。`;document.getElementById('export-annotations').disabled=completed<list.length;
}
function saveAnnotation(key,label){const job=evaluationJobs().find(x=>annotationKey(x)===key);if(!job)return;annotations[key]={job_id:job.job_id,title:job.title,company:job.company,label,note:annotations[key]?.note||'',model_score:Number(job._score.toFixed(4)),components:job._components,profile:getProfile(),profile_fingerprint:profileFingerprint(getProfile()),annotated_at:new Date().toISOString()};persistAnnotations();renderEvaluation()}
function resetCurrentAnnotations(){const fp=profileFingerprint(getProfile());Object.keys(annotations).filter(k=>k.startsWith(`${fp}:`)).forEach(k=>delete annotations[k]);persistAnnotations();renderEvaluation();toast('已重置当前画像标注')}
function exportAnnotations(){const ranked=evaluationJobs(),records=ranked.map(j=>annotations[annotationKey(j)]).filter(Boolean);if(records.length<ranked.length)return;const payload={schema_version:'1.1',task:'profile_job_relevance',ordering:'current_model_rank',label_definition:{2:'高度相关',1:'一般相关',0:'不相关'},exported_at:new Date().toISOString(),profile:getProfile(),records};const blob=new Blob([JSON.stringify(payload,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=`offerlab-relevance-${Date.now()}.json`;a.click();URL.revokeObjectURL(url);toast('标注文件已按当前推荐顺序导出')}
function toast(message){const el=document.getElementById('toast');el.textContent=message;el.classList.add('show');setTimeout(()=>el.classList.remove('show'),1800);}

const resumeSkillLexicon=['Python','SQL','Java','C++','C语言','R','pandas','scikit-learn','TensorFlow','PyTorch','Excel','Tableau','Power BI','Axure','Figma','需求调研','需求分析','数据分析','统计分析','数据清洗','机器学习','深度学习','大模型','智能体','数据治理','产品设计','项目管理','网络安全','系统运维'];
const resumeMajorPatterns=['统计学','精算学','计算机科学与技术','软件工程','人工智能','数据科学与大数据技术','信息管理与信息系统','数学','金融学','经济学','电子信息','通信工程','自动化'];
function mergeUnique(existing,added){return [...new Set([...existing,...added].map(x=>x.trim()).filter(Boolean))];}
function extractResume(text){
  const lower=text.toLowerCase();
  const skills=resumeSkillLexicon.filter(x=>lower.includes(x.toLowerCase()));
  const majors=resumeMajorPatterns.filter(x=>text.includes(x));
  const directions=[];
  if(/产品|需求|原型|用户研究/.test(text))directions.push('AI 产品');
  if(/数据分析|统计|经营分析|商业分析/.test(text))directions.push('数据分析');
  if(/算法|机器学习|深度学习|大模型/.test(text))directions.push('算法工程');
  if(/开发|编程|软件工程|java|python/.test(lower))directions.push('软件开发');
  if(/运维|网络安全|信息安全/.test(text))directions.push(/安全/.test(text)?'网络安全':'系统运维');
  return {skills,majors,directions};
}
function applyResume(text,fileName){
  const extracted=extractResume(text);
  document.getElementById('skills').value=mergeUnique(splitList(document.getElementById('skills').value),extracted.skills).join('、');
  if(!document.getElementById('major-master').value&&extracted.majors[0])document.getElementById('major-master').value=extracted.majors[0];
  if(!document.getElementById('major-bachelor').value&&extracted.majors[1])document.getElementById('major-bachelor').value=extracted.majors[1];
  document.querySelectorAll('#direction-chips .chip').forEach(chip=>{if(extracted.directions.includes(chip.textContent.trim()))chip.classList.add('selected')});
  const experience=document.getElementById('experience'); if(!experience.value.trim())experience.value=text.slice(0,3000);
  const feedback=document.getElementById('resume-feedback'); feedback.classList.remove('hidden');feedback.textContent=`已从 ${fileName} 识别：${extracted.majors.length?`专业 ${extracted.majors.join('、')}；`:''}${extracted.skills.length?`技能 ${extracted.skills.join('、')}；`:''}${extracted.directions.length?`方向 ${extracted.directions.join('、')}`:'未识别到预设能力词，请补充项目证据。'}`;
  profileChanged();
}
function profileChanged(){
  saveProfile();renderAbilityInference(); document.getElementById('profile-version').textContent=new Date().toLocaleTimeString('zh-CN',{hour:'2-digit',minute:'2-digit'});
  if(document.getElementById('page-discover').classList.contains('active'))search();
}
let profileTimer;
function scheduleProfileChanged(){clearTimeout(profileTimer);profileTimer=setTimeout(profileChanged,180);}

document.addEventListener('click',e=>{const page=e.target.closest('[data-page]');if(page)showPage(page.dataset.page);const detail=e.target.closest('[data-detail]');if(detail)openDrawer(detail.dataset.detail);const toggle=e.target.closest('[data-toggle]');if(toggle)toggleCompare(toggle.dataset.toggle);});
document.getElementById('save-profile').addEventListener('click',()=>{saveProfile();document.getElementById('query').value='';showPage('discover');toast('画像已保存，正在按JD发现岗位');});
document.getElementById('search-button').addEventListener('click',search);document.getElementById('query').addEventListener('keydown',e=>{if(e.key==='Enter')search()});
['company-filter','location-filter','family-filter','scope-filter'].forEach(id=>document.getElementById(id).addEventListener('change',search));
document.getElementById('use-profile-query').addEventListener('click',()=>{document.getElementById('query').value='';search()});
document.getElementById('clear-search').addEventListener('click',()=>{document.getElementById('query').value='';['company-filter','location-filter','family-filter'].forEach(id=>document.getElementById(id).value='all');document.getElementById('scope-filter').value='matched';search()});
document.getElementById('close-drawer').addEventListener('click',closeDrawer);document.getElementById('drawer-backdrop').addEventListener('click',closeDrawer);
document.querySelectorAll('#direction-chips .chip').forEach(chip=>chip.addEventListener('click',()=>{chip.classList.toggle('selected');profileChanged()}));
['graduation-year','degree','major-master','major-bachelor','preferred-locations','rotation','skills','experience'].forEach(id=>{
  const el=document.getElementById(id);el.addEventListener(el.tagName==='SELECT'?'change':'input',scheduleProfileChanged);
});
document.getElementById('resume-file').addEventListener('change',event=>{const file=event.target.files?.[0];if(!file)return;const reader=new FileReader();reader.onload=()=>applyResume(String(reader.result||''),file.name);reader.onerror=()=>toast('简历读取失败，请粘贴正文');reader.readAsText(file,'utf-8')});
document.getElementById('reset-annotations').addEventListener('click',resetCurrentAnnotations);document.getElementById('export-annotations').addEventListener('click',exportAnnotations);
restoreProfile();renderAbilityInference();populateFilters();document.getElementById('corpus-count').textContent=jobs.length;document.getElementById('group-count').textContent=new Set(jobs.map(x=>x.parent_group)).size;document.getElementById('compare-count').textContent=selected.size;document.getElementById('annotation-count').textContent=Object.values(annotations).filter(x=>Number.isInteger(x.label)).length;showPage('profile');
