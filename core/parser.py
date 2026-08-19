# -*- coding:utf-8 -*-

"""
开奖数据解析
"""


import re





def parse_numbers(text):


    nums=re.findall(

        r"\d+",

        str(text)

    )


    result=[]



    for n in nums:


        n=int(n)


        if 1<=n<=49:

            result.append(n)



    return result





def parse_history_item(item):


    if not isinstance(item,dict):

        return None



    issue=(

        item.get("expect")

        or

        item.get("issue")

        or

        ""

    )



    code=(

        item.get("openCode")

        or

        item.get("numbers")

        or

        ""

    )



    nums=parse_numbers(code)



    if len(nums)<7:

        return None



    return {


        "issue":

        issue,


        "numbers":

        nums[:6],



        "special":

        nums[6]

    }
