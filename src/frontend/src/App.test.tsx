// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import App from './App';

vi.mock('./Chart', () => ({ Chart: () => <div data-testid="chart" /> }));

const summary = { so: 100, orders: 110, returns: 10, return_rate:10/110, gmv: 1000000, asp: 10000, uv: 1000, cvr: .1, traffic_missing: false };
const categories = {items:[{category:'手机',so:100,orders:110,gmv:1000000,uv:1000,asp:10000,cvr:.11,so_share:1,gmv_share:1},{category:'平板',so:0,orders:0,gmv:0,uv:null,asp:null,cvr:null,so_share:0,gmv_share:0},{category:'AIOT',so:0,orders:0,gmv:0,uv:null,asp:null,cvr:null,so_share:0,gmv_share:0}],total:{so:100,orders:110,gmv:1000000,uv:1000,asp:10000,cvr:.11}};
const diagnosis = {date:'2026-08-07',previous_date:'2026-08-06',direction:'decline',headline:'2026-08-07 实际销量较前一天下降 10.0%',current:summary,previous:{...summary,so:110},changes:{so:-.1,uv:-.05,cvr:0,asp:0,return_rate:.1},checks:[{key:'uv',label:'UV是否下降',status:'negative',change:-.05},{key:'cvr',label:'CVR是否下降',status:'neutral',change:0},{key:'asp',label:'ASP是否变化',status:'neutral',change:0},{key:'stockout',label:'重点SKU是否缺货',status:'positive',count:0},{key:'return_rate',label:'取消/退款率是否上升',status:'negative',change:.1},{key:'sku',label:'哪些SKU对下降贡献最大',status:'negative',count:1},{key:'category',label:'哪些品类拖累最大',status:'negative',count:1},{key:'quality',label:'数据是否完整',status:'positive'}],stockouts:[],sku_drivers:[{sku:'10001',product:'POCO Test',previous_so:20,current_so:10,delta_so:-10}],category_drivers:[{category:'手机',previous_so:20,current_so:10,delta_so:-10}],data_quality:{sales_current:true,sales_previous:true,traffic_current:true,traffic_previous:true,inventory_current:true,inventory_previous:true,complete:true}};
const trend = [{ date:'2026-08-07', so:10, orders:11, returns:1, gmv:100000, asp:10000, uv:100, cvr:.1 }];
const product = { sku:'10001', product:'POCO Test', category:'Смартфоны Android', so:10, orders:11, returns:1, gmv:100000, asp:10000, uv:100, cvr:.1, return_rate:.09, inventory:20, comparisons:{so:.1,orders:.1,gmv:.2,asp:.09,uv:-.1,cvr:.22}, dos:28 };
const psi = { snapshot_date:'2026-08-07', counts:{healthy:0,watch:0,replenish:1,slow:0}, items:[{sku:'10001',product:'POCO Test',inventory:20,lifetime_sales:120,sales_14d:14,average_sales_14d:1,sales_30d:20,dos:20,replenishment:8,status:'replenish'}] };
const inventoryHistory = { formula:'推算进货 = max(0, 今日库存 - 昨日库存 + 今日SO)', selected_sku:null, series:[{date:'2026-08-07',inventory:20,change:null,sales:10,inbound:null}], skus:[{sku:'10001',product:'POCO Test',seller_sku:'POCO-黑色-8/256-EU',memory:'8/256',color:'黑色',region:'EU'}] };
const weekly = { period:{start:'2026-08-01',end:'2026-08-07',previous_start:'2026-07-25',previous_end:'2026-07-31'}, current:summary, previous:summary, comparisons:{so:.1,orders:.1,gmv:.1,asp:0,uv:.1,cvr:0},diagnosis:{...diagnosis,current_start:'2026-08-01',current_end:'2026-08-07',previous_start:'2026-07-25',previous_end:'2026-07-31'}, hot_top10:[product],phone_top10:[product],tablet_top10:[],mobile_top10:[product],wearable_top10:[],slow_top10:psi.items,slow_phone_top10:psi.items,slow_tablet_top10:[],categories:[{category:'手机',so:10,gmv:100000,so_share:1,gmv_share:1},{category:'平板',so:0,gmv:0,so_share:0,gmv_share:0}],insights:['SO增长由测试SKU贡献。'] };
const dataQuality = {period:{start:'2026-08-01',end:'2026-08-07'},complete:false,sources:{sales:{label:'销售',covered_days:7,expected_days:7,row_count:100,latest_date:'2026-08-07',missing_dates:[]},traffic:{label:'流量',covered_days:6,expected_days:7,row_count:80,latest_date:'2026-08-06',missing_dates:['2026-08-07']},inventory:{label:'库存',covered_days:2,expected_days:2,row_count:30,latest_date:'2026-08-08',missing_dates:[]}},issues:[{severity:'warning',code:'traffic_gap',title:'流量数据缺少 1 个销售日期',detail:'缺失日期的 UV/CVR 不参与计算。',action:'补充对应日期的商品分析流量报表。'}],uploads:[{id:1,data_type:'sales',filename:'sales.xlsx',uploaded_at:'2026-08-08T10:00:00',row_count:100,status:'success',error_message:null}]};

