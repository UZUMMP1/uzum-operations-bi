import { useEffect, useMemo, useState } from 'react';
import { AlertTriangle, Bot, CalendarDays, CheckCircle2, ClipboardList, Database, FileClock, LoaderCircle, MessageSquareText, Sparkles } from 'lucide-react';
import { api, fmtNumber, fmtPercent, type DailyDiagnosis, type DataQualityOverview } from './api';
import type { BusinessCategory } from './CategoryFilter';
import { DailyDiagnosisSection, WeeklyReportPage } from './DashboardPages';
import './operations-center.css';

const categoryName:Record<BusinessCategory,string>={all:'全部品类',phone:'手机',tablet:'平板',aiot:'AIOT'};
const sourceOrder:('sales'|'traffic'|'inventory')[]=['sales','traffic','inventory'];
const uploadLabel:Record<string,string>={sales:'销售',traffic:'流量',inventory:'库存'};
const changeText=(value:number|null|undefined)=>value==null?'无可比基数':`${value>=0?'上升':'下降'} ${fmtPercent(Math.abs(value))}`;

function useQuality(start:string,end:string,refreshKey:number){
  const [data,setData]=useState<DataQualityOverview|null>(null),[loading,setLoading]=useState(true),[error,setError]=useState('');
  useEffect(()=>{let active=true;setLoading(true);setError('');api<DataQualityOverview>(`/api/data-quality/overview?${new URLSearchParams({start,end})}`).then(value=>active&&setData(value)).catch(reason=>active&&setError(reason instanceof Error?reason.message:'数据质量检查失败')).finally(()=>active&&setLoading(false));return()=>{active=false}},[start,end,refreshKey]);
  return {data,loading,error};
}

export function OperationsInsightsPage({start,end,category,refreshKey,onAgent,onReports}:{start:string;end:string;category:BusinessCategory;refreshKey:number;onAgent:()=>void;onReports:()=>void}){
  const {data,loading,error}=useQuality(start,end,refreshKey);
  const [diagnosis,setDiagnosis]=useState<DailyDiagnosis|null>(null);
  useEffect(()=>{let active=true;api<DailyDiagnosis>(`/api/dashboard/daily-diagnosis?${new URLSearchParams({day:end})}`).then(value=>active&&setDiagnosis(value)).catch(()=>active&&setDiagnosis(null));return()=>{active=false}},[end,category,refreshKey]);
  const signals=useMemo(()=>diagnosis?.checks.filter(item=>item.status==='negative'||item.status==='missing').slice(0,4)??[],[diagnosis]);
  return <div className="operations-center"><section className="ops-hero"><div><span><Sparkles size={15}/>自动运营洞察</span><h2>{diagnosis?.headline||'正在检查最新经营数据'}</h2><p>{start} 至 {end} · {categoryName[category]} · 所有结论均使用统一 BI 口径</p></div><div className={`quality-score ${data?.complete?'ok':'warn'}`}>{data?.complete?<CheckCircle2 size={28}/>:<AlertTriangle size={28}/>}<b>{data?.complete?'数据可用':'需要补数'}</b><small>{data?.issues[0]?.title||'正在检查'}</small></div></section>
    {loading&&<div className="ops-loading"><LoaderCircle className="spin"/>正在执行数据质量检查</div>}{error&&<div className="ops-error">{error}</div>}
    {data&&<><section className="ops-source-grid">{sourceOrder.map(key=>{const item=data.sources[key];const rate=item.expected_days?item.covered_days/item.expected_days:null;return <article key={key}><div><Database size={18}/><b>{item.label}数据</b></div><strong>{item.expected_days?`${item.covered_days}/${item.expected_days}`:'—'}</strong><span>覆盖日期 · {rate==null?'无可比范围':fmtPercent(rate)}</span><small>记录 {fmtNumber(item.row_count)} 行 · 最新 {item.latest_date||'缺失'}</small></article>})}</section>
      <section className="ops-grid"><article className="ops-panel"><div className="ops-title"><div><h3>自动发现的问题</h3><p>上传后自动刷新，不把缺失数据当作 0</p></div><span>{data.issues.length} 项</span></div><div className="issue-list">{data.issues.map(issue=><div key={issue.code} className={issue.severity}><i>{issue.severity==='info'?<CheckCircle2 size={16}/>:<AlertTriangle size={16}/>}</i><span><b>{issue.title}</b><small>{issue.detail}</small><em>{issue.action}</em></span></div>)}</div></article>
        <article className="ops-panel"><div className="ops-title"><div><h3>今日经营信号</h3><p>自动拆解流量、转化、库存、退货和结构</p></div><span>结束日 {end}</span></div>{signals.length?<div className="signal-list">{signals.map(signal=><div key={signal.key}><span>{signal.label}</span><b>{signal.change!=null?changeText(signal.change):signal.count!=null?`${signal.count} 个`:'数据缺失'}</b><em className={signal.status}>{signal.status==='missing'?'数据受限':'需要关注'}</em></div>)}</div>:<div className="ops-empty"><CheckCircle2 size={24}/><b>当前没有需要优先处理的异常信号</b><span>仍建议查看完整 Agent 分析。</span></div>}</article>
      </section></>}
    <section className="ops-actions"><button onClick={onAgent}><Bot size={19}/><span><b>进入运营 Agent</b><small>继续追问补货、滞销、CVR 和环比原因</small></span></button><button onClick={onReports}><CalendarDays size={19}/><span><b>生成日报 / 周报</b><small>按当前日期和品类生成可复制报告</small></span></button></section>
  </div>;
}

