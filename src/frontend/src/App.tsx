import { useEffect, useState } from 'react';
import { Activity, BarChart3, Bot, Boxes, CheckCircle2, CircleAlert, ClipboardCheck, Database, FileText, FileUp, LayoutDashboard, LoaderCircle, RotateCcw, ShieldCheck, UploadCloud, X } from 'lucide-react';
import { DailyDiagnosisSection, InventoryPage, OverviewPage, ReturnsPage, SalesTrendPage } from './DashboardPages';
import { DateRangePicker } from './DateRangePicker';
import { CategoryFilter, type BusinessCategory } from './CategoryFilter';
import { setApiCategory } from './api';
import { AgentPage } from './AgentPage';
import { StocktakePage } from './StocktakePage';
import { DataQualityPage, OperationsInsightsPage, ReportCenterPage } from './OperationsCenter';
import './functional.css';
import './date-range.css';
import './agent-nav.css';

type PageName = '经营总览'|'销售趋势'|'退货 / 取消'|'库存 PSI'|'库存盘点'|'运营洞察'|'运营 Agent'|'日报 / 周报'|'经营环比分析'|'数据质量'|'数据上传';
const todayInShanghai = new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Shanghai', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date());
const viewStorageKey = 'uzum-bi-view';
const pageNames: PageName[] = ['经营总览','销售趋势','退货 / 取消','库存 PSI','库存盘点','运营洞察','运营 Agent','日报 / 周报','经营环比分析','数据质量','数据上传'];

function loadViewState() {
  const fallback = {active:'经营总览' as PageName,start:'2026-07-01',end:todayInShanghai,category:'all' as BusinessCategory};
  try {
    const saved = JSON.parse(window.localStorage.getItem(viewStorageKey) || '{}') as {active?:string;start?:string;end?:string;category?:BusinessCategory};
    const legacyActive = saved.active === '经营周报'||saved.active === '经营环比分析' ? '日报 / 周报' : saved.active;
    return {
      active: pageNames.includes(legacyActive as PageName) && legacyActive !== '数据上传' ? legacyActive as PageName : fallback.active,
      start: saved.start || fallback.start,
      end: saved.end || fallback.end,
      category: ['all','phone','tablet','aiot'].includes(saved.category||'') ? saved.category as BusinessCategory : fallback.category,
    };
  } catch {
    return fallback;
  }
}

function FileField({label,required,file,onChange,hint}:{label:string;required?:boolean;file:File|null;onChange:(file:File|null)=>void;hint:string}) { return <label className={`file-field ${file?'has-file':''}`}><input type="file" accept=".xlsx,.xlsm" onChange={event=>onChange(event.target.files?.[0]??null)}/><div className="file-icon">{file?<CheckCircle2 size={20}/>:<UploadCloud size={20}/>}</div><div><b>{label}{required&&<em> 必传</em>}</b><span>{file?file.name:hint}</span></div><span className="choose">{file?'重新选择':'选择文件'}</span></label>; }