beforeEach(() => {
  window.localStorage.clear();
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    let body: unknown = summary;
    if (url.includes('/dashboard/daily-diagnosis')) body = diagnosis;
    else if (url.includes('/sales/trend') || url.includes('/dashboard/trend')) body = trend;
    else if (url.includes('/dashboard/categories')) body = categories;
    else if (url.includes('/sales/products')) body = [product];
    else if (url.includes('/inventory/psi')) body = psi;
    else if (url.includes('/inventory/history')) body = inventoryHistory;
    else if (url.includes('/returns')) body = {trend:[{date:'2026-08-07',cancellations:1,refunds:2}],top_refunds:[{sku:'10001',product:'POCO Test',seller_sku:'POCO-黑色-8/256-EU',memory:'8/256',color:'黑色',region:'EU',refunds:2}]};
    else if (url.includes('/reports/weekly')) body = weekly;
    else if (url.includes('/data-quality/overview')) body = dataQuality;
    return { ok: true, json: async () => body } as Response;
  }));
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe('dashboard interactions', () => {
  it('switches day/week/month and opens replenishment details', async () => {
    render(<App />);
    expect(await screen.findByText('经营诊断：昨天为什么销量变化？')).toBeTruthy();
    expect(screen.getByText('2026-08-07 实际销量较前一天下降 10.0%')).toBeTruthy();
    await screen.findByText('SKU 销售表现');
    const week = screen.getByRole('button', {name:'周'});
    fireEvent.click(week);
    expect(week.className).toContain('selected');
    const month = screen.getByRole('button', {name:'月'});
    fireEvent.click(month);
    expect(month.className).toContain('selected');
    fireEvent.click(screen.getByRole('button',{name:'查看补货建议 →'}));
    await screen.findByText('库存 PSI 与补货建议');
    expect(screen.getByText('建议补货总量')).toBeTruthy();
    expect(screen.getAllByText('8').length).toBeGreaterThan(0);
  });

  it('renders real content for every sidebar analysis page', async () => {
    render(<App />);
    await screen.findByText('SKU 销售表现');
    fireEvent.click(screen.getByRole('button',{name:'销售趋势'}));
    await screen.findByText('SO 与 GMV 趋势');
    fireEvent.click(screen.getByRole('button',{name:'退货 / 取消'}));
    await screen.findByText('每日取消 / 退货趋势');
    fireEvent.click(screen.getByRole('button',{name:'库存 PSI'}));
    await screen.findByText('库存 PSI 与补货建议');
    fireEvent.click(screen.getByRole('button',{name:'日报 / 周报'}));
    await screen.findByText('报告生成中心');
    fireEvent.click(screen.getByRole('button',{name:/生成周报/}));
    await screen.findByText('环比销售分析：与上一阶段相比为什么销量变化？');
    expect(screen.getByText('SO增长由测试SKU贡献。')).toBeTruthy();
    fireEvent.click(screen.getByRole('button',{name:'手机 TOP10'}));
    await waitFor(()=>expect(screen.getAllByText('手机 TOP10').length).toBeGreaterThan(0));
  });

  it('remembers the last page and applied date range', async () => {
    const first = render(<App />);
    await screen.findByText('SKU 销售表现');
    fireEvent.click(screen.getByRole('button',{name:'销售趋势'}));
    await screen.findByText('SO 与 GMV 趋势');
    first.unmount();
    render(<App />);
    expect(await screen.findByRole('heading',{name:'销售趋势'})).toBeTruthy();
  });

  it('selects a date range by clicking a start day and an end day', async () => {
    render(<App />);
    await screen.findByText('SKU 销售表现');
    fireEvent.click(screen.getByRole('button',{name:/统计周期/}));
    expect(screen.getByText('选择统计日期')).toBeTruthy();
    fireEvent.click(screen.getAllByRole('button',{name:'2026年7月28日'})[0]);
    const endChoices=screen.getAllByRole('button',{name:'2026年8月3日'});
    fireEvent.click(endChoices[endChoices.length-1]);
    fireEvent.click(screen.getByRole('button',{name:'应用日期'}));
    await waitFor(()=>expect(screen.getByRole('button',{name:/2026-07-28.*2026-08-03/})).toBeTruthy());
  });

  it('selects the full operating period from the quick choices', async () => {
    render(<App />);
    await screen.findByText('SKU 销售表现');
    fireEvent.click(screen.getByRole('button',{name:/统计周期/}));
    fireEvent.click(screen.getByRole('button',{name:'建店至今'}));
    expect(screen.getAllByText('2026-07-01').length).toBeGreaterThan(0);
    expect((screen.getByRole('button',{name:'应用日期'}) as HTMLButtonElement).disabled).toBe(false);
  });

  it('applies the selected category to dashboard requests', async () => {
    render(<App />);
    await screen.findByText('SKU 销售表现');
    fireEvent.click(screen.getByRole('button',{name:'品类范围'}));
    fireEvent.click(screen.getByRole('option',{name:'手机智能手机'}));
    await waitFor(()=>expect(vi.mocked(fetch).mock.calls.some(([input])=>String(input).includes('category=phone'))).toBe(true));
  });

  it('runs the free rule-based Agent and renders the unified result', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText}});
    render(<App />);
    await screen.findByText('SKU 销售表现');
    fireEvent.click(screen.getByRole('button',{name:/运营 Agent/}));
    await screen.findByText('把经营数据变成可以直接执行的结论');
    expect(screen.getAllByText(/昨天为什么销量变化/).length).toBeGreaterThan(0);
    fireEvent.click(screen.getByRole('button',{name:/开始分析/}));
    await screen.findByText('昨日销量变化诊断');
    expect(screen.getByText('核心指标')).toBeTruthy();
    expect(screen.getByText('主要原因')).toBeTruthy();
    expect(screen.getByText('关键 SKU')).toBeTruthy();
    expect(screen.getByText('关键品类')).toBeTruthy();
    expect(screen.getByText('数据完整性')).toBeTruthy();
    expect(screen.getByText('建议动作')).toBeTruthy();
    expect(screen.getByText('数据口径与日期范围')).toBeTruthy();
    fireEvent.click(screen.getByRole('button',{name:/复制为群消息/}));
    await waitFor(()=>expect(writeText).toHaveBeenCalledOnce());
  });

  it('shows automatic insights, data gaps and upload history', async () => {
    render(<App />);
    await screen.findByText('SKU 销售表现');
    fireEvent.click(screen.getByRole('button',{name:/运营洞察/}));
    await screen.findByText('自动发现的问题');
    expect(screen.getAllByText('流量数据缺少 1 个销售日期').length).toBeGreaterThan(0);
    fireEvent.click(screen.getByRole('button',{name:'数据质量'}));
    await screen.findByText('最近上传历史');
    expect(screen.getByText('sales.xlsx')).toBeTruthy();
  });
});