export function ReportCenterPage({start,end,category,refreshKey}:{start:string;end:string;category:BusinessCategory;refreshKey:number}){
  const [mode,setMode]=useState<'daily'|'weekly'>('daily');
  return <div className="report-center"><section className="report-switch"><div><span><ClipboardList size={17}/>报告生成中心</span><h2>使用当前筛选条件生成标准运营报告</h2><p>日报聚焦结束日，周报/阶段报告自动对比紧邻的上一等长周期。</p></div><div><button className={mode==='daily'?'active':''} onClick={()=>setMode('daily')}><MessageSquareText size={17}/>生成日报</button><button className={mode==='weekly'?'active':''} onClick={()=>setMode('weekly')}><CalendarDays size={17}/>生成周报</button></div></section>{mode==='daily'?<DailyDiagnosisSection end={end} category={category} refreshKey={refreshKey}/>:<WeeklyReportPage start={start} end={end} refreshKey={refreshKey}/>}</div>;
}

export function DataQualityPage({start,end,refreshKey,onUpload}:{start:string;end:string;refreshKey:number;onUpload:()=>void}){
  const {data,loading,error}=useQuality(start,end,refreshKey);
  return <div className="data-quality-page">{loading&&<div className="ops-loading"><LoaderCircle className="spin"/>正在读取数据覆盖和上传历史</div>}{error&&<div className="ops-error">{error}</div>}{data&&<><section className="data-quality-head"><div><span><Database size={17}/>数据质量中心</span><h2>{data.complete?'关键数据完整，可以生成报告':'发现缺失或覆盖异常'}</h2><p>{start} 至 {end} · 检查销售、流量、库存边界快照和最近上传批次</p></div><button onClick={onUpload}>上传 / 补充数据</button></section><section className="ops-source-grid">{sourceOrder.map(key=>{const item=data.sources[key];return <article key={key}><div><Database size={18}/><b>{item.label}</b></div><strong>{fmtNumber(item.row_count)}</strong><span>所选周期记录行数</span><small>覆盖 {item.covered_days}/{item.expected_days} · 最新 {item.latest_date||'缺失'}</small></article>})}</section><section className="ops-panel data-issues"><div className="ops-title"><div><h3>异常与缺失提示</h3><p>每条问题都给出明确补救动作</p></div></div><div className="issue-list">{data.issues.map(issue=><div key={issue.code} className={issue.severity}><i>{issue.severity==='info'?<CheckCircle2 size={16}/>:<AlertTriangle size={16}/>}</i><span><b>{issue.title}</b><small>{issue.detail}</small><em>{issue.action}</em></span></div>)}</div></section><section className="ops-panel upload-history"><div className="ops-title"><div><h3>最近上传历史</h3><p>文件哈希去重；累计报表按覆盖日期安全更新</p></div><FileClock size={20}/></div>{data.uploads.length?<div className="upload-table"><div className="upload-row header"><span>类型 / 文件</span><span>时间</span><span>行数</span><span>状态</span></div>{data.uploads.map(item=><div className="upload-row" key={item.id}><span><b>{uploadLabel[item.data_type]||item.data_type}</b><small>{item.filename}</small></span><span>{new Date(item.uploaded_at).toLocaleString('zh-CN',{hour12:false})}</span><span>{fmtNumber(item.row_count)}</span><span className={item.status}>{item.status==='success'?'已入库':item.status}</span></div>)}</div>:<div className="ops-empty"><FileClock size={24}/><b>暂无上传批次</b><span>首次上传后会在这里保留审计记录。</span></div>}</section></>}</div>;
}
