# -*- coding: utf-8 -*-
import json,re,ssl,urllib.request
from datetime import datetime
from collections import defaultdict
from .config import API_HISTORY,API_REALTIME,DB_FILES,LOTTERY_NAMES
from .database import connect_db,init_db,save_draw

def http_json(url,timeout=20):
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 MarkSix-AI-V3.0','Accept':'application/json,text/plain,*/*'})
    try:
        with urllib.request.urlopen(req,timeout=timeout,context=ssl.create_default_context()) as r:return json.loads(r.read().decode('utf-8-sig'))
    except Exception as e:
        if 'marksix6.net' not in url: raise
        print('⚠️ 正常SSL验证失败：',e); print('尝试受控SSL fallback...')
        with urllib.request.urlopen(req,timeout=timeout,context=ssl._create_unverified_context()) as r:
            print('✅ SSL fallback成功'); return json.loads(r.read().decode('utf-8-sig'))

def parse_numbers(v):
    if isinstance(v,list):
        a=[]
        for x in v:
            if isinstance(x,dict):x=x.get('number') or x.get('num') or x.get('value')
            try:n=int(x)
            except:continue
            if 1<=n<=49:a.append(n)
        return a
    return [int(x) for x in re.findall(r'\d{1,2}',str(v or '')) if 1<=int(x)<=49]

def identify(item):
    t=(str(item.get('name',''))+' '+str(item.get('type') or item.get('code') or item.get('lottery') or '')).lower()
    if 'newmacau' in t or '新澳门' in t:return 'newMacau'
    if 'oldmacau' in t or '老澳门' in t:return 'oldMacau'
    if 'hk'==str(item.get('type','')).lower() or '香港' in t:return 'hk'

def sync_all():
    payload=http_json(API_HISTORY); data=payload.get('lottery_data',[]) if isinstance(payload,dict) else []
    added={k:0 for k in DB_FILES}
    for item in data:
        key=identify(item)
        if key not in DB_FILES: continue
        hist=item.get('history',[])
        conn=connect_db(DB_FILES[key]); init_db(conn)
        for raw in hist:
            m=re.search(r'(\d{3,})\s*期?[：:]\s*(.*)',str(raw))
            if not m:continue
            nums=parse_numbers(m.group(2))
            if len(nums)<7:continue
            date=str(item.get('openTime') or '')[:10] or datetime.now().strftime('%Y-%m-%d')
            if save_draw(conn,m.group(1),date,nums[:6],nums[6],'history_api')=='inserted':added[key]+=1
        conn.close()
    for key in DB_FILES:
        try:
            p=http_json(f'{API_REALTIME}?type={key}'); candidates=p.get('lottery_data',[]) if isinstance(p,dict) else []
            if isinstance(p,dict): candidates += [p]
            for item in candidates:
                if identify(item) not in (None,key):continue
                issue=str(item.get('expect') or item.get('issue') or item.get('issueNo') or '')
                nums=parse_numbers(item.get('openCode') or item.get('numbers') or '')
                if issue and len(nums)>=7:
                    conn=connect_db(DB_FILES[key]); init_db(conn); st=save_draw(conn,issue,str(item.get('openTime') or '')[:10],nums[:6],nums[6],'realtime_api'); conn.close();
                    if st=='inserted':added[key]+=1
                    break
        except Exception as e: print(f'⚠️ {LOTTERY_NAMES[key]}实时同步失败：{e}')
    return added
