export type Summary = { so: number; orders: number; returns: number; return_rate?: number | null; gmv: number; asp: number | null; uv: number | null; cvr: number | null; traffic_missing: boolean };
export type Trend = { date: string; so: number; orders: number; returns: number; gmv: number; asp: number | null; uv: number | null; cvr: number | null };
export type SkuIdentity = { sku: string; product: string | null; seller_sku?: string | null; color?: string | null; memory?: string | null; region?: string | null };
export type Product = SkuIdentity & { category: string | null; so: number; orders: number; returns: number; gmv: number; asp: number | null; uv: number | null; cvr: number | null; return_rate: number | null; inventory: number | null; comparisons?:Partial<Record<'so'|'orders'|'gmv'|'asp'|'uv'|'cvr',number|null>>; dos?: number | null; average_sales_14d?: number; sales_30d?: number; stock_status?: PsiItem['status'] };
export type PsiItem = SkuIdentity & { inventory: number; lifetime_sales: number; sales_14d: number; average_sales_14d: number; sales_30d: number; dos: number | null; replenishment: number; status: 'healthy'|'watch'|'replenish'|'slow' };
export type PsiResponse = { snapshot_date: string | null; counts: Record<string, number>; items: PsiItem[] };
export type InventoryHistoryResponse = { formula:string; selected_sku:string|null; series:{date:string;inventory:number|null;change:number|null;sales:number;inbound:number|null}[]; skus:SkuIdentity[] };
export type ReturnsResponse = {
  trend: { date: string; cancellations: number; refunds: number }[];
  top_cancellations: (SkuIdentity & { cancellations: number })[];
  top_refunds: (SkuIdentity & { refunds: number })[];
};
export type WeeklyReport = { period: { start:string;end:string;previous_start:string;previous_end:string }; current: Summary; previous: Summary; comparisons: Record<string,number|null>; diagnosis:DailyDiagnosis; hot_top10: Product[]; phone_top10: Product[]; tablet_top10: Product[]; mobile_top10: Product[]; wearable_top10: Product[]; slow_top10: PsiItem[]; slow_phone_top10: PsiItem[]; slow_tablet_top10: PsiItem[]; categories: {category:string;so:number;gmv:number;so_share:number|null;gmv_share:number|null}[]; insights:string[] };
export type CategorySummary = { items:{category:string;so:number;orders:number;gmv:number;uv:number|null;asp:number|null;cvr:number|null;so_share:number|null;gmv_share:number|null}[]; total:{so:number;orders:number;gmv:number;uv:number|null;asp:number|null;cvr:number|null} };
export type DailyDiagnosis = {
  date:string;
  previous_date:string;
  current_start?:string;
  current_end?:string;
  previous_start?:string;
  previous_end?:string;
  direction:'decline'|'growth'|'flat'|'missing';
  headline:string;
  current:Summary;
  previous:Summary;
  changes:Record<string,number|null>;
  checks:{key:string;label:string;status:'positive'|'negative'|'neutral'|'missing';current?:number|null;previous?:number|null;change?:number|null;count?:number}[];
  stockouts:(SkuIdentity & {previous_so:number;current_so:number;inventory:number})[];
  sku_drivers:(SkuIdentity & {previous_so:number;current_so:number;delta_so:number})[];
  category_drivers:{category:string;previous_so:number;current_so:number;delta_so:number}[];
  data_quality:Record<string,boolean> & {complete:boolean};
};

export type AgentQuestion = 'daily_change'|'replenishment'|'slow_stock'|'cvr_decline'|'period_compare';
export type AgentResult = {
  question:AgentQuestion;
  title:string;
  headline:string;
  summary:string;
  metrics:{label:string;value:string;change?:number|null;note?:string}[];
  reasons:string[];
  skus:(SkuIdentity & {detail:string;value?:string;tone?:'danger'|'positive'|'neutral'})[];
  categories:{name:string;detail:string;value:string}[];
  quality:{label:string;ok:boolean;detail:string}[];
  actions:string[];
  scope:string;
  methodology:string[];
};
export type StocktakeItem = {
  group:string;
  category:string;
  xiaomi_id:string;
  sku:string;
  market_name:string;
  spu:string;
  color:string;
  memory:string;
  region:string;
  mapping_found:boolean;
  supply:number;
  lifetime_so:number;
  inventory:number;
  cancellations:number;
  refunds:number;
  matched:boolean;
  difference:number;
  event_note:string;
};
export type StocktakeResult = {
  snapshot_date:string|null;
  inventory_date:string|null;
  mapping_saved_count:number;
  summary:{total:number;matched:number;mismatched:number;positive:number;negative:number;missing_mapping:number;total_supply:number;total_expected:number;total_difference:number};
  items:StocktakeItem[];
};
export type UploadBatchSummary = {
  id:number;
  data_type:'sales'|'inventory'|'traffic'|string;
  filename:string;
  uploaded_at:string;
  row_count:number;
  status:string;
  error_message:string|null;
};
export type DataQualitySource = {
  label:string;
  covered_days:number;
  expected_days:number;
  row_count:number;
  latest_date:string|null;
  missing_dates:string[];
};
export type DataQualityOverview = {
  period:{start:string;end:string};
  complete:boolean;
  sources:Record<'sales'|'traffic'|'inventory',DataQualitySource>;
  issues:{severity:'critical'|'warning'|'info';code:string;title:string;detail:string;action:string}[];
  uploads:UploadBatchSummary[];
};

let activeCategory = 'all';
export const setApiCategory = (category:string) => { activeCategory = category; };

export async function api<T>(path: string): Promise<T> {
  let requestPath = path;
  if (activeCategory !== 'all' && path.startsWith('/api/') && !/[?&]category=/.test(path)) {
    requestPath += `${path.includes('?')?'&':'?'}category=${encodeURIComponent(activeCategory)}`;
  }
  const response = await fetch(requestPath);
  if (!response.ok) { const body = await response.json().catch(()=>({})); throw new Error(body.detail || '数据加载失败'); }
  return response.json() as Promise<T>;
}

export const fmtNumber = (value: number | null, digits = 0) => value == null ? '—' : new Intl.NumberFormat('zh-CN',{maximumFractionDigits:digits}).format(value);
export const fmtMoney = (value: number | null) => value == null ? '—' : `${fmtNumber(value)} UZS`;
export const fmtPercent = (value: number | null, digits = 1) => value == null ? '—' : `${(value*100).toFixed(digits)}%`;
