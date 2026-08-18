# -*- coding: utf-8 -*-
"""历史数据质量检查。"""
from .config import ALL_NUMBERS


def validate_row(row):
    errors=[]; warnings=[]
    try:
        special=int(row.get("special"))
    except Exception:
        return {"valid":False,"errors":["special无效"],"warnings":[]}
    if special not in ALL_NUMBERS: errors.append("special不在1~49")
    nums=row.get("numbers",[])
    if not isinstance(nums,list) or len(nums)!=6: errors.append("numbers不是6个号码")
    else:
        try: nums=[int(x) for x in nums]
        except Exception: nums=[]; errors.append("numbers含非整数")
        if len(nums)==6 and (len(set(nums))!=6 or not all(1<=x<=49 for x in nums)): errors.append("numbers存在重复或越界")
        if nums and special in nums: errors.append("special与正码重复")
    return {"valid":not errors,"errors":errors,"warnings":warnings}


def deduplicate_history(rows):
    seen=set(); out=[]
    for row in rows:
        issue=str(row.get("issue",row.get("issue_no",""))).strip()
        if not issue or issue in seen: continue
        seen.add(issue); out.append(row)
    return out


def clean_history(rows):
    rows=deduplicate_history(rows)
    valid=[]; invalid=[]; warnings=[]
    for i,row in enumerate(rows):
        q=validate_row(row)
        if q["valid"]: valid.append(row)
        else: invalid.append({"index":i,"issue":row.get("issue",row.get("issue_no")),"errors":q["errors"]})
        warnings.extend(q["warnings"])
    try: valid.sort(key=lambda r:int(str(r.get("issue",r.get("issue_no","0")))), reverse=True)
    except Exception: pass
    return valid,{"valid":len(valid),"invalid":len(invalid),"warnings":len(warnings),"invalid_rows":invalid}