function UploadModal({open,onClose,onSuccess}:{open:boolean;onClose:()=>void;onSuccess:(message:string)=>void}) {
  const [sales,setSales]=useState<File|null>(null),[inventory,setInventory]=useState<File|null>(null),[traffic,setTraffic]=useState<File|null>(null); const [inventoryDate,setInventoryDate]=useState(new Date().toISOString().slice(0,10)); const [loading,setLoading]=useState(false),[error,setError]=useState('');
  useEffect(()=>{if(open)setError('')},[open]); if(!open)return null;
  const submit=async()=>{if(!sales){setError('请选择销售底表。重复的销售文件会自动跳过，但销售文件仍需选择。');return} setLoading(true);setError('');const form=new FormData();form.append('sales',sales);if(inventory){form.append('inventory',inventory);form.append('inventory_date',inventoryDate)}if(traffic)form.append('traffic',traffic);try{const response=await fetch('/api/uploads',{method:'POST',body:form});const result=await response.json();if(!response.ok)throw new Error(result.detail||'上传失败');const success=result.files.filter((item:{status:string})=>item.status==='success');const skipped=result.files.filter((item:{status:string})=>item.status==='skipped');const labels:Record<string,string>={sales:'销售',inventory:'库存',traffic:'流量'};const parts=[];if(success.length)parts.push(`成功导入 ${success.map((item:{type:string;rows:number})=>`${labels[item.type]||item.type} ${item.rows} 行`).join('、')}`);if(skipped.length)parts.push(`已跳过重复文件：${skipped.map((item:{type:string})=>labels[item.type]||item.type).join('、')}`);onSuccess(parts.join('；')||'上传完成');onClose()}catch(reason){const message=reason instanceof Error?reason.message:'上传失败，请检查文件格式';setError(/sqlite|sqlalchemy|unique constraint|insert into|\[sql:/i.test(message)?'数据与已保存记录重复，系统没有重复写入。请重新点击上传，同日库存和流量会自动更新。':message)}finally{setLoading(false)}};
  return <div className="modal-backdrop" onMouseDown={event=>event.target===event.currentTarget&&onClose()}><div className="modal"><div className="modal-head"><div><h2>上传每日数据</h2><p>重复文件自动跳过，累计库存表按 DATE 更新历史</p></div><button onClick={onClose} aria-label="关闭"><X size={19}/></button></div><div className="modal-body"><FileField label="销售底表" required file={sales} onChange={file=>{setSales(file);setError('')}} hint="UZUM 销售明细"/><FileField label="库存底表" file={inventory} onChange={file=>{setInventory(file);setError('')}} hint="可选，支持从 7/27 至今的多日库存历史"/>{inventory&&<label className="snapshot"><span>备用快照日期（仅无 DATE 列时使用）</span><input type="date" value={inventoryDate} onChange={event=>setInventoryDate(event.target.value)}/></label>}<FileField label="流量底表" file={traffic} onChange={file=>{setTraffic(file);setError('')}} hint="可选，UZUM 商品分析报表"/><div className="field-help"><Database size={15}/><span>库存表有 DATE 列时自动逐日保存；重传累计文件会更新覆盖日期，不会重复累计。</span></div>{error&&<div className="upload-error"><CircleAlert size={15}/>{error}</div>}</div><div className="modal-actions"><button className="cancel" onClick={onClose}>取消</button><button className="submit" onClick={submit} disabled={loading}>{loading?<><LoaderCircle className="spin" size={16}/>正在导入</>:<><FileUp size={16}/>上传并更新 Dashboard</>}</button></div></div></div>;
}

const pageDescriptions:Record<PageName,string>={经营总览:'核心经营指标与库存健康概览',销售趋势:'按 SKU 查看 SO、GMV、UV、CVR 与 ASP', '退货 / 取消':'监控每日取消、退货趋势和独立 TOP SKU','库存 PSI':'查看库存历史、DOS 与明确补货量','库存盘点':'上传供货量底表，核对供货、销售和库存是否对应','运营洞察':'自动发现经营变化、数据风险和下一步动作','运营 Agent':'用固定规则回答经营问题，所有结论均可追溯','日报 / 周报':'按当前日期和品类生成标准运营报告',经营环比分析:'选择任意时段，自动对比等长上期并分析变化原因',数据质量:'检查数据覆盖、缺失异常和最近上传历史',数据上传:'上传销售、库存和流量历史数据'};

export default function App(){
  const [initialView] = useState(loadViewState);
  const [active,setActive]=useState<PageName>(initialView.active);const [start,setStart]=useState(initialView.start),[end,setEnd]=useState(initialView.end);const [category,setCategory]=useState<BusinessCategory>(initialView.category);const [draftStart,setDraftStart]=useState(initialView.start),[draftEnd,setDraftEnd]=useState(initialView.end);const [dateOpen,setDateOpen]=useState(false),[uploadOpen,setUploadOpen]=useState(false);const [toast,setToast]=useState(''),[refreshKey,setRefreshKey]=useState(0);
  useEffect(()=>{if(!toast)return;const timer=window.setTimeout(()=>setToast(''),5200);return()=>clearTimeout(timer)},[toast]);
  useEffect(()=>{window.localStorage.setItem(viewStorageKey,JSON.stringify({active,start,end,category}))},[active,start,end,category]);
  useEffect(()=>{setRefreshKey(key=>key+1)},[category]);
  const applyDates=()=>{if(!draftStart||!draftEnd||draftStart>draftEnd){setToast('开始日期不能晚于结束日期');return}setStart(draftStart);setEnd(draftEnd);setDateOpen(false)};const openUpload=()=>setUploadOpen(true);const uploadSuccess=(message:string)=>{setToast(message);setRefreshKey(key=>key+1)};
  const selectPage=(page:PageName)=>{if(page==='数据上传')openUpload();else setActive(page)};
  setApiCategory(category);
  let content;if(active==='销售趋势')content=<SalesTrendPage start={start} end={end} category={category} refreshKey={refreshKey}/>;else if(active==='退货 / 取消')content=<ReturnsPage start={start} end={end} category={category} refreshKey={refreshKey}/>;else if(active==='库存 PSI')content=<InventoryPage start={start} end={end} category={category} refreshKey={refreshKey} onUpload={openUpload}/>;else if(active==='库存盘点')content=<StocktakePage refreshKey={refreshKey}/>;else if(active==='运营洞察')content=<OperationsInsightsPage start={start} end={end} category={category} refreshKey={refreshKey} onAgent={()=>setActive('运营 Agent')} onReports={()=>setActive('日报 / 周报')}/>;else if(active==='运营 Agent')content=<AgentPage start={start} end={end} category={category} refreshKey={refreshKey}/>;else if(active==='日报 / 周报'||active==='经营环比分析')content=<ReportCenterPage start={start} end={end} category={category} refreshKey={refreshKey}/>;else if(active==='数据质量')content=<DataQualityPage start={start} end={end} refreshKey={refreshKey} onUpload={openUpload}/>;else content=<><DailyDiagnosisSection end={end} category={category} refreshKey={refreshKey}/><OverviewPage start={start} end={end} category={category} refreshKey={refreshKey} onInventory={()=>setActive('库存 PSI')} onUpload={openUpload}/></>;
  return <div className="app">
    <aside>
      <div className="brand"><div className="brand-mark">U</div><div><b>UZUM</b><span>运营数据中心</span></div></div>
      <nav><p>数据驾驶舱</p>{[[LayoutDashboard,'经营总览'],[BarChart3,'销售趋势'],[RotateCcw,'退货 / 取消'],[Boxes,'库存 PSI'],[ClipboardCheck,'库存盘点']].map(([Icon,label])=><button key={label as string} className={active===label?'active':''} onClick={()=>selectPage(label as PageName)}><Icon size={18}/>{label as string}</button>)}<p>智能分析</p><button onClick={()=>selectPage('运营洞察')} className={active==='运营洞察'?'active':''}><Activity size={18}/>运营洞察<span className="nav-new">NEW</span></button><button onClick={()=>selectPage('运营 Agent')} className={active==='运营 Agent'?'active':''}><Bot size={18}/>运营 Agent</button><p>报告中心</p><button onClick={()=>selectPage('日报 / 周报')} className={active==='日报 / 周报'||active==='经营环比分析'?'active':''}><FileText size={18}/>日报 / 周报</button><p>数据管理</p><button onClick={()=>selectPage('数据质量')} className={active==='数据质量'?'active':''}><ShieldCheck size={18}/>数据质量</button><button onClick={openUpload}><FileUp size={18}/>数据上传</button></nav>
      <div className="sidebar-foot"><span className="status-dot"/>云端数据库已连接<small>历史数据统一保存，重新打开无需上传</small></div>
    </aside>
    <main>
      <header><div><h1>{active}</h1><p>{pageDescriptions[active]}</p></div><div className="header-actions"><DateRangePicker start={start} end={end} draftStart={draftStart} draftEnd={draftEnd} open={dateOpen} onToggle={()=>setDateOpen(value=>!value)} onStartChange={setDraftStart} onEndChange={setDraftEnd} onApply={applyDates}/><CategoryFilter value={category} onChange={setCategory}/><button className="upload" onClick={openUpload}><FileUp size={16}/>上传数据</button><div className="avatar">UZ</div></div></header>
      {content}
    </main>
    <UploadModal open={uploadOpen} onClose={()=>setUploadOpen(false)} onSuccess={uploadSuccess}/>
    {toast&&<div className="toast"><CheckCircle2 size={17}/>{toast}</div>}
  </div>;
}
