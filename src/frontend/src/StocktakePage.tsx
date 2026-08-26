import { useMemo, useState } from 'react';
import { CheckCircle2, CircleAlert, Download, FileSpreadsheet, LoaderCircle, Search, UploadCloud, XCircle } from 'lucide-react';
import { fmtNumber, type StocktakeItem, type StocktakeResult } from './api';
import './stocktake.css';

type Filter = 'all' | 'matched' | 'mismatch' | 'positive' | 'negative' | 'missingMapping';

const filterLabels: Record<Filter, string> = {
  all: '全部',
  matched: '已对应',
  mismatch: '未对应',
  positive: '供货偏多',
  negative: '供货偏少',
  missingMapping: '缺少产品信息',
};

function statusText(row: StocktakeItem) {
  if (!row.mapping_found) return '⚠️ 缺少产品信息';
  if (row.matched) return '✅ 对应';
  return row.difference > 0 ? '❌ 供货偏多' : '❌ 供货偏少';
}

export function StocktakePage({ refreshKey }: { refreshKey: number }) {
  const [file, setFile] = useState<File | null>(null);
  const [mappingFile, setMappingFile] = useState<File | null>(null);
  const [result, setResult] = useState<StocktakeResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState<Filter>('all');

  const buildForm = (selected = file) => {
    if (!selected) return null;
    const form = new FormData();
    form.append('file', selected);
    if (mappingFile) form.append('mapping_file', mappingFile);
    return form;
  };

  const analyze = async (selected = file) => {
    const form = buildForm(selected);
    if (!form) {
      setError('请先选择供货量底表');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const response = await fetch('/api/stocktake/analyze', { method: 'POST', body: form });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail || '库存盘点失败');
      setResult(body);
    } catch (reason) {
      setResult(null);
      setError(reason instanceof Error ? reason.message : '库存盘点失败，请检查文件格式');
    } finally {
      setLoading(false);
    }
  };

  const download = async () => {
    const form = buildForm();
    if (!form) return;
    setDownloading(true);
    setError('');
    try {
      const response = await fetch('/api/stocktake/export', { method: 'POST', body: form });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail || '导出失败');
      }
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = '库存盘点明细.xlsx';
      link.click();
      URL.revokeObjectURL(url);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : '导出失败，请稍后重试');
    } finally {
      setDownloading(false);
    }
  };

  const rows = useMemo(() => {
    const needle = search.trim().toLowerCase();
    return (result?.items || []).filter(row => {
      const matchesText = !needle || [row.xiaomi_id, row.sku, row.market_name, row.spu, row.color, row.memory, row.region].join(' ').toLowerCase().includes(needle);
      const matchesStatus =
        filter === 'all' ||
        (filter === 'matched' && row.matched) ||
        (filter === 'mismatch' && !row.matched) ||
        (filter === 'positive' && row.difference > 0) ||
        (filter === 'negative' && row.difference < 0) ||
        (filter === 'missingMapping' && !row.mapping_found);
      return matchesText && matchesStatus;
    });
  }, [result, search, filter, refreshKey]);

  return <div className="stocktake-page">
    <section className="stocktake-upload panel">
      <div>
        <span>库存盘点</span>
        <h2>上传供货量底表，核对进销存是否能对上</h2>
        <p>系统会汇总供货表中相同小米 ID 的实际供货量，并用已留存的“小米ID+штрихкод+产品SKU匹配底表”补齐 SPU、颜色、内存、规格，再与库存和建店至今去退 SO 做核对。</p>
      </div>
      <label className={`stocktake-file ${file ? 'has-file' : ''}`}>
        <input type="file" accept=".xlsx,.xlsm" onChange={event => { const selected = event.target.files?.[0] || null; setFile(selected); setResult(null); setError(''); if (selected) analyze(selected); }} />
        <UploadCloud size={19} />
        <span>{file ? file.name : '选择供货量底表'}</span>
      </label>
      <label className={`stocktake-file stocktake-mapping-file ${mappingFile ? 'has-file' : ''}`}>
        <input type="file" accept=".xlsx,.xlsm" onChange={event => { const selected = event.target.files?.[0] || null; setMappingFile(selected); setResult(null); setError(''); }} />
        <UploadCloud size={19} />
        <span>{mappingFile ? mappingFile.name : '产品信息映射表（可选）'}</span>
      </label>
      <button className="stocktake-primary" onClick={() => analyze()} disabled={loading || !file}>{loading ? <><LoaderCircle className="spin" size={16}/>正在盘点</> : <><FileSpreadsheet size={16}/>开始盘点</>}</button>
    </section>

    {error && <div className="stocktake-error"><CircleAlert size={16}/>{error}</div>}

    {result && <section className="stocktake-summary">
      <div className="stocktake-card"><small>盘点 SKU</small><b>{fmtNumber(result.summary.total)}</b><span>以本次供货表为准</span></div>
      <div className="stocktake-card ok"><small>进销存对应</small><b>{fmtNumber(result.summary.matched)}</b><span>供货量 = 库存 + 建店至今 SO</span></div>
      <div className="stocktake-card danger"><small>未对应</small><b>{fmtNumber(result.summary.mismatched)}</b><span>需核对取消/退货或库存</span></div>
      <div className="stocktake-card"><small>缺少产品信息</small><b>{fmtNumber(result.summary.missing_mapping)}</b><span>{result.mapping_saved_count ? `本次已留存 ${fmtNumber(result.mapping_saved_count)} 个映射` : '可上传新品映射表补齐'}</span></div>
      <div className="stocktake-card"><small>最新库存口径</small><b>{result.inventory_date || '未上传'}</b><span>{result.snapshot_date ? `原始库存 DATE ${result.snapshot_date}` : '暂无库存快照'}</span></div>
    </section>}

    {result && <section className="panel stocktake-table-panel">
      <div className="panel-head stocktake-table-head">
        <div><h2>库存盘点明细</h2><p>差额 = 供货量 -（现有库存 + 建店至今去退 SO）；供货偏多时显示最近取消/退货记录。</p></div>
        <div className="stocktake-actions">
          <label className="search"><Search size={16}/><input value={search} onChange={event => setSearch(event.target.value)} placeholder="搜索小米ID / 条形码 / 产品SKU / SPU"/></label>
          <button onClick={download} disabled={downloading}>{downloading ? <LoaderCircle className="spin" size={16}/> : <Download size={16}/>}下载 Excel</button>
        </div>
      </div>
      <div className="stocktake-filters">{(Object.keys(filterLabels) as Filter[]).map(key => <button key={key} className={filter === key ? 'active' : ''} onClick={() => setFilter(key)}>{filterLabels[key]}</button>)}</div>
      {rows.length ? <div className="table-wrap stocktake-table-wrap"><table className="sku-table stocktake-table"><thead><tr><th>商品 / 小米ID</th><th>条形码</th><th>产品SKU</th><th>颜色 / 内存</th><th>规格</th><th>供货量</th><th>建店至今去退 SO</th><th>现有库存</th><th>取消</th><th>退货</th><th>是否对应</th><th>差额</th><th>最近取消/退货记录</th></tr></thead><tbody>{rows.map(row => <tr key={`${row.xiaomi_id}-${row.sku}`} className={row.matched ? 'matched' : 'mismatch'}><td><b>{row.spu || row.market_name || row.xiaomi_id}</b><small>小米ID：{row.xiaomi_id}</small><small>{row.category || row.group || '未分类'}</small></td><td>{row.sku || '—'}</td><td>{row.market_name || '—'}</td><td><span className="variant-stack"><b>{row.memory || '—'}</b><small>{row.color || '—'}</small></span></td><td><span className="variant-pill">{row.region || '—'}</span></td><td>{fmtNumber(row.supply)}</td><td>{fmtNumber(row.lifetime_so)}</td><td>{fmtNumber(row.inventory)}</td><td>{fmtNumber(row.cancellations)}</td><td>{fmtNumber(row.refunds)}</td><td><span className={`stocktake-status ${row.matched ? 'ok' : 'bad'}`}>{row.matched ? <CheckCircle2 size={14}/> : <XCircle size={14}/>} {statusText(row)}</span></td><td className={row.difference === 0 ? '' : row.difference > 0 ? 'positive-diff' : 'negative-diff'}>{fmtNumber(row.difference)}</td><td className="stocktake-note">{row.event_note || '—'}</td></tr>)}</tbody></table></div> : <div className="stocktake-empty">当前筛选条件下没有盘点记录</div>}
    </section>}

    {!result && !error && <section className="stocktake-empty-main"><FileSpreadsheet size={34}/><h3>上传供货量底表后开始盘点</h3><p>新增产品时，先上传产品信息映射表；系统会自动留存小米ID、条形码、SPU、颜色、内存和规格。</p></section>}
  </div>;
}
