import { Check, ChevronDown, Layers3 } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';

export type BusinessCategory = 'all' | 'phone' | 'tablet' | 'aiot';

const categories:{value:BusinessCategory;label:string;description:string}[] = [
  {value:'all',label:'全部品类',description:'手机、平板与 AIOT'},
  {value:'phone',label:'手机',description:'智能手机'},
  {value:'tablet',label:'平板',description:'平板电脑'},
  {value:'aiot',label:'AIOT',description:'可穿戴及智能设备'},
];

export function CategoryFilter({value,onChange}:{value:BusinessCategory;onChange:(value:BusinessCategory)=>void}) {
  const [open,setOpen]=useState(false);
  const root=useRef<HTMLDivElement>(null);
  const selected=categories.find(item=>item.value===value) || categories[0];
  useEffect(()=>{const close=(event:MouseEvent)=>{if(!root.current?.contains(event.target as Node))setOpen(false)};document.addEventListener('mousedown',close);return()=>document.removeEventListener('mousedown',close)},[]);
  return <div className="category-filter-wrap" ref={root}>
    <button className={`category-filter ${open?'open':''}`} aria-label="品类范围" aria-expanded={open} onClick={()=>setOpen(current=>!current)}>
      <Layers3 size={18}/><span><small>品类范围</small><b>{selected.label}</b></span><ChevronDown size={16}/>
    </button>
    {open&&<div className="category-menu" role="listbox" aria-label="选择品类范围">
      <div className="category-menu-title"><b>选择品类范围</b><small>所选品类将应用到全部分析</small></div>
      {categories.map(item=><button role="option" aria-selected={item.value===value} key={item.value} onClick={()=>{onChange(item.value);setOpen(false)}}><span><b>{item.label}</b><small>{item.description}</small></span>{item.value===value&&<Check size={17}/>}</button>)}
    </div>}
  </div>;
}
